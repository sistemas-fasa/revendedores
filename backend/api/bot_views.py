from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from .models import BotConversationLog
from .services.whatsapp import build_basic_reply, extract_text_messages, send_whatsapp_text


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def whatsapp_webhook(request):
    if request.method == "GET":
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        expected_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "")

        if mode == "subscribe" and token == expected_token:
            return HttpResponse(challenge or "", status=200)
        return HttpResponse("Forbidden", status=403)

    messages = extract_text_messages(request.data)
    replies = []

    for message in messages:
        reply_data = build_basic_reply(message["text"])
        reply = reply_data["reply"]
        send_result = send_whatsapp_text(message["from"], reply)
        replies.append(
            {
                "to": message["from"],
                "message_id": message["id"],
                "reply": reply,
                "send_result": send_result,
            }
        )

    return Response(
        {
            "status": "received",
            "messages_processed": len(messages),
            "replies": replies,
        }
    )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def test_chat(request):
    message = (request.data.get("message") or "").strip()
    if not message:
        return Response(
            {
                "status": "error",
                "error": "El mensaje no puede estar vacio.",
            },
            status=400,
        )

    reply_data = build_basic_reply(
        message,
        user=request.user,
        context=request.data.get("context") or {},
    )
    reply = reply_data["reply"]
    context = reply_data.get("context") or {}
    BotConversationLog.objects.create(
        origen="chat_local",
        usuario=request.user,
        mensaje_usuario=message,
        respuesta_bot=reply,
        intencion=_detect_intention(message, reply),
        estado=_detect_state(reply, context),
        contexto=context,
    )
    return Response(
        {
            "status": "ok",
            "message": message,
            "reply": reply,
            "context": context,
            "debug": {
                "local_test": True,
                "username": request.user.get_username(),
            },
        }
    )


def _detect_intention(message, reply):
    text = f"{message} {reply}".lower()
    if any(keyword in text for keyword in ("precio", "stock", "cuanto", "cuánto", "sale")):
        return "precio_stock"
    if "presupuesto" in text:
        return "presupuesto"
    if "seguimiento" in text:
        return "seguimiento"
    return "fallback"


def _detect_state(reply, context):
    text = reply.lower()
    if context.get("pending_options"):
        return "ambiguous"
    if "no encontre" in text or "no encontré" in text:
        return "not_found"
    if text.startswith("recibi tu mensaje"):
        return "fallback"
    return "ok"
