"""Recuperación de contraseña por email para el portal de ventas.

Flujo:
1. POST /api/password-reset/ con {"identificador": "<usuario o email>"}.
   Busca el usuario, exige que tenga email registrado (User.email, que se
   carga en "Editar Cliente") y le envía un link con uid + token.
2. POST /api/password-reset/confirm/ con {"uid": ..., "token": ...,
   "new_password": ...}. Valida el token y cambia la contraseña.

Se usa el generador de tokens estándar de Django (el mismo del admin),
con expiración configurable vía PASSWORD_RESET_TIMEOUT (default 3 días).
"""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle

logger = logging.getLogger('api')

User = get_user_model()


class PasswordResetRateThrottle(AnonRateThrottle):
    """Limita los pedidos de recupero para evitar abuso/spam de emails."""

    rate = '10/hour'


def _enmascarar_email(email):
    """Muestra una versión parcial del email (j***@gmail.com) para confirmar destino."""
    try:
        local, dominio = email.split('@')
    except ValueError:
        return '***'
    if len(local) <= 2:
        visible = local[:1] + '***'
    else:
        visible = local[:1] + '***' + local[-1:]
    return f'{visible}@{dominio}'


def _buscar_usuario(identificador):
    """Busca por username exacto (insensible a mayúsculas) o por email."""
    identificador = (identificador or '').strip()
    if not identificador:
        return None
    usuario = User.objects.filter(username__iexact=identificador).first()
    if usuario is None and '@' in identificador:
        usuario = User.objects.filter(email__iexact=identificador).first()
    return usuario


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def solicitar_recuperacion(request):
    identificador = (request.data.get('identificador') or '').strip()
    if not identificador:
        return Response(
            {'error': 'Ingresá tu usuario o email.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    usuario = _buscar_usuario(identificador)
    if usuario is None or not usuario.is_active:
        return Response(
            {'error': 'No encontramos ese usuario. Verificá el dato ingresado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    email = (usuario.email or '').strip()
    if not email:
        return Response(
            {'error': 'Tu cuenta no tiene email registrado. Pedile a Ventas que lo cargue en tu ficha de cliente para poder recuperar tu contraseña.'},
            status=status.HTTP_409_CONFLICT,
        )
    try:
        validate_email(email)
    except ValidationError:
        return Response(
            {'error': 'El email registrado en tu cuenta no es válido. Pedile a Ventas que lo corrija en tu ficha de cliente.'},
            status=status.HTTP_409_CONFLICT,
        )

    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)
    frontend_base = getattr(settings, 'FRONTEND_URL', '').rstrip('/') or request.build_absolute_uri('/')[:-1]
    reset_url = f'{frontend_base}/recuperar/{uid}/{token}'
    expira_horas = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 60 * 60 * 24 * 3) // 3600

    contexto = {
        'usuario': usuario,
        'reset_url': reset_url,
        'expira_horas': expira_horas,
    }
    try:
        html = render_to_string('emails/recuperar_password.html', contexto)
    except Exception:
        logger.exception('No se pudo renderizar el template de recupero')
        html = None
    texto = (
        f'Hola {usuario.get_full_name() or usuario.username},\n\n'
        f'Pediste recuperar tu contraseña del Portal de Ventas de Ferretería Avenida.\n'
        f'Ingresá a este link para crear una nueva (vence en {expira_horas} hs):\n{reset_url}\n\n'
        'Si no fuiste vos, ignorá este mensaje.'
    )
    try:
        send_mail(
            '[FASA] Recuperá tu contraseña del Portal de Ventas',
            texto,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=html,
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception('Error enviando email de recupero a %s', email)
        return Response(
            {'error': 'No pudimos enviar el email. Intentá más tarde.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    logger.info('Email de recupero enviado a usuario %s (%s)', usuario.username, email)
    return Response({
        'message': f'Te enviamos un link a {_enmascarar_email(email)}. Revisá tu casilla (y spam).',
        'email_enmascarado': _enmascarar_email(email),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def confirmar_recuperacion(request):
    uid = (request.data.get('uid') or '').strip()
    token = (request.data.get('token') or '').strip()
    nueva = request.data.get('new_password') or ''

    if not uid or not token or not nueva:
        return Response(
            {'error': 'Faltan datos para completar el recupero.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        pk = force_str(urlsafe_base64_decode(uid))
        usuario = User.objects.get(pk=pk)
    except Exception:
        return Response(
            {'error': 'El link no es válido. Pedí uno nuevo.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not default_token_generator.check_token(usuario, token):
        return Response(
            {'error': 'El link venció o ya fue usado. Pedí uno nuevo desde "Olvidé mi contraseña".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password(nueva, usuario)
    except ValidationError as exc:
        return Response({'error': ' '.join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

    usuario.set_password(nueva)
    usuario.save(update_fields=['password'])
    logger.info('Contraseña restablecida por recupero para usuario %s', usuario.username)
    return Response({'message': 'Contraseña actualizada. Ya podés ingresar con tu nueva clave.'})
