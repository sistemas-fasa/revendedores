# Activación de cuenta con código de cliente + OTP (email y WhatsApp)

## Objetivo

Permitir que un cliente se loguee con su **código de cliente** (impreso en la factura) y, si aún no tiene contraseña, active su cuenta mediante un **código de única vez (OTP)** enviado a su **email y a su WhatsApp** (vía Vogel WhatsApp API), para luego crear su contraseña (doble campo) y entrar al portal.

## Situación actual

- Login con `User.username` + password: `frontend/src/views/Login.vue:22` → `auth.js: login()` → `POST /api/token/` → `serializers.py:229 CustomTokenObtainPairSerializer` (crea `RegistroSesion`).
- `User.username` (ej: `oscar`) ≠ `Cliente.numero_cliente` (ej: `00040`, `models.py:122`, normalizado con `zfill(5)` en `models.py:133`).
- Recupero por **link** con `uid+token` Django, 3 días (`password_reset_views.py:70-141`). **No se toca, convive**.
- Email SMTP ya configurado (`settings.py:219-232`). WhatsApp: solo bot Meta Cloud API de prueba (`services/whatsapp.py:56`), sin OTP.
- `Cliente`/`User` **no guardan teléfono**. No existe nada de `vogel`, `OTP` ni `totp` en el repo.
- Vogel WhatsApp API (repo privado `oscarvogel/vogel_whatsapp_api`, spec en `docs/API_V1.md` + `docs/INTEGRACION_SISTEMAS.md`):
  - Base: `https://whatsapp.vogelconsultoria.com.ar`
  - Auth: `x-api-key: <key>` (alt. `Authorization: Bearer <key>`)
  - Envío texto: `POST /api/v1/instances/{instanceId}/messages`, body `{phone, message, externalRef, actorId, actorName, sourceApp}` → `202 {success, data:{messageId, status:"queued"}}`
  - Teléfono: solo dígitos internacional (`5493764000000`). `202` = encolado, no entregado.
  - Scopes necesarios: `instances:read` + `messages:send`.

## Decisiones tomadas (con el negocio)

1. El campo Usuario acepta **ambos**: `username` o `numero_cliente` (normalizado `strip` + `zfill(5)`).
2. Hay códigos de factura **sin cuenta creada**: el flujo OTP debe crear `User` (+ `Cliente` si falta).
3. Cuenta "sin contraseña" = `set_unusable_password()` hasta completar la activación.
4. **Un solo OTP** (6 dígitos) enviado **igual** por email y WhatsApp.
5. Vigencia: expira **10 min**, **5 intentos**, reenvío con **cooldown 60s**, throttle **10/hora** (igual que recupero actual).
6. Email → `User.email`; WhatsApp → **nuevo campo** `Cliente.whatsapp` (normalizado `549...`, validación AR).
7. Email **repetido entre clientes permitido** (no validar unicidad).
8. Reglas de password: las actuales (mín 8 + validadores Django), doble campo, **login automático** al terminar.
9. Recupero por link **convive** (solo primera activación usa OTP).
10. Config Vogel: `WHATSAPP_API_URL / WHATSAPP_API_KEY / WHATSAPP_INSTANCE_ID / WHATSAPP_API_TIMEOUT` en `.env` (mismos nombres que recomienda Vogel), servicio separado del bot Meta actual.

## Flujo propuesto

### Fase 0 — Login dual (sin romper lo actual)

1. El label "Usuario" pasa a "Usuario o código de cliente".
2. `CustomTokenObtainPairSerializer` resuelve: `username__iexact` O `cliente__numero_cliente` normalizado. Si el `User` tiene password imposible (`has_usable_password() == False`), responde `409` con `code: "activacion_pendiente"` y el frontend muestra el botón de activar.
3. Botón **"Primera vez / Activar cuenta"** siempre visible bajo el login (no depende de detectar nada).

### Fase 1 — `POST /api/activacion/iniciar` `{codigo_cliente}`

1. Normalizar (`strip`, `zfill(5)`).
2. Resolver cliente vía **contrato ERP** (ver sección ERP/FASA): si no existe en ninguna fuente → `404` "código inexistente, pedí alta a Ventas".
3. Si el `User` ya tiene password usable → `409` "ya tenés contraseña, ingresá o usá ¿Olvidaste?".
4. Responde con datos enmascarados (email `j***@gmail.com` si hay) y pide email + whatsapp. **No crea el OTP todavía** (evita costo de envíos a códigos al voleo).

### Fase 2 — `POST /api/activacion/enviar` `{codigo_cliente, email, whatsapp}`

