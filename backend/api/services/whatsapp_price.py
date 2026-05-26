import re
import unicodedata
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q

from api.models import Articulos, Cliente
from api.services.precios import calcular_precio_articulo
from api.services.related_products import get_related_products_for_article


PRICE_KEYWORDS = ("precio", "sale", "cuanto", "cuánto", "stock", "tenes", "tenés")
MORE_OPTIONS_KEYWORDS = ("mas", "más", "otra", "otras", "solo esas", "alguna mas", "alguna más", "tenes mas", "tenés más")
COMPARISON_KEYWORDS = ("cual es mejor", "cuál es mejor", "mejor", "recomendas", "recomendás", "conviene")
QUERY_STOPWORDS = {
    "de", "del", "la", "el", "los", "las", "un", "una", "y", "o",
    "quiero", "queria", "quería", "necesito", "dame", "pasame", "me",
    "ese", "esa", "esos", "esas", "por", "favor",
}
OPTIONS_PAGE_SIZE = 3
QUOTE_CTA = "Queres que te arme un presupuesto? Tambien puedo sumar otra mercaderia que necesites."


def build_price_reply(text, user=None, context=None):
    pending_reply = _build_reply_from_pending_options(text, user, context)
    if pending_reply:
        return pending_reply

    query = _extract_product_query(text)
    matches = None
    if not query:
        query = _extract_standalone_product_query(text)
        if not query:
            return {"handled": False, "reply": ""}

        matches = list(_search_articulos(query)[:4])
        if not matches:
            return {"handled": False, "reply": ""}

    user = user or _get_bot_user()
    if not user:
        return {
            "handled": True,
            "reply": "El bot todavia no tiene configurado un usuario de precios. Aviso a Sistemas para revisarlo.",
        }

    try:
        cliente = Cliente.objects.select_related("codigo_localidad", "condicion_pago").get(user=user)
    except Cliente.DoesNotExist:
        return {
            "handled": True,
            "reply": "El usuario del bot no tiene cliente asociado para calcular precios. Aviso a Sistemas para revisarlo.",
        }

    if matches is None:
        matches = list(_search_articulos(query)[:4])
    if not matches:
        return {
            "handled": True,
            "reply": f"No encontre un articulo claro para \"{query}\". Me podes pasar marca, medida o algun dato mas?",
        }

    if len(matches) > 1:
        shown = matches[:OPTIONS_PAGE_SIZE]
        options = "\n".join(f"- {articulo.clave}: {articulo.nombre}" for articulo in shown)
        return {
            "handled": True,
            "reply": (
                f"Encontre varias opciones para \"{query}\":\n"
                f"{options}\n"
                f"Me decis cual queres consultar y te armo el presupuesto? "
                f"Tambien puedo sumar otra mercaderia."
            ),
            "context": {
                "pending_options": [
                    {"clave": articulo.clave, "nombre": articulo.nombre}
                    for articulo in shown
                ],
                "last_query": query,
                "shown_count": len(shown),
            },
        }

    articulo = matches[0]
    return _build_articulo_price_reply(articulo, cliente)


def _build_articulo_price_reply(articulo, cliente):
    precio = calcular_precio_articulo(
        articulo=articulo,
        cliente=cliente,
        modalidad="retira",
        con_impuestos=True,
        condicion_pago_id=cliente.condicion_pago_id,
    )

    related_text = _format_related_products(articulo.clave)
    return {
        "handled": True,
        "reply": (
            f"{articulo.nombre}\n"
            f"Codigo: {articulo.clave}\n"
            f"Precio retira con IVA: ${_format_price(precio)}\n"
            f"{related_text}"
            f"{QUOTE_CTA}"
        ),
    }


def _build_reply_from_pending_options(text, user, context):
    if not text or not context:
        return None

    pending_options = context.get("pending_options") or []
    if not pending_options:
        return None

    normalized = text.strip().lower()
    if _asks_for_comparison(normalized):
        return _build_comparison_reply(context)

    if _asks_for_more_options(normalized):
        more_options = _get_more_options_from_context(context)
        if more_options:
            return more_options
        return {
            "handled": True,
            "reply": "Por ahora esas son las opciones mas claras que encontre. Me podes pasar marca, medida, color o codigo?",
            "context": context,
        }

    user = user or _get_bot_user()
    if not user:
        return None

    try:
        cliente = Cliente.objects.select_related("codigo_localidad", "condicion_pago").get(user=user)
    except Cliente.DoesNotExist:
        return {
            "handled": True,
            "reply": "El usuario del bot no tiene cliente asociado para calcular precios. Aviso a Sistemas para revisarlo.",
            "context": context,
        }

    candidates = []
    partial_candidates = []
    query_words = _meaningful_words(normalized)
    for option in pending_options:
        clave = str(option.get("clave", ""))
        nombre = str(option.get("nombre", ""))
        haystack = _normalize_product_query(f"{clave} {nombre}")
        if normalized == clave.lower() or normalized in haystack:
            candidates.append(clave)
            continue

        option_words = set(_meaningful_words(haystack))
        if query_words and set(query_words).issubset(option_words):
            candidates.append(clave)
            continue

        overlap = option_words.intersection(query_words)
        if overlap:
            partial_candidates.append((len(overlap), clave))

    if not candidates:
        if not partial_candidates:
            return None
        best_score = max(score for score, _clave in partial_candidates)
        candidates = [clave for score, clave in partial_candidates if score == best_score]

    articulos = list(Articulos.objects.filter(clave__in=candidates).order_by("clave")[:4])
    if len(articulos) == 1:
        result = _build_articulo_price_reply(articulos[0], cliente)
        result["context"] = {}
        return result

    options = "\n".join(f"- {articulo.clave}: {articulo.nombre}" for articulo in articulos[:3])
    return {
        "handled": True,
        "reply": (
            f"Todavia veo mas de una opcion:\n"
            f"{options}\n"
            f"Me pasas el codigo exacto y te armo el presupuesto?"
        ),
        "context": {
            "pending_options": [
                {"clave": articulo.clave, "nombre": articulo.nombre}
                for articulo in articulos[:3]
            ],
            "last_query": context.get("last_query", ""),
            "shown_count": len(articulos[:3]),
        },
    }


