from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from .models import Articulos, Cliente, FormaPago, Localidades
from .services.whatsapp_price import build_price_reply


class WhatsAppPriceReplyTests(TestCase):
    databases = {"default", "fasa"}

    def setUp(self):
        self.user = User.objects.create_user(username="botwhatsapp", password="test")
        self.forma_pago = FormaPago.objects.create(
            id="00",
            nombre="Contado",
            lista="1",
            descuento=Decimal("0.00"),
            punitorio=Decimal("0.00"),
        )
        self.localidad = Localidades.objects.create(
            codigo="0001",
            nombre="Posadas",
            fletep1=Decimal("0.00"),
            fletetn1=Decimal("0.00"),
            fletep4=Decimal("0.00"),
            fletetn4=Decimal("0.00"),
        )
        Cliente.objects.create(
            user=self.user,
            numero_cliente="00001",
            lista_precio="1",
            nombre="Cliente Bot WhatsApp",
            codigo_localidad=self.localidad,
            condicion_pago=self.forma_pago,
            tipo_responsable_iva="C",
        )
        self._create_articulo("001.001", "Cemento bolsa 50kg", "Cemento comun", Decimal("100.00"), Decimal("12.00"))

    def _create_articulo(self, clave, nombre, descripcion, precio, stock):
        return Articulos.objects.create(
            clave=clave,
            unidad="UN",
            nombre=nombre,
            peso=Decimal("1.00"),
            espesor=Decimal("0.00"),
            iva=Decimal("21.00"),
            mts2=Decimal("0.00"),
            precio1=precio,
            precio4=precio,
            reparto="",
            redferre="",
            tiporeparto="",
            campoa1="",
            reducida="",
            preciopub=Decimal("0.00"),
            recargo=Decimal("0.00"),
            estado="",
            pblret1=precio,
            pblrep1=precio,
            pblret4=precio,
            pblrep4=precio,
            ultact="2026-05-21",
            visible="S",
            grupo="001",
            stock=stock,
            formula="",
            descripcion=descripcion,
            discontinuado="",
            oferta="",
            empresa_id=1,
        )

    @override_settings(WHATSAPP_BOT_USERNAME="botwhatsapp", EMPRESA_ID=1)
    def test_builds_price_reply_for_clear_product_match(self):
        result = build_price_reply("precio cemento")

        self.assertTrue(result["handled"])
        self.assertIn("Cemento bolsa 50kg", result["reply"])
        self.assertIn("$121.00", result["reply"])
        self.assertNotIn("Stock:", result["reply"])
        self.assertIn("presupuesto", result["reply"])
        self.assertIn("otra mercaderia", result["reply"])

    @override_settings(WHATSAPP_BOT_USERNAME="botwhatsapp", EMPRESA_ID=1)
    @patch("api.services.whatsapp_price.get_related_products_for_article")
    def test_offers_related_products_without_stock(self, get_related_products):
        get_related_products.return_value = [
            {"clave": "009.001", "detalle": "Arena embolsada", "unidad": "UN", "origen": "MANUAL"},
            {"clave": "009.002", "detalle": "Cal hidratada", "unidad": "UN", "origen": "AUTO"},
        ]

        result = build_price_reply("precio cemento")

        self.assertTrue(result["handled"])
        self.assertIn("Tambien te puedo ofrecer", result["reply"])
        self.assertIn("009.001: Arena embolsada", result["reply"])
        self.assertIn("009.002: Cal hidratada", result["reply"])
        self.assertNotIn("Stock:", result["reply"])

    @override_settings(WHATSAPP_BOT_USERNAME="botwhatsapp", EMPRESA_ID=1)
    def test_builds_price_reply_when_user_sends_only_product_name(self):
        result = build_price_reply("cemento")

        self.assertTrue(result["handled"])
        self.assertIn("Cemento bolsa 50kg", result["reply"])
        self.assertNotIn("Recibi tu mensaje", result["reply"])

    @override_settings(WHATSAPP_BOT_USERNAME="botwhatsapp", EMPRESA_ID=1)
    def test_asks_for_clarification_when_product_is_ambiguous(self):
        self._create_articulo("001.002", "Cemento rapido 1kg", "Cemento rapido", Decimal("20.00"), Decimal("3.00"))

        result = build_price_reply("precio cemento")

        self.assertTrue(result["handled"])
        self.assertIn("Encontre varias opciones", result["reply"])
        self.assertIn("001.001", result["reply"])
        self.assertIn("001.002", result["reply"])
        self.assertIn("presupuesto", result["reply"])

    @override_settings(WHATSAPP_BOT_USERNAME="botwhatsapp", EMPRESA_ID=1)
    def test_returns_not_found_when_no_product_matches(self):
        result = build_price_reply("precio producto inexistente")

        self.assertTrue(result["handled"])
        self.assertIn("No encontre", result["reply"])

    @override_settings(WHATSAPP_BOT_USERNAME="botwhatsapp", EMPRESA_ID=1)
    def test_returns_more_options_when_user_asks_if_only_those_are_available(self):
        self._create_articulo("002.040", "Ceramica lote 1", "Ceramica piso", Decimal("100.00"), Decimal("2.00"))
        self._create_articulo("002.041", "Ceramica lote 2", "Ceramica piso", Decimal("110.00"), Decimal("2.00"))
        self._create_articulo("002.042", "Ceramica lote 3", "Ceramica piso", Decimal("120.00"), Decimal("2.00"))
        self._create_articulo("002.043", "Ceramica lote 4", "Ceramica piso", Decimal("130.00"), Decimal("2.00"))

        first_result = build_price_reply("tenes ceramica?")
        second_result = build_price_reply("solo esas tenes?", context=first_result["context"])

        self.assertTrue(second_result["handled"])
        self.assertIn("Tengo mas opciones", second_result["reply"])
        self.assertIn("002.043", second_result["reply"])
        self.assertIn("presupuesto", second_result["reply"])
        self.assertNotIn("No encontre", second_result["reply"])

    @override_settings(WHATSAPP_BOT_USERNAME="botwhatsapp", EMPRESA_ID=1)
    def test_matches_plural_product_words(self):
        self._create_articulo("002.040", "Ceramica lote 1", "Ceramica piso", Decimal("100.00"), Decimal("2.00"))

        result = build_price_reply("tenes ceramicas?")

        self.assertTrue(result["handled"])
        self.assertIn("Ceramica lote 1", result["reply"])
        self.assertNotIn("No encontre", result["reply"])

    @override_settings(WHATSAPP_BOT_USERNAME="botwhatsapp", EMPRESA_ID=1)
    def test_understands_natural_selection_from_pending_options(self):
        self._create_articulo("434.000", "Pegamento ceramica Klaukol", "Pegamento impermeable", Decimal("200.00"), Decimal("4.00"))

        result = build_price_reply(
            "pegamento de ceramica quiero",
            context={
                "pending_options": [
                    {"clave": "332.085", "nombre": 'CINTA PVC S/PEGAMENTO 20 MTS.NEG."TACSA"'},
                    {"clave": "434.000", "nombre": "Pegamento ceramica Klaukol"},
                ],
                "last_query": "y pegamento",
                "shown_count": 2,
            },
        )

        self.assertTrue(result["handled"])
        self.assertIn("Pegamento ceramica Klaukol", result["reply"])
        self.assertIn("Precio retira con IVA", result["reply"])
        self.assertNotIn("Recibi tu mensaje", result["reply"])

    @override_settings(WHATSAPP_BOT_USERNAME="botwhatsapp", EMPRESA_ID=1)
    def test_keeps_partial_natural_selection_inside_pending_options(self):
        self._create_articulo("434.000", "PEGAMENTO IMPERMEABLE POTENCIADO KLAUKOL", "Pegamento", Decimal("200.00"), Decimal("4.00"))
        self._create_articulo("434.002", "PEGAMENTO IMPERMEABLE POTENCIADO KLAUKOL", "Pegamento", Decimal("210.00"), Decimal("4.00"))

        result = build_price_reply(
            "pegamento de ceramica quiero",
            context={
                "pending_options": [
                    {"clave": "332.085", "nombre": 'CINTA PVC S/PEGAMENTO 20 MTS.NEG."TACSA"'},
                    {"clave": "434.000", "nombre": "PEGAMENTO IMPERMEABLE POTENCIADO KLAUKOL"},
                    {"clave": "434.002", "nombre": "PEGAMENTO IMPERMEABLE POTENCIADO KLAUKOL"},
                ],
                "last_query": "pegamento",
                "shown_count": 3,
            },
        )

        self.assertTrue(result["handled"])
        self.assertIn("Todavia veo mas de una opcion", result["reply"])
        self.assertIn("434.000", result["reply"])
        self.assertIn("434.002", result["reply"])
        self.assertNotIn("Recibi tu mensaje", result["reply"])

    @override_settings(WHATSAPP_BOT_USERNAME="botwhatsapp", EMPRESA_ID=1)
    def test_handles_comparison_question_inside_pending_options(self):
        result = build_price_reply(
            "cual es mejor?",
            context={
                "pending_options": [
                    {"clave": "434.000", "nombre": "PEGAMENTO IMPERMEABLE POTENCIADO KLAUKOL"},
                    {"clave": "434.002", "nombre": "PEGAMENTO IMPERMEABLE POTENCIADO KLAUKOL"},
                ],
                "last_query": "pegamento",
                "shown_count": 2,
            },
        )

        self.assertTrue(result["handled"])
        self.assertIn("para recomendarte mejor", result["reply"].lower())
        self.assertIn("434.000", result["reply"])
        self.assertIn("434.002", result["reply"])
        self.assertNotIn("Recibi tu mensaje", result["reply"])
