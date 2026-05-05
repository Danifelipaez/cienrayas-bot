import asyncio
from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from core.prompts import SYSTEM_PROMPT, build_fishing_prompt

_client = genai.Client(api_key=GEMINI_API_KEY)
_MODEL = "gemini-2.0-flash"


def _call_gemini(prompt: str) -> str:
    response = _client.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    return response.text


async def generate_fishing_response(weather: dict, satellite: dict, semaphore_color: str) -> str:
    prompt = build_fishing_prompt(weather, satellite, semaphore_color)
    return await asyncio.to_thread(_call_gemini, prompt)


async def generate_feedback_ack(feedback_text: str) -> str:
    prompt = (
        f"Un pescador respondió al feedback: \"{feedback_text}\"\n"
        "Escribe un agradecimiento corto (máx 2 líneas), coloquial y cercano. "
        "Menciona que su reporte ayuda a mejorar el sistema."
    )
    return await asyncio.to_thread(_call_gemini, prompt)
