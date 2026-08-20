from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from api.models import Articulos, Cliente, FormaPago, Localidades, Pedido
from api.serializers import PedidoSerializer


class PedidoSnapshotTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cliente-snapshot',
            email='original@example.com',
            password='test',
        )
        self.localidad = Localidades.objects.create(
            codigo='0001', nombre='Puerto Rico', distancia=0, reparto='S'
        )
        self.contado = FormaPago.objects.create(
            id='00', nombre='Contado', descuento=Decimal('0'), punitorio=Decimal('0')
        )
        self.cuenta = FormaPago.objects.create(
            id='30', nombre='Cuenta corriente 30 días', descuento=Decimal('0'), punitorio=Decimal('10')
        )
        self.cliente = Cliente.objects.create(
            user=self.user,
            numero_cliente='125',
            lista_precio='1',
            nombre='Cliente Original SRL',
            codigo_localidad=self.localidad,
            condicion_pago=self.contado,
            tipo_responsable_iva='C',
            direccion='Av. Siempre Viva 123',
            cuit='30-00000000-0',
        )
        self.articulo = Articulos.objects.create(
            clave='001.001', unidad='UN', nombre='Articulo test', peso=Decimal('1'),
            pblret1=Decimal('100'), pblrep1=Decimal('100'),
            pblret4=Decimal('100'), pblrep4=Decimal('100'),
            ultact=date.today(), visible='S', descripcion='Test', iva=Decimal('0'),
        )

    def _crear_pedido(self):
        request = APIRequestFactory().post('/api/pedidos/')
        request.user = self.user
        serializer = PedidoSerializer(
            data={
                'modalidad': 'retira',
                'con_impuestos': False,
                'condicion_pago': self.cuenta.id,
                'items': [{
                    'articulo': self.articulo.clave,
                    'cantidad': 1,
                    'precio_unitario': '1.00',
                }],
            },
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save(user=self.user)

    def test_persiste_condicion_y_snapshot(self):
        pedido = self._crear_pedido()
        self.assertEqual(pedido.condicion_pago_id, '30')
        self.assertEqual(pedido.cliente_snapshot['numero_cliente'], '00125')
        self.assertEqual(pedido.cliente_snapshot['nombre'], 'Cliente Original SRL')
        self.assertEqual(pedido.cliente_snapshot['email'], 'original@example.com')
        self.assertEqual(pedido.cliente_snapshot['condicion_pago_id'], '30')
        self.assertEqual(pedido.cliente_snapshot['condicion_pago_nombre'], 'Cuenta corriente 30 días')
        # El precio debe usar la condición persistida: 100 + 10% punitorio.
        self.assertEqual(pedido.items.get().precio_unitario, Decimal('110.00'))

    def test_snapshot_no_cambia_si_cambia_el_cliente(self):
        pedido = self._crear_pedido()
        self.cliente.nombre = 'Cliente Renombrado SA'
        self.cliente.condicion_pago = self.contado
        self.cliente.save()
        self.user.email = 'nuevo@example.com'
        self.user.save()

        pedido.refresh_from_db()
        self.assertEqual(pedido.cliente_snapshot['nombre'], 'Cliente Original SRL')
        self.assertEqual(pedido.cliente_snapshot['email'], 'original@example.com')
        self.assertEqual(pedido.cliente_snapshot['condicion_pago_id'], '30')

    def test_pedido_historico_sin_snapshot_sigue_siendo_legible(self):
        pedido = Pedido.objects.create(user=self.user, modalidad='retira', con_impuestos=True)
        self.assertEqual(pedido.cliente_snapshot, {})
        self.assertIsNone(pedido.condicion_pago)
