"""Resolución del código de cliente contra el ERP (contrato para el hilo del ERP).

`resolver_codigo(codigo)` normaliza y devuelve un dict o None:

    {'existe': True, 'nombre': ..., 'cliente': Cliente|None, 'fuente': 'local'|'facturas'}

Fuentes actuales:
1. `api_cliente` local (campo `numero_cliente`).
2. Fallback: última factura en la base contable (`ACCOUNTING_DB_ALIAS`).

El hilo del ERP puede reemplazar el fallback por la tabla maestra real sin
cambiar la firma. Ver docs/specs/activacion-cuenta-otp.md.
"""

import logging

from django.conf import settings

logger = logging.getLogger('api')


def normalizar_codigo(codigo):
    """'40' -> '00040'. Devuelve None si no es numérico."""
    numero = (codigo or '').strip()
    if not numero.isdigit():
        return None
    return numero.zfill(5)


def resolver_codigo(codigo):
    from .models import Cliente

    numero = normalizar_codigo(codigo)
    if numero is None:
        return None

    cliente = Cliente.objects.filter(numero_cliente=numero).select_related('user').first()
    if cliente is not None:
        return {
            'existe': True,
            'nombre': cliente.nombre,
            'cliente': cliente,
            'fuente': 'local',
        }

    # Fallback: el código tuvo movimientos facturados (nombre del último).
    try:
        from .models import Factura
        alias = getattr(settings, 'ACCOUNTING_DB_ALIAS', 'default')
        factura = (
            Factura.objects.using(alias)
            .filter(cliente=numero)
            .order_by('-fecha')
            .values('nombre')
            .first()
        )
    except Exception:
        logger.warning('resolver_codigo: sin acceso a facturas para %s (fallback no disponible)', numero)
        return None
    if not factura:
        return None
    return {
        'existe': True,
        'nombre': (factura.get('nombre') or '').strip() or numero,
        'cliente': None,
        'fuente': 'facturas',
    }