1. Validar email (formato) y whatsapp (AR → normalizar a `549...`, 12-13 dígitos).
2. Guardar en `User.email` + `Cliente.whatsapp` (sobrescribe; email repetido permitido).
3. Generar OTP 6 dígitos (`secrets`), guardar **solo hash SHA-256 + salt** con `expira_at`, `intentos=0`. Invalidar OTPs previos del cliente.
4. Enviar en paralelo: email SMTP (template nuevo `emails/activacion_otp.html`) + Vogel (`sourceApp: "revendedores"`, `externalRef: "activacion:{codigo}:{uuid4}"`, `actorName: "Portal Revendedores"`).
5. Responder `202` con `expira_en: 600`. Si un canal falla, igual continuar con el otro y reportar `canales: {email: ok, whatsapp: error}` (el mismo código viaja por ambos, basta uno).

### Fase 3 — `POST /api/activacion/verificar` `{codigo_cliente, otp}` + `POST /api/activacion/confirmar` `{codigo_cliente, otp, password1, password2}`

1. Verificar: hash coincide, no expirado, `intentos < 5` (cada fallo suma; al llegar a 5 se invalida). Cooldown reenvío 60s (`POST /api/activacion/reenviar` regenera y reenvía por ambos canales).
2. Confirmar: `password1 == password2`, `validate_password()`, `set_password()`, marcar `Cliente.whatsapp_verificado=True`, invalidar OTP, emitir JWT (`access`, `refresh`, `session_id` vía mismo camino que login) → frontend entra a `/productos`.
3. Throttle `10/hour` por IP + por código en todos los endpoints (reusar `PasswordResetRateThrottle`).

## Modelos y migraciones

- `Cliente.whatsapp = CharField(max_length=15, blank=True, default="")` + `whatsapp_verificado = BooleanField(default=False)`.
- Nueva tabla `ActivacionOTP`: `cliente FK, codigo_hash CharField(64), salt, expira_at DateTime, intentos PositiveInteger, canal_email_estado, canal_whatsapp_estado, message_id_whatsapp, creado_at`. Sin plaintext jamás.
- Backfill: cuentas nunca activadas (a definir con Ventas, típicamente las creadas por alta masiva) → `set_unusable_password()`.

## Servicio Vogel

- Nuevo `api/services/vogel_whatsapp.py` (`VogelWhatsAppClient`): `validate_configuration()`, `normalize_phone_ar()`, `send_text()`. Timeout configurable, traduce errores HTTP (401/403/404/5xx + timeout) sin exponer la key en logs, persiste `messageId`.
- **No** reusar `services/whatsapp.py` (Meta Cloud API del bot): son proveedores distintos.
- Config instancia **por ambiente** vía `.env` (instancia configurable = cambiar `WHATSAPP_INSTANCE_ID` sin redeploy de código). ABM en Admin: fuera de alcance, solo si se pide después.

## Frontend

- `Login.vue`: label dual, manejo de `409 activacion_pendiente`, botón "Primera vez / Activar cuenta" → wizard de 3 pasos (código → email/whatsapp → OTP → doble password) en el mismo estilo visual actual.
- Sin cambios en `RecuperarPassword.vue`, `auth.js` (solo suma `activar()`), `api.js` (mismo interceptor).

## Seguridad y auditoría

- OTP hasheado (SHA-256 + salt por código), expiración server-side, sin exponer si el código existe en listados (el `404` de fase 1 es aceptado: el código de factura no es secreto).
- No loguear OTP ni API key. Registrar en `RegistroSesion`/log: activación iniciada, enviada, verificada, fallos.
- WhatsApp `202` = encolado: para OTP **no hacer polling** de estado; si el cliente no lo recibe usa reenviar.

## ERP / FASA (contrato para el hilo del ERP)

**Lo que se sabe hoy (código):** doble conexión `default` + `fasa` (`settings.py:92-107`); `Factura` (`db_table facturas`) y `CuentaCorrienteCliente` (`cuenta_corriente_clientes`, vista sobre `fasa.movi`) tienen columna `cliente CHAR(5)` pero **no hay maestro de clientes mapeado**; el actualizador horario de automatizaciones escribe clientes en sus propias tablas (VFP/Peewee), no en `api_cliente`.

**Contrato que implementa el hilo del ERP** — función `resolver_cliente_erp(codigo) -> {existe, nombre, ...} | None`:

