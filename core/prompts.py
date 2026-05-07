SYSTEM_PROMPT = """
Eres CienRayas, el asistente de pesca de la Ciénaga Grande de Santa Marta.
Hablas como un colega pescador del Caribe colombiano: coloquial, directo y cercano.
Usas términos locales: "faena", "viento de loma", "subienda", "palangre", "atarraya", "mancha".
La seguridad siempre va primero — si hay riesgo, lo dices claro y rápido.
Eres conciso: WhatsApp no es para novelas. Mensajes cortos y claros.
No usas lenguaje técnico innecesario con los pescadores.
"""


def build_fishing_prompt(weather: dict, satellite: dict, semaphore_color: str) -> str:
    sst = satellite.get("sst", "N/A")
    chl = satellite.get("chlorophyll", "N/A")
    sst_src = satellite.get("sst_source", "")
    chl_src = satellite.get("chlorophyll_source", "")

    clima_header = "CLIMA (Open-Meteo) ⚠️ — datos no disponibles, usa precaución:" if weather.get("fallback") else "CLIMA (Open-Meteo):"

    return f"""
Datos ambientales actuales de la Ciénaga Grande de Santa Marta:

{clima_header}
- Viento: {weather.get('wind_speed', 'N/A')} km/h del {weather.get('wind_direction_name', 'N/A')}
- Ráfagas: {weather.get('wind_gusts', 'N/A')} km/h
- Lluvia actual: {weather.get('precipitation', 'N/A')} mm
- Condición general: {weather.get('condition', 'N/A')}

DATOS DEL AGUA ({sst_src}):
- Temperatura superficial: {sst}°C
- Clorofila-a ({chl_src}): {chl} mg/m³  ← más clorofila = más peces

SEMÁFORO DEL DÍA: {semaphore_color.upper()}

Genera un mensaje de WhatsApp para un pescador artesanal de la Ciénaga.
Instrucciones:
1. Empieza con el semáforo y si vale la pena salir a faena
2. Explica el clima en 1-2 líneas con lenguaje local
3. Comenta la temperatura y si hay mancha de peces por la clorofila
4. Da una recomendación concreta (zona o acción)
5. Máximo 180 palabras
6. Usa emojis con moderación (🎣🌊💨⚠️🟢🟡🔴)
NO incluyas la pregunta de feedback — esa se agrega sola.
"""
