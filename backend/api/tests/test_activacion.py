"""Tests del flujo de activación con código de cliente + OTP.

El throttle de recupero se relaja en este módulo (1000/hora) para no
interferir entre pruebas; el valor real (10/hora) se testea aparte.
"""

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from rest_framework.test import APIClient

from api.activacion_views import _hash_otp, ActivacionRateThrottle
from api.erp_clientes import normalizar_codigo
from api.models import ActivacionOTP, Cliente, FormaPago, Localidades
from api.services.vogel_whatsapp import VogelWhatsAppClient, normalize_phone_ar

ActivacionRateThrottle.rate = '1000/hour'


def _crear_cliente(numero='00040', username='cliente40', password=None):
    if password:
        user = User.objects.create_user(username=username, password=password)
    else:
        user = User.objects.create(username=username)
        user.set_unusable_password()
        user.save()
    loc, _ = Localidades.objects.get_or_create(codigo='9999', defaults={'nombre': 'Prueba'})
    pago, _ = FormaPago.objects.get_or_create(
        id='99', defaults={'nombre': 'Contado', 'descuento': 0, 'punitorio': 0})
    cliente = Cliente.objects.create(
        user=user, numero_cliente=numero, nombre='Cliente Cuarenta',
        lista_precio='1', codigo_localidad=loc, condicion_pago=pago,
        tipo_responsable_iva='C',
    )
    return user, cliente


class NormalizarCodigoTests(TestCase):
    def test_zfill_y_no_numerico(self):
        self.assertEqual(normalizar_codigo('40'), '00040')
        self.assertEqual(normalizar_codigo(' 00040 '), '00040')
        self.assertIsNone(normalizar_codigo('oscar'))
        self.assertIsNone(normalizar_codigo(''))


class IniciarTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        _, self.cliente = _crear_cliente()

    def test_codigo_inexistente_404(self):
        resp = self.api.post('/api/activacion/iniciar/', {'codigo_cliente': '99998'}, format='json')
        self.assertEqual(resp.status_code, 404)

    def test_codigo_no_numerico_400(self):
        resp = self.api.post('/api/activacion/iniciar/', {'codigo_cliente': 'oscar'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_cuenta_sin_password_devuelve_enmascarados(self):
        resp = self.api.post('/api/activacion/iniciar/', {'codigo_cliente': '40'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['numero_cliente'], '00040')
        self.assertIsNone(resp.data['email_enmascarado'])
        self.assertIsNone(resp.data['whatsapp_enmascarado'])

    def test_cuenta_con_password_409(self):
        _crear_cliente(numero='00041', username='cliente41', password='Clave12345')
        resp = self.api.post('/api/activacion/iniciar/', {'codigo_cliente': '00041'}, format='json')
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.data['code'], 'ya_activa')


class EnviarTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._override = override_settings(WHATSAPP_ENABLED=False, ACTIVACION_EMAIL_VIA_COLA=False)
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._override.disable()
        super().tearDownClass()

    def setUp(self):
        self.api = APIClient()
        _, self.cliente = _crear_cliente()

    def test_email_invalido_400(self):
        resp = self.api.post('/api/activacion/enviar/', {
            'codigo_cliente': '00040', 'email': 'no-es-mail', 'whatsapp': '11-1234-5678'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_whatsapp_invalido_400(self):
        resp = self.api.post('/api/activacion/enviar/', {
            'codigo_cliente': '00040', 'email': 'c@mail.com', 'whatsapp': 'abc'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_envio_ok_202_y_persiste_hash(self):
        resp = self.api.post('/api/activacion/enviar/', {
            'codigo_cliente': '00040', 'email': 'c@mail.com', 'whatsapp': '11-1234-5678'}, format='json')
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('c@mail.com', mail.outbox[0].to)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.whatsapp, '5491112345678')
        registro = ActivacionOTP.objects.get(cliente=self.cliente)
        self.assertEqual(len(registro.codigo_hash), 64)
        for valor in (registro.codigo_hash, registro.salt, registro.whatsapp_message_id):
            self.assertNotRegex(valor or 'x', r'^\d{6}$')
        self.assertEqual(registro.canal_email_estado, 'ENVIADO')
        # Sin WHATSAPP_ENABLED en tests, el canal queda omitido (sin error).
        self.assertEqual(registro.canal_whatsapp_estado, 'PENDIENTE')

    def test_cooldown_reenvio_429(self):
        datos = {'codigo_cliente': '00040', 'email': 'c@mail.com', 'whatsapp': '11-1234-5678'}
        self.assertEqual(self.api.post('/api/activacion/enviar/', datos, format='json').status_code, 202)
        resp = self.api.post('/api/activacion/enviar/', datos, format='json')
        self.assertEqual(resp.status_code, 429)
        self.assertIn('reintentar_en', resp.data)


class VerificarConfirmarTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        _, self.cliente = _crear_cliente()
        # OTP conocido: hash de '123456' con salt fijo.
        self.otp = '123456'
        self.registro = ActivacionOTP.objects.create(
            cliente=self.cliente,
            codigo_hash=_hash_otp(self.otp, 's' * 32),
            salt='s' * 32,
            expira_at=timezone.now() + timedelta(minutes=10),
            ultimo_envio_at=timezone.now(),
        )

    def test_codigo_mal_resta_intentos(self):
        resp = self.api.post('/api/activacion/verificar/',
                             {'codigo_cliente': '00040', 'otp': '000000'}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.registro.refresh_from_db()
        self.assertEqual(self.registro.intentos, 1)

    def test_codigo_ok(self):
        resp = self.api.post('/api/activacion/verificar/',
                             {'codigo_cliente': '00040', 'otp': '123456'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['ok'])

    def test_bloqueo_por_intentos(self):
        for _ in range(5):
            self.api.post('/api/activacion/verificar/',
                          {'codigo_cliente': '00040', 'otp': '000000'}, format='json')
        resp = self.api.post('/api/activacion/verificar/',
                             {'codigo_cliente': '00040', 'otp': '123456'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_expirado_rechazado(self):
        self.registro.expira_at = timezone.now() - timedelta(seconds=1)
        self.registro.save(update_fields=['expira_at'])
        resp = self.api.post('/api/activacion/verificar/',
                             {'codigo_cliente': '00040', 'otp': '123456'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_confirmar_passwords_distintas_400(self):
        resp = self.api.post('/api/activacion/confirmar/', {
            'codigo_cliente': '00040', 'otp': '123456',
            'password1': 'Clave12345', 'password2': 'Otra12345'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_confirmar_clave_debil_400(self):
        resp = self.api.post('/api/activacion/confirmar/', {
            'codigo_cliente': '00040', 'otp': '123456',
            'password1': '123', 'password2': '123'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_confirmar_ok_login_automatico(self):
        resp = self.api.post('/api/activacion/confirmar/', {
            'codigo_cliente': '00040', 'otp': '123456',
            'password1': 'Clave12345', 'password2': 'Clave12345'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.data)
        self.assertIn('session_id', resp.data)
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.whatsapp_verificado)
        self.assertTrue(self.cliente.user.has_usable_password())
        self.registro.refresh_from_db()
        self.assertIsNotNone(self.registro.consumido_at)
        # El JWT sirve para endpoints autenticados.
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        self.assertEqual(self.api.get('/api/permiso-descarga-lista/').status_code, 200)


class LoginDualTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        _, self.cliente = _crear_cliente(username='cliente40', password='Clave12345')

    def test_login_con_numero_cliente(self):
        resp = self.api.post('/api/token/', {'username': '40', 'password': 'Clave12345'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('session_id', resp.data)

    def test_login_con_username_sigue_igual(self):
        resp = self.api.post('/api/token/', {'username': 'cliente40', 'password': 'Clave12345'}, format='json')
        self.assertEqual(resp.status_code, 200)

    def test_login_sin_password_409(self):
        user = User.objects.create(username='sinclave')
        user.set_unusable_password()
        user.save()
        loc = Localidades.objects.get(codigo='9999')
        pago = FormaPago.objects.get(id='99')
        Cliente.objects.create(user=user, numero_cliente='00042', nombre='Sin Clave',
                               lista_precio='1', codigo_localidad=loc, condicion_pago=pago,
                               tipo_responsable_iva='C')
        resp = self.api.post('/api/token/', {'username': '00042', 'password': 'x'}, format='json')
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.data['code'], 'activacion_pendiente')


@override_settings(WHATSAPP_ENABLED=False)
class VogelClientTests(TestCase):
    def test_normalize_phone_ar(self):
        self.assertEqual(normalize_phone_ar('11-1234-5678'), '5491112345678')
        self.assertEqual(normalize_phone_ar('03764-123456'), '5493764123456')
        self.assertEqual(normalize_phone_ar('+54 9 376 412-3456'), '5493764123456')
        self.assertIsNone(normalize_phone_ar('abc'))
        self.assertIsNone(normalize_phone_ar('123'))

    def test_deshabilitado_no_hace_red(self):
        resultado = VogelWhatsAppClient().send_text('5491112345678', 'hola', external_ref='test')
        self.assertEqual(resultado, {'sent': False, 'reason': 'not_configured'})


class ColaEmailTests(TestCase):
    def _sin_fe(self):
        dbs = dict(settings.DATABASES)
        dbs.pop('fe', None)
        return dbs

    def test_sanitizar_latin1(self):
        from api.services.email_cola import sanitizar_latin1
        self.assertEqual(sanitizar_latin1('código verificación'), 'código verificación')
        self.assertNotIn('😀', sanitizar_latin1('hola 😀'))
        self.assertIsNone(sanitizar_latin1(None))

    def test_sin_alias_fe_devuelve_none(self):
        from api.services.email_cola import encolar_email
        with self.settings(DATABASES=self._sin_fe()):
            self.assertIsNone(encolar_email('a@b.com', 'asunto', cuerpo_texto='hola'))

    def test_destinatario_invalido_devuelve_none(self):
        from api.services.email_cola import encolar_email
        with self.settings(DATABASES=self._sin_fe()):
            self.assertIsNone(encolar_email('a@b.com,otro@c.com', 'asunto'))
            self.assertIsNone(encolar_email('áé@b.com', 'asunto'))

    def test_enviar_cae_a_smtp_si_no_hay_cola(self):
        # Sin alias `fe`, el envío cae al SMTP directo (locmem en CI).
        with self.settings(DATABASES=self._sin_fe(),
                           ACTIVACION_EMAIL_VIA_COLA=True,
                           WHATSAPP_ENABLED=False):
            _, cliente = _crear_cliente(numero='00043', username='cliente43')
            api = APIClient()
            resp = api.post('/api/activacion/enviar/', {
                'codigo_cliente': '00043', 'email': 'c@mail.com',
                'whatsapp': '11-1234-5678'}, format='json')
            self.assertEqual(resp.status_code, 202)
            self.assertEqual(resp.data['canales']['email'], 'ok')
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn('c@mail.com', mail.outbox[0].to)
