from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.models import Articulos, Cliente, FormaPago, Localidades
from api.serializers import PedidoSerializer


class PedidoReviewDataTests(TestCase):
    def test_observaciones_quedan_en_snapshot(self):
        forma = FormaPago.objects.create(id='00', nombre='Contado', descuento=0, punitorio=0)
        localidad = Localidades.objects.create(codigo='0099', nombre='Puerto Rico')
        user = User.objects.create_user(username='review-user', password='test')
        Cliente.objects.create(
            user=user, numero_cliente='990', lista_precio='1', nombre='Cliente Review',
            codigo_localidad=localidad, condicion_pago=forma, tipo_responsable_iva='C'
        )
        articulo = Articulos.objects.create(
            clave='099.001', unidad='UN', nombre='Articulo Review', peso=Decimal('1'),
            pblret1=Decimal('10'), pblrep1=Decimal('10'), pblret4=Decimal('10'), pblrep4=Decimal('10'),
            ultact=date.today(), visible='S', descripcion='Review', iva=0
        )
        serializer = PedidoSerializer(data={
            'modalidad': 'reparto', 'con_impuestos': True, 'condicion_pago': '00',
            'observaciones': 'Entregar por la tarde',
            'items': [{'articulo': articulo.clave, 'cantidad': '1', 'precio_unitario': '10.00'}],
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        pedido = serializer.save(user=user)
        self.assertEqual(pedido.cliente_snapshot['observaciones'], 'Entregar por la tarde')
        self.assertEqual(pedido.modalidad, 'reparto')
