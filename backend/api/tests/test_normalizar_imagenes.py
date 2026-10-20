"""Tests del comando ``manage.py normalizar_imagenes``.

El caso que se cubre: la importacion del ERP deja referencias con la extension
en mayuscula (``002.534.PNG``) mientras que el archivo en disco esta en
minuscula (``002.534.png``). En Linux eso es un 404 y el catalogo muestra el
texto alternativo en vez de la imagen.
"""

import os
import shutil
import tempfile
from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings

from api.models import Articulos


class NormalizarImagenesCommandTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix='test-media-')
        # Archivo real en disco, en minuscula.
        with open(os.path.join(self.media_root, '002.534.png'), 'wb') as fh:
            fh.write(b'x')
        with open(os.path.join(self.media_root, '002.110.png'), 'wb') as fh:
            fh.write(b'x')

        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(shutil.rmtree, self.media_root, True)

    def _crear(self, clave, imagen):
        return Articulos.objects.create(
            clave=clave,
            unidad='UN',
            nombre='Articulo Test',
            peso=Decimal('25.00'),
            descripcion='',
            pblret1=Decimal('0.00'),
            pblrep1=Decimal('0.00'),
            pblret4=Decimal('0.00'),
            pblrep4=Decimal('0.00'),
            ultact=date(2026, 1, 1),
            visible='S',
            imagen=imagen,
            empresa_id=1,
        )

    def test_corrige_extension_en_mayuscula(self):
        """Referencia en mayuscula + archivo en minuscula -> se corrige."""
        self._crear('TST0001', '002.534.PNG')

        call_command('normalizar_imagenes', stdout=StringIO())

        self.assertEqual(Articulos.objects.get(clave='TST0001').imagen.name, '002.534.png')

    def test_no_toca_referencia_correcta(self):
        """La referencia que ya coincide con el archivo no se modifica."""
        self._crear('TST0002', '002.110.png')

        call_command('normalizar_imagenes', stdout=StringIO())

        self.assertEqual(Articulos.objects.get(clave='TST0002').imagen.name, '002.110.png')

    def test_no_toca_referencia_sin_archivo(self):
        """Si el archivo no existe en ningun case, la referencia no se cambia."""
        self._crear('TST0003', 'NO.EXISTE.png')

        call_command('normalizar_imagenes', stdout=StringIO())

        self.assertEqual(Articulos.objects.get(clave='TST0003').imagen.name, 'NO.EXISTE.png')

    def test_dry_run_no_modifica_nada(self):
        """--dry-run informa pero no escribe."""
        self._crear('TST0004', '002.534.PNG')

        out = StringIO()
        call_command('normalizar_imagenes', '--dry-run', stdout=out)

        self.assertEqual(Articulos.objects.get(clave='TST0004').imagen.name, '002.534.PNG')
        self.assertIn('DRY-RUN', out.getvalue())

    def test_corrige_todas_las_filas_que_comparten_el_archivo(self):
        """Varias filas pueden apuntar a la misma imagen: se corrigen todas."""
        self._crear('TST0005', '002.534.PNG')
        self._crear('TST0006', '002.534.PNG')

        call_command('normalizar_imagenes', stdout=StringIO())

        self.assertEqual(Articulos.objects.get(clave='TST0005').imagen.name, '002.534.png')
        self.assertEqual(Articulos.objects.get(clave='TST0006').imagen.name, '002.534.png')

    def test_es_idempotente(self):
        """Correrlo dos veces no cambia nada la segunda vez."""
        self._crear('TST0007', '002.534.PNG')

        call_command('normalizar_imagenes', stdout=StringIO())
        call_command('normalizar_imagenes', stdout=StringIO())

        self.assertEqual(Articulos.objects.get(clave='TST0007').imagen.name, '002.534.png')

    def test_corrige_espacios_al_final(self):
        """La importacion del ERP tambien deja espacios al final del nombre."""
        self._crear('TST0008', '002.110.png     ')

        call_command('normalizar_imagenes', stdout=StringIO())

        self.assertEqual(Articulos.objects.get(clave='TST0008').imagen.name, '002.110.png')

    def test_corrige_case_y_espacios_juntos(self):
        """Case en mayuscula y espacios al final en la misma referencia."""
        self._crear('TST0009', '002.534.PNG   ')

        call_command('normalizar_imagenes', stdout=StringIO())

        self.assertEqual(Articulos.objects.get(clave='TST0009').imagen.name, '002.534.png')
