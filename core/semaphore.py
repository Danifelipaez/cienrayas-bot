from dataclasses import dataclass


@dataclass
class SemaphoreResult:
    color: str    # "verde" | "amarillo" | "rojo"
    emoji: str    # 🟢 | 🟡 | 🔴
    reason: str
    safe: bool    # False = no salir


def evaluate(weather: dict, satellite: dict) -> SemaphoreResult:
    if weather.get("fallback"):
        return SemaphoreResult(
            "amarillo", "🟡",
            "No se pudo obtener el clima — salga con precaución",
            True,
        )

    wind_speed = weather.get("wind_speed", 0) or 0
    wind_gusts = weather.get("wind_gusts", 0) or 0
    precipitation = weather.get("precipitation", 0) or 0
    sst = satellite.get("sst") or 28.0
    chlorophyll = satellite.get("chlorophyll") or 3.0

    # --- ROJO: no salir ---
    if wind_speed > 30 or wind_gusts > 45:
        return SemaphoreResult("rojo", "🔴", "Vientos muy fuertes — viento de loma bravo", False)
    if precipitation > 10:
        return SemaphoreResult("rojo", "🔴", "Lluvia intensa — aguacero en la ciénaga", False)
    if wind_speed > 20 and precipitation > 5:
        return SemaphoreResult("rojo", "🔴", "Tormenta posible — mucho riesgo", False)

    # --- AMARILLO: salir con cuidado ---
    yellow_reasons = []
    if wind_speed > 20:
        yellow_reasons.append("viento moderado (más de 20 km/h)")
    if precipitation > 3:
        yellow_reasons.append("llovizna o lluvia leve")
    if sst < 25 or sst > 32:
        yellow_reasons.append("temperatura del agua fuera del rango ideal")
    if chlorophyll < 1.0:
        yellow_reasons.append("poca productividad del agua")

    if yellow_reasons:
        return SemaphoreResult(
            "amarillo", "🟡",
            "Precaución: " + ", ".join(yellow_reasons),
            True
        )

    # --- VERDE: buen día ---
    bonuses = []
    if chlorophyll > 5:
        bonuses.append("hay buena mancha de peces")
    if 26 <= sst <= 30:
        bonuses.append("temperatura del agua ideal")
    if wind_speed < 10:
        bonuses.append("mar tranquilo")

    reason = "Condiciones favorables"
    if bonuses:
        reason += " — " + ", ".join(bonuses)

    return SemaphoreResult("verde", "🟢", reason, True)
