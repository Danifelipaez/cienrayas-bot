import asyncio
import logging
from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from core.prompts import SYSTEM_PROMPT, build_fishing_prompt

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=GEMINI_API_KEY)
_MODEL = "gemini-2.0-flash-lite"  # mayor cuota gratuita que gemini-2.0-flash


def _call_gemini(prompt: str) -> str:
    last_exc = None
    for attempt in range(3):
        try:
            response = _client.models.generate_content(
                model=_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            return response.text
        except Exception as e:
            last_exc = e
            # 429 = límite de peticiones — esperar antes de reintentar
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 10 * (attempt + 1)  # 10s, 20s, 30s
                logger.warning(f"Gemini 429 intento {attempt + 1} — esperando {wait}s")
                import time
                time.sleep(wait)
            else:
                raise
    raise last_exc


async def generate_fishing_response(
    weather: dict, satellite: dict, water_quality: dict, semaphore_color: str
) -> str:
    prompt = build_fishing_prompt(weather, satellite, water_quality, semaphore_color)
    return await asyncio.to_thread(_call_gemini, prompt)


async def generate_feedback_ack(feedback_text: str) -> str:
    prompt = (
        f"Un pescador respondió al feedback: \"{feedback_text}\"\n"
        "Escribe un agradecimiento corto (máx 2 líneas), coloquial y cercano. "
        "Menciona que su reporte ayuda a mejorar el sistema."
    )
    return await asyncio.to_thread(_call_gemini, prompt)
