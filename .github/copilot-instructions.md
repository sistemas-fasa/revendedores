# Copilot instructions for revendedores

## Big picture architecture
- Full-stack app: Django REST backend in backend/, Vue 3 + Vite frontend in frontend/.
- Backend apps: api (core REST + auth + pedidos) and graficos (dashboard endpoints) wired in backend/urls.py.
- Frontend routes live in frontend/src/router/index.js with auth/staff guards; views are in frontend/src/views/.

## Key data flows & patterns
- Auth flow: frontend uses Pinia store in frontend/src/stores/auth.js.
  - Login hits POST /api/token/ and expects access/refresh + user + session_id.
  - Tokens and user are stored in localStorage keys access_token, refresh_token, user, session_id.
  - Keep-alive pings POST /api/keep-alive/ every 10 minutes.
- API client in frontend/src/services/api.js uses axios with lazy import of the auth store to avoid circular deps.
  - It attaches Bearer access token and auto-refreshes via POST /api/token/refresh/.
- Cart flow: frontend/src/services/cart.js persists to localStorage and syncs every change to POST /api/sincronizar-carrito/.
  - Checkout creates pedido via POST /api/pedidos/ then confirms via POST /api/pedidos/{id}/confirmar_pedido/.
  - Backend confirmation sends emails asynchronously in a thread (api/views.py).
- Articulos pricing/images: api/serializers.py computes imagen URL with fallback to “parent” clave and exposes pricing fields; viewset uses search + ordering and tracks Busqueda.

## Backend conventions
- Base viewsets should extend backend/BaseViewSet.py BaseAppModelViewSet for pagination + debug serializer errors.
- Settings are driven by python-decouple; see backend/backend/settings.py for DB, CORS, JWT cookie settings, email, and logging.
- Two DB connections are configured: default and fasa (backend/backend/settings.py).
- Staff APIs live under /api/staff/* in backend/api/staff_views.py.

## Frontend conventions
- API base URL is relative in production and hardcoded to http://192.168.0.200:8000/ in dev (frontend/src/services/api.js).
- Use vue-router meta flags (requiresAuth, requiresStaff) in frontend/src/router/index.js.

## Developer workflows
- Backend dev server: run in backend/: py manage.py runserver 0.0.0.0:8000.
- Frontend dev server: run in frontend/: npm install then npm run dev.
- Production deploy guidance exists in install.sh (Docker + nginx reverse proxy).

## Integration points
- Email templates are in backend/api/templates/emails/ and used in pedido confirmation.
- Media files are served via /media/ (backend/backend/settings.py, backend/backend/urls.py).

## Gotchas
- Backend tests live in the package `backend/api/tests/` (one file per topic, `test_*.py`).
  Do NOT create `backend/api/tests.py`: the package shadows the module of the same name and
  any test written there never runs.
- Fechas del ERP legacy: la base `fasa` (origen VFP) usa '0000-00-00' como centinela de
  "sin fecha" en las columnas de vencimiento. pymysql devuelve ese valor como texto y el
  backend MySQL de Django no lo convierte, así que `.strftime()` sobre el atributo revienta.
  Las columnas de la cuenta corriente, facturas y cobranzas usan `FechaContableField`
  (backend/api/fechas.py), que lo normaliza a `None`. Para fechas del ERP usá siempre
  `formatear_fecha()` / `normalizar_fecha()` / `esta_vencido()` de ese módulo, y el lookup
  `con_fecha_valida` para excluir esas filas de los agregados.
- `cuenta_corriente_clientes`, `facturas` y `cobranzas` son `managed = False`: son vistas
  sobre `fasa.movi`. Cambiar sus campos NO genera migraciones ni altera la base.