def _asks_for_more_options(normalized_text):
    return any(keyword in normalized_text for keyword in MORE_OPTIONS_KEYWORDS)


def _asks_for_comparison(normalized_text):
    normalized = _normalize_product_query(normalized_text)
    return any(_normalize_product_query(keyword) in normalized for keyword in COMPARISON_KEYWORDS)


def _build_comparison_reply(context):
    pending_options = context.get("pending_options") or []
    options = "\n".join(
        f"- {option.get('clave')}: {option.get('nombre')}"
        for option in pending_options[:OPTIONS_PAGE_SIZE]
    )
    return {
        "handled": True,
        "reply": (
            "Para recomendarte mejor necesito saber el uso: interior o exterior, "
            "superficie y si priorizas precio o rendimiento.\n"
            f"Por ahora tengo estas opciones:\n{options}\n"
            "Si queres, pasame esos datos y te ayudo a elegir para armar el presupuesto."
        ),
        "context": context,
    }


def _format_related_products(article_code):
    related = get_related_products_for_article(article_code, limit=3)
    if not related:
        return ""

    options = "\n".join(
        f"- {item['clave']}: {item['detalle']}"
        for item in related
    )
    return f"Tambien te puedo ofrecer:\n{options}\n"


def _get_more_options_from_context(context):
    query = context.get("last_query")
    if not query:
        return None

    shown_count = int(context.get("shown_count") or len(context.get("pending_options") or []))
    matches = list(_search_articulos(query)[shown_count : shown_count + OPTIONS_PAGE_SIZE + 1])
    if not matches:
        return None

    shown = matches[:OPTIONS_PAGE_SIZE]
    options = "\n".join(f"- {articulo.clave}: {articulo.nombre}" for articulo in shown)
    new_shown_count = shown_count + len(shown)
    return {
        "handled": True,
        "reply": (
            f"Tengo mas opciones para \"{query}\":\n"
            f"{options}\n"
            f"Cual queres consultar y te armo el presupuesto? "
            f"Tambien puedo sumar otra mercaderia."
        ),
        "context": {
            "pending_options": [
                {"clave": articulo.clave, "nombre": articulo.nombre}
                for articulo in shown
            ],
            "last_query": query,
            "shown_count": new_shown_count,
        },
    }


def _get_bot_user():
    username = getattr(settings, "WHATSAPP_BOT_USERNAME", "")
    if not username:
        return None
    return get_user_model().objects.filter(username=username).first()


def _extract_product_query(text):
    if not text:
        return ""

    normalized = text.strip().lower()
    if not any(keyword in normalized for keyword in PRICE_KEYWORDS):
        return ""

    query = normalized
    replacements = (
        "precio de",
        "precio",
        "cuanto sale",
        "cuánto sale",
        "cuanto vale",
        "cuánto vale",
        "tenes",
        "tenés",
        "hay stock de",
        "stock de",
        "stock",
        "?",
        "¿",
    )
    for value in replacements:
        query = query.replace(value, " ")

    return _normalize_product_query(query)


def _extract_standalone_product_query(text):
    if not text:
        return ""

    query = _normalize_product_query(text)
    if len(query) < 3:
        return ""
    return query


def _normalize_product_query(text):
    normalized = text.strip().lower().replace("?", " ").replace("¿", " ")
    normalized = "".join(
        char for char in unicodedata.normalize("NFKD", normalized)
        if not unicodedata.combining(char)
    )
    words = []
    for word in re.split(r"\s+", normalized):
        word = _singularize_word(word)
        if word and word not in QUERY_STOPWORDS:
            words.append(word)
    return " ".join(words)


def _meaningful_words(text):
    return [word for word in re.split(r"\s+", _normalize_product_query(text)) if len(word) >= 2]


def _singularize_word(word):
    if len(word) > 4 and word.endswith("es"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s"):
        return word[:-1]
    return word


def _search_articulos(query):
    empresa_id = getattr(settings, "EMPRESA_ID", 1)
    base = Articulos.objects.filter(empresa_id=empresa_id).exclude(discontinuado="S")

    exact = base.filter(clave__iexact=query)
    if exact.exists():
        return exact.order_by("clave")

    words = [word for word in re.split(r"\s+", query) if len(word) >= 2]
    if not words:
        return base.none()

    filters = Q()
    for word in words:
        filters &= Q(nombre__icontains=word) | Q(descripcion__icontains=word) | Q(clave__icontains=word)

    return base.filter(filters).order_by("clave")


def _format_price(value):
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return f"{value:.2f}"
