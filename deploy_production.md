# Deploy de Producción — `ventas.ferreteriaavenida.com.ar`

> **Stack actual: Coolify sobre `fasa_189` (192.168.0.189).**
> Ver la sección **[0. Setup actual y procedimiento de deploy](#0-setup-actual-y-procedimiento-de-deploy-coolify--fasa_189)**.
>
> La sección 1 documenta el setup **anterior** (`fasa_195` + nginx/systemd), que
> **ya no está en uso**: las imágenes hoy se construyen en el server y se
> despliegan vía la API de Coolify.

>
> **Dominio:** `https://ventas.ferreteriaavenida.com.ar`
> **Rama canónica:** `main`
> **Servidor:** `fasa_189` (192.168.0.189) — usuario `fasa`, key `~/.ssh/id_ed25519`
> **Panel Coolify:** `https://coolify.vogelconsultoria.com.ar`

---

## 0. Setup actual y procedimiento de deploy (Coolify / fasa_189)

### 0.1 Topología

```
Internet
  └── coolify-proxy (Traefik v3.6)
        └── frontend-1ezipmojg…   (nginx:alpine, imagen fasa-revendedores-frontend:staging)
              ├── /            → /usr/share/nginx/html  (SPA Vue compilada)
              └── /api/, /media/, /static/, /admin/, /t/  → http://backend:8000
                    └── backend-1ezipmojg…  (gunicorn, imagen fasa-revendedores-backend:staging-env2)
                          └── MySQL externo  192.168.0.150:3306   (DB `revendedores` + `fasa`)
```

> El contenedor `mysql` del compose **no** es el que usa la app: el backend
> conecta al MySQL **externo** `192.168.0.150:3306` (definido en
> `/srv/fasa-data/data/revendedores/.env.docker`).

### 0.2 Componentes y paths en el server

| Qué | Dónde |
|---|---|
| Source del proyecto | `/srv/fasa-data/compose/revendedores-src/` (**no es un repo git**) |
| Compose de Coolify | `/srv/fasa-data/compose/revendedores-coolify.compose.yml` |
| Secrets / env del backend | `/srv/fasa-data/data/revendedores/.env.docker` → montado como `/run/secrets/revendedores.env` |
| Media y logs (volumes) | `/srv/fasa-data/data/revendedores/{media,logs}` |
| Registry local de imágenes | `127.0.0.1:5000` (`registry:2` en el host) |
| Imagen backend | `127.0.0.1:5000/fasa-revendedores-backend:staging-env2` |
| Imagen frontend | `127.0.0.1:5000/fasa-revendedores-frontend:staging` |
| Dockerfile backend | `revendedores-src/staging/Dockerfile.revendedores.backend` |
| Dockerfile frontend | `revendedores-src/docker/Dockerfile.frontend` |

**IDs de Coolify** (para la API):

| Recurso | UUID |
|---|---|
| Proyecto | `l0h5euhntsennj8llc1t1f99` |
| Entorno `production` | `fiztusoqxra9y9toj29ibt9y` |
| Servicio (compose) | `1ezipmojg3zemckxlug8ndjv` |
| Sub-aplicación backend | `suoalpnbt3xhmsppgrwzzdea` |
| Sub-aplicación frontend | `qeqfukgjmxwecbvdagxffqnm` |

> El servicio se llama `revendedores-staging` **pero sirve el dominio de
> producción** y vive en el entorno `production`. El nombre es engañoso.

### 0.3 Procedimiento de deploy

Las imágenes **no** se construyen en Coolify: se construyen en el server y se
pushean al registry local. La secuencia completa es:

**1. Mergear a `main`** (los deploys salen de `main`).

**2. Sincronizar el source en el server** (el source no es un repo git):

```bash
ssh fasa_189
BUILD=/tmp/revend-build
git clone --depth 1 --branch main https://github.com/sistemas-fasa/revendedores.git $BUILD
# …o actualizar un clone existente:
git -C $BUILD fetch --depth 1 origin main && git -C $BUILD checkout -q FETCH_HEAD

SRC=/srv/fasa-data/compose/revendedores-src
# backup antes de tocar nada
tar czf /tmp/revendedores-src-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C /srv/fasa-data/compose revendedores-src/backend revendedores-src/frontend/src

chmod -R u+w $SRC/backend $SRC/frontend/src $SRC/docker
rsync -a --exclude '__pycache__' --exclude '*.pyc' --exclude '.pytest_cache' \
  $BUILD/backend/ $SRC/backend/
rsync -a --exclude '__pycache__' $BUILD/frontend/src/ $SRC/frontend/src/
rsync -a $BUILD/docker/nginx/ $SRC/docker/nginx/
cp -f $BUILD/frontend/{package.json,package-lock.json,vite.config.ts,index.html} $SRC/frontend/
```

> ⚠️ El `rsync` de `docker/nginx/` **es obligatorio**: `docker/Dockerfile.frontend`
> hace `COPY docker/nginx/default.conf /etc/nginx/conf.d/default.conf`, así que
> la config de nginx queda horneada en la imagen. Sin este sync, los cambios en
> `docker/nginx/default.conf` **nunca llegan a producción** (y el build usa
> silenciosamente la conf vieja que quedó en el server).
>
> `chmod -R u+w` incluye `$SRC/docker` porque en el server ese árbol es
> read-only (`dr-xr-sr-x`) y `rsync` necesita permiso de escritura en el
> directorio para reemplazar el archivo.


**3. Construir y pushear las imágenes:**

```bash
cd $SRC
docker build -f staging/Dockerfile.revendedores.backend \
  -t 127.0.0.1:5000/fasa-revendedores-backend:staging-env2 .
docker build -f docker/Dockerfile.frontend \
  -t 127.0.0.1:5000/fasa-revendedores-frontend:staging .
docker push 127.0.0.1:5000/fasa-revendedores-backend:staging-env2
docker push 127.0.0.1:5000/fasa-revendedores-frontend:staging
```

**4. Redeploy vía la API de Coolify** (solo las apps que cambiaron; MySQL no se toca):

```bash
TOKEN='<token de la API de Coolify>'
BASE=https://coolify.vogelconsultoria.com.ar/api/v1
SVC=1ezipmojg3zemckxlug8ndjv

curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "$BASE/services/$SVC/applications/suoalpnbt3xhmsppgrwzzdea/start?latest=true&force=true"
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "$BASE/services/$SVC/applications/qeqfukgjmxwecbvdagxffqnm/start?latest=true&force=true"
```

### 0.4 Verificación post-deploy

```bash
# 1. Las imágenes nuevas están corriendo
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' | grep 1ezipmojg
docker inspect -f '{{.Image}}' backend-1ezipmojg3zemckxlug8ndjv

# 2. El fix está dentro del contenedor
docker exec backend-1ezipmojg3zemckxlug8ndjv grep -c FechaContableField /app/api/models.py

# 3. La API responde (usar el Host real: si no, 400 por ALLOWED_HOSTS)
curl -s -H "Host: ventas.ferreteriaavenida.com.ar" \
  "http://<ip-backend>:8000/api/comprobantes/" -H "Authorization: Bearer <jwt>"

# 4. Sin errores nuevos en el log
docker logs --since 10m backend-1ezipmojg3zemckxlug8ndjv | grep -iE "Traceback|Error"
```

Para los comandos que corren Django dentro del contenedor hay que usar el
entrypoint, porque es el que carga `/run/secrets/revendedores.env`:

```bash
docker exec backend-1ezipmojg… revendedores-entrypoint python manage.py shell -c "…"
```

### 0.5 Rollback

El digest anterior queda registrado en el registry. Para volver atrás:

1. `docker pull 127.0.0.1:5000/fasa-revendedores-backend@sha256:<digest-anterior>`
2. Reetiquetar el tag al digest viejo:
   `docker tag 127.0.0.1:5000/fasa-revendedores-backend@sha256:<anterior> 127.0.0.1:5000/fasa-revendedores-backend:staging-env2`
3. `docker push` del tag y redeploy con `?latest=true`.

También hay backups del source en `/tmp/revendedores-src-backup-*.tar.gz`.

### 0.6 Gotchas

- **`restart` NO hace pull.** `POST …/applications/{uuid}/restart` reinicia el
  contenedor con la imagen **local vieja**. Para tomar la imagen nueva del
  registry hay que usar `POST …/applications/{uuid}/start?latest=true&force=true`.
- **El source del server tiene código que NO está en git.** El feature bot
  (`api/services/bot_*.py`, `api/bot_views.py`, migraciones 0027/0028/0031)
  vive **solo en el server**. Por eso el `rsync` **no debe usar `--delete`**:
  se perdería ese código. Verificá que sigue presente después del sync.
- **El source no es un repo git**: los cambios se sincronizan con `rsync`
  desde un clone de `main`, no con `git pull`.
- **`docker exec` no carga el env**: sin el entrypoint, Django falla con
  `SECRET_KEY not found`.
- **`ALLOWED_HOSTS`**: al curls directo contra el contenedor hay que mandar
  `-H "Host: ventas.ferreteriaavenida.com.ar"`, si no responde 400.
- **El service deploy completo** (`POST /services/{uuid}/start`) devuelve 400
  si el servicio ya está `running`. Para redeployar se va por aplicación.
- **La API de Coolify 4.4.6 está rota para TODOS los tokens** (verificado
  2026-10-20): `app/Models/PersonalAccessToken.php` define `casts()` como
  **método**, y eso pisa la propiedad `$casts` de Sanctum
  (`'abilities' => 'json'`). Entonces `abilities` queda como **string** y
  `tokenCan()` revienta con
  `in_array(): Argument #2 ($haystack) must be of type array, string given`
  → la API responde **500** (no 401), así que el token parece válido pero no
  funciona. No hay token en el panel que sirva: en `personal_access_tokens` el
  campo `token` es un **hash sha256**, no el texto plano.
  **Workaround sin API:** recrear el contenedor con el compose efectivo que
  Coolify ya genera (tiene las labels de traefik adentro), ver 0.7.

### 0.7 Redeploy sin la API de Coolify (compose efectivo)

Coolify genera un compose final **con las labels de traefik ya inyectadas**.
Ese archivo es el que hay que usar para recrear un contenedor a mano:

```bash
# 1. Copiar el compose efectivo + su .env a un directorio accesible
docker exec coolify cat /var/www/html/storage/app/services/1ezipmojg3zemckxlug8ndjv/docker-compose.yml > /tmp/rev/docker-compose.yml
docker exec coolify cat /var/www/html/storage/app/services/1ezipmojg3zemckxlug8ndjv/.env > /tmp/rev/.env

# 2. Recrear SOLO el frontend con la imagen nueva del registry
cd /tmp/rev && docker compose up -d --no-deps --force-recreate frontend
```

> **No usar** `docker compose` con `/srv/fasa-data/compose/revendedores-coolify.compose.yml`
> (el que está en el repo): ese no tiene las labels de traefik, y recrear el
> contenedor con él **deja el sitio sin ruta y sin HTTPS**.
>
> `docker compose up` recrea el contenedor con el **mismo nombre**
> (`frontend-1ezipmojg3zemckxlug8ndjv`), así que Coolify sigue viéndolo
> running y no se rompe el estado.
>
> Alternativa sin recrear nada, para cambios **solo de nginx**: copiar la conf
> al contenedor y recargar, sin downtime ni recrear:
>
> ```bash
> docker cp /tmp/rev/default.conf frontend-1ezipmojg3zemckxlug8ndjv:/etc/nginx/conf.d/default.conf
> docker exec frontend-1ezipmojg3zemckxlug8ndjv nginx -s reload
> ```
>
> Esto **no** es permanente: la próxima vez que se recree el contenedor vuelve
> la conf vieja. Por eso hay que pushear la imagen igual.


### 0.8 Imágenes de productos: case del filesystem y archivos faltantes

Las imágenes de productos se sirven desde `/media/` → backend → Django
(`Articulos.imagen`). Hay **dos problemas distintos** que se ven igual en el
navegador (el texto alternativo en vez de la foto):

**1. Case de la extensión (arreglado).** La importación del ERP dejó
referencias con la extensión en mayúscula (`002.534.PNG`, `COR.000.jpg`)
mientras que el archivo en disco está en minúscula (`002.534.png`,
`cor.000.jpg`). En Linux el filesystem es case-sensitive, así que esas URLs
daban 404.

Se corrige con un comando, **no con una migración**: el grafo de migraciones
del server tiene hojas que solo existen en producción (`0028_rename_botconversation_indexes`,
`0031_merge_20260821_1033`), así que agregar una migración nueva en el repo
genera un segundo nodo hoja y `manage.py migrate` falla con *"Conflicting
migrations detected"*.

```bash
# Ver qué haría, sin tocar nada
docker exec backend-1ezipmojg… revendedores-entrypoint \
  python manage.py normalizar_imagenes --dry-run

# Aplicar
docker exec backend-1ezipmojg… revendedores-entrypoint \
  python manage.py normalizar_imagenes
```

> **Correrlo después de cada importación del ERP**, que es lo que introduce
> el case incorrecto. El comando es idempotente.
>
> El comando compara contra el listado exacto del directorio (`os.listdir`), no
> contra `os.path.exists`, porque en Windows `exists()` es case-insensitive y
> el resultado sería distinto según el sistema.

**2. Archivos que directamente no existen (sin resolver).** Hay referencias en
la DB a imágenes que no están en `MEDIA_ROOT` ni en mayúscula ni en minúscula.
Aproximadamente **570 referencias (~570 artículos)** al momento de esta
documentación. Estas **no** se pueden arreglar desde la app: hay que copiar
el archivo al `media/` del server o corregir el dato en el ERP.

```bash
# Listar las que faltan (el comando las reporta al final)
docker exec backend-1ezipmojg… revendedores-entrypoint \
  python manage.py normalizar_imagenes --dry-run
```



---

## 1. Setup anterior (fasa_195 + nginx/systemd) — histórico, ya no vigente

> ⚠️ **Este setup ya no está en uso.** La producción migró a Coolify sobre
> `fasa_189` (ver sección 0). Se conserva como referencia histórica.

### 1.0 Topología de producción

### 1.1 Servicios activos

| Servicio | Mecanismo | Puerto | Origen / config |
|---|---|---|---|
| **Frontend** (Vue estático) | nginx (host) sirve archivos | `443` (`80` redirige a `443`) | `/var/www/html/reventa/frontend/` (build output) — config en `/etc/nginx/sites-enabled/ventas` |
| **Backend** (Django + gunicorn) | systemd (`reventa.service`) | `127.0.0.1:8088` | `/var/www/html/reventa/backend/` con `backend.backend.wsgi`; venv `/var/www/html/reventa/venv` |
| **MySQL** | servidor externo | `192.168.0.150:3306` | DB `revendedores` + `fasa` (legado ERP) |

nginx hace de reverse proxy: `https://ventas.ferreteriaavenida.com.ar/api/* → http://127.0.0.1:8088`.

### 1.2 Stack Docker de pruebas (NO TOCAR en deploy de producción)

| Servicio | Contenedor | Puerto |
|---|---|---|
| MySQL | `revendedores-mysql` | `3307` |
| Backend | `revendedores-backend` | `18089` |
| Frontend | `revendedores-frontend` | `15173` |

> Este stack se usa para validar cambios antes de pasarlos a producción. **No
> comparte datos** con producción (DB local en `docker_mysql_data`, config en
> `docker/.env.docker`). El deploy de producción **no toca** este stack.

### 1.3 Volúmenes / paths protegidos (no se sobrescriben en deploy de prod)

| Path | Contenido | Notas |
|---|---|---|
| `/var/www/html/reventa/backend/.env` | Config Django prod (DB, email, OpenRouter) | **NO TOCAR** salvo cambio explícito aprobado |
| `/var/www/html/reventa/venv/` | Python venv (lo usa `reventa.service`) | Solo actualizar si cambia `requirements.txt` |
| `/var/www/html/reventa/logs/gunicorn.log` | Log del backend prod | Rotación a definir |
| `/var/www/html/reventa/sockets/` | (vacío) | — |
| `/var/www/html/reventa/_backup_codex/` | Backups antiguos | — |
| `/var/www/html/reventa/docker/` | Config del stack Docker de pruebas | Solo se toca en deploys de **pruebas** |
| `/var/www/html/reventa/frontend/dist/` | Salida del último `npm run build` | Se usa como fuente para copiar al root nginx |
| `192.168.0.150:3306` | MySQL externo | **NO TOCAR** estructura, sí se pueden correr migrations |

### 1.4 Permisos clave

```
/var/www/html/reventa                  root:www-data       777
/var/www/html/reventa/frontend         administracion:...  777
/var/www/html/reventa/frontend/src     ferreteria:...      555  ← sin write
/var/www/html/reventa/backend          root:www-data       777
/var/www/html/reventa/backend/api      root:www-data       777
/var/www/html/reventa/venv             root:www-data       777
```

> **Permisos reales (verificado 2026-08-21):** aunque `backend/` es `777`,
> los subdirectorios (`api/`, `api/migrations/`, `api/services/`, etc.) están
>owned por `root:www-data` y `ferreteria` **NO puede hacer `chmod`** en ellos.
> Los .py files dentro sí son owned por `ferreteria` y se pueden sobrescribir.
> Los directorios nuevos (ej: `api/tests/`) en `555` impiden crear archivos.

---

## 2. Cómo hacer deploy (paso a paso real)

> Este es el procedimiento **real tal como se ejecutó** el 2026-08-21.
> Incluye los workarounds que funcionaron.

### 2.1 Pre-flight local

```bash
# Rama correcta
git branch --show-current   # debe decir: ui-venta-rapida

# Actualizar
git fetch origin
git pull --ff-only origin ui-venta-rapida

# Verificar qué cambió
git log --oneline --since="<fecha_ultimo_deploy>" ui-venta-rapida
git diff <commit_anterior>..HEAD --name-only
```

### 2.2 Backup en el server (siempre antes de tocar algo)

```bash
ssh fasa_195 'cd /var/www/html/reventa && \
  tar czf /tmp/backend_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    backend/api backend/backend backend/graficos backend/manage.py backend/requirements.txt && \
  tar czf /tmp/frontend_src_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    frontend/src frontend/index.html frontend/package.json frontend/package-lock.json \
    frontend/vite.config.ts frontend/tailwind.config.js frontend/tsconfig.json frontend/.eslintrc.cjs'
```

### 2.3 Sync BACKEND (método que funciona)

**NO usar rsync desde Windows** (no funciona bien con UNC paths). Usar **tar local + scp + extract**:

```powershell
# 1. Crear carpeta temporal
$tmpDir = "C:\Users\Ventas\AppData\Local\Temp\opencode\reventa_deploy\backend"
New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null

# 2. Copiar archivos (robocopy excluyendo migraciones, venv, __pycache__)
robocopy "\\pc-oscar\programacion\web\revendedores\backend\api" "$tmpDir\api" /E /XD migrations __pycache__ | Out-Null
robocopy "\\pc-oscar\programacion\web\revendedores\backend\backend" "$tmpDir\backend" /E /XD __pycache__ | Out-Null
robocopy "\\pc-oscar\programacion\web\revendedores\backend\graficos" "$tmpDir\graficos" /E /XD __pycache__ | Out-Null
Copy-Item "\\pc-oscar\programacion\web\revendedores\backend\manage.py" "$tmpDir\manage.py" -Force
Copy-Item "\\pc-oscar\programacion\web\revendedores\backend\requirements.txt" "$tmpDir\requirements.txt" -Force

# 3. Tar y subir
tar -czf "$tmpDir\..\backend_code.tar.gz" -C "$tmpDir\.." backend
scp "$tmpDir\..\backend_code.tar.gz" "ferreteria@fasa_195:/tmp/backend_code.tar.gz"
```

En el server:

```bash
# 4. Extraer (ignorar errores de permisos en directorios — los .py SÍ se copian)
ssh fasa_195 'cd /var/www/html/reventa && \
  tar xzf /tmp/backend_code.tar.gz --strip-components=1 -C backend/ \
    backend/api backend/backend backend/graficos backend/manage.py backend/requirements.txt'
```

> **Nota:** el `tar` muestra errores como "No se puede efectuar utime" y
> "No se puede cambiar el modo" — son por permisos de directorios. Los
> archivos .py SÍ se extraen correctamente. Verificar después con `head`
> en los archivos clave.

### 2.4 Sync MIGRACIONES

Las migraciones se sync por separado porque se excluyen del tar principal:

```powershell
# Local: copiar migraciones nuevas a carpeta temporal
$migDir = "C:\Users\Ventas\AppData\Local\Temp\opencode\reventa_deploy\migrations"
Copy-Item "\\pc-oscar\programacion\web\revendedores\backend\api\migrations\0027_pedido_*.py" "$migDir\" -Force
Copy-Item "\\pc-oscar\programacion\web\revendedores\backend\api\migrations\0028_alter_*.py" "$migDir\" -Force
Copy-Item "\\pc-oscar\programacion\web\revendedores\backend\api\migrations\0029_*.py" "$migDir\" -Force
Copy-Item "\\pc-oscar\programacion\web\revendedores\backend\api\migrations\0030_*.py" "$migDir\" -Force

# Tar y subir
tar -czf "$migDir\..\migrations.tar.gz" -C $migDir .
scp "$migDir\..\migrations.tar.gz" "ferreteria@fasa_195:/tmp/migrations.tar.gz"
```

En el server:

```bash
# Extraer a carpeta temporal y copiar (por permisos del directorio migrations)
ssh fasa_195 'mkdir -p /tmp/mig_extract && cd /tmp/mig_extract && \
  tar xzf /tmp/migrations.tar.gz && \
  cp *.py /var/www/html/reventa/backend/api/migrations/'
```

### 2.5 Aplicar migraciones

```bash
ssh fasa_195 'cd /var/www/html/reventa/backend && \
  ../venv/bin/python manage.py migrate --noinput 2>&1'
```

> Si hay ramas de migración sin merge (error "multiple leaf nodes"), crear
> migración merge primero:
> ```bash
> ssh fasa_195 'cd /var/www/html/reventa/backend && \
>   ../venv/bin/python manage.py makemigrations --merge --noinput'
> ```

### 2.6 Sync FRONTEND fuente + build

```powershell
# 1. Copiar source files
$tmpDir = "C:\Users\Ventas\AppData\Local\Temp\opencode\reventa_deploy\frontend"
$src = "\\pc-oscar\programacion\web\revendedores\frontend"
robocopy "$src\src" "$tmpDir\src" /E | Out-Null
Copy-Item "$src\package.json" "$tmpDir\" -Force
Copy-Item "$src\package-lock.json" "$tmpDir\" -Force
Copy-Item "$src\vite.config.ts" "$tmpDir\" -Force
Copy-Item "$src\tailwind.config.js" "$tmpDir\" -Force
Copy-Item "$src\tsconfig.json" "$tmpDir\" -Force
Copy-Item "$src\.eslintrc.cjs" "$tmpDir\" -Force
Copy-Item "$src\index.html" "$tmpDir\" -Force

# 2. Tar y subir
tar -czf "$tmpDir\..\frontend_source.tar.gz" -C "$tmpDir\.." frontend
scp "$tmpDir\..\frontend_source.tar.gz" "ferreteria@fasa_195:/tmp/frontend_source.tar.gz"
```

En el server:

```bash
# 3. Extraer
ssh fasa_195 'cd /var/www/html/reventa && \
  tar xzf /tmp/frontend_source.tar.gz --strip-components=1 -C frontend/ \
    frontend/src frontend/index.html frontend/package.json frontend/package-lock.json \
    frontend/vite.config.ts frontend/tailwind.config.js frontend/tsconfig.json frontend/.eslintrc.cjs'

# 4. Build
ssh fasa_195 'cd /var/www/html/reventa/frontend && \
  npm install --legacy-peer-deps && npm run build'

# 5. Publicar (copiar dist/* al root de nginx)
ssh fasa_195 'cd /var/www/html/reventa/frontend && cp -r dist/* .'
```

### 2.7 Reiniciar gunicorn

**Opción A — systemctl (requiere sudo):**

```bash
ssh fasa_195 'sudo systemctl restart reventa'
# Te va a pedir la contraseña de ferreteria
```

**Opción B — HUP signal (sin sudo, si ya tenés la sesión SSH):**

```bash
ssh fasa_195 'kill -HUP $(pgrep -f "gunicorn.*reventa" | head -1)'
```

> `kill -HUP` hace graceful restart: mata workers viejos y crea nuevos
> cargando el código actualizado. Funciona sin sudo porque `ferreteria`
> es owner del proceso gunicorn.

### 2.8 Verificar

```bash
# Estado del servicio
ssh fasa_195 'systemctl status reventa --no-pager | head -10'

# Backend responde
ssh fasa_195 'curl -sk https://127.0.0.1/api/token/ -H "Host: ventas.ferreteriaavenida.com.ar" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"test\",\"password\":\"test\"}" 2>&1'

# Frontend sirve bundle nuevo
ssh fasa_195 'curl -sk https://127.0.0.1/ -H "Host: ventas.ferreteriaavenida.com.ar" 2>&1 | \
  grep -oE "assets/index-[^\"]+\.(css|js)"'

# Django check
ssh fasa_195 'cd /var/www/html/reventa/backend && ../venv/bin/python manage.py check --no-color 2>&1'
```

> **El usuario `oscar` tiene password diferente en producción** (DB externa
> `192.168.0.150`) que en el stack Docker de pruebas. No confundir.

---

## 3. Troubleshooting

### 3.1 `sudo: se requiere una contraseña`

`ferreteria` tiene sudo pero **necesita ingresar la contraseña**. No hay
workaround sin contraseña. Alternativa: usar `kill -HUP` (ver 2.7 opción B).

### 3.2 tar errores "No se puede efectuar utime" / "Permiso denegado"

Es normal. Los directorios `api/`, `api/migrations/`, `api/services/` están
owned por `root:www-data` y `ferreteria` no puede cambiar timestamps/perms.
**Los archivos .py SÍ se extraen.** Verificar con `head` después.

### 3.3 `Conflicting migrations detected; multiple leaf nodes`

Django detecta ramas de migración sin merge (ej: bot y pedido). Solución:

```bash
ssh fasa_195 'cd /var/www/html/reventa/backend && \
  ../venv/bin/python manage.py makemigrations --merge --noinput && \
  ../venv/bin/python manage.py migrate --noinput'
```

### 3.4 Después del deploy el sitio muestra el bundle viejo

- `Ctrl+Shift+R` en el navegador
- Verificar hash: `curl -sk https://127.0.0.1/ -H "Host: ventas.ferreteriaavenida.com.ar" | grep -oE "assets/index-[^\"]+\.js"`
- Confirmar que `cp -r dist/* .` se ejecutó en `frontend/`

### 3.5 Backend devuelve 500

```bash
ssh fasa_195 'tail -100 /var/www/html/reventa/logs/gunicorn.log'
```

### 3.6 Verificar qué migraciones faltan en prod

```bash
ssh fasa_195 'cd /var/www/html/reventa/backend && \
  ../venv/bin/python manage.py showmigrations api 2>&1 | grep "\[ \]"'
```

### 3.7 Verificar estado de la DB (columnas de pedido)

```bash
ssh fasa_195 'cd /var/www/html/reventa/backend && \
  ../venv/bin/python manage.py shell -c "
from django.db import connection
c = connection.cursor()
c.execute(\"DESCRIBE api_pedido\")
for r in c.fetchall():
    print(r[0], r[1])
"'
```

---

## 4. Rollback

### 4.1 Frontend

```bash
# Restaurar desde backup
ssh fasa_195 'ls /tmp/frontend_src_backup_*.tar.gz'  # identificar backup
ssh fasa_195 'cd /var/www/html/reventa && tar xzf /tmp/frontend_src_backup_<fecha>.tar.gz'
ssh fasa_195 'cd /var/www/html/reventa/frontend && npm run build && cp -r dist/* .'
```

### 4.2 Backend

```bash
# Restaurar desde backup
ssh fasa_195 'ls /tmp/backend_backup_*.tar.gz'
ssh fasa_195 'cd /var/www/html/reventa && tar xzf /tmp/backend_backup_<fecha>.tar.gz'

# Rollback de migración
ssh fasa_195 'cd /var/www/html/reventa/backend && \
  ../venv/bin/python manage.py migrate api <migration_anterior>'

# Reiniciar
ssh fasa_195 'kill -HUP $(pgrep -f "gunicorn.*reventa" | head -1)'
```

---

## 5. Cache de navegador

nginx define `Cache-Control: public, max-age=3600` para `/`. Después de cada
deploy el usuario debe hacer **`Ctrl+Shift+R`** (o ventana incógnito).

---

## 6. Cheat sheet

```bash
# === BACKEND ===
# Backup
ssh fasa_195 'cd /var/www/html/reventa && tar czf /tmp/backend_backup_$(date +%Y%m%d_%H%M%S).tar.gz backend/api backend/backend backend/graficos backend/manage.py backend/requirements.txt'

# Sync (desde Windows, crear tar local primero, luego:)
ssh fasa_195 'cd /var/www/html/reventa && tar xzf /tmp/backend_code.tar.gz --strip-components=1 -C backend/ backend/api backend/backend backend/graficos backend/manage.py backend/requirements.txt'

# Migrations
ssh fasa_195 'cd /var/www/html/reventa/backend && ../venv/bin/python manage.py migrate --noinput'

# === FRONTEND ===
# Build
ssh fasa_195 'cd /var/www/html/reventa/frontend && npm install --legacy-peer-deps && npm run build'
ssh fasa_195 'cd /var/www/html/reventa/frontend && cp -r dist/* .'

# === REINICIAR ===
ssh fasa_195 'kill -HUP $(pgrep -f "gunicorn.*reventa" | head -1)'  # sin sudo
# o
ssh fasa_195 'sudo systemctl restart reventa'  # pide contraseña

# === VALIDAR ===
ssh fasa_195 'curl -sk https://127.0.0.1/ -H "Host: ventas.ferreteriaavenida.com.ar" | grep -oE "assets/index-[^\"]+\.js"'
ssh fasa_195 'systemctl status reventa --no-pager | head -5'
```

---

## 7. Diferencias con el stack de pruebas (Docker)

| Aspecto | Producción | Pruebas (Docker) |
|---|---|---|
| HTTPS | ✅ Let's Encrypt | ❌ HTTP plano |
| Dominio | `ventas.ferreteriaavenida.com.ar` | `192.168.0.195:15173` |
| Frontend servido por | nginx (host) | nginx dentro de contenedor |
| Backend corre como | systemd (`reventa.service`) | contenedor `revendedores-backend` |
| gunicorn puerto | `127.0.0.1:8088` | `0.0.0.0:8000` (mapeado a `18089`) |
| MySQL | `192.168.0.150:3306` (externo) | contenedor `revendedores-mysql` (volumen local) |
| Email backend | SMTP real (`dtc035.ferozo.com:465`) | `console.EmailBackend` (logs) |
| Logs | `/var/www/html/reventa/logs/gunicorn.log` | `docker logs revendedores-backend` |
| Cabeceras seguridad | HSTS, CSP, X-Frame-Options, etc. | Ninguna (solo nginx default) |
| Build frontend | `npm run build` + `cp dist/* .` | docker compose build (Vite + nginx alpine) |

> **Regla de oro:** todo cambio se prueba primero en el stack Docker (puerto
> 15173), y solo cuando está validado se promote a producción.
