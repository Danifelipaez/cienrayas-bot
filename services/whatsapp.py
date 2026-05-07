import logging
import httpx
from config import WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID

logger = logging.getLogger(__name__)

_API_URL = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
_HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    "Content-Type": "application/json",
}

if not WHATSAPP_TOKEN:
    logger.error("WHATSAPP_TOKEN no está configurado — los mensajes no se enviarán")
if not WHATSAPP_PHONE_NUMBER_ID:
    logger.error("WHATSAPP_PHONE_NUMBER_ID no está configurado")


async def send_text(to: str, body: str):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body, "preview_url": False},
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(_API_URL, headers=_HEADERS, json=payload)
            r.raise_for_status()
    except Exception as e:
        logger.error(f"Error enviando texto a {to}: {e}")
        raise


async def send_image(to: str, image_url: str, caption: str = ""):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": image_url, "caption": caption},
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(_API_URL, headers=_HEADERS, json=payload)
            r.raise_for_status()
    except Exception as e:
        logger.error(f"Error enviando imagen a {to}: {e}")
        raise


async def send(to: str, body: str, image_url: str = None):
    if image_url:
        await send_image(to, image_url, caption=body)
    else:
        await send_text(to, body)
