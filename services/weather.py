import asyncio
import logging
import httpx
from config import CIENAGA_LAT, CIENAGA_LON

logger = logging.getLogger(__name__)

WTTR_URL = f"https://wttr.in/{CIENAGA_LAT},{CIENAGA_LON}?format=j1"

_WIND_DIRS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO",
]

_WEATHER_FALLBACK = {
    "temperature": None,
    "wind_speed": 25,
    "wind_direction": 45,
    "wind_direction_name": "NE",
    "wind_gusts": 30,
    "precipitation": 0.0,
    "condition": "Sin datos de clima",
    "weather_code": -1,
    "fallback": True,
}


from datetime import datetime, timezone, timedelta

_weather_cache: dict | None = None
_weather_cache_ts: datetime | None = None
_CACHE_TTL_MINUTES = 10


def _direction_name(degrees: float) -> str:
    idx = round(degrees / 22.5) % 16
    return _WIND_DIRS[idx]


async def get_weather() -> dict:
    global _weather_cache, _weather_cache_ts

    if _weather_cache is not None and _weather_cache_ts is not None:
        age = datetime.now(timezone.utc) - _weather_cache_ts
        if age.total_seconds() < _CACHE_TTL_MINUTES * 60:
            logger.info("Retornando clima desde caché en memoria")
            return _weather_cache

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(WTTR_URL)
                logger.info(f"wttr.in status: {response.status_code}")
                response.raise_for_status()
                data = response.json()

            current = data["current_condition"][0]
            wind_speed = int(current.get("windspeedKmph", 0))
            wind_dir = int(current.get("winddirDegree", 0))
            precip = float(current.get("precipMM", 0))
            condition = current.get("weatherDesc", [{}])[0].get("value", "Desconocido")

            result = {
                "temperature": float(current.get("temp_C", 0)),
                "wind_speed": wind_speed,
                "wind_direction": wind_dir,
                "wind_direction_name": _direction_name(wind_dir),
                "wind_gusts": round(wind_speed * 1.4),  # wttr.in no da ráfagas — estimado
                "precipitation": round(precip, 1),
                "condition": condition,
                "weather_code": int(current.get("weatherCode", 0)),
            }

            _weather_cache = result
            _weather_cache_ts = datetime.now(timezone.utc)
            return result
        except Exception as e:
            logger.warning(f"wttr.in intento {attempt + 1} falló: {e}")
            if attempt == 0:
                await asyncio.sleep(3)

    logger.error("wttr.in falló 2 veces — usando fallback AMARILLO")
    # No guardamos el fallback en caché para intentar de nuevo la próxima vez
    return _WEATHER_FALLBACK

