"""
Gestión en memoria del estado de conversación por número de teléfono.
En producción reemplazar por Redis o base de datos.
"""
from datetime import datetime

_conversations: dict[str, dict] = {}

# Palabras que indican que el pescador quiere un nuevo análisis (no feedback)
_NEW_QUERY_KEYWORDS = [
    "puedo pescar", "puedo salir", "como esta", "cómo está", "semaforo",
    "condiciones", "clima", "como va", "cómo va", "hoy como", "hoy cómo",
]


def get_state(phone: str) -> dict:
    return _conversations.get(phone, {})


def set_state(phone: str, data: dict):
    _conversations[phone] = {**_conversations.get(phone, {}), **data}


def record_query(phone: str):
    set_state(phone, {
        "last_query": datetime.now().isoformat(),
        "awaiting_feedback": True,
    })


def record_feedback(phone: str, text: str):
    state = get_state(phone)
    feedbacks = state.get("feedbacks", [])
    feedbacks.append({
        "text": text,
        "timestamp": datetime.now().isoformat(),
    })
    set_state(phone, {"feedbacks": feedbacks, "awaiting_feedback": False})


def is_awaiting_feedback(phone: str) -> bool:
    return _conversations.get(phone, {}).get("awaiting_feedback", False)


def looks_like_new_query(message: str) -> bool:
    """Detecta si el pescador quiere un análisis nuevo en lugar de dar feedback."""
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in _NEW_QUERY_KEYWORDS)


def looks_like_feedback(message: str) -> bool:
    """
    Cuando el bot está esperando feedback, cualquier mensaje se trata como
    reporte del pescador, a menos que sea claramente una consulta nueva.
    """
    return not looks_like_new_query(message)
