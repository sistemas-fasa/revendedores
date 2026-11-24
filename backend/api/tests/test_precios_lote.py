"""Lote de precios para auto-carga por visibilidad (Héctor: ver todo rápido)."""
from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory, force_authenticate

from django.test import TestCase

from api.models import Articulos, Cliente, ConsultaPrecio, FormaPago, Localidades
from api.services.precios import calcular_precio_articulo
from api.views import consultar_precios_lote


def _articulo(clave, pbl=Decimal("100.00")):
    return Articulos.objects.create(
        clave=clave, unidad="UN", nombre=f"Art {clave}", peso=Decimal("1.00"),
        precio1=Decimal("100.00"), precio4=Decimal("120.00"),
        pblret1=pbl, pblrep1=pbl, pblret4=pbl, pblrep4=pbl,
        ultact="2026-05-21", visible="S", descripcion="d",
        stock=Decimal("5.00"), empresa_id=1,
    )


class PreciosLoteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="lote", password="t")
        self.fp = FormaPago.objects.create(id="00", nombre="Contado", lista="1",
                                           descuento=Decimal("0.00"), punitorio=Decimal("0.00"))
        self.loc = Localidades.objects.create(codigo="0001", nombre="Pos", fletep1=Decimal("0.00"),
                                               fletetn1=Decimal("0.00"), fletep4=Decimal("0.00"),
                                               fletetn4=Decimal("0.00"))
        self.cliente = Cliente.objects.create(
            user=self.user, numero_cliente="00001", lista_precio="1", nombre="C",
            codigo_localidad=self.loc, condicion_pago=self.fp, tipo_responsable_iva="C")
        self.a1 = _articulo("A001")
        self.a2 = _articulo("A002", Decimal("200.00"))
        self.factory = APIRequestFactory()

    def _post(self, user, body):
        req = self.factory.post("/api/consultar-precios-lote/", body, format="json")
        if user:
            force_authenticate(req, user=user)
        return consultar_precios_lote(req)

    def test_lote_devuelve_precios_y_registra_consultas(self):
        resp = self._post(self.user, {"claves": ["A001", "A002", "NOEXISTE"],
                                      "modalidad": "retira", "con_impuestos": True,
                                      "condicion_pago": "00"})
        self.assertEqual(resp.status_code, 200)
        precios = resp.data["precios"]
        self.assertEqual(set(precios), {"A001", "A002"})
        esperado = calcular_precio_articulo(articulo=self.a1, cliente=self.cliente,
                                            modalidad="retira", con_impuestos=True,
                                            condicion_pago_id="00")
        self.assertEqual(str(precios["A001"]), str(esperado))
        self.assertEqual(ConsultaPrecio.objects.filter(usuario=self.user).count(), 2)

    def test_lote_respeta_tope_y_requiere_auth(self):
        resp = self._post(self.user, {"claves": [f"X{i:03d}" for i in range(60)]})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["precios"], {})
        resp = self._post(None, {"claves": ["A001"]})
        self.assertIn(resp.status_code, (401, 403))
        resp = self._post(self.user, {"claves": []})
        self.assertEqual(resp.status_code, 400)

    def test_lote_sin_registrar_no_crea_consultas(self):
        resp = self._post(self.user, {"claves": ["A001", "A002"], "registrar": False})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(set(resp.data["precios"]), {"A001", "A002"})
        self.assertEqual(ConsultaPrecio.objects.filter(usuario=self.user).count(), 0)
