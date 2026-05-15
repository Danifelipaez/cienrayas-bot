from dataclasses import dataclass
from core.knowledge import local_wind_name, VIENTO_PELIGRO


@dataclass
class SemaphoreResult:
    color: str    # "verde" | "amarillo" | "rojo"
    emoji: str    # 🟢 | 🟡 | 🔴
    reason: str
    safe: bool    # False = no salir


def evaluate(weather: dict, satellite: dict, water_quality: dict) -> SemaphoreResult:
    if weather.get("fallback"):
        return SemaphoreResult(
            "amarillo", "🟡",
            "No se pudo obtener el clima — salga con precaución",
            True,
        )

    wind_speed    = weather.get("wind_speed", 0) or 0
    wind_gusts    = weather.get("wind_gusts", 0) or 0
    precipitation = weather.get("precipitation", 0) or 0
    wind_dir_code = weather.get("wind_direction_name", "E")
    sst           = satellite.get("sst") or 28.0
    chlorophyll   = satellite.get("chlorophyll") or 3.0

    od            = water_quality.get("dissolved_oxygen") or 5.0
    ph            = water_quality.get("ph") or 7.5
    salinity      = water_quality.get("salinity") or 10.0
    turbidity     = water_quality.get("turbidity") or 60.0

    viento_local, viento_peligroso = local_wind_name(wind_dir_code)
    viento_desc_local = VIENTO_PELIGRO.get(viento_local, viento_local)

    # --- ROJO: no salir ---
    if wind_speed > 30 or wind_gusts > 45:
        return SemaphoreResult("rojo", "🔴", f"Vientos muy fuertes — {viento_desc_local}", False)
    # Norte o Burro con viento fuerte: frentes fríos, riesgo alto en la ciénaga
    if viento_peligroso and wind_speed > 25:
        return SemaphoreResult("rojo", "🔴", f"{viento_local} bravo — {viento_desc_local}", False)
    if precipitation > 10:
        return SemaphoreResult("rojo", "🔴", "Lluvia intensa — aguacero en la ciénaga", False)
    if wind_speed > 20 and precipitation > 5:
        return SemaphoreResult("rojo", "🔴", "Tormenta posible — mucho riesgo", False)
    # Hipoxia crítica: los peces mueren o huyen, pesca nula
    if od < 3.0:
        return SemaphoreResult("rojo", "🔴", "Oxígeno muy bajo en el agua — riesgo de mortandad de peces", False)

    # --- AMARILLO: salir con cuidado ---
    yellow_reasons = []
    # Viento peligroso local aunque no supere el umbral de km/h
    if viento_peligroso and wind_speed > 15:
        yellow_reasons.append(f"{viento_local} (viento malo) — {viento_desc_local}")
    if wind_speed > 20:
        yellow_reasons.append("viento moderado (más de 20 km/h)")
    if precipitation > 3:
        yellow_reasons.append("llovizna o lluvia leve")
    if sst < 25 or sst > 32:
        yellow_reasons.append("temperatura del agua fuera del rango ideal")
    if chlorophyll < 1.0:
        yellow_reasons.append("poca productividad del agua")
    # Estrés por oxígeno: peces agrupados en superficie, difíciles de capturar
    if 3.0 <= od < 4.5:
        yellow_reasons.append(f"oxígeno disuelto bajo ({od} mg/L)")
    # pH fuera de rango estuarino normal
    if ph < 6.5:
        yellow_reasons.append(f"pH ácido ({ph}) — acidificación del agua")
    if ph > 9.0:
        yellow_reasons.append(f"pH muy alto ({ph}) — posible bloom de algas")
    # Hipersalinidad: afecta lisas, mojarras y camarones estuarinos
    if salinity > 32:
        yellow_reasons.append(f"salinidad alta ({salinity:.0f} PSU) — especies estuarinas bajo estrés")
    # Turbidez extrema: afecta boliche y trasmallo, reduce visibilidad
    if turbidity > 120:
        yellow_reasons.append(f"agua muy turbia ({turbidity:.0f} NTU) — dificulta boliche y redes")

    if yellow_reasons:
        return SemaphoreResult(
            "amarillo", "🟡",
            "Precaución: " + ", ".join(yellow_reasons),
            True
        )

    # --- VERDE: buen día ---
    from core.knowledge import get_lunar_phase
    lunar = get_lunar_phase()

    bonuses = []
    if chlorophyll > 5:
        bonuses.append("hay buena mancha de peces")
    if 26 <= sst <= 30:
        bonuses.append("temperatura del agua ideal")
    if wind_speed < 10:
        bonuses.append(f"mar tranquilo — {viento_local.lower()}")
    if od >= 6.0:
        bonuses.append("agua bien oxigenada")
    if salinity < 10 and water_quality.get("season") == "lluvias":
        bonuses.append("agua dulce — buena para lisa y mojarra")
    if lunar["shrimp_active"]:
        bonuses.append(f"{lunar['phase']} {lunar['emoji']} — {lunar['shrimp_note']}")

    reason = "Condiciones favorables"
    if bonuses:
        reason += " — " + ", ".join(bonuses)

    return SemaphoreResult("verde", "🟢", reason, True)
