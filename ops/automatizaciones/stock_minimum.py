"""Stock mínimo por rotación para el semáforo de stock de Revendedores.

Calcula el mínimo de cada artículo padre desde la venta neta de los últimos
90 días en ``fasa.facturas`` (empresa 1, comprobantes fiscales reales) y lo
escala a los hijos que descuentan del padre (``Artxmedidas.DESCUENTA``).

Los días de cobertura son parametrizables: CLI ``--coverage-days`` o env
``STOCK_MIN_COVERAGE_DAYS`` (default 14).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

DEFAULT_COVERAGE_DAYS = 14
SALES_WINDOW_DAYS = 90
DEFAULT_EMPRESA_ID = 1
SALE_CODES = ("F", "FS", "D")
CREDIT_CODES = ("C", "CS")
# Solo comprobantes fiscales reales; se excluye '201' (movimientos internos).
REAL_TIPOCOMP = ("001", "002", "003", "006", "007", "008")
LOCK_PATH = Path("/data/locks/stock_minimum_calc.lock")
LEGACY_PATH = "/var/www/html/utiles"

_FORMULA_RE = re.compile(r"^([*/+-])\s*(\d+(?:\.\d*)?|\.\d+)$")


def parse_coverage_days(value: Any) -> int:
    """Valida los días de cobertura: entero positivo obligatorio."""
    try:
        days = int(str(value).strip())
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"días de cobertura inválidos: {value!r}") from exc
    if days < 1:
        raise ValueError(f"días de cobertura inválidos: {value!r} (mínimo 1)")
    return days


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("valor decimal inválido") from exc


def apply_formula(value: Decimal, formula: Any) -> Decimal | None:
    """Aplica un sufijo aritmético VFP (``*0.5``, ``/2``) a un valor."""
    text = str(formula or "").strip()
    if not text:
        return value
    match = _FORMULA_RE.fullmatch(text)
    if not match:
        return None
    operator, operand = match.groups()
    operand_value = _decimal(operand)
    if operator == "/":
        return value / operand_value if operand_value else None
    if operator == "*":
        return value * operand_value
    if operator == "+":
        return value + operand_value
    return value - operand_value


def formula_factor(formula: Any) -> Decimal | None:
    """Factor de conversión hijo->padre: la fórmula evaluada en 1."""
    result = apply_formula(Decimal("1"), formula)
    if result is None or result <= 0:
        return None
    return result


def calculate_minimum(
    net_sales: Any,
    coverage_days: int,
    *,
    window_days: int = SALES_WINDOW_DAYS,
) -> int | None:
    """Mínimo = techo(venta neta / ventana × cobertura).

    Devuelve ``None`` (sin rotación) cuando la venta neta es nula o
    negativa. Piso 1 si hubo venta pero el cálculo da 0.
    """
    days = parse_coverage_days(coverage_days)
    net = _decimal(net_sales)
    if net <= 0:
        return None
    raw = net / Decimal(window_days) * Decimal(days)
    return max(1, int(math.ceil(raw)))


def child_minimum(parent_min: int | None, formula: Any) -> int | None:
    """Mínimo del hijo escalado desde el mínimo del padre."""
    if parent_min is None:
        return None
    factor = formula_factor(formula)
    if factor is None:
        return None
    return max(1, int(math.ceil(Decimal(parent_min) / factor)))


def net_sales_from_rows(rows: list[tuple[Any, Any, Any]]) -> dict[str, Decimal]:
    """Agrega renglones (clave, código, cantidad) a venta neta por artículo."""
    net: dict[str, Decimal] = {}
    for clave, codigo, cantidad in rows:
        key = str(clave or "").strip()
        if not key:
            continue
        code = str(codigo or "").strip()
        try:
            qty = _decimal(cantidad)
        except ValueError:
            continue
        if code in SALE_CODES:
            net[key] = net.get(key, Decimal("0")) + qty
        elif code in CREDIT_CODES:
            net[key] = net.get(key, Decimal("0")) - qty
    return net


def compute_minima(
    net_sales: dict[str, Decimal],
    children: dict[str, tuple[str, str]],
    coverage_days: int,
    *,
    window_days: int = SALES_WINDOW_DAYS,
) -> dict[str, int | None]:
    """Mínimos de padres por rotación y de hijos escalados por fórmula."""
    days = parse_coverage_days(coverage_days)
    minima: dict[str, int | None] = {}
    for clave, net in net_sales.items():
        minima[clave] = calculate_minimum(net, days, window_days=window_days)
    for child, (parent, formula) in children.items():
        if child == parent:
            # Fila de unidad del propio padre (p.ej. pack): conserva su mínimo.
            continue
        minima[child] = child_minimum(minima.get(parent), formula)
    return minima


def _is_lock_held(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        import fcntl

        with path.open("a+") as lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return True
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            return False
    except OSError:
        return True


def _load_runtime(empresa_id: int, window_days: int) -> dict[str, Any]:
    """Lee ventas/hijos desde el ERP y escribe mínimos en Revendedores."""
    jobs_path = str(Path(__file__).resolve().parent)
    for path in (LEGACY_PATH, jobs_path):
        if path not in sys.path:
            sys.path.insert(0, path)

    original_argv = sys.argv
    original_cwd = os.getcwd()
    sys.argv = [original_argv[0] if original_argv else "stock_minimum.py"]
    try:
        # libs.utiles parsea -i/-a al importar y resuelve fasa.ini
        # relativo al directorio del actualizador.
        os.chdir(LEGACY_PATH)
        from modelos.ModeloBase import db as fasa_db
        from modelos.ModeloBase import db_reventa
    finally:
        sys.argv = original_argv
        os.chdir(original_cwd)

    tipocomp = ", ".join(f"'{code}'" for code in REAL_TIPOCOMP)

    def fetch_net_sales() -> dict[str, Decimal]:
        cursor = fasa_db.execute_sql(
            "SELECT TRIM(CLAVE), TRIM(CODIGO), SUM(CANTIDAD) FROM facturas "
            f"WHERE FECHA >= CURDATE() - INTERVAL {int(window_days)} DAY "
            "AND empresa_id = %s "
            f"AND TipoComp IN ({tipocomp}) "
            "GROUP BY TRIM(CLAVE), TRIM(CODIGO)",
            (int(empresa_id),),
        )
        return net_sales_from_rows(list(cursor.fetchall()))

    def fetch_children() -> dict[str, tuple[str, str]]:
        # Fórmula canónica: la de stock (una por clave). DESCUENTA viene de
        # Artxmedidas (una clave puede tener varias unidades). Se excluye la
        # autorreferencia (padre que es su propia unidad alternativa).
        cursor = fasa_db.execute_sql(
            "SELECT TRIM(s.CLAVE), MAX(TRIM(a.DESCUENTA)), TRIM(s.FORMU) "
            "FROM Artxmedidas a JOIN stock s ON s.CLAVE = a.CLAVE "
            "WHERE a.DESCUENTA IS NOT NULL AND TRIM(a.DESCUENTA) <> '' "
            "AND TRIM(s.CLAVE) <> TRIM(a.DESCUENTA) "
            "AND s.empresa_id = %s "
            "GROUP BY TRIM(s.CLAVE), TRIM(s.FORMU)",
            (int(empresa_id),),
        )
        return {
            str(child): (str(parent), str(formula or ""))
            for child, parent, formula in cursor.fetchall()
        }

    def fetch_current(keys: list[str]) -> dict[str, Any]:
        if not keys:
            return {}
        placeholders = ", ".join(["%s"] * len(keys))
        cursor = db_reventa.execute_sql(
            "SELECT clave, stock_minimo, descuenta_de FROM api_articulos "
            f"WHERE clave IN ({placeholders})",
            tuple(keys),
        )
        return {str(row[0]).strip(): (row[1], row[2]) for row in cursor.fetchall()}

    def save_minima(
        minima: dict[str, int | None],
        children: dict[str, tuple[str, str]],
    ) -> int:
        updated = 0
        for clave, minimum in minima.items():
            parent = children.get(clave, ("", ""))[0]
            cursor = db_reventa.execute_sql(
                "UPDATE api_articulos SET stock_minimo = %s, descuenta_de = %s "
                "WHERE clave = %s",
                (
                    None if minimum is None else str(minimum),
                    parent,
                    clave,
                ),
            )
            updated += cursor.rowcount or 0
        return updated

    return {
        "fetch_net_sales": fetch_net_sales,
        "fetch_children": fetch_children,
        "fetch_current": fetch_current,
        "save_minima": save_minima,
    }


def run_update(
    coverage_days: int = DEFAULT_COVERAGE_DAYS,
    *,
    dry_run: bool = False,
    empresa_id: int = DEFAULT_EMPRESA_ID,
    window_days: int = SALES_WINDOW_DAYS,
    runtime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calcula mínimos por rotación y los persiste en Revendedores."""
    days = parse_coverage_days(coverage_days)
    if _is_lock_held(LOCK_PATH):
        return {"status": "already_running", "coverage_days": days}
    runtime = runtime or _load_runtime(int(empresa_id), int(window_days))

    net_sales = runtime["fetch_net_sales"]()
    children = runtime["fetch_children"]()
    minima = compute_minima(net_sales, children, days, window_days=int(window_days))

    changed = 0
    with_rotation = 0
    samples: list[dict[str, Any]] = []
    if "fetch_current" in runtime and callable(runtime["fetch_current"]):
        current = runtime["fetch_current"](list(minima))
        for clave in sorted(minima):
            new_min, new_parent = minima[clave], children.get(clave, ("", ""))[0]
            if minima[clave] is not None:
                with_rotation += 1
            old = current.get(clave)
            old_min = str(old[0]) if old and old[0] is not None else None
            old_parent = str(old[1]).strip() if old and old[1] else ""
            if old is None or old_min != str(new_min) or old_parent != new_parent:
                changed += 1
                if len(samples) < 10:
                    samples.append(
                        {
                            "articulo": clave,
                            "anterior": old_min,
                            "nuevo": new_min,
                            "descuenta_de": new_parent,
                        }
                    )
    else:
        with_rotation = sum(1 for value in minima.values() if value is not None)
        changed = len(minima)

    updated = 0
    if not dry_run:
        updated = int(runtime["save_minima"](minima, children))

    return {
        "status": "dry_run" if dry_run else "ok",
        "coverage_days": days,
        "empresa_id": int(empresa_id),
        "window_days": int(window_days),
        "articulos": len(minima),
        "con_rotacion": with_rotation,
        "hijos": len(children),
        "cambiados": changed,
        "actualizados": updated,
        "muestras": samples,
    }


def main(argv: list[str] | None = None) -> int:
    try:
        env_days = parse_coverage_days(
            os.environ.get("STOCK_MIN_COVERAGE_DAYS", DEFAULT_COVERAGE_DAYS)
        )
    except ValueError as exc:
        print(f"STOCK_MIN_COVERAGE_DAYS inválido: {exc}", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description="Recalcula el stock mínimo por rotación")
    parser.add_argument(
        "--coverage-days",
        type=parse_coverage_days,
        default=env_days,
    )
    parser.add_argument("--empresa-id", type=int, default=int(os.environ.get("STOCK_MIN_EMPRESA_ID", DEFAULT_EMPRESA_ID)))
    parser.add_argument("--window-days", type=int, default=SALES_WINDOW_DAYS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run_update(
            args.coverage_days,
            dry_run=args.dry_run,
            empresa_id=args.empresa_id,
            window_days=args.window_days,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
