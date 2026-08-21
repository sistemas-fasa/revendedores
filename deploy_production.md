# Deploy de Producción — `ventas.ferreteriaavenida.com.ar`

> Procedimiento operativo para desplegar cambios del repo `revendedores` en
> el servidor de producción `fasa_195` (192.168.0.195).
>
> **Dominio:** `https://ventas.ferreteriaavenida.com.ar`
> **Rama canónica:** `ui-venta-rapida`
> **Path del proyecto en el server:** `/var/www/html/reventa/`
>
> ⚠️ **En este server conviven dos stacks** que se deployan de forma distinta:
> el stack Docker de **pruebas** (puerto 15173/18089) y el stack de
> **producción** (puerto 443/8088). Este documento describe el de **producción**.

---

## 1. Topología de producción

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
