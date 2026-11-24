"""Temporal: verifica que ?oferta=1 filtre por oferta='S' (regresión del bug ofertas_enviadas)."""
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from api.models import Articulos
from api.views import ArticuloViewSet


def _art(clave, oferta, stock, stock_efectivo=None):
    return Articulos.objects.create(
        clave=clave, unidad='UN', nombre=f'Art {clave}', peso=1,
        pblret1=Decimal('10'), pblrep1=Decimal('10'),
        pblret4=Decimal('10'), pblrep4=Decimal('10'),
        ultact=date.today(), visible='S', descripcion='d',
        oferta=oferta, stock=stock, stock_efectivo=stock_efectivo,
        empresa_id=1,
    )


class OfertaFilterTest(TestCase):
    def test_oferta_filtra_solo_S_con_stock(self):
        user = User.objects.create_user(username='t-oferta')
        _art('OF-S-STOCK', 'S', Decimal('5'))
        _art('OF-S-SINSTOCK', 'S', Decimal('0'))
        _art('OF-N-STOCK', 'N', Decimal('5'))
        _art('OF-VACIO-STOCK', '', Decimal('5'))

        factory = APIRequestFactory()
        request = factory.get('/api/articulos/', {'oferta': '1', 'page_size': 50})
        force_authenticate(request, user=user)
        view = ArticuloViewSet.as_view({'get': 'list'})
        with self.settings(EMPRESA_ID=1):
            response = view(request)
        self.assertEqual(response.status_code, 200)
        claves = [r['clave'] for r in response.data['results']]
        self.assertEqual(claves, ['OF-S-STOCK'])
