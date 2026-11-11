"""Cliente HTTP para Vogel WhatsApp API (gateway central).

Se usa para el envío del OTP de activación de cuentas. Es un proveedor
distinto del bot Meta Cloud API (`services/whatsapp.py`): no mezclar.

Referencia: docs/specs/activacion-cuenta-otp.md + docs/API_V1.md del
repo privado oscarvogel/vogel_whatsapp_api.
"""

import json
import logging
import re
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from django.conf import settings

logger = logging.getLogger('api')

SOURCE_APP = 'revendedores'


def normalize_phone_ar(raw):
    """Normaliza un teléfono argentino a formato internacional sin '+'.

    Acepta '11-1234-5678', '0376 4-123456', '+549...', etc. y devuelve
    '549...' (12-13 dígitos). Devuelve None si no es válido.
    """
    if not raw:
        return None
    digitos = re.sub(r'\D', '', str(raw))
    # Sacar prefijos comunes: 0 nacional, 15 de móvil local, + ya removido.
    if digitos.startswith('549'):
        normal = digitos
    elif digitos.startswith('54'):
        normal = digitos
    else:
        if digitos.startswith('0'):
            digitos = digitos[1:]
        if digitos.startswith('15'):
            digitos = digitos[2:]
        normal = '549' + digitos if not digitos.startswith('549') else digitos
    if not re.fullmatch(r'549\d{10}', normal):
        return None
    return normal


class VogelWhatsAppClient:
    """Envoltorio mínimo del gateway para envío de texto."""

    def __init__(self, api_url=None, api_key=None, instance_id=None, timeout=None):
        self.api_url = (api_url or getattr(settings, 'WHATSAPP_API_URL', '')).rstrip('/')
        self.api_key = api_key if api_key is not None else getattr(settings, 'WHATSAPP_API_KEY', '')
        self.instance_id = instance_id or getattr(settings, 'WHATSAPP_INSTANCE_ID', 'default')
        self.timeout = timeout or getattr(settings, 'WHATSAPP_API_TIMEOUT', 15)

    def is_configured(self):
        enabled = getattr(settings, 'WHATSAPP_ENABLED', False)
        return bool(enabled and self.api_url and self.api_key and self.instance_id)

    def send_text(self, phone, message, external_ref='', actor_name='Portal Revendedores'):
        """Envía un texto. 202 = encolado (no entregado). Nunca loguea la key."""
        phone = normalize_phone_ar(phone) or (phone or '').strip()
        if not self.is_configured():
            logger.info('Vogel send omitido: integración no configurada')
            return {'sent': False, 'reason': 'not_configured'}
        if not phone:
            return {'sent': False, 'reason': 'telefono_invalido'}

        url = f'{self.api_url}/api/v1/instances/{self.instance_id}/messages'
        body = json.dumps({
            'phone': phone,
            'message': message,
            'externalRef': external_ref,
            'sourceApp': SOURCE_APP,
            'actorName': actor_name,
        }).encode('utf-8')
        req = urlrequest.Request(
            url,
            data=body,
            headers={'x-api-key': self.api_key, 'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urlrequest.urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode('utf-8') or '{}')
        except HTTPError as exc:
            logger.warning('Vogel send HTTP %s para %s', exc.code, external_ref)
            return {'sent': False, 'reason': f'http_{exc.code}'}
        except (URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            logger.warning('Vogel send fallo de red para %s: %s', external_ref, type(exc).__name__)
            return {'sent': False, 'reason': 'error_red'}
        data = payload.get('data') or {}
        return {'sent': True, 'message_id': data.get('messageId'), 'status': data.get('status')}
