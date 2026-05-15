"""
Análisis multivariable para determinar la zona de mayor probabilidad de pesca
en la Ciénaga Grande de Santa Marta.

Metodología: cada parámetro recibe un puntaje parcial (0–100) según su
idoneidad ecológica para la pesca, luego se pondera por su peso relativo.
El resultado es un índice de potencial pesquero (IPP) de 0 a 100 por zona.

Pesos (suman 100 %):
  Oxígeno disuelto  25 %  — crítico: sin O₂ no hay peces
  Temperatura SST   20 %  — regula metabolismo y migración
  Salinidad         20 %  — determina qué especies están presentes
  Clorofila-a       15 %  — proxy de productividad (alimento)
  Turbidez          10 %  — afecta eficacia del arte de pesca
  pH                10 %  — estrés ambiental general

Zonas definidas según sectores INVEMAR-CGSM 2025 y gradiente de salinidad.
"""
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Definición de zonas
# Cada zona tiene un rango típico de salinidad (PSU) que la caracteriza
# ecológicamente, y las especies dominantes.
# ---------------------------------------------------------------------------
@dataclass
class Zone:
    name: str
    sal_min: float        # salinidad típica mínima (PSU)
    sal_max: float        # salinidad típica máxima (PSU)
    species: list[str]    # especies dominantes
    arts: list[str]       # artes de pesca recomendadas
    local_points: list[str]  # puntos de pesca locales (saber de Adelmo)
    camaron_zone: bool = False  # zona buena para camarón con luna


ZONES: list[Zone] = [
    Zone(
        name="Boca de la Barra / Zona Marina",
        sal_min=20, sal_max=36,
        species=["macabí", "sábalo", "mapalé"],
        arts=["palangre", "trasmallo"],
        local_points=["Boquerón", "Barra Vieja", "Punta Blanca", "Punta Gruesa"],
    ),
    Zone(
        name="Nueva Venecia – Palafíticos Norte",
        sal_min=8, sal_max=22,
        species=["lisa", "mojarra rayada", "chivo cabezón"],
        arts=["atarraya lisera", "boliche", "trasmallo"],
        local_points=["Palancar", "Los Micos", "Los Medios", "Boca del Pájaro", "El Rincón de las Garzas"],
    ),
    Zone(
        name="Buenavista – Palafíticos Sur",
        sal_min=5, sal_max=18,
        species=["lisa", "mojarra lora", "jaiba azul"],
        arts=["atarraya", "nasa", "trasmallo"],
        local_points=["Las Mujeres", "La Bodega", "Rincón de Veranillo", "Caño Grande", "Palo Blanco"],
    ),
    Zone(
        name="Caño Clarín – Sector Carretera Norte",
        sal_min=2, sal_max=12,
        species=["mojarra rayada", "mapalé", "camarón"],
        arts=["atarraya camaronera", "releo", "palangre"],
        local_points=["Pancú", "Riají", "Palenque", "Boca del Caño", "Punta del Caño"],
        camaron_zone=True,
    ),
    Zone(
        name="Tasajera / Puebloviejo – Sector Carretera Sur",
        sal_min=3, sal_max=15,
        species=["lisa", "mojarra", "almeja"],
        arts=["atarraya", "buceo", "trasmallo"],
        local_points=["Tasajera", "Majahualito", "La Punta de Majahualito", "Flamenquito", "Santa Rosa"],
        camaron_zone=True,
    ),
    Zone(
        name="Suroccidente – Pivijay / Santa Rita",
        sal_min=0, sal_max=8,
        species=["mojarra lora", "mapalé", "chivo cabezón"],
        arts=["atarraya", "palangre", "nasa"],
        local_points=["El Torno", "Caimán", "Corralito", "Mahoma", "Jaguey"],
    ),
]


# ---------------------------------------------------------------------------
# Funciones de puntaje por parámetro (0–100)
# ---------------------------------------------------------------------------

def _score_od(od: float) -> float:
    """Oxígeno disuelto: 0 mg/L → 0, óptimo 7 mg/L → 100."""
    if od < 2.0:
        return 0.0
    if od < 4.0:
        return (od - 2.0) / 2.0 * 40    # 0–40
    if od <= 8.0:
        return 40 + (od - 4.0) / 4.0 * 60  # 40–100
    return 90.0  # supersaturación — leve penalización


