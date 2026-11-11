"""Activación de cuenta con código de cliente + OTP (email y WhatsApp).

Flujo:
1. POST /api/activacion/iniciar/   {codigo_cliente} -> datos enmascarados.
2. POST /api/activacion/enviar/     {codigo_cliente, email, whatsapp} -> envía OTP.
3. POST /api/activacion/reenviar/   {codigo_cliente} -> regenera y reenvía (cooldown 60s).
4. POST /api/activacion/verificar/  {codigo_cliente, otp} -> valida sin consumir.
5. POST /api/activacion/confirmar/  {codigo_cliente, otp, password1, password2}
   -> valida, consume, fija password y devuelve JWT (login automático).

Ver docs/specs/activacion-cuenta-otp.md.
"""

import hashlib
import logging
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .erp_clientes import normalizar_codigo, resolver_codigo
from .services.vogel_whatsapp import VogelWhatsAppClient, normalize_phone_ar

logger = logging.getLogger('api')


class ActivacionRateThrottle(AnonRateThrottle):
    """Limita los pedidos de activación para evitar abuso/spam de OTP."""

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


def _otp_settings():
    return {
        'longitud': getattr(settings, 'ACTIVACION_OTP_LONGITUD', 6),
        'expira_seg': getattr(settings, 'ACTIVACION_OTP_EXPIRA_SEG', 600),
        'max_intentos': getattr(settings, 'ACTIVACION_OTP_MAX_INTENTOS', 5),
        'cooldown_seg': getattr(settings, 'ACTIVACION_OTP_REENVIO_COOLDOWN_SEG', 60),
    }


def _enmascarar_whatsapp(phone):
    if not phone or len(phone) < 5:
        return '***'
    return f'{phone[:3]}***{phone[-2:]}'


def _generar_otp(longitud):
    return str(secrets.randbelow(10 ** longitud)).zfill(longitud)


def _hash_otp(otp, salt):
    return hashlib.sha256(f'{salt}{otp}'.encode('utf-8')).hexdigest()


def _otp_vigente(cliente):
    from .models import ActivacionOTP
    return (
        ActivacionOTP.objects.filter(
            cliente=cliente, consumido_at__isnull=True, expira_at__gt=timezone.now(),
        )
        .order_by('-creado_at')
        .first()
    )


def _expirar_pendientes(cliente):
    from .models import ActivacionOTP
    ActivacionOTP.objects.filter(
        cliente=cliente, consumido_at__isnull=True, expira_at__gt=timezone.now(),
    ).update(expira_at=timezone.now())


def _texto_whatsapp(otp, expira_min):
    return (
        'Ferretería Avenida - Portal de Ventas. '
        f'Tu código de verificación es {otp}. '
        f'Vence en {expira_min} minutos. No lo compartas con nadie.'
    )


