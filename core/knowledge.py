"""
Conocimiento técnico y empírico de la Ciénaga Grande de Santa Marta.
Fuente técnica: INVEMAR — Proyecto GEF7-CGSM "Cogestión pesquera" (2025).
Fuente empírica: entrevistas a pescadores artesanales de Tasajera y pueblos
palafíticos — Seminario Aluna IA 2025, Universidad del Magdalena.
"""
import math
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Puntos de monitoreo INVEMAR (Sipein — activos desde 1994)
# ---------------------------------------------------------------------------
MONITORING_POINTS = [
    "Tasajera (muelle pesquero)",
    "Mercadito",
    "Bocas de Aracataca",
    "Km 15 vía Barranquilla",
    "Ciénaga de Torno",
]


# ---------------------------------------------------------------------------
# Puntos de pesca locales — memoria territorial
# Registrados por Sr. Adelmo, pescador de Tasajera.
# Fuente: trabajo de campo Seminario Aluna IA — mayo 2026.
# ---------------------------------------------------------------------------
FISHING_POINTS_ADELMO = [
    "Boquerón", "Palancar", "Los Micos", "Los Medios", "La Punta de Chino",
    "Rincón de Chino", "La Pared de Punta de Burro", "Punta de Burro",
    "Río Frío", "Las Palomas", "López", "Guapo", "Bongo", "Boca del Pájaro",
    "Punta Blanca", "Rincón Cagao", "Troja de Aracataca", "Pancú", "La Lata",
    "Riají", "Palenque", "El Rincón de las Garzas", "Palo Blanco",
    "Las Mujeres", "La Bodega", "Rincón de Veranillo", "Caño Grande",
    "Boca del Caño", "Punta del Caño", "Los Muertos", "La Ahuyama",
    "El Chivato", "La Punta del Tambor", "Rincón del Hospitalito",
    "La Rinconá", "Caimán", "El Torno", "Barra Vieja", "Punta Gruesa",
    "Corralito", "La Punta de Corralito", "Majahualito",
    "La Punta de Majahualito", "Mahoma", "Jaguey", "La Punta de Jaguey",
    "Los Murciélagos", "Palo Quemado", "Flamenquito", "Santa Rosa",
    "Tasajera",
]


# ---------------------------------------------------------------------------
# Clasificación de vientos con nombres locales
# Fuente: entrevistas a pescadores artesanales — Seminario Aluna IA 2026.
# ---------------------------------------------------------------------------
# Mapeo dirección cardinal → (nombre local, peligroso)
VIENTOS_LOCALES: dict[str, tuple[str, bool]] = {
    "N":   ("Norte",    True),   # frentes fríos del norte — muy peligroso
    "NNE": ("Norte",    True),
    "NNO": ("Norte",    True),
    "NO":  ("Burro",    True),   # viento bruto del noroeste — malo
    "ONO": ("Burro",    True),
    "NE":  ("Terral",   False),  # viento de tierra — variable
    "ENE": ("Terral",   False),
    "E":   ("Leste",    False),  # brisa del este — favorable
    "ESE": ("Leste",    False),
    "SE":  ("Leste",    False),
    "SSE": ("Cañero",   False),  # sur-sureste — moderado
    "S":   ("Cañero",   False),
    "SSO": ("Vendaval", True),   # giro al suroeste — tempestades
    "SO":  ("Vendaval", True),
    "OSO": ("Vendaval", True),
    "O":   ("Vendaval", True),
}

# Interpretaciones de peligro por nombre local
VIENTO_PELIGRO = {
    "Norte":    "viento de loma del norte — peligroso, riesgo de tormenta",
    "Burro":    "viento burro del noroeste — bravo, no conviene salir",
    "Vendaval": "vendaval del suroeste — riesgo de marejada",
    "Terral":   "viento terral de tierra — salir con precaución",
    "Leste":    "brisa del leste — buen tiempo para la faena",
    "Cañero":   "viento cañero del sur — moderado, ojo a los cambios",
}


def local_wind_name(direction_code: str) -> tuple[str, bool]:
    """
    Devuelve (nombre_local, es_peligroso) para un código de dirección cardinal.
    Ejemplo: "N" → ("Norte", True),  "E" → ("Leste", False)
    """
    return VIENTOS_LOCALES.get(direction_code, ("brisa", False))


