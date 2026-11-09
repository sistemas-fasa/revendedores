from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient


class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='hartge', password='clave-vieja-123', email='cliente@test.com',
        )
        self.sin_email = User.objects.create_user(username='sinemail', password='clave-vieja-123')

    def test_solicitar_envia_email(self):
        resp = self.client.post('/api/password-reset/', {'identificador': 'hartge'})
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('cliente@test.com', mail.outbox[0].to)
        self.assertIn('/recuperar/', mail.outbox[0].body)
        self.assertIn('email_enmascarado', resp.data)

    def test_solicitar_por_email_tambien_funciona(self):
        resp = self.client.post('/api/password-reset/', {'identificador': 'cliente@test.com'})
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(len(mail.outbox), 1)

    def test_sin_email_exige_carga(self):
        resp = self.client.post('/api/password-reset/', {'identificador': 'sinemail'})
        self.assertEqual(resp.status_code, 409, resp.content)
        self.assertIn('email', resp.data['error'].lower())
        self.assertEqual(len(mail.outbox), 0)

    def test_usuario_inexistente_404(self):
        resp = self.client.post('/api/password-reset/', {'identificador': 'nadie'})
        self.assertEqual(resp.status_code, 404, resp.content)

    def test_confirmar_cambia_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        resp = self.client.post('/api/password-reset/confirm/', {
            'uid': uid, 'token': token, 'new_password': 'nueva-clave-4567',
        })
        self.assertEqual(resp.status_code, 200, resp.content)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('nueva-clave-4567'))

    def test_confirmar_token_invalido(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        resp = self.client.post('/api/password-reset/confirm/', {
            'uid': uid, 'token': 'invalido', 'new_password': 'nueva-clave-4567',
        })
        self.assertEqual(resp.status_code, 400, resp.content)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('clave-vieja-123'))
