from decimal import Decimal
from types import SimpleNamespace

from django.test import TestCase

from api.services.stock import apply_factor, effective_stock, stock_estado


class StockServiceTests(TestCase):
    def test_apply_factor(self):
        self.assertEqual(apply_factor("*0.5", ), Decimal("0.5"))
        self.assertEqual(apply_factor("/2.000"), Decimal("0.5"))
        self.assertEqual(apply_factor("*3"), Decimal("3"))
        self.assertEqual(apply_factor(""), Decimal("1"))
        self.assertIsNone(apply_factor("zzz"))
        self.assertIsNone(apply_factor("/0"))

    def test_effective_stock_uses_parent_scaled(self):
        self.assertEqual(
            effective_stock(Decimal("0"), Decimal("16591.27"), "*0.5"),
            Decimal("16591.27") / Decimal("0.5"),
        )
        self.assertEqual(
            effective_stock(Decimal("0"), Decimal("16591.27"), "/2.000"),
            Decimal("16591.27") / Decimal("0.5"),
        )

    def test_effective_stock_falls_back_to_own(self):
        self.assertEqual(
            effective_stock(Decimal("5"), None, "*0.5"), Decimal("5")
        )
        self.assertEqual(
            effective_stock(Decimal("5"), Decimal("10"), "zzz"), Decimal("5")
        )

    def test_stock_estado(self):
        self.assertEqual(stock_estado(Decimal("0"), Decimal("1")), "rojo")
        self.assertEqual(stock_estado(Decimal("-2"), None), "rojo")
        self.assertEqual(stock_estado(Decimal("1"), Decimal("1")), "amarillo")
        self.assertEqual(stock_estado(Decimal("319"), Decimal("319")), "amarillo")
        self.assertEqual(stock_estado(Decimal("320"), Decimal("319")), "verde")
        self.assertEqual(stock_estado(Decimal("5"), None), "verde")
        self.assertEqual(stock_estado(None, Decimal("1")), "sin_datos")


class ArticuloStockEstadoSerializerTests(TestCase):
    def _articulo(self, **kwargs):
        from api.models import Articulos

        base = dict(
            clave="900.001",
            unidad="UN",
            nombre="Test",
            peso=Decimal("1"),
            espesor=Decimal("0"),
            iva=Decimal("21"),
            mts2=Decimal("0"),
            precio1=Decimal("0"),
            precio4=Decimal("0"),
            pblret1=Decimal("0"),
            pblrep1=Decimal("0"),
            pblret4=Decimal("0"),
            pblrep4=Decimal("0"),
            ultact="2026-01-01",
            visible="S",
            descripcion="Test",
        )
        base.update(kwargs)
        return Articulos(**base)

    def test_serializer_estado_rojo_amarillo_verde(self):
        from api.serializers import ArticuloSerializer

        rojo = self._articulo(stock=Decimal("0"), stock_efectivo=Decimal("0"),
                              stock_minimo=Decimal("1"))
        self.assertEqual(ArticuloSerializer(rojo).data["stock_estado"], "rojo")
        amarillo = self._articulo(stock=Decimal("16591.27"),
                                  stock_efectivo=Decimal("638"),
                                  stock_minimo=Decimal("638"))
        self.assertEqual(ArticuloSerializer(amarillo).data["stock_estado"], "amarillo")
        verde = self._articulo(stock=Decimal("16591.27"),
                               stock_efectivo=Decimal("16591.27"),
                               stock_minimo=Decimal("319"))
        self.assertEqual(ArticuloSerializer(verde).data["stock_estado"], "verde")

    def test_serializer_estado_fallback_stock_propio(self):
        from api.serializers import ArticuloSerializer

        art = self._articulo(stock=Decimal("3"), stock_efectivo=None,
                             stock_minimo=None)
        self.assertEqual(ArticuloSerializer(art).data["stock_estado"], "verde")
