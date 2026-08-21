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
| `/var/www/html/reventa/frontend/dist/`` | Salida del último `npm run build` | Se usa como fuente para copiar al root nginx |
| `192.168.0.150:3306` | MySQL externo | **NO TOCAR** estructura, sí se pueden correr migrations |

### 1.4 Permisos clave

```
/var/www/html/reventa                  root:www-data       777
/var/www/html/reventa/frontend         administracion:...  777
/var/www/html/reventa/frontend/src     ferreteria:...      555  ← sin write
/var/www/html/reventa/backend          root:www-data       777
/var/www/html/reventa/venv             root:www-data       777
```

> El usuario `ferreteria` puede escribir en la mayoría de los paths vía el bit
> `777` o siendo owner. Para `systemctl restart reventa` y para
> `nginx -s reload` se necesita **sudo**, que el usuario `ferreteria` **no
> tiene configurado sin password**. Coordinar con un admin que sí tenga sudo,
> o pedir agregar la regla en `/etc/sudoers.d/`.

---

## 2. Pre-flight local (Windows → repo)

```bash
# 1. Estado limpio
git status

# 2. Rama correcta
git branch --show-current   # debe decir: ui-venta-rapida

# 3. Actualizar al HEAD remoto
git fetch origin
git checkout ui-venta-rapida
git pull --ff-only origin ui-venta-rapida
git log -1 --oneline
```

> Si `git pull` dice `Not possible to fast-forward`, **PARAR**. Hay commits
> locales divergentes — resolver antes de seguir.

### 2.1 Si hay cambios sin commitear que querés preservar

```bash
git stash push -u -m "backup antes de deploy $(date +%Y-%m-%d)"
```

> Después del deploy podés hacer `git stash pop` para restaurarlos.

---

## 3. Identificar archivos a sincronizar

```bash
# Diff contra el último commit deployado a PRODUCCIÓN
git diff <commit_anterior>..HEAD --stat
```

> **Cuidado:** el último deploy a producción puede ser muy viejo. Confirmá
> el `index.html` actual de nginx:
> ```bash
> ssh fasa_195 "stat /var/www/html/reventa/frontend/index.html | grep Modify"
> ```
> Si la fecha es muy anterior al HEAD que querés deployar, ese es tu
> `<commit_anterior>`.

---

## 4. Sincronizar al servidor

### 4.1 Permisos del server (referencia)

```
/var/www/html/reventa                    root:www-data       777
/var/www/html/reventa/frontend           administracion:...  777
/var/www/html/reventa/frontend/src       ferreteria:...      555  ← sin write (permite sobreescribir archivos existentes pero no crear nuevos)
/var/www/html/reventa/backend            root:www-data       777
/var/www/html/reventa/docker             ferreteria:...      555
```

> Si `scp` falla con `Permission denied` al crear un archivo nuevo, el
> directorio destino está en `555`. Workaround:
> ```bash
> ssh fasa_195 "chmod u+w /var/www/html/reventa/<directorio>"
> ```

### 4.2 scp de archivos

```bash
scp -q "\\pc-oscar\programacion\web\revendedores\<ruta_relativa>" \
     "ferreteria@fasa_195:/var/www/html/reventa/<ruta_relativa>"

# Ejemplos reales:
scp -q "\\pc-oscar\programacion\web\revendedores\backend\api\views.py" \
     "ferreteria@fasa_195:/var/www/html/reventa/backend/api/views.py"

scp -q "\\pc-oscar\programacion\web\revendedores\frontend\src\views\ArticulosView.vue" \
     "ferreteria@fasa_195:/var/www/html/reventa/frontend/src/views/ArticulosView.vue"
```

### 4.3 Borrar archivos eliminados en el repo (si aplica)

```bash
ssh fasa_195 "rm -f /var/www/html/reventa/<ruta>/<archivo_eliminado>"
```

---

## 5. Build & deploy de FRONTEND (producción)

> El nginx de producción sirve `/var/www/html/reventa/frontend/` directamente.
> El build de Vite genera `/var/www/html/reventa/frontend/dist/`, y los
> archivos del `dist/` se copian al directorio padre (`frontend/`) para que
> nginx los sirva en el root.

```bash
ssh fasa_195 'cd /var/www/html/reventa/frontend && \
  npm install --legacy-peer-deps && \
  npm run build'
