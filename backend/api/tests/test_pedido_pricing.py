from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from api.models import Articulos, Cliente, FormaPago, Localidades, PedidoItem
from api.serializers import PedidoSerializer


class PedidoPricingSecurityTests(TestCase):
    def setUp(self):
        self.forma_pago = FormaPago.objects.create(
            id='00',
            nombre='Contado',
            lista='1',
            descuento=Decimal('10.00'),
            punitorio=Decimal('0.00'),
        )
        self.localidad = Localidades.objects.create(
            codigo='0001',
            nombre='Puerto Rico',
            fletep1=Decimal('0.00'),
            fletetn1=Decimal('0.00'),
            fletep4=Decimal('0.00'),
            fletetn4=Decimal('0.00'),
        )
        self.user = User.objects.create_user(username='cliente-test', password='test12345')
        self.cliente = Cliente.objects.create(
            user=self.user,
            numero_cliente='123',
            lista_precio='1',
            nombre='Cliente Test',
            codigo_localidad=self.localidad,
            condicion_pago=self.forma_pago,
            tipo_responsable_iva='C',
        )
        self.articulo = Articulos.objects.create(
            clave='001.001',
            unidad='UN',
            nombre='Articulo Test',
            peso=Decimal('1.00'),
            iva=Decimal('21.00'),
            mts2=Decimal('0.00'),
            pblret1=Decimal('100.00'),
            pblrep1=Decimal('100.00'),
            pblret4=Decimal('100.00'),
            pblrep4=Decimal('100.00'),
            ultact=date.today(),
            visible='S',
            descripcion='Articulo para test',
        )

    def test_tampered_frontend_price_is_not_persisted(self):
        serializer = PedidoSerializer(data={
            'modalidad': 'retira',
            'con_impuestos': True,
            'items': [{
                'articulo': self.articulo.clave,
                'cantidad': 2,
                'precio_unitario': '1.00',
            }],
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)

        pedido = serializer.save(user=self.user)
        item = PedidoItem.objects.get(pedido=pedido)

        # 100 - 10% descuento + 21% IVA = 108.90
        self.assertEqual(item.precio_unitario, Decimal('108.90'))
        self.assertEqual(item.subtotal, Decimal('217.80'))
        self.assertEqual(pedido.total, Decimal('217.80'))

    def test_nonexistent_article_is_rejected_by_serializer(self):
        serializer = PedidoSerializer(data={
            'modalidad': 'retira',
            'con_impuestos': True,
            'items': [{
                'articulo': '999.999',
                'cantidad': 1,
                'precio_unitario': '1.00',
            }],
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('articulo', serializer.errors['items'][0])

    def test_negative_quantity_is_rejected(self):
        serializer = PedidoSerializer(data={
            'modalidad': 'retira',
            'con_impuestos': True,
            'items': [{
                'articulo': self.articulo.clave,
                'cantidad': -1,
                'precio_unitario': '1.00',
            }],
        })

        self.assertFalse(serializer.is_valid())
        item_errors = serializer.errors['items'][0]
        self.assertTrue(
            'cantidad' in item_errors or 'non_field_errors' in item_errors,
            item_errors,
        )
