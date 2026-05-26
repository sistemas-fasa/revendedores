from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import BotConversationLog


class BotReportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = get_user_model().objects.create_user(
            username="staff",
            password="test",
            is_staff=True,
        )
        self.user = get_user_model().objects.create_user(username="cliente", password="test")

        BotConversationLog.objects.create(
            origen="chat_local",
            usuario=self.staff,
            mensaje_usuario="precio cemento",
            respuesta_bot="Encontre varias opciones",
            intencion="precio_stock",
            estado="ambiguous",
            contexto={"pending_options": [{"clave": ".03.011"}]},
        )
        BotConversationLog.objects.create(
            origen="chat_local",
            usuario=self.staff,
            mensaje_usuario="holcim",
            respuesta_bot="CEMENTO HOLCIM Precio retira con IVA: $1",
            intencion="precio_stock",
            estado="ok",
            contexto={},
        )
        BotConversationLog.objects.create(
            origen="whatsapp",
            telefono="5493760000000",
            mensaje_usuario="hola",
            respuesta_bot="Hola",
            intencion="fallback",
            estado="fallback",
            contexto={},
        )

    def test_report_requires_staff_user(self):
        self.client.force_authenticate(self.user)

        response = self.client.get("/api/staff/bot/report/")

        self.assertEqual(response.status_code, 403)

    def test_report_summarizes_bot_logs_for_staff(self):
        self.client.force_authenticate(self.staff)

        response = self.client.get("/api/staff/bot/report/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_messages"], 3)
        self.assertEqual(response.data["by_origin"]["chat_local"], 2)
        self.assertEqual(response.data["by_origin"]["whatsapp"], 1)
        self.assertEqual(response.data["by_intention"]["precio_stock"], 2)
        self.assertEqual(response.data["by_status"]["ambiguous"], 1)
        self.assertEqual(response.data["by_status"]["ok"], 1)
        self.assertEqual(len(response.data["recent"]), 3)
        self.assertIn("recommendations", response.data)
