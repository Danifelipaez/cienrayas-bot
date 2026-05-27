import asyncio
import logging
import time
from datetime import datetime, timezone
from groq import Groq
from config import GROQ_API_KEY
from core.prompts import SYSTEM_PROMPT, build_fishing_prompt

logger = logging.getLogger(__name__)

_client = Groq(api_key=GROQ_API_KEY)
_MODEL = "llama-3.3-70b-versatile"

# Máx 3 llamadas Groq concurrentes — evita 429 con 50 usuarios simultáneos
_LLM_SEMAPHORE: asyncio.Semaphore | None = None

# Caché por color de semáforo: todos los usuarios con las mismas condiciones
# comparten la respuesta — reduce llamadas Groq de 50 a 1 por cada 15 min
_response_cache: dict[str, tuple[str, datetime]] = {}
_RESPONSE_CACHE_TTL = 15 * 60  # 15 minutos


def _get_semaphore() -> asyncio.Semaphore:
    global _LLM_SEMAPHORE
    if _LLM_SEMAPHORE is None:
        _LLM_SEMAPHORE = asyncio.Semaphore(3)
    return _LLM_SEMAPHORE


def _call_groq(prompt: str) -> str:
    last_exc = None
    for attempt in range(3):
        try:
            response = _client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=400,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_exc = e
            if "429" in str(e) or "rate_limit" in str(e).lower():
                wait = 5 * (attempt + 1)  # 5s, 10s, 15s
                logger.warning(f"Groq 429 intento {attempt + 1} — esperando {wait}s")
                time.sleep(wait)
            else:
                raise
    raise last_exc


async def generate_fishing_response(
    weather: dict, satellite: dict, water_quality: dict, semaphore_color: str
) -> str:
    # Fast path: cache hit — todos los usuarios con el mismo semáforo comparten respuesta
    cached = _response_cache.get(semaphore_color)
    if cached:
        text, ts = cached
        if (datetime.now(timezone.utc) - ts).total_seconds() < _RESPONSE_CACHE_TTL:
            logger.info(f"LLM cache hit — semáforo {semaphore_color}")
            return text

    async with _get_semaphore():
        # Double-check dentro del semáforo: otro request puede haber poblado el caché
        cached = _response_cache.get(semaphore_color)
        if cached:
            text, ts = cached
            if (datetime.now(timezone.utc) - ts).total_seconds() < _RESPONSE_CACHE_TTL:
                logger.info(f"LLM cache hit (post-lock) — semáforo {semaphore_color}")
                return text

        logger.info(f"LLM call — semáforo {semaphore_color} (generando respuesta nueva)")
        prompt = build_fishing_prompt(weather, satellite, water_quality, semaphore_color)
        text = await asyncio.to_thread(_call_groq, prompt)
        _response_cache[semaphore_color] = (text, datetime.now(timezone.utc))
        return text


async def generate_feedback_ack(feedback_text: str) -> str:
    prompt = f"""Un pescador de la Ciénaga Grande te contó cómo le fue hoy en la faena:
"{feedback_text}"

Escríbele una respuesta corta (máx 3 líneas) siguiendo estas reglas:
- Habla como un compañero pescador del Caribe, con confianza y calidez
- Reacciona específicamente a lo que dijo: si le fue bien, celebra con él; si le fue mal, acompáñalo
- Si menciona una zona, especie o condición del agua, comenta sobre eso
- Agradécele el reporte porque ayuda a que las alertas sean más exactas para todos
- Termina invitándolo a consultar mañana
- Máximo 3 líneas, sin emojis excesivos (máx 1)
- Cero palabras técnicas"""
    async with _get_semaphore():
        return await asyncio.to_thread(_call_groq, prompt)
