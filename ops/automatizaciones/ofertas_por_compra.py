"""Ofertas personalizadas según compras del cliente.

Para cada cliente con email y ``recibe_ofertas_email`` cruza sus compras
(facturas ``codigo = 'F'`` del ERP en los últimos ``--dias-compras`` días)
con las ofertas vigentes del portal (``api_articulos.oferta = 'S'`` con
stock y no discontinuadas) y le escribe ofreciéndole las suyas.

Reglas anti-saturación (igual que oportunidades_miro_no_compro):
- un mail por cliente cada ``CLIENTE_COOLDOWN_DIAS``;
- el mismo artículo no se repite hasta ``ARTICULO_COOLDOWN_DIAS``;
- hasta ``MAX_ARTICULOS_MAIL`` artículos por mail.

Cada artículo ofrecido queda en ``api_ofertaenviada`` (``consultas`` guarda
las veces que lo compró en la ventana). El envío va por la cola
``<FE_DB_NAME>.emails_pendientes``.

Uso:
    ofertas_por_compra.py --dry-run            # muestra lo que mandaría
    ofertas_por_compra.py --to otro@ejemplo.com --dry-run
    ofertas_por_compra.py --enviar              # encola de verdad + reporte

Los clientes sin compras en oferta reciben un fallback grupal con las
``--top`` ofertas destacadas (próximas a vencer primero).
"""

from __future__ import annotations

import argparse
import os
import re
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
UTC = ZoneInfo("UTC")

DEFAULT_DIAS_COMPRAS = 90
DEFAULT_TOP_FALLBACK = 5
CLIENTE_COOLDOWN_DIAS = 7
ARTICULO_COOLDOWN_DIAS = 30
MAX_ARTICULOS_MAIL = 5
EMPRESA_ID = 1
QUIEN_ENVIA = "ventas@ferreteriaavenida.com.ar"
PORTAL_URL = "https://ventas.ferreteriaavenida.com.ar/productos?oferta=1"
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_IDENT_RE = re.compile(r"^[A-Za-z0-9_]+$")


def _qualified(env_var: str, default_db: str, name: str) -> str:
    db = os.environ.get(env_var, default_db).strip()
    if not _IDENT_RE.match(db) or not _IDENT_RE.match(name):
        raise ValueError(f"nombre de base/tabla inválido: {db!r}.{name!r}")
    return f"`{db}`.`{name}`"


def fasa_table(name: str = "facturas") -> str:
    return _qualified("FASA_DB_NAME", "fasa", name)


def fe_table(name: str = "emails_pendientes") -> str:
    return _qualified("FE_DB_NAME", "fe", name)


def sanitizar_latin1(texto: str) -> str:
    normalizado = unicodedata.normalize("NFC", str(texto))
    return normalizado.encode("latin1", errors="replace").decode("latin1")


def _to_local_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        aware = value if value.tzinfo else value.replace(tzinfo=UTC)
        return aware.astimezone(LOCAL_TZ).date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text or text.startswith("0000"):
        return None
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values


def _load_runtime_local(env_path: Path) -> dict[str, Any]:
    """Conexión directa con las credenciales del backend (para probar local)."""
    import pymysql

    env = _read_env(env_path)
    for key in ("FASA_DB_NAME", "FE_DB_NAME"):
        if env.get(key) and key not in os.environ:
            os.environ[key] = env[key]
    conn = pymysql.connect(
        host=env.get("DB_HOST") or "localhost",
        port=int(env.get("DB_PORT") or 3306),
        user=env["DB_USER"],
        password=env.get("DB_PASSWORD", ""),
        database=env["DB_NAME"],
        charset="utf8mb4",
        autocommit=True,
    )

    def query(sql: str, params: tuple[Any, ...]) -> list[tuple[Any, ...]]:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())

    def execute_batch(statements: list[tuple[str, tuple[Any, ...]]]) -> None:
        conn.begin()
        try:
            with conn.cursor() as cur:
                for sql, params in statements:
                    cur.execute(sql, params)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    return {"query": query, "execute_batch": execute_batch}


