"""
Constantes reutilizables para el paquete `backend.api`.

Cuando se complete la migración del largo de clave, actualiza este valor
o reemplázalo por una configuración más global.
"""

# Umbral usado en comparaciones como `len(clave) > CLAVE_LEN_THRESHOLD`
CLAVE_LEN_THRESHOLD = 7

# Tipos de comprobante de la cuenta corriente (columna `codigo` de fasa.movi).
# 'E' no existe en la tabla `tipocomp` del ERP: son los débitos por devolución
# de cheque, que igual aparecen en la cuenta corriente del cliente.
TIPOS_COMPROBANTE = {
    'F': 'Factura',
    'D': 'Débito',
    'R': 'Recibo/Pago',
    'C': 'Crédito',
    'E': 'Débito por devolución de cheque',
}
