"""Ofertas personalizadas según compras: cada cliente recibe las ofertas
vigentes de artículos que compró habitualmente (facturas ERP)."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from ops.automatizaciones.ofertas_por_compra import (
    encolar_mails_clientes,
    fetch_candidatos,
    fetch_todos_clientes,
    fetch_top_ofertas,
    mail_cliente,
    plan_mails,
    plan_mails_fallback,
)

ARG = ZoneInfo("America/Argentina/Buenos_Aires")
NOW = datetime(2026, 11, 24, 8, 0, tzinfo=ARG)

# cliente, clave, veces, ultima
COMPRAS = [
    ("00040", "CEM001", 5, date(2026, 11, 10)),
    ("00040", "CAL002", 2, date(2026, 10, 5)),
    ("00077", "HIE003", 3, date(2026, 11, 1)),
    ("00099", "CEM001", 4, date(2026, 11, 12)),
]

# id, numero, nombre, email, recibe
CLIENTES = [
    (10, "00040", "Corralon Uno", "uno@ejemplo.com", 1),
    (20, "00077", "Ferreteria Dos", "dos@ejemplo.com", 1),
    (30, "00099", "Cliente Baja", "baja@ejemplo.com", 0),
]

# clave, nombre, vencimiento (solo ofertas vigentes con stock y no discontinuadas)
OFERTAS = [
    ("CEM001", "CEMENTO 50KG (OFERTA)", date(2026, 11, 30)),
    ("HIE003", "HIERRO 8", None),
]


def _runtime(previas=(), executed=None):
    def query(sql, params):
        if "FROM `fasa`.`facturas`" in sql:
            assert "codigo = 'F'" in sql
            return list(COMPRAS)
        if "FROM api_cliente" in sql:
            if "numero_cliente IN" in sql:
                return list(CLIENTES)
            # la base real filtra recibe_ofertas_email = 1; replicarlo en el mock
            return [(i, n, c, e) for i, n, c, e, r in CLIENTES if r]
        if "FROM api_articulos" in sql:
            assert "oferta" in sql
            return list(OFERTAS)
        if "FROM api_ofertaenviada" in sql:
            return list(previas)
        raise AssertionError(sql)

    def execute_batch(stmts):
        executed.append(stmts)

    return {"query": query, "execute_batch": execute_batch}


def test_cruza_compras_con_ofertas_y_respeta_baja():
    cands = fetch_candidatos(_runtime(), dias_compras=90, now=NOW)
    por_cli = {c["numero"]: sorted(a["clave"] for a in c["articulos"]) for c in cands}
    # 00040 compro CEM001 (en oferta) y CAL002 (no en oferta) -> solo CEM001
    assert por_cli["00040"] == ["CEM001"]
    # 00077 compro HIE003 en oferta -> va
    assert por_cli["00077"] == ["HIE003"]
    # 00099 pidio la baja -> no va aunque haya comprado en oferta
    assert "00099" not in por_cli


def test_cooldown_articulo_y_cliente():
    # CEM001 ya ofrecido a 00040 hace 10 dias (< 30) -> se excluye;
    # 00077 con mail hace 2 dias (< 7) -> se excluye entero
    previas = [
        (10, "CEM001", datetime(2026, 11, 14, 8, 0)),
        (20, "OTRA001", datetime(2026, 11, 22, 8, 0)),
    ]
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(), now=NOW)
    # reconstruir con previas: plan_mails recibe runtime con historial
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(previas=previas), now=NOW)
    assert mails == []


def test_plan_respeta_maximo_y_ordena_por_recencia():
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(), now=NOW, max_articulos=5)
    assert {m["numero"] for m in mails} == {"00040", "00077"}
    m40 = next(m for m in mails if m["numero"] == "00040")
    assert [a["clave"] for a in m40["articulos"]] == ["CEM001"]
    assert m40["email"] == "uno@ejemplo.com"


def test_mail_menciona_compras_y_portal_con_baja():
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(), now=NOW)
    asunto, texto, html = mail_cliente(mails[0])
    assert "oferta" in asunto.lower()
    assert "BAJA" in texto
    assert "oferta=1" in html
    assert "compr" in texto.lower()
    # disenio: marca, CTA por articulo, nombre limpio y vencimiento
    assert "Ferretería Avenida" in html
    assert "Ver mi precio" in html
    assert "Ver todas mis ofertas" in html
    assert "(OFERTA)" not in html
    assert "30/11/2026" in html
    assert "30/11/2026" in texto


def test_encolar_registra_oferta_y_cola(monkeypatch):
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(), now=NOW)
    executed = []
    n = encolar_mails_clientes(mails, runtime=_runtime(executed=executed), now=NOW)
    assert n == 2
    assert len(executed) == 2
    cola, historial = executed[0][0], executed[0][1:]
    assert "emails_pendientes" in cola[0]
    assert "api_ofertaenviada" in historial[0][0]
    # email invalido nunca llega a encolar
    assert all("@" in m["email"] for m in mails)


def test_top_ofertas_ordena_por_vencimiento():
    top = fetch_top_ofertas(_runtime(), limit=5)
    assert [a["clave"] for a in top] == ["CEM001", "HIE003"]
    assert top[0]["vence"] == "30/11/2026"
    assert top[1]["vence"] is None
    assert fetch_top_ofertas(_runtime(), limit=1) == top[:1]


def test_fallback_solo_a_quienes_no_recibieron_personalizado():
    top = fetch_top_ofertas(_runtime(), limit=5)
    todos = fetch_todos_clientes(_runtime())
    # la baja (00099) no figura en todos
    assert {c["numero"] for c in todos} == {"00040", "00077"}
    mails = plan_mails_fallback(todos, top, _runtime(),
                                ya_atendidos={10}, now=NOW)
    assert [m["numero"] for m in mails] == ["00077"]
    assert mails[0]["fallback"] is True
    asunto, texto, html = mail_cliente(mails[0])
    assert asunto == "Ofertas destacadas de la semana"
    assert "destacadas" in texto.lower()


def test_fallback_respeta_cooldown_cliente():
    top = fetch_top_ofertas(_runtime(), limit=5)
    todos = fetch_todos_clientes(_runtime())
    previas = [(20, "OTRA001", datetime(2026, 11, 22, 8, 0))]
    mails = plan_mails_fallback(todos, top, _runtime(previas=previas),
                                ya_atendidos=set(), now=NOW)
    assert [m["numero"] for m in mails] == ["00040"]


def test_mail_con_tracking_usa_link_corto_y_pixel(monkeypatch):
    import ops.automatizaciones.ofertas_por_compra as mod

    def fake_tracking(email, campaign, url=None, **k):
        if url and "buscar=" in url:
            return {"cta": "https://ventas.ferreteriaavenida.com.ar/api/t/ART123/",
                    "pixel": None}
        return {"cta": "https://ventas.ferreteriaavenida.com.ar/api/t/ALL456/",
                "pixel": "https://ventas.ferreteriaavenida.com.ar/api/track-pixel/?t=TOK"}

    monkeypatch.setattr(mod, "generar_tracking", fake_tracking)
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(), now=NOW)
    ejecutados = []

    def fake_batch(stmts):
        ejecutados.append(stmts)

    n = encolar_mails_clientes(mails, runtime={"query": lambda s, p: [], "execute_batch": fake_batch},
                               now=NOW)
    assert n == 2
    html = ejecutados[0][0][1][3]
    assert "/api/t/ART123/" in html  # ver mi precio por articulo
    assert "/api/t/ALL456/" in html  # ver todas
    assert "/api/track-pixel/?t=TOK" in html
    assert mails[0].get("link_trackeado", "").endswith("/api/t/ALL456/")
    # version texto plano tambien lleva links (cortos) por articulo
    texto = ejecutados[0][0][1][4]
    assert "/api/t/ART123/" in texto


def test_mail_sin_tracking_usa_links_directos():
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(), now=NOW)
    asunto, texto, html = mail_cliente(mails[0], None)
    assert "productos?oferta=1" in html
    assert "buscar=CEM001" in html
    assert "buscar=CEM001" in texto
    assert "track-pixel" not in html


def test_tracking_con_fallo_igual_encola(monkeypatch):
    import ops.automatizaciones.ofertas_por_compra as mod
    # portal caído: sin cta ni pixel -> links directos, el mail sale igual
    monkeypatch.setattr(mod, "generar_tracking",
                        lambda email, campaign, url=None, **k: {"cta": None, "pixel": None})
    mails = plan_mails(fetch_candidatos(_runtime(), dias_compras=90, now=NOW),
                       _runtime(), now=NOW)
    ejecutados = []

    def fake_batch(stmts):
        ejecutados.append(stmts)

    n = encolar_mails_clientes(mails, runtime={"query": lambda s, p: [], "execute_batch": fake_batch},
                               now=NOW)
    assert n == 2
    assert "productos?oferta=1" in ejecutados[0][0][1][3]
    assert "track-pixel" not in ejecutados[0][0][1][3]