def _placeholders(n: int) -> str:
    return ", ".join(["%s"] * n)


def fetch_candidatos(
    runtime: dict[str, Any],
    *,
    dias_compras: int = DEFAULT_DIAS_COMPRAS,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Cruza compras recientes del ERP con ofertas vigentes del portal."""
    now = now or datetime.now(LOCAL_TZ)
    q = runtime["query"]
    desde = (now.astimezone(LOCAL_TZ).date()
             - timedelta(days=int(dias_compras))).isoformat()

    compras = q(
        f"SELECT cliente, clave, COUNT(*), MAX(fecha) FROM {fasa_table()} "
        "WHERE codigo = 'F' AND fecha >= %s "
        "GROUP BY cliente, clave",
        (desde,),
    )
    por_numero: dict[str, list[dict[str, Any]]] = {}
    for numero, clave, veces, ultima in compras:
        numero = str(numero or "").strip()
        clave = str(clave or "").strip()
        if not numero or not clave:
            continue
        por_numero.setdefault(numero, []).append({
            "clave": clave,
            "veces": int(veces or 0),
            "ultima_compra": _to_local_date(ultima),
        })
    if not por_numero:
        return []

    numeros = sorted(por_numero)
    try:
        clientes = q(
            "SELECT ac.id, ac.numero_cliente, ac.nombre, COALESCE(au.email, ''), "
            "ac.recibe_ofertas_email FROM api_cliente ac "
            "JOIN auth_user au ON au.id = ac.user_id "
            f"WHERE ac.numero_cliente IN ({_placeholders(len(numeros))})",
            (*numeros,),
        )
    except Exception as exc:  # noqa: BLE001
        if "recibe_ofertas_email" not in str(exc):
            raise
        print("AVISO: falta la migración 0041 (recibe_ofertas_email); "
              "no se enviarán mails a clientes.")
        return []

    ofertas = q(
        "SELECT clave, nombre, vencimiento_oferta FROM api_articulos "
        "WHERE empresa_id = %s AND oferta = 'S' "
        "AND COALESCE(discontinuado, '') != 'S' "
        "AND COALESCE(stock_efectivo, stock, 0) > 0",
        (EMPRESA_ID,),
    )
    en_oferta = {}
    for clave, nombre, vence in ofertas:
        clave = str(clave or "").strip()
        if not clave:
            continue
        en_oferta[clave] = {
            "nombre": _limpiar_nombre(str(nombre or "").strip()),
            "vence": _fmt_fecha(_to_local_date(vence)),
        }

    candidatos: list[dict[str, Any]] = []
    for cliente_id, numero, nombre, email, recibe in clientes:
        numero = str(numero or "").strip()
        email = str(email or "").strip()
        if not recibe or not _EMAIL_RE.match(email):
            continue
        articulos = []
        for c in por_numero.get(numero, []):
            if c["clave"] not in en_oferta:
                continue
            of = en_oferta[c["clave"]]
            articulos.append({
                "clave": c["clave"],
                "articulo": of["nombre"],
                "vence": of["vence"],
                "veces": c["veces"],
                "ultima_compra": (c["ultima_compra"].isoformat()
                                  if c["ultima_compra"] else None),
            })
        if not articulos:
            continue
        articulos.sort(key=lambda a: (-a["veces"], a["clave"]))
        candidatos.append({
            "cliente_id": int(cliente_id),
            "numero": numero,
            "cliente": str(nombre or "").strip(),
            "email": email,
            "articulos": articulos,
        })
    return candidatos


def fetch_top_ofertas(
    runtime: dict[str, Any],
    *,
    limit: int = DEFAULT_TOP_FALLBACK,
) -> list[dict[str, Any]]:
    """Destacadas para el fallback grupal: próximas a vencer primero."""
    ofertas = runtime["query"](
        "SELECT clave, nombre, vencimiento_oferta FROM api_articulos "
        "WHERE empresa_id = %s AND oferta = 'S' "
        "AND COALESCE(discontinuado, '') != 'S' "
        "AND COALESCE(stock_efectivo, stock, 0) > 0",
        (EMPRESA_ID,),
    )
    rows = []
    for clave, nombre, vence in ofertas:
        clave = str(clave or "").strip()
        if not clave:
            continue
        fecha = _to_local_date(vence)
        rows.append({
            "clave": clave,
            "articulo": _limpiar_nombre(str(nombre or "").strip()),
            "vence": _fmt_fecha(fecha),
            "_vence_fecha": fecha,
            "veces": 0,
            "ultima_compra": None,
        })
    rows.sort(key=lambda a: (a["_vence_fecha"] is None, a["_vence_fecha"] or date.max,
                             a["clave"]))
    return [{k: v for k, v in a.items() if k != "_vence_fecha"}
            for a in rows[:max(int(limit), 0)]]


def fetch_todos_clientes(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    """Todos los opt-in con email válido (base del fallback grupal)."""
    try:
        filas = runtime["query"](
            "SELECT ac.id, ac.numero_cliente, ac.nombre, COALESCE(au.email, '') "
            "FROM api_cliente ac JOIN auth_user au ON au.id = ac.user_id "
            "WHERE ac.recibe_ofertas_email = 1",
            (),
        )
    except Exception as exc:  # noqa: BLE001
        if "recibe_ofertas_email" not in str(exc):
            raise
        return []
    clientes = []
    for cliente_id, numero, nombre, email in filas:
        email = str(email or "").strip()
        if not _EMAIL_RE.match(email):
            continue
        clientes.append({
            "cliente_id": int(cliente_id),
            "numero": str(numero or "").strip(),
            "cliente": str(nombre or "").strip(),
            "email": email,
        })
    return clientes


def plan_mails_fallback(
    clientes: list[dict[str, Any]],
    top_ofertas: list[dict[str, Any]],
    runtime: dict[str, Any],
    *,
    ya_atendidos: set[int] | None = None,
    now: datetime | None = None,
    cliente_cooldown: int = CLIENTE_COOLDOWN_DIAS,
    articulo_cooldown: int = ARTICULO_COOLDOWN_DIAS,
    max_articulos: int = MAX_ARTICULOS_MAIL,
) -> list[dict[str, Any]]:
    """Fallback grupal: destacadas a quienes no recibieron personalizado."""
    now = now or datetime.now(LOCAL_TZ)
    ya_atendidos = ya_atendidos or set()
    pendientes = [c for c in clientes if c["cliente_id"] not in ya_atendidos]
    if not pendientes or not top_ofertas:
        return []
    ids = sorted({c["cliente_id"] for c in pendientes})
    desde_cli = (now - timedelta(days=cliente_cooldown)).astimezone(UTC)
    desde_art = (now - timedelta(days=articulo_cooldown)).astimezone(UTC)
    previas = runtime["query"](
        "SELECT cliente_id, articulo_id, enviado_en FROM api_ofertaenviada "
        f"WHERE cliente_id IN ({_placeholders(len(ids))}) AND enviado_en >= %s",
        (*ids, desde_art.strftime("%Y-%m-%d %H:%M:%S")),
    )
    ya_ofrecido: set[tuple[int, str]] = set()
    con_mail_reciente: set[int] = set()
    for cli_id, art, enviado in previas:
        ya_ofrecido.add((int(cli_id), str(art or "").strip()))
        if isinstance(enviado, datetime):
            aware = enviado if enviado.tzinfo else enviado.replace(tzinfo=UTC)
            if aware >= desde_cli:
                con_mail_reciente.add(int(cli_id))

    mails: list[dict[str, Any]] = []
    for c in pendientes:
        if c["cliente_id"] in con_mail_reciente:
            continue
        elegidos = [a for a in top_ofertas
                    if (c["cliente_id"], a["clave"]) not in ya_ofrecido
                    ][:max_articulos]
        if elegidos:
            mails.append({**c, "articulos": elegidos, "fallback": True})
    return mails


def plan_mails(
    candidatos: list[dict[str, Any]],
    runtime: dict[str, Any],
    *,
    now: datetime | None = None,
    cliente_cooldown: int = CLIENTE_COOLDOWN_DIAS,
    articulo_cooldown: int = ARTICULO_COOLDOWN_DIAS,
    max_articulos: int = MAX_ARTICULOS_MAIL,
) -> list[dict[str, Any]]:
    """Aplica cooldowns e historial para no repetir ni saturar."""
    now = now or datetime.now(LOCAL_TZ)
    if not candidatos:
        return []
    ids = sorted({c["cliente_id"] for c in candidatos})
    desde_cli = (now - timedelta(days=cliente_cooldown)).astimezone(UTC)
    desde_art = (now - timedelta(days=articulo_cooldown)).astimezone(UTC)
    previas = runtime["query"](
        "SELECT cliente_id, articulo_id, enviado_en FROM api_ofertaenviada "
        f"WHERE cliente_id IN ({_placeholders(len(ids))}) AND enviado_en >= %s",
        (*ids, desde_art.strftime("%Y-%m-%d %H:%M:%S")),
    )
    ya_ofrecido: set[tuple[int, str]] = set()
    con_mail_reciente: set[int] = set()
    for cli_id, art, enviado in previas:
        ya_ofrecido.add((int(cli_id), str(art or "").strip()))
        if isinstance(enviado, datetime):
            aware = enviado if enviado.tzinfo else enviado.replace(tzinfo=UTC)
            if aware >= desde_cli:
                con_mail_reciente.add(int(cli_id))

    mails: list[dict[str, Any]] = []
    for c in candidatos:
        if c["cliente_id"] in con_mail_reciente:
            continue
        elegidos = [a for a in c["articulos"]
                    if (c["cliente_id"], a["clave"]) not in ya_ofrecido
                    ][:max_articulos]
        if elegidos:
            mails.append({**c, "articulos": elegidos})
    return mails


def _limpiar_nombre(nombre: str) -> str:
    """Saca el sufijo ' (OFERTA)' que trae el ERP para mostrarlo limpio."""
    texto = re.sub(r"\s*\(OFERTA\)\s*$", "", nombre, flags=re.IGNORECASE)
    return texto.strip() or nombre


def _fmt_fecha(fecha: date | None) -> str | None:
    return fecha.strftime("%d/%m/%Y") if fecha else None


def mail_cliente(mail: dict[str, Any]) -> tuple[str, str, str]:
    """(asunto, texto, html) del mail. Sin emojis: la cola es latin1."""
    def esc(value: Any) -> str:
        return (str(value).replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;"))

    nombre = mail["cliente"] or "cliente"
    arts = mail["articulos"]
    generico = bool(mail.get("fallback"))
    if len(arts) == 1 and not generico:
        asunto = f"Oferta: {arts[0]['articulo'] or arts[0]['clave']}"
    elif generico:
        asunto = "Ofertas destacadas de la semana"
    else:
        asunto = "Ofertas en artículos que comprás habitualmente"

    if generico:
        bajada = ("Estas son las ofertas destacadas de esta semana "
                  "en Ferretería Avenida:")
        bajada_html = ("Estas son las <strong>ofertas destacadas</strong> "
                       "de esta semana:")
    else:
        bajada = ("Estos artículos que comprás habitualmente están "
                  "en oferta esta semana en Ferretería Avenida:")
        bajada_html = ("Estos artículos que comprás habitualmente están "
                       "<strong>en oferta</strong> esta semana:")

    lineas = []
    for a in arts:
        linea = f"  - {a['articulo'] or a['clave']} (cód. {a['clave']})"
        if a.get("vence"):
            linea += f" - válida hasta {a['vence']}"
        lineas.append(linea)
    texto = (
        f"Hola {nombre},\n\n"
        f"{bajada}\n\n"
        + "\n".join(lineas)
        + "\n\nSi querés que te los preparemos, o necesitás precio por cantidad, "
        "respondé este mail y te contactamos.\n"
        f"También podés ver todas las ofertas en {PORTAL_URL}\n\n"
        "Saludos,\nVentas - Ferretería Avenida\n\n"
        "Si no querés recibir estas sugerencias, respondé BAJA.\n"
    )
    tarjetas = "".join(
        f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 12px 0;background:#ffffff;border:1px solid #e5e7eb;border-left:4px solid #b91c1c;border-radius:6px">
<tr><td style="padding:14px 16px">
<div style="font-size:15px;font-weight:bold;color:#111827;margin:0 0 4px 0">{esc(a['articulo'] or a['clave'])}</div>
<div style="font-size:12px;color:#6b7280;margin:0 0 4px 0">Cód. {esc(a['clave'])}"""
        + (f""" <span style="display:inline-block;background:#fef3c2;color:#92400e;font-size:11px;font-weight:bold;padding:2px 8px;border-radius:10px;margin-left:6px">Válida hasta {esc(a['vence'])}</span>""" if a.get("vence") else "")
        + f"""</div>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:8px"><tr><td style="background:#b91c1c;border-radius:4px"><a href="{PORTAL_URL}" style="display:inline-block;padding:9px 18px;font-size:13px;font-weight:bold;color:#ffffff;text-decoration:none">Ver mi precio</a></td></tr></table>
</td></tr></table>"""
        for a in arts
    )
    html = f"""<html><body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">Ofertas en artículos que comprás habitualmente, solo por esta semana.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:20px 10px"><tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:8px;overflow:hidden">
<tr><td style="background:#b91c1c;padding:22px 24px;text-align:left">
<div style="font-size:20px;font-weight:bold;color:#ffffff;margin:0">Ferretería Avenida</div>
<div style="font-size:13px;color:#fecaca;margin:4px 0 0 0">Portal de clientes &bull; Ofertas para vos</div>
</td></tr>
<tr><td style="padding:24px">
<p style="font-size:15px;color:#111827;margin:0 0 8px 0">Hola {esc(nombre)},</p>
<p style="font-size:14px;color:#374151;margin:0 0 16px 0">{bajada_html}</p>
{tarjetas}
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:20px auto 8px auto"><tr><td align="center" style="background:#1d4ed8;border-radius:4px"><a href="{PORTAL_URL}" style="display:inline-block;padding:12px 28px;font-size:14px;font-weight:bold;color:#ffffff;text-decoration:none">Ver todas mis ofertas</a></td></tr></table>
<p style="font-size:13px;color:#6b7280;margin:16px 0 0 0">Si querés que te los preparemos, o necesitás precio por cantidad, <strong>respondé este mail</strong> y te contactamos.</p>
</td></tr>
<tr><td style="background:#f9fafb;padding:16px 24px;border-top:1px solid #e5e7eb">
<p style="font-size:11px;color:#9ca3af;margin:0">Ventas - Ferretería Avenida &bull; Respondé BAJA si no querés recibir estas sugerencias.</p>
</td></tr>
</table>
</td></tr></table>
</body></html>"""
    return asunto, texto, html


