"""
Webhook para Meta WhatsApp Cloud API.

Flujo de verificación inicial (una sola vez al configurar):
  GET /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
  → Responde con hub.challenge si el token coincide

Flujo de mensajes (cada mensaje del usuario):
  POST /webhook  con JSON de Meta
  → Respondemos 200 inmediatamente
  → BackgroundTask procesa y envía respuesta via WhatsApp API
"""
import asyncio
import logging
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)

from config import WEBHOOK_VERIFY_TOKEN, BASE_URL
from services.whatsapp import send
from services.weather import get_weather
from services.satellite import get_satellite_data
from services.map_generator import generate_map
from services.llm import generate_fishing_response, generate_feedback_ack
from core.semaphore import evaluate
from core.state import (
    record_query, record_feedback,
    is_awaiting_feedback, looks_like_feedback,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Tareas de fondo
# ---------------------------------------------------------------------------

async def _handle_fishing_query(from_number: str, user_message: str):
    try:
        weather, satellite = await asyncio.gather(
            get_weather(),
            get_satellite_data(),
        )
    except Exception as e:
        logger.error(f"Error obteniendo datos para {from_number}: {e}")
        await send(from_number,
                   f"Ay compa, no pude conectarme con los datos del clima 😅 "
                   f"Intente en unos minutos. ({e.__class__.__name__})")
        return

    result = evaluate(weather, satellite)

    # ROJO — alerta de seguridad, sin mapa
    if not result.safe:
        await send(
            from_number,
            f"⚠️ *ALERTA DE SEGURIDAD*\n\n"
            f"{result.emoji} *{result.reason}*\n\n"
            f"Compa, hoy NO se recomienda salir a faena. "
            f"La vida primero. Espere que pasen estas condiciones.",
        )
        record_query(from_number)
        await send(from_number,
                   "Cuénteme cómo está la ciénaga por donde usted está, "
                   "eso me ayuda a mejorar las alertas 🙏")
        return

    # VERDE / AMARILLO — análisis completo
    try:
        response_text, map_filename = await asyncio.gather(
            generate_fishing_response(weather, satellite, result.color),
            asyncio.to_thread(
                generate_map, result.color,
                satellite["sst"], satellite["chlorophyll"]
            ),
        )
    except Exception as e:
        logger.error(f"Error generando análisis para {from_number}: {e}")
        await send(from_number,
                   f"Tuve un problema generando el análisis 😓 Error: {str(e)[:60]}")
        return

    footer = (
        f"\n\n━━━━━━━━━━━━━\n"
        f"_{result.emoji} {result.reason}_\n"
        f"_Fuentes: NASA · Open-Meteo · {satellite['sst_source']}_"
    )
    await send(from_number, response_text + footer)

    map_url = f"{BASE_URL}/media/{map_filename}"
    await send(from_number, "📍 *Mapa de zonas para hoy:*", map_url)

    await send(
        from_number,
        "Compa, ¿cómo le fue hoy? Cuénteme si la zona estaba buena "
        "para que yo aprenda 🎣",
    )
    record_query(from_number)


async def _handle_feedback(from_number: str, message: str):
    record_feedback(from_number, message)
    try:
        ack = await generate_feedback_ack(message)
    except Exception:
        ack = "¡Gracias compa! Su reporte me ayuda a mejorar 💪"
    await send(from_number, ack + "\n\nEscriba cuando quiera consultar las condiciones 🎣")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta llama a este endpoint una sola vez para verificar el webhook."""
    if hub_mode == "subscribe" and hub_verify_token == WEBHOOK_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge)
    raise HTTPException(status_code=403, detail="Token de verificación inválido")


@router.post("/webhook")
async def receive_webhook(background_tasks: BackgroundTasks, request: Request):
    """Meta envía aquí cada mensaje entrante."""
    data = await request.json()

    try:
        entry = data["entry"][0]
        change = entry["changes"][0]["value"]

        # Ignorar notificaciones de estado (delivered, read, etc.)
        if "messages" not in change:
            return {"status": "ok"}

        message = change["messages"][0]
        if message.get("type") != "text":
            return {"status": "ok"}  # Ignorar audio/imagen/stickers por ahora

        from_number = message["from"]          # e.g. "573001234567"
        body = message["text"]["body"].strip()

        if is_awaiting_feedback(from_number) and looks_like_feedback(body):
            background_tasks.add_task(_handle_feedback, from_number, body)
        else:
            background_tasks.add_task(_handle_fishing_query, from_number, body)

    except (KeyError, IndexError):
        pass  # Ignorar formatos inesperados sin romper el webhook

    # Meta requiere 200 inmediato — el procesamiento es async
    return {"status": "ok"}