```

> Solo si cambió `frontend/package.json` o `frontend/package-lock.json`:
> `npm install` puede omitirse.

Verificar el build:

```bash
ssh fasa_195 'ls -la /var/www/html/reventa/frontend/dist/index.html'
```

Publicar (copiar `dist/*` al root que sirve nginx):

```bash
ssh fasa_195 'cd /var/www/html/reventa/frontend && \
  shopt -s dotglob && \
  cp -r dist/* . && \
  chmod 644 index.html assets/* 2>/dev/null'
```

> `dotglob` copia también archivos ocultos (e.g. `.htaccess` si lo hubiera).
> El `chmod` es porque `cp` preserva los permisos del `dist/` y nginx prefiere
> `644` para archivos servidos.

---

## 6. Deploy de BACKEND (producción)

### 6.1 Si cambió `requirements.txt`

```bash
ssh fasa_195 'cd /var/www/html/reventa && \
  venv/bin/pip install -r requirements.txt'
```

### 6.2 Si hay migrations nuevas

```bash
ssh fasa_195 'cd /var/www/html/reventa/backend && \
  ../venv/bin/python manage.py migrate --noinput'
```

> `--noinput` porque no hay consola interactiva en el server. Si una migration
> tiene `RunPython` con input, va a fallar — revisar antes.

> Si la tabla `django_migrations` quedó desincronizada (caso típico de
> un server que perdió histórico), puede hacer falta `--fake` para las
> antiguas y reales para las nuevas:
> ```bash
> ssh fasa_195 'cd /var/www/html/reventa/backend && \
>   ../venv/bin/python manage.py migrate --fake <app> <migration_name>'
> ```

### 6.3 Recolectar estáticos (si corresponde)

```bash
ssh fasa_195 'cd /var/www/html/reventa/backend && \
  ../venv/bin/python manage.py collectstatic --noinput'
```

> Solo si cambió `STATIC_ROOT` o se agregaron estáticos nuevos. La config
> nginx ya apunta a `/var/www/html/reventa/backend/static/` para `/static/`.

### 6.4 Reiniciar gunicorn

```bash
ssh fasa_195 'sudo systemctl restart reventa'
```

> Requiere sudo. Ver sección 1.4.

Verificar:

```bash
ssh fasa_195 'systemctl status reventa --no-pager | head -10 && \
  curl -sI http://127.0.0.1:8088/api/health 2>&1 | head -3'
```

---

## 7. Validación post-deploy

### 7.1 Frontend sirviendo bundle nuevo

```bash
ssh fasa_195 'curl -sI https://ventas.ferreteriaavenida.com.ar 2>&1 | head -10'
```

> Debe devolver `HTTP/2 200` con cabeceras de seguridad:
> `Strict-Transport-Security`, `X-Frame-Options`, `Content-Security-Policy`.

Confirmar bundle actualizado:

```bash
ssh fasa_195 'curl -s https://ventas.ferreteriaavenida.com.ar/ | \
  grep -oE "assets/index-[^\"]+\.(css|js)"'
```

El hash debe corresponder al último build.

### 7.2 Backend respondiendo

```bash
ssh fasa_195 'curl -sI https://ventas.ferreteriaavenida.com.ar/api/health 2>&1 | head -3'
```

### 7.3 E2E completo

```bash
TOKEN=$(curl -s -X POST https://ventas.ferreteriaavenida.com.ar/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"oscar","password":"<password>"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")

curl -s -X POST https://ventas.ferreteriaavenida.com.ar/api/pedidos/checkout/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: prod-test-$(date +%s)" \
  -d '{"modalidad":"retira","con_impuestos":true,"items":[{"articulo":".030011","cantidad":1,"precio_unitario":1.00}]}' | \
  python3 -c "import sys,json; r=json.load(sys.stdin); print('id:', r.get('id'), 'total:', r.get('total'))"
```

Esperado: HTTP 201, `id` numérico, `total` recalculado por backend.

---

## 8. Cache de navegador

`/etc/nginx/sites-enabled/ventas` define:

```
location /         add_header Cache-Control "public, max-age=3600";
location /static/  expires 1y; add_header Cache-Control "public, immutable";
location /media/   expires 1y; add_header Cache-Control "public";
```

> **Después de cada deploy el usuario debe hacer `Ctrl+Shift+R`** (o abrir
> en ventana incógnito) en `https://ventas.ferreteriaavenida.com.ar`.

---

## 9. Troubleshooting

### 9.1 `systemctl restart reventa` falla con "permission denied"

`ferreteria` no tiene sudo sin password. Opciones:
1. Coordinar con admin que sí tenga sudo
2. Agregar a `/etc/sudoers.d/reventa`:
   ```
   ferreteria ALL=(root) NOPASSWD: /bin/systemctl restart reventa
   ```
3. Usar `kill -HUP <gunicorn-master-pid>` (signal-based reload, no requiere sudo):
   ```bash
   ssh fasa_195 'kill -HUP $(cat /var/www/html/reventa/sockets/* 2>/dev/null || pgrep -f "gunicorn.*reventa")'
   ```

### 9.2 Después del deploy el sitio sigue mostrando el bundle viejo

- Forzar hard refresh (`Ctrl+Shift+R`)
- Verificar que el hash en `https://ventas.ferreteriaavenida.com.ar/` cambió
- Si no cambió, revisar que `cp -r dist/* .` haya sobrescrito `index.html`:
  ```bash
  ssh fasa_195 'stat /var/www/html/reventa/frontend/index.html | grep Modify'
  ```

### 9.3 Backend devuelve 500 después del deploy

```bash
ssh fasa_195 'tail -100 /var/www/html/reventa/logs/gunicorn.log'
```

Causas comunes:
- Falta `migrate`
- Falta `pip install -r requirements.txt`
- `backend/.env` quedó desincronizado
- `SECRET_KEY` regenerado (invalidaría sesiones existentes)

### 9.4 Migración falla con "table doesn't exist" o "relation already exists"

Tabla `django_migrations` desincronizada. Aplicar `--fake` selectivo:

```bash
ssh fasa_195 'cd /var/www/html/reventa/backend && \
  ../venv/bin/python manage.py migrate --fake'
```

> Esto marca todas las migrations como aplicadas sin ejecutarlas. Usar
> SOLO si la tabla está efectivamente al día (comparar con dump de la app).

---

## 10. Rollback

### 10.1 Frontend

Si el último deploy rompió el frontend, restaurar `frontend/` desde backup
previo:

```bash
# 1. Identificar backup
ssh fasa_195 'ls -la /var/www/html/reventa/_backup_codex/'

# 2. Restaurar desde un tar.gz si existe
ssh fasa_195 "cd /var/www/html/reventa && \
  tar xzf /var/backups/reventa-frontend-<fecha>.tar.gz"
```

> **Backup preventivo:** antes de cada deploy de frontend, hacer snapshot:
> ```bash
> ssh fasa_195 "tar czf /tmp/frontend-$(date +%Y%m%d-%H%M%S).tar.gz \
>   -C /var/www/html/reventa frontend"
> ```

### 10.2 Backend

Rollback de código:

```bash
ssh fasa_195 'cd /var/www/html/reventa/backend && \
  git checkout <commit_anterior>'   # solo si .git existe, sino restaurar desde backup
```

Rollback de migración (Django):

```bash
ssh fasa_195 'cd /var/www/html/reventa/backend && \
  ../venv/bin/python manage.py migrate <app> <migration_anterior>'
```

Reiniciar:

```bash
ssh fasa_195 'sudo systemctl restart reventa'
```

### 10.3 MySQL

**NO** se hace rollback de MySQL en deploys normales. La DB de producción
está en `192.168.0.150:3306` y solo se toca para migrations explícitas.

---

## 11. Acceso al server

```bash
ssh ferreteria@fasa_195
```

> El usuario `ferreteria`:
> - ✅ puede escribir en `frontend/`, `backend/`, `venv/`, `docker/`, `logs/`
> - ✅ puede ejecutar `git`, `docker`, `npm`, `pip` (en su venv)
> - ❌ NO tiene sudo sin password para `systemctl`, `nginx -s reload`
>
> Si necesitás sudo, pedir a un admin que ejecute el comando, o que agregue
> la regla correspondiente en `/etc/sudoers.d/`.

---

## 12. Resumen rápido (cheat sheet)

```bash
# Local
git fetch origin && git checkout ui-venta-rapida && git pull --ff-only origin ui-venta-rapida
git diff <prev>..HEAD --stat

# Sync
scp -q "\\pc-oscar\programacion\web\revendedores\<arch>" "ferreteria@fasa_195:/var/www/html/reventa/<arch>"

# Server — frontend
ssh fasa_195 "cd /var/www/html/reventa/frontend && npm install --legacy-peer-deps && npm run build"
ssh fasa_195 "cd /var/www/html/reventa/frontend && shopt -s dotglob && cp -r dist/* ."

# Server — backend
ssh fasa_195 "cd /var/www/html/reventa/backend && ../venv/bin/python manage.py migrate --noinput"
ssh fasa_195 "sudo systemctl restart reventa"

# Validar
ssh fasa_195 "curl -s https://ventas.ferreteriaavenida.com.ar/ | grep -oE 'assets/index-[^\"]+\.js'"
```

> **Recordar:** Ctrl+Shift+R en el navegador después de cada deploy.

---

## 13. Diferencias con el stack de pruebas (Docker)

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