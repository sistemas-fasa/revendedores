"""
Tratamiento de las fechas que llegan desde el ERP legacy (VFP -> MySQL).

La informacion contable viene del ERP legacy (VFP), que se exporta a la base
MySQL `fasa`. En esa base las columnas de vencimiento pueden traer el
centinela '0000-00-00' cuando el comprobante no tiene fecha de vencimiento
(pagos en efectivo, notas de credito auxiliares, debitos por devolucion de
cheque).

pymysql devuelve los valores DATE invalidos tal cual (como texto) y el
backend MySQL de Django no los convierte, asi que el string terminaba en el
atributo del modelo y cualquier `.strftime()` reventaba con:

    AttributeError: 'str' object has no attribute 'strftime'

Eso hacia que /api/comprobantes/ respondiera HTTP 500 para cualquier cliente
con al menos un comprobante en esas condiciones (3.535 clientes y 8.435
comprobantes de 1.265.574). Los datos no se pueden corregir desde la web
porque `cuenta_corriente_clientes` es una vista sobre `fasa.movi`, que es la
fuente de verdad del ERP.

Este modulo centraliza el tratamiento de esas fechas:

- `FechaContableField`: campo de modelo que normaliza '0000-00-00' a `None`
  ("sin fecha"), para que el resto del codigo trate esas columnas como fechas
  opcionales.
- `normalizar_fecha` / `formatear_fecha`: helpers para las vistas, que
  toleran tanto `None` como el string crudo que entrega MySQL.
- `ConFechaValida`: lookup que excluye del SQL las filas con fecha cero.
  Hace falta porque en MySQL '0000-00-00' ordena antes que cualquier fecha
  real, asi que un filtro `fechaven < hoy` las cuenta como "deuda vencida"
  aunque en realidad no tengan vencimiento.
"""

from datetime import date as date_cls
from datetime import datetime

from django.db.models import DateField, Lookup
from django.utils.dateparse import parse_date

ZERO_DATE = '0000-00-00'


def normalizar_fecha(valor):
    """Devuelve un `datetime.date` o `None` si el valor no es una fecha valida.

    Acepta `date`, `datetime`, texto 'YYYY-MM-DD' y el centinela '0000-00-00'
    del ERP, que se interpreta como "sin fecha".
    """
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date_cls):
        return valor
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto or texto == ZERO_DATE:
            return None
        try:
            return parse_date(texto)
        except ValueError:
            # Fechas imposibles como '0000-00-00' o '2026-02-31'.
            return None
    return None


def formatear_fecha(valor):
    """Devuelve la fecha como 'YYYY-MM-DD' o `None` si no hay fecha."""
    fecha = normalizar_fecha(valor)
    return fecha.strftime('%Y-%m-%d') if fecha else None


def esta_vencido(comprobante, hoy=None):
    """True si el comprobante tiene saldo pendiente y su vencimiento ya paso.

    Los comprobantes sin fecha de vencimiento (fecha cero del ERP) no estan
    vencidos: no hay contra que vencerse.
    """
    from django.utils import timezone

    vencimiento = normalizar_fecha(getattr(comprobante, 'fechaven', None))
    if vencimiento is None:
        return False
    if hoy is None:
        hoy = timezone.localdate()
    try:
        saldo = float(getattr(comprobante, 'saldo', 0) or 0)
    except (TypeError, ValueError):
        saldo = 0
    return saldo > 0 and vencimiento < hoy


class ConFechaValida(Lookup):
    """Lookup `con_fecha_valida`: deja pasar solo las fechas reales.

    Se traduce a `columna IS NOT NULL AND columna <> '0000-00-00'`.
    """

    lookup_name = 'con_fecha_valida'
    prepare_rhs = False

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        return f'({lhs} IS NOT NULL AND {lhs} <> %s)', [*lhs_params, ZERO_DATE]


class FechaContableField(DateField):
    """DateField que interpreta la fecha cero del ERP ('0000-00-00') como `None`."""

    def from_db_value(self, value, expression, connection):
        return normalizar_fecha(value)


FechaContableField.register_class_lookup(ConFechaValida)
