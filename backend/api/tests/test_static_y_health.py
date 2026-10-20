"""Tests de la exposicion de ``/static/`` y del health check publico.

Contexto: el admin de Django (``/admin/``) llegaba sin CSS y el health check
no era distinguible del index.html de la SPA. Los dos casos se cubren aca:

* ``/static/`` lo sirve el backend con WhiteNoise, no nginx. Django bajo
  gunicorn no sirve archivos estaticos, asi que sin WhiteNoise + collectstatic
  el admin se ve sin estilos.
* ``/health/`` tiene que devolver JSON con ``"status": "ok"``, no el HTML de la
  SPA (que devolvia HTTP 200 y hacia que un monitor diera falso positivo).
"""

import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase

REPO_ROOT = Path(__file__).resolve().parents[3]
NGINX_CONF = REPO_ROOT / 'docker' / 'nginx' / 'default.conf'


class StaticFilesConfigTests(TestCase):
    def test_static_url_es_absoluta(self):
        """Con 'static/' (sin barra) Django genera URLs relativas y todo 404."""
        self.assertTrue(
            settings.STATIC_URL.startswith('/'),
            'STATIC_URL tiene que empezar con "/", si no las URLs son relativas '
            'y desde /admin/ resuelven a /admin/static/...'
        )

    def test_whitenoise_esta_en_el_middleware(self):
        """Sin el middleware de WhiteNoise /static/ no lo sirve nadie."""
        self.assertIn(
            'whitenoise.middleware.WhiteNoiseMiddleware',
            settings.MIDDLEWARE,
        )

    def test_whitenoise_esta_antes_de_common_middleware(self):
        """WhiteNoise tiene que interceptar antes del handler de archivos."""
        middleware = list(settings.MIDDLEWARE)
        self.assertLess(
            middleware.index('whitenoise.middleware.WhiteNoiseMiddleware'),
            middleware.index('django.middleware.common.CommonMiddleware'),
        )

    def test_storages_usa_whitenoise(self):
        """El storage de staticfiles tiene que ser el de WhiteNoise."""
        backend = settings.STORAGES['staticfiles']['BACKEND']
        self.assertTrue(
            backend.startswith('whitenoise.'),
            'El storage de staticfiles deberia ser de WhiteNoise, es %r' % backend
        )

    def test_storages_no_usa_manifest(self):
        """Con manifest, collectstatic falla si falta un archivo y no arranca.

        Se usa a proposito la variante sin manifest: es preferible un admin sin
        CSS a un backend caido.
        """
        backend = settings.STORAGES['staticfiles']['BACKEND']
        self.assertNotIn('Manifest', backend)


class HealthCheckTests(TestCase):
    def test_health_devuelve_200_con_status_ok(self):
        response = self.client.get('/health/')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['status'], 'ok')
        self.assertEqual(payload['database'], 'ok')

    def test_health_devuelve_json_y_no_html(self):
        """La SPA devuelve HTML con 200: por eso el chequeo tiene que ser JSON."""
        response = self.client.get('/health/')

        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('service', response.json())

    def test_health_no_requiere_autenticacion(self):
        """El monitor externo no tiene credenciales: /health/ es publico."""
        response = self.client.get('/health/')

        self.assertEqual(response.status_code, 200)

    def test_health_no_esta_bajo_api(self):
        """La ruta real es /health/; /api/health/ daria 404."""
        self.assertEqual(self.client.get('/api/health/').status_code, 404)


class NginxConfigTests(TestCase):
    """La conf de nginx queda horneada en la imagen del frontend.

    Por eso un cambio aca solo llega a produccion si se rebuilda la imagen, y
    por eso vale la persona tener un test que avise si alguien saca un ``^~``.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.conf = NGINX_CONF.read_text(encoding='utf-8')

    def test_el_archivo_de_conf_existe(self):
        self.assertTrue(NGINX_CONF.is_file())

    def test_health_tiene_match_exacto(self):
        """El "=" gana sobre cualquier otra location: /health/ no cae en la SPA."""
        self.assertRegex(
            self.conf,
            r'location\s+=\s+/health/\s*\{',
            'Falta el match exacto de /health/ en el nginx del frontend',
        )

    def test_health_va_al_backend(self):
        bloque = self._bloque('/health/')
        self.assertIn('proxy_pass', bloque)
        self.assertIn('backend:8000/health/', bloque)

    def test_health_no_tiene_cache(self):
        bloque = self._bloque('/health/')
        self.assertIn('access_log off;', bloque)

    def test_los_prefijos_criticos_usan_rewrite_jerarquico(self):
        """Sin ^~, la location de assets por regex captura /media/*.png -> 404."""
        for prefijo in ('/api/', '/admin/', '/media/', '/static/', '/t/'):
            self.assertRegex(
                self.conf,
                r'location\s+\^~\s+%s\s*\{' % re.escape(prefijo),
                'La location %s tiene que usar ^~, sino la regex de assets la captura' % prefijo
            )

    def test_la_regex_de_assets_sigue_ahi(self):
        """La regex es la que exige el ^~ de arriba: si desaparece, el fix se pierde."""
        self.assertRegex(self.conf, r'location\s+\~\*')

    def _bloque(self, path):
        """Devuelve el bloque de una location del archivo de conf."""
        patron = re.compile(
            r'location\s+(?:=\s+|\^~\s+)?%s\s*\{(.*?)\n\s*\}' % re.escape(path),
            re.DOTALL,
        )
        match = patron.search(self.conf)
        self.assertIsNotNone(match, 'No se encontro la location %s' % path)
        return match.group(1)
