"""
LLM: Google Gemini Flash — completamente gratis (1500 req/día, 1M tokens/día).
Obtener API key en: https://aistudio.google.com/app/apikey
"""
import asyncio
import google.generativeai as genai
from config import GEMINI_API_KEY
from core.prompts import SYSTEM_PROMPT, build_fishing_prompt

genai.configure(api_key=GEMINI_API_KEY)

_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT,
)


def _call_gemini(prompt: str) -> str:
    return _model.generate_content(prompt).text


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
