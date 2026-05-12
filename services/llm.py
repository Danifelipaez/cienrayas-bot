import asyncio
import logging
from groq import Groq
from config import GROQ_API_KEY
from core.prompts import SYSTEM_PROMPT, build_fishing_prompt

logger = logging.getLogger(__name__)

_client = Groq(api_key=GROQ_API_KEY)
_MODEL = "llama-3.3-70b-versatile"


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
                wait = 8 * (attempt + 1)
                logger.warning(f"Groq 429 intento {attempt + 1} — esperando {wait}s")
                import time
                time.sleep(wait)
            else:
                raise
    raise last_exc


async def generate_fishing_response(
    weather: dict, satellite: dict, water_quality: dict, semaphore_color: str
) -> str:
    prompt = build_fishing_prompt(weather, satellite, water_quality, semaphore_color)
    return await asyncio.to_thread(_call_groq, prompt)


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
    return await asyncio.to_thread(_call_groq, prompt)