1. Determinar tabla maestra real del código impreso en factura (candidatas: tabla de clientes del FASA vía `using('fasa')`, o `DISTINCT cliente` en `facturas`/`movi` como fallback con `nombre` de la última factura).
2. Si el `Cliente` local no existe y el ERP lo confirma, autocrear `User(username=numero_cliente, usable_password=False)` + `Cliente(numero_cliente, nombre=ERP, valores por defecto de lista_pago/localidad a definir con Ventas)`.
3. El flujo OTP **no avanza** sin `existe=True` del contrato (evita crear cuentas basura).

### Autocreación (self-service)

Si el código es válido en el ERP pero no tiene ficha local, `iniciar`/`enviar`
la crean sola (`_alta_automatica`): `User(username=codigo, usable=False)` +
`Cliente` con nombre/lista/localidad/pago de la última factura y defaults
(`ACTIVACION_DEFAULT_*`, hoy: lista `1`, localidad `0001`, pago `00`, IVA `F`).
Si falta algún default, no inventa nada: `409 requiere_alta`.
La ficha queda marcada `alta_automatica=True` para que Ventas la revise.
Verificado con código real 24458 (2026-11-11).

## Email: cola centralizada (no SMTP directo)

El portal **no envía SMTP directo**: encola en `fe.emails_pendientes`
(`api/services/email_cola.py`, modelo no gestionado `EmailPendiente`) y los
manda el servidor genera-fe-2025 (`smtp-relay.gmail.com`).

- **Base correcta: `192.168.0.117` NO, `192.168.0.150` SÍ.** La `.117` tiene
  `ENVIO_EMAILS_ACTIVO='N'` (consumidor pausado, solo saldría de la `.150`
  por seguridad). La `.150` tiene `ENVIO_EMAILS_ACTIVO='S'`.
- `FE_DB_HOST=192.168.0.150`, `FE_DB_NAME=fe` (credenciales en `.env`, gitignored).
- Contrato: `estado='pendiente'`, `intentos=0`, `empresa_id=1`,
  `quien_envia=ventas@ferreteriaavenida.com.ar`, un destinatario ASCII,
  cuerpo representable en **latin1** (sin emojis ni `—`; el sanitizador
  reemplaza lo que no entra).
- Si la cola no está disponible, cae a SMTP directo de Django (fallback).
- Ojo operativo: la cola comparte el tope de 100/hora con las campañas;
  el OTP por WhatsApp es el canal instantáneo, el email es respaldo.
- Verificado 2026-11-11: fila encolada en `.150`, email recibido OK.

## Datos pendientes (produción)

1. **API key de revendedores + instanceId autorizado** ✅ key de prueba en `backend/.env` local (instancia `oscar_claro_2`, empresa `forestal_garuhape`, verificada conectada 2026-11-11).
   **Falta para producción:** cargar en el env de producción `WHATSAPP_API_URL/KEY/INSTANCE_ID/TIMEOUT` + `FE_DB_*` (`ACTIVACION_EMAIL_VIA_COLA=True`), y definir si se usa una instancia propia de Ferretería Avenida (ej: `ceramica` cuando se reconecte — hoy está `disconnected`) o se asocia `oscar_claro_2` a la empresa que corresponda.
2. **Texto del mensaje OTP** (formal, definido): `Ferretería Avenida - Portal de Ventas. Tu código de verificación es {otp}. Vence en 10 minutos. No lo compartas con nadie.`
3. **Asunto del email OTP**: `[FASA] Tu código de activación del Portal de Ventas` (remitente `DEFAULT_FROM_EMAIL`, template `emails/activacion_otp.html`).
4. Confirmar valores por defecto al autocrear `Cliente` (lista de precio, condición de pago, localidad) y criterio de backfill `set_unusable_password()`. Mientras tanto: código válido sin ficha local → `409 requiere_alta`. Hilo del ERP.

## Verificación de aceptación

1. Login con `username` viejo sigue funcionando; login con `00040` entra a la misma cuenta.
2. Cuenta sin password recibe `409 activacion_pendiente` y el wizard la activa de punta a punta.
3. El mismo OTP llega por email y WhatsApp; cualquiera de los dos canales alcanza.
4. OTP expirado (>10 min), 5 intentos fallidos y reenvío <60s son rechazados con mensajes claros.
5. `password1 != password2` y clave débil son rechazadas con validadores Django.
6. Al confirmar, entra logueado a `/productos` con `RegistroSesion` creada.
7. Código de factura inexistente → `404` sin crear nada ni enviar nada.
8. Sin `WHATSAPP_*` configurado, el envío WhatsApp se degrada a "solo email" con aviso visible (no 500).
9. En `ActivacionOTP` y logs jamás hay OTP en plaintext ni API keys.
10. Nota: esta rama no tiene módulo de recupero por link (`password_reset_views` no existe acá); al mergear con `main` ambos flujos conviven sin tocarse.
