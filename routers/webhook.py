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
from services.water_quality import get_water_quality
from services.map_generator import generate_map
from services.llm import generate_fishing_response, generate_feedback_ack
from core.semaphore import evaluate
from core.zone_analysis import recommend_zone, full_ranking
from core.state import (
    record_query, record_feedback,
    is_awaiting_feedback, looks_like_feedback,
    is_duplicate,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Tareas de fondo
# ---------------------------------------------------------------------------

async def _handle_fishing_query(from_number: str, user_message: str):
    try:
        weather, satellite, water_quality = await asyncio.gather(
            get_weather(),
            get_satellite_data(),
            get_water_quality(),
        )
    except Exception as e:
        logger.error(f"Error obteniendo datos para {from_number}: {e}")
        await send(from_number,
                   f"Ay compa, no pude conectarme con los datos del clima 😅 "
                   f"Intente en unos minutos. ({e.__class__.__name__})")
        return

    result = evaluate(weather, satellite, water_quality)
    ranking = full_ranking(satellite, water_quality)
    best_zone = ranking[0]

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
            generate_fishing_response(weather, satellite, water_quality, result.color),
            asyncio.to_thread(
                generate_map, result.color,
                satellite["sst"], satellite["chlorophyll"],
                water_quality, ranking,
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
        f"_Datos: NASA · IDEAM · clima en tiempo real_"
    )

    try:
        await send(from_number, response_text + footer)
    except Exception as e:
        logger.error(f"Error enviando análisis a {from_number}: {e}")

    try:
        map_url = f"{BASE_URL}/media/{map_filename}"
        await send(from_number, "📍 *Mapa de zonas para hoy:*", map_url)
    except Exception as e:
        logger.error(f"Error enviando mapa a {from_number}: {e}")

    try:
        await send(
            from_number,
            "Cuénteme compa, ¿cómo le fue en la faena hoy? "
            "¿Pescó bien, la zona estaba buena? Su reporte me ayuda a mejorar las alertas 🙏",
        )
    except Exception as e:
        logger.error(f"Error enviando pregunta feedback a {from_number}: {e}")
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

        # Ignorar reintentos de Meta — mismo mensaje_id ya procesado
        if is_duplicate(message.get("id", "")):
            logger.info(f"Mensaje duplicado ignorado: {message.get('id')}")
            return {"status": "ok"}

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
