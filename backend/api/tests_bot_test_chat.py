from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Articulos, BotConversationLog, Cliente, FormaPago, Localidades


class BotTestChatApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="tester", password="test", is_staff=True)
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
            nombre="Cliente de prueba",
            codigo_localidad=self.localidad,
            condicion_pago=self.forma_pago,
            tipo_responsable_iva="C",
        )
        Articulos.objects.create(
            clave="001.001",
            unidad="UN",
            nombre="Cemento bolsa 50kg",
            peso=Decimal("1.00"),
            espesor=Decimal("0.00"),
            iva=Decimal("21.00"),
            mts2=Decimal("0.00"),
            precio1=Decimal("100.00"),
            precio4=Decimal("100.00"),
            reparto="",
            redferre="",
            tiporeparto="",
            campoa1="",
            reducida="",
            preciopub=Decimal("0.00"),
            recargo=Decimal("0.00"),
            estado="",
            pblret1=Decimal("100.00"),
            pblrep1=Decimal("100.00"),
            pblret4=Decimal("100.00"),
            pblrep4=Decimal("100.00"),
            ultact="2026-05-21",
            visible="S",
            grupo="001",
            stock=Decimal("12.00"),
            formula="",
            descripcion="Cemento comun",
            discontinuado="",
            oferta="",
            empresa_id=1,
        )
        Articulos.objects.create(
            clave="001.002",
            unidad="UN",
            nombre="Cemento rapido 1kg",
            peso=Decimal("1.00"),
            espesor=Decimal("0.00"),
            iva=Decimal("21.00"),
            mts2=Decimal("0.00"),
            precio1=Decimal("20.00"),
            precio4=Decimal("20.00"),
            reparto="",
            redferre="",
            tiporeparto="",
            campoa1="",
            reducida="",
            preciopub=Decimal("0.00"),
            recargo=Decimal("0.00"),
            estado="",
            pblret1=Decimal("20.00"),
            pblrep1=Decimal("20.00"),
            pblret4=Decimal("20.00"),
            pblrep4=Decimal("20.00"),
            ultact="2026-05-21",
            visible="S",
            grupo="001",
            stock=Decimal("3.00"),
            formula="",
            descripcion="Cemento rapido",
            discontinuado="",
            oferta="",
            empresa_id=1,
        )

    def test_local_chat_uses_authenticated_user_for_price_context(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/bot/test-chat/",
            {"message": "precio 001.001"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["message"], "precio 001.001")
        self.assertIn("Cemento bolsa 50kg", response.data["reply"])
        self.assertIn("Precio retira con IVA: $121.00", response.data["reply"])
        self.assertTrue(response.data["debug"]["local_test"])

        log = BotConversationLog.objects.get()
        self.assertEqual(log.origen, "chat_local")
        self.assertEqual(log.usuario, self.user)
        self.assertEqual(log.mensaje_usuario, "precio 001.001")
        self.assertIn("Cemento bolsa 50kg", log.respuesta_bot)
        self.assertEqual(log.intencion, "precio_stock")
        self.assertEqual(log.estado, "ok")

    def test_local_chat_requires_staff_user(self):
        normal_user = get_user_model().objects.create_user(username="cliente", password="test")
        self.client.force_authenticate(normal_user)

        response = self.client.post(
            "/api/bot/test-chat/",
            {"message": "precio 001.001"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_local_chat_resolves_follow_up_against_pending_options(self):
        self.client.force_authenticate(self.user)

        first_response = self.client.post(
            "/api/bot/test-chat/",
            {"message": "precio cemento"},
            format="json",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertIn("Encontre varias opciones", first_response.data["reply"])
        self.assertIn("pending_options", first_response.data["context"])
        first_log = BotConversationLog.objects.latest("fecha_hora")
        self.assertEqual(first_log.estado, "ambiguous")
        self.assertEqual(first_log.origen, "chat_local")

        second_response = self.client.post(
            "/api/bot/test-chat/",
            {
                "message": "rapido",
                "context": first_response.data["context"],
            },
            format="json",
        )

        self.assertEqual(second_response.status_code, 200)
        self.assertIn("Cemento rapido 1kg", second_response.data["reply"])
        self.assertIn("Precio retira con IVA: $24.20", second_response.data["reply"])
        second_log = BotConversationLog.objects.latest("fecha_hora")
        self.assertEqual(second_log.estado, "ok")
        self.assertEqual(second_log.contexto, {})