# ---------------------------------------------------------------------------
# Colores del agua y su interpretación pesquera
# Fuente: entrevistas — "el agua habla si uno sabe leerla"
# ---------------------------------------------------------------------------
WATER_COLOR_SIGNALS = {
    "verde":       "agua buena para la pesca — hay mancha, peces cargados",
    "blanca":      "agua mala o estancada — los peces se alejan",
    "clara_mar":   "entró agua del mar — buen momento para lisa y macabí",
    "verdin":      "cambio ambiental en curso — ojo a lo que viene",
    "oscura":      "agua baja en oxígeno — los peces están raros o se van",
}


def interpret_water_color(chlorophyll: float, turbidity: float, salinity: float) -> str:
    """
    Infiere el 'color' del agua a partir de datos satelitales/IDEAM
    y lo traduce al lenguaje de color que usan los pescadores.
    """
    if salinity > 20 and turbidity < 40:
        return WATER_COLOR_SIGNALS["clara_mar"]
    if chlorophyll > 4 and turbidity < 100:
        return WATER_COLOR_SIGNALS["verde"]
    if turbidity > 130 and chlorophyll < 1.5:
        return WATER_COLOR_SIGNALS["blanca"]
    if chlorophyll > 8:
        return WATER_COLOR_SIGNALS["verdin"]
    return WATER_COLOR_SIGNALS["verde"] if chlorophyll >= 2 else WATER_COLOR_SIGNALS["blanca"]


# ---------------------------------------------------------------------------
# Luna y camarón
# Hallazgo clave de las entrevistas: "El camarón se mueve con la luna."
# Los pescadores relacionan cuarto creciente, cuarto menguante y luna nueva
# con el desplazamiento del camarón.
# ---------------------------------------------------------------------------
def get_lunar_phase() -> dict:
    """
    Calcula la fase lunar actual y su relevancia para el camarón.
    Algoritmo basado en luna nueva de referencia: 2000-01-06 18:14 UTC.
    """
    now = datetime.now(timezone.utc)
    ref_new_moon = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
    LUNAR_CYCLE = 29.53059  # días

    elapsed_days = (now - ref_new_moon).total_seconds() / 86400
    day = elapsed_days % LUNAR_CYCLE

    if day < 2.0 or day >= 27.5:
        phase, emoji = "luna nueva", "🌑"
        shrimp_note = "el camarón se mueve esta noche — buena para la camaronera"
        shrimp_active = True
    elif day < 8.5:
        phase, emoji = "cuarto creciente", "🌒"
        shrimp_note = "el camarón empieza a moverse — ojo al releo"
        shrimp_active = True
    elif day < 16.5:
        phase, emoji = "luna llena", "🌕"
        shrimp_note = "el camarón está muy activo — noche clave para la camaronera"
        shrimp_active = True
    elif day < 23.0:
        phase, emoji = "cuarto menguante", "🌘"
        shrimp_note = "el camarón está tranquilo — menos actividad de noche"
        shrimp_active = False
    else:
        phase, emoji = "luna menguante", "🌑"
        shrimp_note = "el camarón está quieto — espere la luna nueva"
        shrimp_active = False

    return {
        "phase":          phase,
        "emoji":          emoji,
        "shrimp_note":    shrimp_note,
        "shrimp_active":  shrimp_active,
        "cycle_day":      round(day, 1),
    }


# ---------------------------------------------------------------------------
# Señales naturales que usan los pescadores
# Fuente: saber tradicional documentado en entrevistas — mayo 2026.
# ---------------------------------------------------------------------------
TRADITIONAL_SIGNALS = {
    # Agua
    "agua_verde":          "Agua buena — hay mancha y peces cargados",
    "agua_blanca":         "Agua mala o estancada — peces se alejan",
    "agua_clara_mar":      "Salinidad alta, entró agua marina — buena para lisa y macabí",
    "agua_movida":         "Movimiento superficial del agua indica cardumen activo",
    "agua_vibra":          "Vibración del agua — comportamiento de cardumen",
    # Peces
    "peces_saltando":      "Macabí, sábalo o lisa activos — usar atarraya grande o red de enmalle",
    "peces_respirando":    "Peces en superficie respirando — oxígeno bajo en el fondo, atarraya cerca",
    "peces_volando":       "Cardumen huyendo de depredador — boliche rápido",
    # Aves
    "aves_sobrevolando":   "Cardumen cerca de superficie — boliche o atarraya robalera",
    "aves_anuncian_brisa": "Aves volando bajo y nervioso — brisa fuerte viene",
    # Viento
    "norte_fuerte":        "Viento de loma del norte — señal de bajanza de lisa (nov-feb) pero peligroso",
    "leste_suave":         "Brisa del leste — buen tiempo, favorece la faena",
    "vendaval":            "Vendaval del sur-oeste — no salir, riesgo de tormenta",
    "burro":               "Viento burro del noroeste — no salir, muy peligroso",
    # Luna
    "luna_camaron":        "El camarón se mueve con la luna — activo en luna nueva, creciente y llena",
    # Sedimentación
    "zona_seca":           "Zona que antes era navegable ahora es baja — cambió el fondo por sedimento",
}


