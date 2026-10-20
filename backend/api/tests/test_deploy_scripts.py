"""Tests de los archivos de deploy que no se pueden verificar en runtime.

El entrypoint y el script de cron viven en el repo pero se ejecutan **dentro
del container** y **en el host**, respectivamente: si alguien los borra o les
saca una linea, en produccion no se ve ningun error claro (el admin queda sin
CSS, o las imagenes del catalogo se rompen de nuevo en silencio).

Estos tests no ejecutan nada: solo verifican que los archivos esten y que
contengan lo que tienen que contener.
"""

from pathlib import Path

from django.test import SimpleTestCase

REPO_ROOT = Path(__file__).resolve().parents[3]
ENTRYPOINT = REPO_ROOT / 'staging' / 'revendedores-entrypoint.sh'
BACKEND_DOCKERFILE = REPO_ROOT / 'staging' / 'Dockerfile.revendedores.backend'
BACKEND_DOCKERFILE_GIT = REPO_ROOT / 'docker' / 'Dockerfile.backend'
CRON_SCRIPT = REPO_ROOT / 'scripts' / 'normalizar-imagenes-cron.sh'


class StagingVersionadoTests(SimpleTestCase):
    """``staging/`` solo existia en el server: ahora esta en git.

    El build de produccion del backend usa
    ``staging/Dockerfile.revendedores.backend``, asi que si estos archivos no
    estan en el repo el build no es reproducible.
    """

    def test_el_entrypoint_esta_versionado(self):
        self.assertTrue(ENTRYPOINT.is_file(), 'Falta %s' % ENTRYPOINT)

    def test_el_dockerfile_de_staging_esta_versionado(self):
        self.assertTrue(BACKEND_DOCKERFILE.is_file(), 'Falta %s' % BACKEND_DOCKERFILE)

    def test_el_script_de_cron_esta_versionado(self):
        self.assertTrue(CRON_SCRIPT.is_file(), 'Falta %s' % CRON_SCRIPT)

    def test_el_entrypoint_corre_collectstatic(self):
        """Sin collectstatic, /app/staticfiles queda vacio y /static/ da 404."""
        contenido = ENTRYPOINT.read_text(encoding='utf-8')

        self.assertIn('collectstatic', contenido)
        self.assertIn('--noinput', contenido)

    def test_el_entrypoint_carga_el_secret(self):
        """Sin cargar el .env del secret, Django no encuentra SECRET_KEY."""
        contenido = ENTRYPOINT.read_text(encoding='utf-8')

        self.assertIn('/run/secrets/revendedores.env', contenido)

    def test_collectstatic_no_aborta_el_arranque(self):
        """Si collectstatic falla, el backend tiene que levantar igual."""
        contenido = ENTRYPOINT.read_text(encoding='utf-8')

        self.assertIn('returncode', contenido)
        self.assertNotIn('sys.exit(', contenido.split('def run_collectstatic')[1].split('def ')[0])

    def test_los_dockerfiles_instalan_el_entrypoint(self):
        """Los dos Dockerfiles del backend usan la misma fuente del entrypoint."""
        for dockerfile in (BACKEND_DOCKERFILE, BACKEND_DOCKERFILE_GIT):
            contenido = dockerfile.read_text(encoding='utf-8')
            with self.subTest(dockerfile=dockerfile.name):
                self.assertIn('staging/revendedores-entrypoint.sh', contenido)
                self.assertIn('ENTRYPOINT ["/usr/local/bin/revendedores-entrypoint"]', contenido)


class CronNormalizarImagenesTests(SimpleTestCase):
    def test_el_script_usa_el_comando_de_normalizacion(self):
        contenido = CRON_SCRIPT.read_text(encoding='utf-8')

        self.assertIn('normalizar_imagenes', contenido)

    def test_el_script_usa_el_entrypoint_para_cargar_el_env(self):
        """Sin el entrypoint, el comando falla con SECRET_KEY not found."""
        contenido = CRON_SCRIPT.read_text(encoding='utf-8')

        self.assertIn('revendedores-entrypoint', contenido)

    def test_el_script_resuelve_el_contenedor_en_vuelo(self):
        """El sufijo del contenedor lo genera Coolify: no se puede hardcodear."""
        contenido = CRON_SCRIPT.read_text(encoding='utf-8')

        self.assertIn('docker ps', contenido)
        self.assertNotIn('backend-1ezipmojg3zemckxlug8ndjv', contenido)

    def test_el_script_escribe_log(self):
        contenido = CRON_SCRIPT.read_text(encoding='utf-8')

        self.assertIn('normalizar-imagenes.log', contenido)


class PwaServiceWorkerConfigTests(SimpleTestCase):
    """El service worker de la PWA sirve el index.html de la SPA en TODA navegacion.

    Eso tapaba el admin de Django: al abrir /admin/ el SW contestaba con la
    SPA en vez de dejar que la request fuera al backend. Y de paso podia
    servir un health check viejo desde el cache.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = (REPO_ROOT / 'frontend' / 'vite.config.ts').read_text(encoding='utf-8')

    def test_el_denylist_excluye_admin_y_health(self):
        """Sin denylist, la navegacion a /admin/ y /health/ devuelve la SPA."""
        self.assertIn('navigateFallbackDenylist', self.config)
        self.assertIn(r'/^\/admin\//', self.config)
        self.assertIn(r'/^\/health\//', self.config)

    def test_admin_y_health_van_siempre_a_la_red(self):
        self.assertIn('no-cache-backend', self.config)
        self.assertIn("url.pathname === '/health/'", self.config)

    def test_la_regla_de_admin_y_health_va_antes_de_la_same_origin(self):
        """En Workbox gana la primera ruta que matchea, y la same-origin
        (NetworkFirst) matchea TODO lo del mismo origen."""
        self.assertLess(
            self.config.index('no-cache-backend'),
            self.config.index('url.origin === self.origin'),
        )