def _score_sst(sst: float) -> float:
    """Temperatura superficial: óptimo 26–30 °C → 100."""
    if sst < 22 or sst > 35:
        return 10.0
    if sst < 26:
        return 50 + (sst - 22) / 4.0 * 30    # 50–80
    if sst <= 30:
        return 80 + (sst - 26) / 4.0 * 20    # 80–100
    return 100 - (sst - 30) / 5.0 * 40       # 100–60


def _score_chlorophyll(chl: float) -> float:
    """Clorofila: >4 mg/m³ es buena mancha; <0.5 agua pobre."""
    if chl < 0.5:
        return 10.0
    if chl < 2.0:
        return 10 + (chl - 0.5) / 1.5 * 40   # 10–50
    if chl <= 8.0:
        return 50 + (chl - 2.0) / 6.0 * 50   # 50–100
    return 85.0  # bloom excesivo — puede indicar hipoxia


def _score_turbidity(turb: float) -> float:
    """Turbidez: baja (<30 NTU) es mejor para boliche; muy alta perjudica redes."""
    if turb < 30:
        return 100.0
    if turb < 80:
        return 100 - (turb - 30) / 50.0 * 30  # 100–70
    if turb < 150:
        return 70 - (turb - 80) / 70.0 * 40   # 70–30
    return 20.0


def _score_ph(ph: float) -> float:
    """pH: rango ideal estuarino 7.0–8.5."""
    if ph < 5.5 or ph > 10:
        return 0.0
    if ph < 7.0:
        return (ph - 5.5) / 1.5 * 50    # 0–50
    if ph <= 8.5:
        return 50 + (ph - 7.0) / 1.5 * 50  # 50–100
    return 100 - (ph - 8.5) / 1.5 * 40  # 100–60


def _score_salinity_for_zone(current_sal: float, zone: Zone) -> float:
    """
    Puntaje de salinidad: cuánto se acerca la salinidad actual al rango
    óptimo de la zona. Zonas bien adaptadas a la salinidad actual = 100.
    """
    zone_mid = (zone.sal_min + zone.sal_max) / 2
    zone_width = max(zone.sal_max - zone.sal_min, 2.0)

    if zone.sal_min <= current_sal <= zone.sal_max:
        return 100.0
    distance = min(abs(current_sal - zone.sal_min), abs(current_sal - zone.sal_max))
    return max(0.0, 100 - (distance / zone_width) * 80)


# ---------------------------------------------------------------------------
# Pesos del modelo (deben sumar 1.0)
# ---------------------------------------------------------------------------
_WEIGHTS = {
    "od":          0.25,
    "sst":         0.20,
    "salinity":    0.20,
    "chlorophyll": 0.15,
    "turbidity":   0.10,
    "ph":          0.10,
}


def _zone_ipp(zone: Zone, satellite: dict, wq: dict) -> float:
    """Índice de Potencial Pesquero (IPP) de 0 a 100 para una zona."""
    od   = wq.get("dissolved_oxygen", 5.0)
    sst  = satellite.get("sst", 28.0)
    chl  = satellite.get("chlorophyll", 3.0)
    turb = wq.get("turbidity", 60.0)
    ph   = wq.get("ph", 7.5)
    sal  = wq.get("salinity", 10.0)

    scores = {
        "od":          _score_od(od),
        "sst":         _score_sst(sst),
        "salinity":    _score_salinity_for_zone(sal, zone),
        "chlorophyll": _score_chlorophyll(chl),
        "turbidity":   _score_turbidity(turb),
        "ph":          _score_ph(ph),
    }

    ipp = sum(scores[k] * _WEIGHTS[k] for k in scores)
    return round(ipp, 1)


def recommend_zone(satellite: dict, wq: dict) -> dict:
    """Devuelve la zona con el IPP más alto."""
    results = full_ranking(satellite, wq)
    return results[0]


def full_ranking(satellite: dict, wq: dict) -> list[dict]:
    """Ranking completo de zonas — útil para el mapa y el LLM."""
    results = []
    for zone in ZONES:
        score = _zone_ipp(zone, satellite, wq)
        results.append({
            "name":         zone.name,
            "score":        score,
            "species":      zone.species,
            "arts":         zone.arts,
            "local_points": zone.local_points,
            "camaron_zone": zone.camaron_zone,
        })
    return sorted(results, key=lambda z: z["score"], reverse=True)
