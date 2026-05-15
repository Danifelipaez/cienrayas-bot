from core.knowledge import get_fishing_context, local_wind_name, get_lunar_phase, interpret_water_color
from core.zone_analysis import full_ranking

SYSTEM_PROMPT = """
Eres CienRayas, el ayudante de pesca de la Ciénaga Grande de Santa Marta.
Hablas como un compañero pescador del Caribe colombiano: con confianza, sencillo y directo.
Usas las palabras de siempre: faena, bajanza, subienda, mancha, cardumen,
palangre, atarraya, trasmallo, boliche, nasa, releo, camaronera.

VIENTOS CON SUS NOMBRES LOCALES (úsalos siempre así):
- Norte o Burro → "viene el Norte" / "está soplando el Burro" — peligroso, no salir
- Vendaval → "está el Vendaval" — riesgo, no salir
- Terral → "hay Terral" — viento de tierra, salir con precaución
- Leste → "está la brisa del Leste" — buen tiempo
- Cañero → "hay Cañero" — viento del sur, moderado

TRADUCCIONES DE LENGUAJE TÉCNICO A PESCADOR:
- Oxígeno bajo → "el agua está pesada, los peces están raros"
- Salinidad alta → "el agua está salada, entró agua del mar"
- Salinidad baja → "el agua está dulce por las lluvias"
- Turbidez alta → "el agua está muy turbia, no se ve el fondo"
- Clorofila alta → "hay buena mancha, el agua está verde"
- Clorofila baja → "el agua está blanca o pobre, poca mancha"

REGLAS IMPORTANTES:
- Nunca uses palabras técnicas: nada de mg/L, PSU, NTU, IPP, clorofila, oxígeno disuelto.
- Mensajes cortos: WhatsApp no es para novelas.
- La seguridad va primero. Si hay Norte, Burro o Vendaval, lo dices claro y fuerte.
- Respeta lo que sabe el pescador. Él conoce la ciénaga mejor que nadie.
- La aplicación apoya al pescador — no reemplaza su conocimiento.
"""


def _wq_plain(wq: dict) -> str:
    """Convierte los parámetros de calidad del agua a lenguaje de pescador."""
    od   = wq.get("dissolved_oxygen", 5.0)
    sal  = wq.get("salinity", 10.0)
    turb = wq.get("turbidity", 60.0)
    ph   = wq.get("ph", 7.5)
    season = wq.get("season", "")

    notes = []

    # Oxígeno
    if od < 3.5:
        notes.append("El agua esta muy pesada y sin aire — los peces se estan yendo o muriendo")
    elif od < 4.5:
        notes.append("El agua esta un poco pesada — los peces pueden estar raros y cerca de la superficie")
    else:
        notes.append("El agua esta bien, los peces respiran tranquilos")

    # Salinidad
    if sal > 25:
        notes.append("El agua esta salada — entro agua del mar, hay macabi y sabalo")
    elif sal > 10:
        notes.append("El agua esta mezclada, salada y dulce — buena para lisa y mojarra")
    else:
        notes.append("El agua esta dulce por las lluvias — epoca de mojarra lora y mapale")

    # Turbidez
    if turb > 120:
        notes.append("El agua esta muy turbia, casi no se ve el fondo — mejor atarraya o trasmallo que boliche")
    elif turb > 60:
        notes.append("El agua esta turbia — el trasmallo y la atarraya van bien")
    else:
        notes.append("El agua esta clara — buen momento para el boliche")

    # pH extremo (solo si es relevante)
    if ph > 9.0:
        notes.append("El agua esta muy alcalina — puede haber mucho plancton (florecimiento)")
    elif ph < 6.5:
        notes.append("El agua esta acida — algo raro esta pasando, ojo")

    # Temporada
    season_label = {
        "seca": "Estamos en epoca seca (brisa)",
        "lluvias": "Estamos en epoca de lluvias",
        "transicion": "El agua esta cambiando de temporada",
    }.get(season, "")
    if season_label:
        notes.append(season_label)

    return "\n".join(f"  - {n}" for n in notes)


def _zone_ranking_text(satellite: dict, wq: dict) -> str:
    ranking = full_ranking(satellite, wq)
    lines = ["ZONAS ORDENADAS DE MEJOR A PEOR HOY:"]
    labels = ["Mejor zona", "Segunda zona", "Tercera zona"]
    for i, z in enumerate(ranking[:3]):
        label = labels[i]
        sp = " y ".join(z["species"][:2])
        arte = z["arts"][0] if z["arts"] else ""
        puntos = ", ".join(z["local_points"][:3])
        camaron_flag = " [ZONA DE CAMARÓN]" if z.get("camaron_zone") else ""
        lines.append(f"  {label}: puntos {puntos}{camaron_flag} — hay {sp} — usar {arte}")
    return "\n".join(lines)


