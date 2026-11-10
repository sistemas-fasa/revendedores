"""Estado de stock para el semáforo (verde/amarillo/rojo/sin_datos).

Funciones puras, sin acceso a base de datos: el stock efectivo lo calcula el
actualizador horario y el mínimo el job semanal de rotación.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

_FORMULA_RE = re.compile(r"^([*/+-])\s*(\d+(?:\.\d*)?|\.\d+)$")


def _decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError, AttributeError):
        return None


def apply_factor(formula: Any) -> Decimal | None:
    """Factor hijo->padre: la fórmula VFP evaluada en 1 (None si inválida)."""
    text = str(formula or "").strip()
    if not text:
        return Decimal("1")
    match = _FORMULA_RE.fullmatch(text)
    if not match:
        return None
    operator, operand = match.groups()
    try:
        operand_value = Decimal(operand)
    except InvalidOperation:
        return None
    if operator == "/":
        return (Decimal("1") / operand_value) if operand_value else None
    if operator == "*":
        return operand_value
    if operator == "+":
        return Decimal("1") + operand_value
    return Decimal("1") - operand_value


def effective_stock(stock: Any, parent_stock: Any, formula: Any) -> Decimal | None:
    """Stock efectivo: propio, o del padre escalado si descuenta de otro."""
    own = _decimal(stock)
    if parent_stock is None:
        return own
    parent = _decimal(parent_stock)
    if parent is None:
        return own
    factor = apply_factor(formula)
    if factor is None or factor <= 0:
        return own
    return parent / factor


def stock_estado(efectivo: Any, minimo: Any) -> str:
    """Semáforo: rojo sin stock, amarillo bajo el mínimo, verde resto."""
    value = _decimal(efectivo)
    if value is None:
        return "sin_datos"
    if value <= 0:
        return "rojo"
    limit = _decimal(minimo) if minimo is not None else None
    if limit is None:
        return "verde"
    return "amarillo" if value <= limit else "verde"
