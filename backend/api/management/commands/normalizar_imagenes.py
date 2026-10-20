"""Corrige el case de la extension en ``Articulos.imagen``.

La importacion del ERP deja algunas referencias con la extension en mayuscula
(por ejemplo ``002.534.PNG``) mientras que el archivo en disco esta en
minuscula (``002.534.png``). En Linux el filesystem es case-sensitive, asi que
esas imagenes devolvian 404 y el catalogo mostraba el texto alternativo en
lugar de la foto del producto.

Se usa como comando y no como migracion a proposito: el grafo de migraciones
del server tiene hojas que solo existen en produccion (el feature bot), asi
que agregar una migracion nueva en el repo genera un segundo nodo hoja y
`manage.py migrate` falla con "Conflicting migrations detected".

Uso:
    python manage.py normalizar_imagenes --dry-run   # solo informa
    python manage.py normalizar_imagenes             # aplica
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand

from api.models import Articulos


class Command(BaseCommand):
    help = (
        'Normaliza el case de la extension de articulo.imagen para que las '
        'imagenes referenciadas existan en el filesystem (Linux es case-sensitive)'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin hacer cambios reales (solo mostrar lo que se haria)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        media_root = getattr(settings, 'MEDIA_ROOT', '')

        if not media_root or not os.path.isdir(media_root):
            self.stdout.write(
                self.style.ERROR(f'MEDIA_ROOT no existe o no es un directorio: {media_root!r}')
            )
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo DRY-RUN: no se haran cambios reales'))

        # Listado exacto del disco. os.path.exists() no sirve para esto porque
        # en Windows es case-insensitive: comparamos contra los nombres reales
        # del directorio para que el resultado sea igual en cualquier SO.
        listados = {}

        def nombres_de(directorio):
            if directorio not in listados:
                try:
                    listados[directorio] = set(os.listdir(directorio))
                except OSError:
                    listados[directorio] = set()
            return listados[directorio]

        referencias = {}
        for art in Articulos.objects.exclude(imagen='').exclude(imagen=None):
            nombre = art.imagen.name
            if nombre:
                referencias.setdefault(nombre, []).append(art.pk)

        self.stdout.write(f'Referencias a imagenes distintas: {len(referencias)}')

        a_corregir = []
        ausentes = []

        for nombre, pks in referencias.items():
            relativo = nombre.replace('\\', '/').lstrip('/')
            partes = relativo.split('/')
            directorio = os.path.join(media_root, *partes[:-1])
            archivo = partes[-1]
            en_disco = nombres_de(directorio)

            if archivo in en_disco:
                continue

            minuscula = archivo.lower()
            if minuscula in en_disco:
                nuevo = '/'.join(partes[:-1] + [minuscula])
                a_corregir.append((nombre, nuevo, pks))
            else:
                ausentes.append((nombre, pks))

        self.stdout.write('')
        self.stdout.write(f'Filas a corregir por case: {len(a_corregir)} referencias '
                          f'({sum(len(p) for _, _, p in a_corregir)} articulos)')
        self.stdout.write(f'Referencias sin archivo en disco: {len(ausentes)} '
                          f'({sum(len(p) for _, p in ausentes)} articulos)')

        for nombre, nuevo, pks in a_corregir[:20]:
            self.stdout.write(self.style.SUCCESS(f'  {nombre} -> {nuevo}  ({len(pks)} articulos)'))
        if len(a_corregir) > 20:
            self.stdout.write(f'  ... y {len(a_corregir) - 20} mas')

        corregidos = 0
        if not dry_run:
            for nombre, nuevo, pks in a_corregir:
                corregidos += Articulos.objects.filter(pk__in=pks).update(imagen=nuevo)

        if ausentes:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'Las siguientes referencias NO tienen archivo en MEDIA_ROOT '
                '(no se puede corregir con este comando; hay que copiar la imagen '
                'o corregir el dato del ERP):'
            ))
            for nombre, pks in sorted(ausentes)[:20]:
                self.stdout.write(self.style.WARNING(f'  {nombre}  ({len(pks)} articulos)'))
            if len(ausentes) > 20:
                self.stdout.write(self.style.WARNING(f'  ... y {len(ausentes) - 20} mas'))

        self.stdout.write('')
        self.stdout.write('=' * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY-RUN: {len(a_corregir)} referencias se corregirian '
                f'({sum(len(p) for _, _, p in a_corregir)} articulos)'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f'Articulos actualizados: {corregidos}'))
