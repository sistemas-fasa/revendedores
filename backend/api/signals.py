from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Cliente, PedidoItem
from .services.precios import calcular_precio_articulo


@receiver(pre_save, sender=PedidoItem, dispatch_uid="pedido_item_precio_backend")
def recalcular_precio_pedido_item(sender, instance, **kwargs):
    """Impide que el precio enviado por el navegador sea la fuente de verdad.

    La regla se aplica al crear el ítem. El precio y subtotal se recalculan con
    los datos comerciales del cliente autenticado y las condiciones del pedido.
    """
    if not instance._state.adding:
        return

    try:
        cliente = instance.pedido.user.cliente
    except Cliente.DoesNotExist as exc:
        raise ValidationError(
            "No se puede crear el pedido: el usuario no tiene un cliente asociado."
        ) from exc

    precio = calcular_precio_articulo(
        articulo=instance.articulo,
        cliente=cliente,
        modalidad=instance.pedido.modalidad,
        con_impuestos=instance.pedido.con_impuestos,
        condicion_pago_id=cliente.condicion_pago_id,
    )

    precio = Decimal(str(precio)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    instance.precio_unitario = precio
    instance.subtotal = (precio * Decimal(str(instance.cantidad))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
