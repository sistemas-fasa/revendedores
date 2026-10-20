#!/bin/sh
# Corre la normalizacion de referencias de imagen de productos.
#
# POR QUE: la importacion del ERP escribe api_articulos.imagen con la
# extension en mayusculas (ej. "002.534.PNG" cuando el archivo es
# "002.534.png") y a veces con espacios al final. En Linux el filesystem es
# case-sensitive y los espacios viajan en la URL, asi que esas referencias
# dan 404 y el articulo se ve sin foto en el catalogo.
#
# El comando "manage.py normalizar_imagenes" corrige los nombres contra los
# archivos reales del media y es idempotente: se puede correr cada tanto sin
# riesgo. Tarda ~4 segundos.
#
# INSTALACION en el host (fasa_189), usuario fasa:
#   crontab -l 2>/dev/null | grep -v 'normalizar-imagenes-cron.sh' > /tmp/cron.txt || true
#   cat /tmp/cron.txt > /dev/null
#   echo '*/30 * * * * /srv/fasa-data/compose/revendedores-src/scripts/normalizar-imagenes-cron.sh' >> /tmp/cron.txt
#   crontab /tmp/cron.txt
set -eu

LOG=/srv/fasa-data/data/revendedores/logs/normalizar-imagenes.log

# El nombre del contenedor lleva un sufijo que Coolify genera, asi que se
# resuelve en cada corrida en vez de hardcodearlo.
CONTAINER=$(docker ps --format '{{.Names}}' | grep '^backend-' | head -n 1 || true)

if [ -z "$CONTAINER" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') el contenedor del backend no esta corriendo, se omite" >> "$LOG"
    exit 0
fi

{
    echo "===== $(date '+%Y-%m-%d %H:%M:%S') normalizar_imagenes en $CONTAINER ====="
    # El entrypoint es lo que carga /run/secrets/revendedores.env: sin el,
    # Django no encuentra SECRET_KEY y el comando falla.
    docker exec "$CONTAINER" revendedores-entrypoint python manage.py normalizar_imagenes
} >> "$LOG" 2>&1