def _crear_y_enviar(cliente, email, whatsapp):
    """Genera OTP, lo persiste hasheado y lo envía. Invalida pendientes previos."""
    from .models import ActivacionOTP
    cfg = _otp_settings()
    _expirar_pendientes(cliente)
    otp = _generar_otp(cfg['longitud'])
    salt = secrets.token_hex(16)
    ahora = timezone.now()
    registro = ActivacionOTP.objects.create(
        cliente=cliente,
        codigo_hash=_hash_otp(otp, salt),
        salt=salt,
        expira_at=ahora + timedelta(seconds=cfg['expira_seg']),
        ultimo_envio_at=ahora,
    )
    expira_min = max(1, cfg['expira_seg'] // 60)
    resultado = {'email': 'error', 'whatsapp': 'omitido', 'whatsapp_message_id': ''}

    try:
        html = render_to_string('emails/activacion_otp.html', {
            'otp': otp,
            'expira_min': expira_min,
            'nombre': cliente.nombre,
        })
    except Exception:
        logger.exception('No se pudo renderizar el template de activación')
        html = None
    texto = (
        f'Hola {cliente.nombre},\n\nTu código de verificación es {otp}. '
        f'Vence en {expira_min} minutos. No lo compartas con nadie.\n\n'
        'Ferretería Avenida - Portal de Ventas'
    )
    asunto = '[FASA] Tu código de activación del Portal de Ventas'
    email_ok = False
    if getattr(settings, 'ACTIVACION_EMAIL_VIA_COLA', True):
        # Vía cola centralizada fe.emails_pendientes (la manda genera-fe-2025).
        try:
            from .services.email_cola import encolar_email
            email_ok = encolar_email(email, asunto, cuerpo_html=html, cuerpo_texto=texto) is not None
            if not email_ok:
                logger.warning('Cola de emails no disponible, caigo a SMTP directo')
        except Exception:
            logger.exception('No se pudo encolar el OTP, caigo a SMTP directo')
            email_ok = False
    if not email_ok:
        try:
            send_mail(asunto, texto, settings.DEFAULT_FROM_EMAIL, [email],
                      html_message=html, fail_silently=False)
            email_ok = True
        except Exception:
            logger.exception('Error enviando OTP por email a %s', email)
    if email_ok:
        resultado['email'] = 'ok'

    envio = VogelWhatsAppClient().send_text(
        whatsapp,
        _texto_whatsapp(otp, expira_min),
        external_ref=f"activacion:{cliente.numero_cliente}:{uuid.uuid4().hex[:8]}",
    )
    if envio.get('sent'):
        resultado['whatsapp'] = 'ok'
        resultado['whatsapp_message_id'] = envio.get('message_id') or ''
    elif envio.get('reason') == 'not_configured':
        resultado['whatsapp'] = 'omitido'
    else:
        resultado['whatsapp'] = 'error'
        logger.warning('OTP WhatsApp no enviado a %s: %s', _enmascarar_whatsapp(whatsapp), envio.get('reason'))

    registro.canal_email_estado = 'ENVIADO' if resultado['email'] == 'ok' else 'ERROR'
    registro.canal_whatsapp_estado = (
        'ENVIADO' if resultado['whatsapp'] == 'ok'
        else ('PENDIENTE' if resultado['whatsapp'] == 'omitido' else 'ERROR')
    )
    registro.whatsapp_message_id = resultado['whatsapp_message_id']
    registro.save(update_fields=[
        'canal_email_estado', 'canal_whatsapp_estado', 'whatsapp_message_id'])
    return resultado


def _validar_otp(cliente, otp):
    """Devuelve (registro, error). Suma intento ante código incorrecto."""
    from .models import ActivacionOTP
    cfg = _otp_settings()
    registro = _otp_vigente(cliente)
    if registro is None:
        return None, 'No hay un código vigente. Pedí uno nuevo.'
    if registro.intentos >= cfg['max_intentos']:
        registro.expira_at = timezone.now()
        registro.save(update_fields=['expira_at'])
        return None, 'Superaste los intentos. Pedí un código nuevo.'
    if not secrets.compare_digest(registro.codigo_hash, _hash_otp((otp or '').strip(), registro.salt)):
        registro.intentos += 1
        if registro.intentos >= cfg['max_intentos']:
            registro.expira_at = timezone.now()
        registro.save(update_fields=['intentos', 'expira_at'])
        restantes = max(0, cfg['max_intentos'] - registro.intentos)
        return None, f'Código incorrecto. Te quedan {restantes} intentos.'
    return registro, None


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ActivacionRateThrottle])
def iniciar(request):
    numero = normalizar_codigo(request.data.get('codigo_cliente'))
    if numero is None:
        return Response(
            {'error': 'Ingresá tu código de cliente (solo números, como figura en la factura).'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    resuelto = resolver_codigo(numero)
    if resuelto is None:
        logger.info('Activación: código inexistente %s', numero)
        return Response(
            {'error': 'No encontramos ese código de cliente. Verificá el número de tu factura o pedí el alta a Ventas.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    cliente = resuelto['cliente']
    if cliente is None:
        logger.info('Activación: código %s válido en ERP pero sin ficha local', numero)
        return Response(
            {'error': 'Tu código es válido pero tu ficha aún no está creada. Pedí el alta a Ventas.',
             'code': 'requiere_alta'},
            status=status.HTTP_409_CONFLICT,
        )
    if cliente.user.has_usable_password():
        return Response(
            {'error': 'Esta cuenta ya tiene contraseña. Ingresá o usá "¿Olvidaste tu contraseña?".',
             'code': 'ya_activa'},
            status=status.HTTP_409_CONFLICT,
        )
    return Response({
        'numero_cliente': cliente.numero_cliente,
        'nombre': cliente.nombre,
        'email_enmascarado': _enmascarar_email(cliente.user.email) if cliente.user.email else None,
        'whatsapp_enmascarado': _enmascarar_whatsapp(cliente.whatsapp) if cliente.whatsapp else None,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ActivacionRateThrottle])
def enviar(request):
    numero = normalizar_codigo(request.data.get('codigo_cliente'))
    email = (request.data.get('email') or '').strip()
    whatsapp_raw = (request.data.get('whatsapp') or '').strip()
    if numero is None or not email or not whatsapp_raw:
        return Response(
            {'error': 'Completá código de cliente, email y WhatsApp.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        validate_email(email)
    except ValidationError:
        return Response({'error': 'El email no es válido.'}, status=status.HTTP_400_BAD_REQUEST)
    whatsapp = normalize_phone_ar(whatsapp_raw)
    if whatsapp is None:
        return Response(
            {'error': 'El WhatsApp no es válido. Usá un móvil argentino, ej: 11-1234-5678.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    resuelto = resolver_codigo(numero)
    cliente = resuelto['cliente'] if resuelto else None
    if cliente is None or cliente.user.has_usable_password():
        return Response(
            {'error': 'No se puede activar esta cuenta. Verificá el código o pedí ayuda a Ventas.'},
            status=status.HTTP_409_CONFLICT,
        )

    cfg = _otp_settings()
    pendiente = _otp_vigente(cliente)
    if pendiente is not None and pendiente.ultimo_envio_at:
        espera = cfg['cooldown_seg'] - (timezone.now() - pendiente.ultimo_envio_at).total_seconds()
        if espera > 0:
            return Response(
                {'error': f'Ya te enviamos un código. Podés pedir otro en {int(espera)} segundos.',
                 'reintentar_en': int(espera)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

    cliente.user.email = email
    cliente.user.save(update_fields=['email'])
    cliente.whatsapp = whatsapp
    cliente.save(update_fields=['whatsapp'])

    canales = _crear_y_enviar(cliente, email, whatsapp)
    logger.info('Activación OTP enviada a cliente %s (email=%s whatsapp=%s)',
                numero, canales['email'], canales['whatsapp'])
    return Response({
        'message': 'Te enviamos un código de verificación por email y WhatsApp.',
        'expira_en': cfg['expira_seg'],
        'canales': {'email': canales['email'], 'whatsapp': canales['whatsapp']},
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ActivacionRateThrottle])
def reenviar(request):
    numero = normalizar_codigo(request.data.get('codigo_cliente'))
    if numero is None:
        return Response({'error': 'Ingresá tu código de cliente.'}, status=status.HTTP_400_BAD_REQUEST)
    resuelto = resolver_codigo(numero)
    cliente = resuelto['cliente'] if resuelto else None
    if cliente is None or cliente.user.has_usable_password():
        return Response({'error': 'No hay activación pendiente para este código.'},
                        status=status.HTTP_409_CONFLICT)
    email = (cliente.user.email or '').strip()
    whatsapp = (cliente.whatsapp or '').strip()
    if not email or not whatsapp:
        return Response({'error': 'Primero completá tu email y WhatsApp.'},
                        status=status.HTTP_409_CONFLICT)

    cfg = _otp_settings()
    pendiente = _otp_vigente(cliente)
    if pendiente is not None and pendiente.ultimo_envio_at:
        espera = cfg['cooldown_seg'] - (timezone.now() - pendiente.ultimo_envio_at).total_seconds()
        if espera > 0:
            return Response(
                {'error': f'Podés pedir otro código en {int(espera)} segundos.',
                 'reintentar_en': int(espera)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
    canales = _crear_y_enviar(cliente, email, whatsapp)
    return Response({
        'message': 'Te enviamos un código nuevo por email y WhatsApp.',
        'expira_en': cfg['expira_seg'],
        'canales': {'email': canales['email'], 'whatsapp': canales['whatsapp']},
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ActivacionRateThrottle])
def verificar(request):
    numero = normalizar_codigo(request.data.get('codigo_cliente'))
    if numero is None:
        return Response({'error': 'Ingresá tu código de cliente.'}, status=status.HTTP_400_BAD_REQUEST)
    resuelto = resolver_codigo(numero)
    cliente = resuelto['cliente'] if resuelto else None
    if cliente is None or cliente.user.has_usable_password():
        return Response({'error': 'No hay activación pendiente para este código.'},
                        status=status.HTTP_409_CONFLICT)
    _, error = _validar_otp(cliente, request.data.get('otp'))
    if error:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'ok': True, 'message': 'Código correcto. Creá tu contraseña.'})


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ActivacionRateThrottle])
def confirmar(request):
    numero = normalizar_codigo(request.data.get('codigo_cliente'))
    password1 = request.data.get('password1') or ''
    password2 = request.data.get('password2') or ''
    if numero is None:
        return Response({'error': 'Ingresá tu código de cliente.'}, status=status.HTTP_400_BAD_REQUEST)
    if not password1 or not password2:
        return Response({'error': 'Escribí la contraseña dos veces.'},
                        status=status.HTTP_400_BAD_REQUEST)
    if password1 != password2:
        return Response({'error': 'Las contraseñas no coinciden.'},
                        status=status.HTTP_400_BAD_REQUEST)
    resuelto = resolver_codigo(numero)
    cliente = resuelto['cliente'] if resuelto else None
    if cliente is None or cliente.user.has_usable_password():
        return Response({'error': 'No hay activación pendiente para este código.'},
                        status=status.HTTP_409_CONFLICT)

    registro, error = _validar_otp(cliente, request.data.get('otp'))
    if error:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

    usuario = cliente.user
    try:
        validate_password(password1, usuario)
    except ValidationError as exc:
        return Response({'error': ' '.join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

    usuario.set_password(password1)
    usuario.save(update_fields=['password'])
    cliente.whatsapp_verificado = True
    cliente.save(update_fields=['whatsapp_verificado'])
    registro.consumido_at = timezone.now()
    registro.save(update_fields=['consumido_at'])

    # Login automático: mismo payload que el login normal.
    refresh = RefreshToken.for_user(usuario)
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR')
    from .models import RegistroSesion
    sesion = RegistroSesion.objects.create(
        usuario=usuario, cliente=cliente,
        ip_address=ip, user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    logger.info('Cuenta activada para cliente %s', numero)
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': usuario.id,
            'username': usuario.username,
            'email': usuario.email,
            'first_name': usuario.first_name,
            'last_name': usuario.last_name,
            'is_staff': usuario.is_staff,
            'is_superuser': usuario.is_superuser,
        },
        'session_id': sesion.id,
    })