# ---------------------------------------------------------------------------
# Cambio climático — contexto documentado en entrevistas
# ---------------------------------------------------------------------------
CLIMATE_CHANGE_CONTEXT = {
    "descripcion": (
        "Con el cambio climático las temporadas tradicionales han cambiado. "
        "Antes los meses de cada especie eran claros; ahora los peces aparecen "
        "fuera de temporada y las lluvias son irregulares."
    ),
    "especies_estables": ["camarón", "lisa"],
    "nota": (
        "Camarón y lisa son las especies que aún mantienen más estabilidad. "
        "Las demás pueden aparecer fuera de temporada."
    ),
}


# ---------------------------------------------------------------------------
# Riesgos identificados
# ---------------------------------------------------------------------------
RIESGOS_AMBIENTALES = [
    "mal clima", "brisa fuerte", "frentes fríos", "sedimentación",
    "agua caliente", "contaminación", "poca profundidad",
]

RIESGOS_SOCIALES = [
    "conflictos entre pescadores", "sobreexplotación",
    "competencia por puntos", "robos y piratería en zonas apartadas",
]


# ---------------------------------------------------------------------------
# Especies principales y su comportamiento estacional
# Fuente: 30 años de monitoreo Sipein / INVEMAR
# ---------------------------------------------------------------------------
SPECIES = {
    "lisa": {
        "nombre_cientifico": "Mugil incilis",
        "temporada_alta": [11, 12, 1, 2],   # nov-feb: bajanza/brisa fuerte
        "temporada_baja": [5, 6, 7, 8],
        "artes": ["atarraya lisera", "trasmallo", "boliche"],
        "talla_minima_cm": 24,
        "nota": "Especie más capturada. Baja a la mar en noviembre con la brisa. Mantiene ciclo estable.",
    },
    "mojarra_rayada": {
        "nombre_cientifico": "Eugerres plumieri",
        "temporada_alta": [3, 4, 5, 9, 10],
        "temporada_baja": [12, 1, 2],
        "artes": ["atarraya mojarrera", "chinchorro"],
        "talla_minima_cm": 22,
        "nota": "Abunda más en aguas con buena salinidad.",
    },
    "mojarra_lora": {
        "nombre_cientifico": "Oreochromis niloticus",
        "temporada_alta": [4, 5, 6, 7, 8],   # aguas dulces / lluvias
        "temporada_baja": [12, 1, 2],
        "artes": ["chinchorra", "atarraya mojarrera"],
        "talla_minima_cm": 22,
        "nota": "Especie introducida. Domina en épocas de lluvia y aguas dulces.",
    },
    "mapale": {
        "nombre_cientifico": "Cathorops mapale",
        "temporada_alta": [1, 2, 3, 10, 11, 12],
        "temporada_baja": [6, 7, 8],
        "artes": ["palangre", "atarraya"],
        "talla_minima_cm": 17,
        "nota": "Fondo de la ciénaga. El palangre va bien cerca del manglar.",
    },
    "chivo_cabezon": {
        "nombre_cientifico": "Ariopsis canteri",
        "temporada_alta": [10, 11, 12, 1, 2],
        "temporada_baja": [5, 6, 7],
        "artes": ["palangre"],
        "talla_minima_cm": 30,
        "nota": "Sale con las primeras brisas. Palangre en el fondo.",
    },
    "macabi": {
        "nombre_cientifico": "Elops smithi",
        "temporada_alta": [3, 4, 5],
        "temporada_baja": [9, 10],
        "artes": ["atarraya robalera", "red de enmalle"],
        "talla_minima_cm": 30,
        "nota": "Especie fuerte, salta. Se detecta por movimiento en superficie.",
    },
    "sabalo": {
        "nombre_cientifico": "Megalops atlanticus",
        "temporada_alta": [1, 2, 3, 4],
        "temporada_baja": [8, 9],
        "artes": ["red de enmalle", "boliche"],
        "talla_minima_cm": 40,
        "nota": "Especie grande, salta. Indica aguas bien oxigenadas.",
    },
    "jaiba_azul": {
        "nombre_cientifico": "Callinectes sapidus",
        "temporada_alta": [3, 4, 5, 6],
        "temporada_baja": [11, 12],
        "artes": ["nasas"],
        "talla_minima_cm": 9,
        "nota": "Nasa en zonas de fondo blando. Más activa de noche.",
    },
    "camaron": {
        "nombre_cientifico": "Penaeus schmitti / P. notialis",
        "temporada_alta": [9, 10, 11],
        "temporada_baja": [3, 4, 5],
        "artes": ["red camaronera / releo"],
        "talla_minima_cm": 7,
        "nota": (
            "Especie de ciclo estable. Se mueve con la luna — activo en "
            "luna nueva, creciente y llena. Máx 4 redes/faena."
        ),
    },
}