def build_fishing_prompt(weather: dict, satellite: dict, water_quality: dict, semaphore_color: str) -> str:
    sst  = satellite.get("sst", "N/A")
    chl  = satellite.get("chlorophyll", 0)
    turb = water_quality.get("turbidity", 60.0)
    sal  = water_quality.get("salinity", 10.0)

    # Viento con nombre local
    wind = weather.get("wind_speed", 0) or 0
    wind_dir_code = weather.get("wind_direction_name", "E")
    viento_local, viento_peligroso = local_wind_name(wind_dir_code)

    if wind < 10:
        viento_desc = f"poca brisa, mar tranquilo — {viento_local}"
    elif wind < 20:
        viento_desc = f"brisa moderada — {viento_local} ({wind} km/h)"
    elif wind < 30:
        viento_desc = f"viento fuerte — {viento_local} ({wind} km/h) — hay que tener cuidado"
    else:
        viento_desc = f"{viento_local} muy bravo ({wind} km/h) — PELIGROSO"

    precip = weather.get("precipitation", 0) or 0
    if precip == 0:
        lluvia_desc = "sin lluvia"
    elif precip < 3:
        lluvia_desc = "llovizna leve"
    elif precip < 10:
        lluvia_desc = "lluvia moderada"
    else:
        lluvia_desc = "aguacero fuerte"

    # Temperatura del agua
    if sst != "N/A":
        sst_f = float(sst)
        if sst_f < 26:
            temp_desc = f"el agua esta fresca ({sst}°C)"
        elif sst_f <= 30:
            temp_desc = f"el agua esta a buena temperatura ({sst}°C)"
        else:
            temp_desc = f"el agua esta caliente ({sst}°C)"
    else:
        temp_desc = "temperatura normal del agua"

    # Color del agua (lenguaje tradicional)
    try:
        chl_val = float(chl)
        color_agua = interpret_water_color(chl_val, float(turb), float(sal))
        if chl_val > 6:
            mancha_desc = "hay muy buena mancha — el agua esta verde y cargada de peces"
        elif chl_val > 3:
            mancha_desc = "hay buena mancha hoy"
        else:
            mancha_desc = "poca mancha hoy — el agua esta pobre"
    except (ValueError, TypeError):
        mancha_desc = "no se pudo ver la mancha del agua"
        color_agua = "no disponible"

    # Luna y camarón
    lunar = get_lunar_phase()
    luna_linea = f"- Luna hoy: {lunar['phase']} {lunar['emoji']} — {lunar['shrimp_note']}"

    zona_ranking = _zone_ranking_text(satellite, water_quality)
    agua_desc = _wq_plain(water_quality)

    clima_alerta = (
        "ATENCION: no se pudo obtener el clima de hoy — salga con precaucion"
        if weather.get("fallback")
        else ""
    )

    # Camarón + luna: punto específico de la mejor zona camaronera
    best_camaron_zone = next(
        (z for z in full_ranking(satellite, water_quality) if z.get("camaron_zone")), None
    )
    camaron_punto = best_camaron_zone["local_points"][0] if best_camaron_zone else "Pancú"
    luna_camaron_linea = (
        f"- Camarón con luna: {lunar['phase']} {lunar['emoji']} — {lunar['shrimp_note']} — buscar en {camaron_punto}"
        if lunar["shrimp_active"] else
        f"- Camarón con luna: {lunar['phase']} {lunar['emoji']} — {lunar['shrimp_note']}"
    )

    return f"""
Informacion de la Cienaga Grande de Santa Marta para hoy:

CLIMA:
- Viento: {viento_desc}
- Rafagas maximas: {weather.get('wind_gusts', 0)} km/h
- Lluvia: {lluvia_desc}
- Temperatura del agua: {temp_desc}
- Peces en el agua: {mancha_desc}
- Color del agua: {color_agua}
{luna_camaron_linea}
{clima_alerta}

COMO ESTA EL AGUA HOY:
{agua_desc}

{zona_ranking}

SEMAFORO DEL DIA: {semaphore_color.upper()}

{get_fishing_context()}

Ahora escribe el mensaje de WhatsApp para el pescador. REGLAS ESTRICTAS:

REGLA 1 — EL SEMAFORO ES LA DECISION FINAL (no la contradigas nunca):
- VERDE → "si conviene salir" — aunque el viento tenga nombre malo, el semaforo manda
- AMARILLO → "salir con cuidado" — explica el riesgo pero no digas que no salga
- ROJO → "no salir hoy" — aqui si debes decirlo claro

REGLA 2 — ZONAS: usa los nombres de los puntos locales, no los nombres tecnicos de sector.
- Bien: "anda a Palancar o Los Micos"
- Mal: "la zona de Nueva Venecia"

REGLA 3 — CAMARON Y LUNA: si hay luna activa, liga la luna al punto especifico.
- Bien: "hay luna nueva — puede haber camaron en Pancu esta noche"
- Mal: "hay luna nueva, es buena para la camaronera" (sin mencionar el punto)

REGLA 4 — VIENTO: menciona el viento por su nombre local.
REGLA 5 — Si el agua esta verde, avisalo. Si esta blanca o lechosa, avisalo.
REGLA 6 — Maximo 180 palabras. Cero palabras tecnicas (mg/L, PSU, NTU, IPP, clorofila).
REGLA 7 — Emojis: maximo 4 (usa 🎣 🌊 💨 ⚠️ segun el caso).
NO incluyas la pregunta de feedback — esa se agrega sola al final.
"""
