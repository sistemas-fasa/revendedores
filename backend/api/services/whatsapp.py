import json
import logging
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from django.conf import settings

from api.services.whatsapp_price import build_price_reply

logger = logging.getLogger("api")


def extract_text_messages(payload):
    messages = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                messages.append(
                    {
                        "from": message.get("from"),
                        "id": message.get("id"),
                        "text": message.get("text", {}).get("body", "").strip(),
                    }
                )
    return messages


def build_basic_reply(text, user=None, context=None):
    price_reply = build_price_reply(text, user=user, context=context)
    if price_reply["handled"]:
        return price_reply

    if not text:
        return {"reply": "Hola, recibi tu mensaje. Me podes escribir tu consulta?", "context": {}}

    normalized = text.lower()
    if normalized in {"hola", "buenas", "buen dia", "buen día"}:
        return {
            "reply": "Hola, soy el asistente de Ferreteria Avenida. Ya estoy recibiendo mensajes de prueba.",
            "context": {},
        }

    return {
        "reply": (
            "Recibi tu mensaje: "
            f"\"{text}\". En esta primera prueba solo confirmo recepcion; "
            "el siguiente paso es consultar precios y stock."
        ),
        "context": context or {},
    }


def send_whatsapp_text(to, text):
    access_token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "")
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")

    if not access_token or not phone_number_id or not to:
        logger.info("WhatsApp send skipped: missing token, phone number id, or recipient")
        return {"sent": False, "reason": "not_configured"}

    url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
    body = json.dumps(
        {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
    ).encode("utf-8")
    req = urlrequest.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlrequest.urlopen(req, timeout=20) as response:
            response_body = response.read().decode("utf-8")
            return {"sent": True, "response": json.loads(response_body)}
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.exception("WhatsApp send failed")
        return {"sent": False, "reason": str(exc)}
