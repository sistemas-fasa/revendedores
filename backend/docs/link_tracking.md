## Generar el link desde una aplicación estilo Visual FoxPro (VFP)

Hay dos enfoques comunes desde una app VFP:
## Generar el link desde una aplicación estilo Visual FoxPro (VFP)

Hay dos enfoques comunes desde una app VFP:
- A) El servidor genera el token firmado y VFP solo arma la URL final con ese token.
- B) VFP solicita al backend (HTTP) que genere el token y lo devuelve; luego VFP arma el link y lo inserta en el correo.

Formato del link
Siempre el formato es:

```
https://ventas.ferreteriaavenida.com.ar/api/track/?t=<TOKEN_FIRMADO>

```
El `<TOKEN_FIRMADO>` debe provenir de `django.core.signing.dumps(payload)` (servidor). El `payload` típicamente incluye al menos `url` (destino final) y opcionalmente `email` y `campaign`.

Ejemplo de payload (servidor):
```json
{
    "email": "cliente@example.com",
    "campaign": "votacion_2026",
    "url": "https://forms.gle/UuxAKPN4BJBy3gpv7"
}
```
Ejemplo VFP (opción A — token ya generado por tu backend)

```
* lcToken es la cadena devuelta por tu backend previamente
lcToken = "<TOKEN_GENERADO_POR_BACKEND>"
lcTrackUrl = "https://ventas.ferreteriaavenida.com.ar/api/track/?t=" + lcToken
* Inserta lcTrackUrl en el cuerpo del email
```

Ejemplo VFP (opción B — pedir token al backend vía HTTP)

```
* Función que solicita un token al backend y devuelve la URL de tracking.
* Además realiza una llamada a `/api/track-preview/` para validar el payload
* sin crear un registro de apertura (útil para VFP o scripts que quieran
* comprobar antes de insertar el link en el mail).
FUNCTION GetTrackUrl(tcEmail, tcCampaign, tcTargetUrl)
    LOCAL loHttp, lcBody, lcResp, lcToken, lcTrackUrl, lcPreviewUrl

    lcBody = '{"email":"' + ALLTRIM(tcEmail) + '","campaign":"' + ALLTRIM(tcCampaign) + '","url":"' + ALLTRIM(tcTargetUrl) + '"}'

    * 1) Pedir token al servidor
    loHttp = CREATEOBJECT("MSXML2.ServerXMLHTTP")
    TRY
        loHttp.setTimeouts(5000,5000,15000,15000)
        loHttp.open('POST','https://ventas.ferreteriaavenida.com.ar/api/track-token/',.F.)
        loHttp.setRequestHeader('Content-Type','application/json')
        loHttp.send(lcBody)
    CATCH TO loEx
        MESSAGEBOX('Error HTTP al pedir token: ' + loEx.Message)
        RETURN ""
    ENDTRY

    IF loHttp.status <> 200
        MESSAGEBOX('Error HTTP al pedir token: ' + TRANSFORM(loHttp.status) + ' - ' + loHttp.statusText)
        RETURN ""
    ENDIF

    lcResp = ALLTRIM(loHttp.responseText) && el endpoint devuelve el token en texto plano
    IF EMPTY(lcResp)
        MESSAGEBOX('Respuesta vacía del servidor (token)')
        RETURN ""
    ENDIF

    lcToken = lcResp
    * URL-encode mínimo para tokens base64
    lcToken = STRTRAN(lcToken, '+', '%2B')
    lcToken = STRTRAN(lcToken, '/', '%2F')
    lcToken = STRTRAN(lcToken, '=', '%3D')

    * 2) OPTIONALLY: validar payload vía /api/track-preview/ (NO CREA LinkOpen)
    lcPreviewUrl = 'https://ventas.ferreteriaavenida.com.ar/api/track-preview/?t=' + lcToken
    TRY
        loHttp.open('GET', lcPreviewUrl, .F.)
        loHttp.setRequestHeader('Accept','application/json')
        loHttp.send()
    CATCH TO loEx
        * Si falla el preview, no bloqueamos el envío del mail, sólo avisamos
        MESSAGEBOX('Advertencia: no se pudo validar el token (preview): ' + loEx.Message)
        lcTrackUrl = 'https://ventas.ferreteriaavenida.com.ar/api/track/?t=' + lcToken
        RETURN lcTrackUrl
    ENDTRY

    IF loHttp.status <> 200
        * Preview falló: devolvemos la URL de tracking igual
        MESSAGEBOX('Advertencia: preview devolvió HTTP ' + TRANSFORM(loHttp.status))
        lcTrackUrl = 'https://ventas.ferreteriaavenida.com.ar/api/track/?t=' + lcToken
        RETURN lcTrackUrl
    ENDIF

    * Si el preview respondió OK, podemos comprobar que la URL objetivo coincide
    lcResp = ALLTRIM(loHttp.responseText)
    IF '"url"' $ lcResp AND AT(ALLTRIM(tcTargetUrl), lcResp) > 0
        * Todo bien: retornar link de tracking
        lcTrackUrl = 'https://ventas.ferreteriaavenida.com.ar/api/track/?t=' + lcToken
        RETURN lcTrackUrl
    ELSE
        * Si el preview no contiene la url esperada, avisar y devolver el link
        MESSAGEBOX('Advertencia: la validación del token no devolvió la URL esperada')
        lcTrackUrl = 'https://ventas.ferreteriaavenida.com.ar/api/track/?t=' + lcToken
        RETURN lcTrackUrl
    ENDIF
ENDFUNC

* Uso:
lcUrl = GetTrackUrl('cliente@example.com', 'votacion_2026', 'https://forms.gle/UuxAKPN4BJBy3gpv7')
IF !EMPTY(lcUrl)
    * Insertar lcUrl en el cuerpo del mail
    ? lcUrl
ENDIF
```