# ---------------------------------------------------------------------------
# Zonas de pesca conocidas (sectores INVEMAR + puntos locales de Adelmo)
# ---------------------------------------------------------------------------
FISHING_ZONES = [
    "Boca del Mar (zona norte, alta salinidad — lisa y mapalé)",
    "Nueva Venecia (zona central palafítica — mojarra rayada y jaiba)",
    "Buenavista (zona centro-occidental palafítica — mojarra lora en lluvias)",
    "Bocas de Aracataca (zona sur — aguas dulces, mojarra lora)",
    "Zona del manglar (fondo — palangre para mapalé y chivo cabezón)",
]


# ---------------------------------------------------------------------------
# Función principal: contexto de conocimiento para el prompt
# ---------------------------------------------------------------------------
def get_fishing_context() -> str:
    """
    Genera un bloque de contexto para el LLM combinando:
    - Datos técnicos INVEMAR (especies, artes, tallas)
    - Saber tradicional de pescadores (señales, vientos locales, luna)
    - Contexto de cambio climático documentado en entrevistas
    """
    month = datetime.now().month
    lunar = get_lunar_phase()

    en_temporada = [
        name for name, data in SPECIES.items()
        if month in data["temporada_alta"]
    ]
    nombres = {
        "lisa": "lisa", "mojarra_rayada": "mojarra rayada",
        "mojarra_lora": "mojarra lora", "mapale": "mapalé",
        "chivo_cabezon": "chivo cabezón", "macabi": "macabí",
        "sabalo": "sábalo", "jaiba_azul": "jaiba azul", "camaron": "camarón",
    }
    especies_hoy = [nombres.get(e, e) for e in en_temporada]

    artes_relevantes = list({
        arte
        for name in en_temporada
        for arte in SPECIES[name]["artes"]
    })

    camaron_en_temporada = "camaron" in en_temporada
    luna_nota = ""
    if camaron_en_temporada:
        luna_nota = f"\n- Luna ({lunar['phase']} {lunar['emoji']}): {lunar['shrimp_note']}"

    bloque = f"""
CONOCIMIENTO PESQUERO DE LA CIÉNAGA GRANDE (INVEMAR + saber pescador):
- Especies en temporada este mes: {', '.join(especies_hoy) if especies_hoy else 'consultar con pescadores locales'}
- Artes recomendados: {', '.join(artes_relevantes[:4]) if artes_relevantes else 'según especie objetivo'}
- Tallas mínimas legales: lisa≥24cm, mojarra≥22cm, mapalé≥17cm, chivo cabezón≥30cm, jaiba≥9cm caparazón{luna_nota}

SEÑALES DEL AGUA Y LA NATURALEZA (saber tradicional):
- Agua verde: hay mancha, peces cargados — buen día
- Agua blanca o lechosa: agua mala o estancada — peces se alejan
- Agua clara como de mar: entró agua salada — buena para lisa y macabí
- Aves sobrevolando: cardumen en superficie — boliche o atarraya robalera
- Peces saltando o volando: macabí o sábalo activos — usar red de enmalle
- Peces respirando en superficie: oxígeno bajo en el fondo — ojo

VIENTOS CON SUS NOMBRES:
- Norte o Burro: peligroso — no salir
- Vendaval: riesgo de tormenta — no salir
- Terral: viento de tierra — salir con precaución
- Leste o brisa fresca: buen tiempo — favorece la faena

CAMBIO CLIMÁTICO:
- Las temporadas ya no son las de antes — las especies aparecen fuera de ciclo
- El camarón y la lisa siguen siendo las más estables
- La sedimentación ha cambiado el fondo — hay zonas antes navegables ahora secas
"""
    return bloque
