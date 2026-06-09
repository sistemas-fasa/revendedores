from unittest.mock import MagicMock, patch

from django.test import Client, SimpleTestCase


class HealthCheckTests(SimpleTestCase):
    def test_health_check_reports_application_and_database_status(self):
        with patch("api.health.connection") as connection:
            db_cursor = MagicMock()
            connection.cursor.return_value.__enter__.return_value = db_cursor

            response = Client().get("/health/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "ventas-ferreteria")
        self.assertIn("database", payload)
        db_cursor.execute.assert_called_once_with("SELECT 1")
