from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from .bot_views import whatsapp_webhook


class WhatsAppWebhookTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    @override_settings(WHATSAPP_VERIFY_TOKEN="token-prueba")
    def test_verifies_meta_webhook_with_expected_token(self):
        request = self.factory.get(
            "/api/whatsapp/webhook/",
            {
                "hub.mode": "subscribe",
                "hub.verify_token": "token-prueba",
                "hub.challenge": "12345",
            },
        )

        response = whatsapp_webhook(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "12345")

    @override_settings(WHATSAPP_VERIFY_TOKEN="token-prueba")
    def test_rejects_meta_webhook_with_wrong_token(self):
        request = self.factory.get(
            "/api/whatsapp/webhook/",
            {
                "hub.mode": "subscribe",
                "hub.verify_token": "otro-token",
                "hub.challenge": "12345",
            },
        )

        response = whatsapp_webhook(request)

        self.assertEqual(response.status_code, 403)

    @override_settings(
        WHATSAPP_ACCESS_TOKEN="",
        WHATSAPP_PHONE_NUMBER_ID="",
    )
    def test_receives_text_message_and_returns_local_reply(self):
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "5493760000000",
                                        "id": "wamid.test",
                                        "type": "text",
                                        "text": {"body": "Hola"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        request = self.factory.post("/api/whatsapp/webhook/", payload, format="json")

        response = whatsapp_webhook(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "received")
        self.assertEqual(response.data["messages_processed"], 1)
        self.assertIn("Hola", response.data["replies"][0]["reply"])
