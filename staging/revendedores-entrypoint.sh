#!/bin/sh
# Entrypoint del backend de produccion (container Coolify / fasa_189).
#
# Hace dos cosas:
#  1. Carga las variables de entorno desde /run/secrets/revendedores.env
#     (montado desde el .env.docker del host). Sin esto, Django no encuentra
#     SECRET_KEY y arranca con error.
#  2. Antes de levantar gunicorn, corre "manage.py collectstatic" para
#     poblar /app/staticfiles. Es lo que permite que WhiteNoise sirva
#     /static/ (el CSS del admin de Django y el de DRF). Django bajo gunicorn
#     no sirve archivos estaticos: sin collectstatic, /static/ da 404.
set -eu

exec python - "$@" <<'PY'
import ast
import os
import subprocess
import sys
from pathlib import Path

secret_file = Path("/run/secrets/revendedores.env")
if secret_file.is_file():
    for raw_line in secret_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            try:
                value = str(ast.literal_eval(value))
            except (ValueError, SyntaxError):
                value = value[1:-1]
        os.environ[key] = value

if len(sys.argv) < 2:
    raise SystemExit("missing command")


def run_collectstatic():
    """Genera /app/staticfiles para que WhiteNoise sirva /static/.

    Si falla NO se aborta el arranque: es preferible que el backend levante
    y solo se pierda el CSS del admin, antes que dejar el servicio caido
    por un problema de archivos estaticos.
    """
    manage_py = Path("/app/manage.py")
    if not manage_py.is_file():
        print(
            "entrypoint: no se encontro /app/manage.py, se omite collectstatic",
            flush=True,
        )
        return

    env = dict(os.environ)
    env.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

    print("entrypoint: ejecutando collectstatic", flush=True)
    result = subprocess.run(
        [sys.executable, str(manage_py), "collectstatic", "--noinput"],
        cwd="/app",
        env=env,
    )
    if result.returncode != 0:
        print(
            "entrypoint: collectstatic fallo con codigo %s; el backend sigue "
            "levantando pero /static/ puede dar 404" % result.returncode,
            flush=True,
        )


# Solo tiene sentido cuando lo que se levanta es el servidor HTTP.
if os.path.basename(sys.argv[1]) == "gunicorn":
    run_collectstatic()

os.execvp(sys.argv[1], sys.argv[1:])
PY
