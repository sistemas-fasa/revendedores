# Pruebas MVP WhatsApp bot

## Endpoint creado

```text
/api/whatsapp/webhook/
```

## Variables necesarias

Para validacion de webhook:

```env
WHATSAPP_VERIFY_TOKEN=un-token-de-prueba
```

Para envio real por WhatsApp Cloud API:

```env
WHATSAPP_ACCESS_TOKEN=token-de-meta
WHATSAPP_PHONE_NUMBER_ID=id-del-numero
```

Para consultar precios desde el bot:

```env
WHATSAPP_BOT_USERNAME=usuario-django-con-cliente-asociado
```

Si `WHATSAPP_ACCESS_TOKEN` o `WHATSAPP_PHONE_NUMBER_ID` estan vacios, el endpoint recibe el mensaje y genera respuesta local, pero no envia nada a Meta.

## Prueba local de verificacion

Con el servidor Django levantado:

```powershell
curl.exe "http://127.0.0.1:8000/api/whatsapp/webhook/?hub.mode=subscribe&hub.verify_token=un-token-de-prueba&hub.challenge=12345"
```

Resultado esperado:

```text
12345
```

## Prueba local de mensaje entrante

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/whatsapp/webhook/" `
  -H "Content-Type: application/json" `
  -d "{\"entry\":[{\"changes\":[{\"value\":{\"messages\":[{\"from\":\"5493760000000\",\"id\":\"wamid.test\",\"type\":\"text\",\"text\":{\"body\":\"Hola\"}}]}}]}]}"
```

Resultado esperado:

```json
{
  "status": "received",
  "messages_processed": 1,
  "replies": [
    {
      "to": "5493760000000",
      "message_id": "wamid.test",
      "reply": "Hola, soy el asistente de Ferreteria Avenida. Ya estoy recibiendo mensajes de prueba.",
      "send_result": {
        "sent": false,
        "reason": "not_configured"
      }
    }
  ]
}
```

## Prueba local de consulta de precio

Requiere que `WHATSAPP_BOT_USERNAME` apunte a un usuario Django existente con `Cliente` asociado. Ese cliente define la lista de precios, condicion de pago y localidad para calcular el precio.

Ejemplo:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/whatsapp/webhook/" `
  -H "Content-Type: application/json" `
  -d "{\"entry\":[{\"changes\":[{\"value\":{\"messages\":[{\"from\":\"5493760000000\",\"id\":\"wamid.precio\",\"type\":\"text\",\"text\":{\"body\":\"precio cemento\"}}]}}]}]}"
```

Resultados posibles:

- Si hay una coincidencia clara: responde nombre, codigo, precio retira con IVA y stock.
- Si hay varias coincidencias: pide elegir una opcion.
- Si no encuentra articulo: pide mas datos.
- Si falta `WHATSAPP_BOT_USERNAME`: avisa que falta configurar el usuario de precios.

## Pruebas automatizadas

```powershell
$env:DB_ENGINE='django.db.backends.sqlite3'
$env:DB_NAME=':memory:'
$env:FASA_DB_ENGINE='django.db.backends.sqlite3'
$env:FASA_DB_NAME=':memory:'
.\.venv\Scripts\python.exe backend\manage.py test api.tests_whatsapp_bot
.\.venv\Scripts\python.exe backend\manage.py test api.tests_whatsapp_price
```

## Nota

Este MVP ya puede recibir mensajes, generar una respuesta basica y responder consultas simples de precio/stock usando el servicio comun de precios. Todavia no usa IA ni Meta en una prueba real si faltan las credenciales.
