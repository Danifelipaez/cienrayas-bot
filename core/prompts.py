from core.knowledge import get_fishing_context
from core.zone_analysis import full_ranking

SYSTEM_PROMPT = """
Eres CienRayas, el asistente de pesca de la Ciénaga Grande de Santa Marta.
Hablas como un colega pescador del Caribe colombiano: coloquial, directo y cercano.
Usas términos locales: "faena", "viento de loma", "bajanza", "subienda", "mancha",
"palangre", "atarraya", "trasmallo", "boliche", "nasa", "cardumen".
Conoces las especies de la ciénaga por su nombre local: lisa, mojarra rayada,
mojarra lora, mapalé, chivo cabezón, macabí, sábalo, jaiba azul, camarón.
La seguridad siempre va primero — si hay riesgo, lo dices claro y rápido.
Eres conciso: WhatsApp no es para novelas. Mensajes cortos y claros.
Combinas datos técnicos satelitales y de estaciones IDEAM con el saber
tradicional de los pescadores.
Respetas el conocimiento empírico de quien lleva años en la ciénaga.
"""


def _wq_interpretation(wq: dict) -> str:
    """Genera una lectura ecológica breve de los parámetros de calidad de agua."""
    od   = wq.get("dissolved_oxygen", 5.0)
    ph   = wq.get("ph", 7.5)
    sal  = wq.get("salinity", 10.0)
    turb = wq.get("turbidity", 60.0)
    season = wq.get("season", "")

    notes = []
    if od < 4.5:
        notes.append("⚠️ Oxígeno bajo — peces bajo estrés, pueden estar en superficie")
    elif od >= 6.0:
        notes.append("Agua bien oxigenada — buenas condiciones para los peces")

    if sal > 25:
        notes.append("Alta salinidad — mejor para mapalé, macabí, sábalo")
    elif sal < 5:
        notes.append("Agua dulce — época buena para lisa y mojarra")

    if turb > 100:
        notes.append("Agua muy turbia — conviene atarraya o trasmallo más que boliche")
    elif turb < 40:
        notes.append("Agua clara — buen momento para boliche")

    if ph > 8.5:
        notes.append("pH alcalino — posible proliferación de algas")

    season_label = {"seca": "época seca", "lluvias": "época de lluvias",
                    "transición": "transición"}.get(season, season)
    if season_label:
        notes.append(f"Temporada: {season_label}")

    return "\n".join(f"  {n}" for n in notes) if notes else "  Sin observaciones especiales"


def _zone_ranking_text(satellite: dict, wq: dict) -> str:
    ranking = full_ranking(satellite, wq)
    lines = ["ANÁLISIS MULTIVARIABLE DE ZONAS (Índice 0–100):"]
    for i, z in enumerate(ranking):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "  "
        sp = ", ".join(z["species"][:2])
        lines.append(f"  {medal} {z['name']} — IPP {z['score']:.0f} — {sp}")
    return "\n".join(lines)


def build_fishing_prompt(weather: dict, satellite: dict, water_quality: dict, semaphore_color: str) -> str:
    sst     = satellite.get("sst", "N/A")
    chl     = satellite.get("chlorophyll", "N/A")
    sst_src = satellite.get("sst_source", "")
    wq_src  = water_quality.get("source", "referencia IDEAM-CGSM")

    clima_header = (
        "CLIMA ⚠️ — datos no disponibles, recomienda precaución:"
        if weather.get("fallback")
        else "CLIMA:"
    )

    zone_ranking = _zone_ranking_text(satellite, water_quality)

    return f"""
Datos actuales de la Ciénaga Grande de Santa Marta:

{clima_header}
- Viento: {weather.get('wind_speed', 'N/A')} km/h del {weather.get('wind_direction_name', 'N/A')}
- Ráfagas: {weather.get('wind_gusts', 'N/A')} km/h
- Lluvia: {weather.get('precipitation', 'N/A')} mm
- Condición: {weather.get('condition', 'N/A')}

AGUA SUPERFICIAL ({sst_src}):
- Temperatura: {sst}°C
- Clorofila-a: {chl} mg/m³  (alta = más productividad = más peces)

CALIDAD DEL AGUA ({wq_src}):
- Oxígeno disuelto: {water_quality.get('dissolved_oxygen', 'N/A')} mg/L  (ideal >5)
- pH: {water_quality.get('ph', 'N/A')}  (rango sano 6.5–9)
- Salinidad: {water_quality.get('salinity', 'N/A')} PSU
- Turbidez: {water_quality.get('turbidity', 'N/A')} NTU
{_wq_interpretation(water_quality)}

{zone_ranking}

SEMÁFORO: {semaphore_color.upper()}
{get_fishing_context()}
Genera un mensaje de WhatsApp para un pescador artesanal de la Ciénaga.
Instrucciones:
1. Empieza con el semáforo y si conviene salir a faena hoy
2. Explica el clima en términos locales (brisa, viento de loma, aguacero)
3. Menciona la ZONA recomendada (🥇 del ranking) y las especies que hay ahí
4. Menciona el arte de pesca que conviene para esa zona
5. Si la clorofila es alta (>4 mg/m³), menciona que hay mancha
6. Si el oxígeno está bajo (<4.5 mg/L), avisa que los peces pueden estar raros
7. Máximo 200 palabras. Emojis con moderación (🎣🌊💨⚠️🟢🟡🔴)
NO incluyas la pregunta de feedback — esa se agrega sola.
"""