def encolar_mails_clientes(
    mails: list[dict[str, Any]],
    *,
    runtime: dict[str, Any],
    now: datetime | None = None,
) -> int:
    """Encola cada mail en fe y registra lo ofrecido (una transacción por mail)."""
    now_utc = (now or datetime.now(LOCAL_TZ)).astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")
    cola = fe_table("emails_pendientes")
    enviados = 0
    for mail in mails:
        asunto, texto, html = mail_cliente(mail)
        stmts: list[tuple[str, tuple[Any, ...]]] = [(
            f"INSERT INTO {cola} (destinatario, quien_envia, asunto, cuerpo_html, "
            "cuerpo_texto, intentos, estado, creado_en, empresa_id) "
            "VALUES (%s, %s, %s, %s, %s, 0, 'pendiente', %s, 1)",
            (mail["email"], QUIEN_ENVIA, sanitizar_latin1(asunto),
             sanitizar_latin1(html), sanitizar_latin1(texto), now_utc),
        )]
        for a in mail["articulos"]:
            stmts.append((
                "INSERT INTO api_ofertaenviada (cliente_id, articulo_id, enviado_en, "
                "consultas, email) VALUES (%s, %s, %s, %s, %s)",
                (mail["cliente_id"], a["clave"], now_utc, a["veces"], mail["email"]),
            ))
        try:
            runtime["execute_batch"](stmts)
        except Exception as exc:  # noqa: BLE001 - sigue con los demás clientes
            print(f"ERROR encolando mail a {mail['numero']} {mail['email']}: {exc}")
            continue
        enviados += 1
    return enviados


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ofertas personalizadas según compras del cliente")
    parser.add_argument("--dias-compras", type=int, default=DEFAULT_DIAS_COMPRAS,
                        help=f"ventana de compras hacia atrás (default {DEFAULT_DIAS_COMPRAS})")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP_FALLBACK,
                        help=f"destacadas del fallback grupal (default {DEFAULT_TOP_FALLBACK})")
    parser.add_argument("--sin-fallback", action="store_true",
                        help="no mandar el grupal a quienes no cruzaron compras")
    parser.add_argument("--to", action="append", default=[],
                        help="destinatario del reporte (repite la opción)")
    parser.add_argument("--enviar", action="store_true",
                        help="encola los mails a clientes (sin esto solo muestra)")
    parser.add_argument("--env", default=None,
                        help="usar las credenciales de este .env en vez de la conexión "
                             "del legado; para probar desde una PC")
    args = parser.parse_args(argv)
    if args.dias_compras < 1:
        parser.error("--dias-compras debe ser >= 1")

    try:
        if args.env:
            runtime = _load_runtime_local(Path(args.env))
        else:
            from resumen_busquedas_precios import _load_runtime
            runtime = _load_runtime()
    except ImportError:
        from ops.automatizaciones.resumen_busquedas_precios import _load_runtime
        runtime = _load_runtime()

    now = datetime.now(LOCAL_TZ)
    candidatos = fetch_candidatos(runtime, dias_compras=args.dias_compras, now=now)
    mails = plan_mails(candidatos, runtime, now=now)
    fallback = []
    if not args.sin_fallback:
        top = fetch_top_ofertas(runtime, limit=args.top)
        todos = fetch_todos_clientes(runtime)
        atendidos = {m["cliente_id"] for m in mails}
        fallback = plan_mails_fallback(todos, top, runtime,
                                       ya_atendidos=atendidos, now=now,
                                       max_articulos=args.top)
        mails = mails + fallback

    print(f"clientes con compras en oferta: {len(candidatos)}; "
          f"mails a encolar: {len(mails)} "
          f"(personalizados: {len(mails) - len(fallback)}, grupal: {len(fallback)})")
    for m in mails:
        asunto, texto, _html = mail_cliente(m)
        print(f"Para: {m['email']} ({m['numero']} {m['cliente']}) | Asunto: {asunto}")
        print(texto)

    if mails and args.enviar:
        n = encolar_mails_clientes(mails, runtime=runtime, now=now)
        print(f"MAILS A CLIENTES ENCOLADOS: {n}/{len(mails)}")

    if args.to and not args.enviar:
        print(f"(reporte a {', '.join(args.to)} omitido: sin --enviar no se manda nada)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