Notas importantes
- Siempre URL-encodea el token si tu método de envío no lo hace automáticamente (por ejemplo, reemplazar `+`, `/`, `=` según corresponda) antes de incluirlo en el querystring.
- Si no querés implementar `/api/track-token/` en el backend, puedes generar los tokens en otro servicio que controle `SECRET_KEY` y luego entregarlos a VFP.
- Por privacidad y seguridad, evita construir tokens en el cliente (VFP) sin firmarlos en el servidor.

Si querés, implemento ahora un endpoint auxiliar `/api/track-token/` que reciba `{email, campaign, url}` y devuelva `{"token":"..."}` para que tu VFP lo consuma fácilmente.
# Tracking de aperturas de links

Este documento explica cómo funciona el tracker de links, cómo generar tokens firmados, y cómo probarlo.

Resumen
- Se añadió el modelo `LinkOpen` en `backend/api/models.py` que registra: token, email (opcional), campaign, target_url, ip, user_agent, referer y opened_at.
- Endpoint público: `/api/track/?t=<token>` que registra la apertura y redirige al `target_url` contenido en el token.

Generar un token (servidor)
Usa `django.core.signing.dumps` para crear un token seguro que incluya la URL de destino y opcionalmente el email/campaign.
Ejemplo (desde una vista o función que envía emails):

```python
from django.core.signing import dumps
from django.urls import reverse

payload = {
    'email': cliente.email,           # opcional
    'campaign': 'votacion_2026',      # opcional
    'url': 'https://forms.gle/UuxAKPN4BJBy3gpv7',
}
token = dumps(payload)
track_path = reverse('track_redirect')  # nombre de la ruta: 'track_redirect'
track_url = request.build_absolute_uri(f"{track_path}?t={token}")
# Incluir `track_url` en la plantilla del email en lugar del link directo
lcResp = ALLTRIM(loHttp.responseText)  && el endpoint devuelve el token en texto plano

* En este caso lcResp es el token directamente
- Reemplaza el link directo por `{{ track_url }}` en la plantilla HTML/Texto.
- Por ejemplo: "Hacé click aquí para votar: <a href="{{ track_url }}">Votar</a>"

Migraciones
- Crea y aplica migraciones para registrar el nuevo modelo:

```bash
python manage.py makemigrations api
python manage.py migrate
```

Registro/visualización
- El modelo `LinkOpen` está registrado en el admin (ver `backend/api/admin.py`).
- También puedes consultarlo mediante queries en la DB, p. ej. `LinkOpen.objects.filter(campaign='votacion_2026')`.

Pruebas rápidas
1. Generar manualmente un token desde el shell:

```bash
python manage.py shell
```

```python
from django.core.signing import dumps
payload = {'email': 'test@example.com', 'campaign': 'test', 'url': 'https://forms.gle/UuxAKPN4BJBy3gpv7'}
print(dumps(payload))
```

2. Construir la URL de tracking:
```
https://ventas.ferreteriaavenida.com.ar/api/track/?t=<token>
```
Abrirla en el navegador — deberías ser redirigido y en la DB aparecerá un registro en `LinkOpen`.

Nota sobre aperturas duplicadas
- Algunos clientes de correo, proxys o antivirus realizan comprobaciones automáticas de enlaces y pueden generar solicitudes adicionales al abrir un link. Para evitar registros dobles, el endpoint implementa una deduplicación simple: si ya existe un registro con el mismo `token`, `ip_address` y `user_agent` en los últimos 10 segundos, la segunda solicitud será ignorada. Esto reduce falsos positivos por prefetch/checks.

Si necesitas una política distinta (por ejemplo, window más amplia o deduplicación basada solo en token), dime y lo ajusto.

Privacidad y cumplimiento
- Informa a los destinatarios que se realizará un tracking de aperturas si la legislación local lo exige.
- Evita guardar datos sensibles en texto claro dentro del token. Es preferible usar `email` o `user_id` solo si estás seguro de los requisitos de privacidad.
- Considera permitir que el usuario se "opte-out" del tracking.

Rotación y expiración
- En la view usamos `signing.loads(token, max_age=60*60*24*30)` para que el token expire en 30 días.
- Si necesitas rotar claves, revisa `settings.SECRET_KEY` y en casos avanzados usa `django.core.signing.TimestampSigner` con claves específicas.

Notas de implementación
- El endpoint está en `backend/api/urls.py` como `track/` y la view en `backend/api/views.py` (`track_redirect`).
- Si usas proxys (nginx, load balancer) asegúrate de que `REMOTE_ADDR` o `HTTP_X_FORWARDED_FOR` pasen correctamente para registrar IPs.

Si querés, puedo:
- Crear la migración inicial por vos (generarla y añadir al repo), o
- Generar un script para enviar los emails con `track_url` ya construido.

