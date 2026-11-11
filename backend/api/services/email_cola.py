"""Envío de emails del portal por la cola centralizada `fe.emails_pendientes`.

El portal NO usa SMTP directo: encola (estado 'pendiente', empresa 1 =
Ferretería Avenida) y los manda el servidor genera-fe-2025
(`controladores/EnvioEmailsPendientes.py`, `smtp-relay.gmail.com`).

Contrato de la cola (ver automatizaciones/scripts/OFERTAS_EMAIL.md):
- un solo destinatario ASCII por fila (la tabla es latin1);
- cuerpo representable en latin1 (sin emojis);
- sin imágenes inline (el logo va por URL);
- `quien_envia` del mismo dominio que la cuenta que autentica (DMARC).

Si la base `fe` no está configurada o falla, el llamador decide el
fallback (SMTP directo de Django).
"""

import logging
import unicodedata

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('api')

COLA_DB_ALIAS = 'fe'
ESTADO_PENDIENTE = 'pendiente'


def sanitizar_latin1(texto):
    """Deja el texto representable en latin1 (lo que exige la cola).

    Normaliza y reemplaza por '?' lo que no entra (emojis, etc.).
    """
    if texto is None:
        return None
    normalizado = unicodedata.normalize('NFC', str(texto))
    return normalizado.encode('latin1', errors='replace').decode('latin1')


def cola_disponible():
    """True si hay alias `fe` configurado en DATABASES."""
    return COLA_DB_ALIAS in settings.DATABASES


def encolar_email(destinatario, asunto, cuerpo_html=None, cuerpo_texto=None,
                  quien_envia=None, empresa_id=None):
    """Encola un email. Devuelve el registro o None si la cola no está disponible."""
    if not cola_disponible():
        logger.info('Cola de emails no configurada (sin alias fe)')
        return None
    if not destinatario or ',' in destinatario or ';' in destinatario:
        logger.warning('Destinatario inválido para la cola: %s', destinatario)
        return None
    try:
        ascii_dest = destinatario.strip().encode('ascii').decode('ascii')
    except (UnicodeEncodeError, ValueError):
        logger.warning('Destinatario no ASCII para la cola: %s', destinatario)
        return None

    from api.models import EmailPendiente
    return EmailPendiente.objects.using(COLA_DB_ALIAS).create(
        destinatario=ascii_dest,
        quien_envia=quien_envia or getattr(
            settings, 'ACTIVACION_EMAIL_QUIEN_ENVIA', 'ventas@ferreteriaavenida.com.ar'),
        asunto=sanitizar_latin1(asunto),
        cuerpo_html=sanitizar_latin1(cuerpo_html),
        cuerpo_texto=sanitizar_latin1(cuerpo_texto),
        intentos=0,
        estado=ESTADO_PENDIENTE,
        creado_en=timezone.now(),
        empresa_id=empresa_id if empresa_id is not None else getattr(
            settings, 'ACTIVACION_EMAIL_EMPRESA_ID', 1),
    )
