from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from api.models import Articulos, ArticuloOculto


def _articulo(clave, nombre='Producto'):
    return Articulos.objects.create(
        clave=clave, nombre=nombre, unidad='UN', peso=1,
        pblret1=Decimal('10'), pblrep1=Decimal('20'),
        pblret4=Decimal('10'), pblrep4=Decimal('20'),
        ultact=date.today(), visible='S', descripcion=nombre,
    )


class ArticuloOcultoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cliente')
        self.staff = User.objects.create_user(username='staff', is_staff=True, is_superuser=True)
        _articulo('REM0022', 'CHOMBA TALLE L')
        _articulo('COR0000', 'CORTE DE MATERIAL')
        _articulo('0290106', 'PERFIL C')
        self.client = APIClient()

    def _claves(self):
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/articulos/', {'page_size': 100})
        self.assertEqual(response.status_code, 200)
        return [r['clave'] for r in response.data['results']]

    def test_sin_reglas_todo_visible(self):
        self.assertEqual(set(self._claves()), {'REM0022', 'COR0000', '0290106'})

    def test_oculta_exacta(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post('/api/ocultos/', {'tipo': 'exacta', 'patron': 'REM0022', 'motivo': 'indumentaria'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('REM0022', self._claves())
        self.assertIn('COR0000', self._claves())

    def test_oculta_prefijo(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post('/api/ocultos/', {'tipo': 'prefijo', 'patron': 'COR0', 'motivo': 'servicio'}, format='json')
        self.assertEqual(response.status_code, 201)
        claves = self._claves()
        self.assertNotIn('COR0000', claves)
        self.assertIn('REM0022', claves)

    def test_prefijo_corto_rechazado(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post('/api/ocultos/', {'tipo': 'prefijo', 'patron': 'CO'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_exacta_inexistente_rechazada(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post('/api/ocultos/', {'tipo': 'exacta', 'patron': 'NOEXISTE'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_no_staff_no_puede_gestionar(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post('/api/ocultos/', {'tipo': 'exacta', 'patron': 'REM0022'}, format='json').status_code, 403)
        self.assertEqual(self.client.get('/api/ocultos/').status_code, 403)

    def test_al_mostrar_vuelve_a_listar(self):
        self.client.force_authenticate(self.staff)
        creado = self.client.post('/api/ocultos/', {'tipo': 'exacta', 'patron': 'REM0022'}, format='json')
        self.assertNotIn('REM0022', self._claves())
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.delete(f"/api/ocultos/{creado.data['id']}/").status_code, 204)
        self.assertIn('REM0022', self._claves())
