"""
Obtiene temperatura superficial del agua (SST) y clorofila-a desde NASA ERDDAP.
Ambos datasets son públicos, sin autenticación.
  SST   → jplMURSST41    (NASA MUR, resolución 0.01°, diario)
  Chl-a → erdMH1chla8day (MODIS Aqua, compuesto 8 días)
"""
import httpx
from datetime import datetime, timedelta, timezone
from config import LAT_MIN, LAT_MAX, LON_MIN, LON_MAX

ERDDAP = "https://coastwatch.pfeg.noaa.gov/erddap/griddap"

# SST típica mensual de la Ciénaga Grande (fallback sin internet)
_SST_SEASONAL = {
    1: 26.5, 2: 26.0, 3: 26.5, 4: 27.5, 5: 28.5, 6: 29.0,
    7: 28.5, 8: 28.0, 9: 28.5, 10: 29.0, 11: 28.5, 12: 27.5,
}


async def _erddap_average(dataset: str, variable: str, time_str: str) -> float | None:
    lat0, lat1 = LAT_MIN + 0.15, LAT_MAX - 0.15
    lon0, lon1 = LON_MIN + 0.15, LON_MAX - 0.15
    url = (
        f"{ERDDAP}/{dataset}.json"
        f"?{variable}[({time_str})]"
        f"[({lat0:.2f}):({lat1:.2f})]"
        f"[({lon0:.2f}):({lon1:.2f})]"
    )
    async with httpx.AsyncClient(timeout=25) as client:
        r = await client.get(url)
        r.raise_for_status()
        rows = r.json()["table"]["rows"]

    values = [row[3] for row in rows if row[3] is not None and 0 < row[3] < 1000]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


async def get_sst() -> tuple[float, str]:
    """Devuelve (sst_celsius, fuente)."""
    # MUR SST tiene ~2 días de latencia
    time_str = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%dT09:00:00Z")
    try:
        sst = await _erddap_average("jplMURSST41", "analysed_sst", time_str)
        if sst is not None and 15 < sst < 40:
            return sst, "NASA MUR SST"
    except Exception:
        pass

    # Fallback estacional
    month = datetime.now().month
    return _SST_SEASONAL.get(month, 28.0), "valor histórico estacional"


async def get_chlorophyll() -> tuple[float, str]:
    """Devuelve (chl_mg_m3, fuente). Usa compuesto de 8 días para mejor cobertura nubosa."""
    time_str = (datetime.now(timezone.utc) - timedelta(days=4)).strftime("%Y-%m-%dT00:00:00Z")
    try:
        chl = await _erddap_average("erdMH1chla8day", "chlorophyll", time_str)
        if chl is not None and 0 < chl < 100:
            return chl, "NASA MODIS Aqua"
    except Exception:
        pass

    return 4.5, "valor histórico estacional"


_satellite_cache: dict | None = None
_satellite_cache_ts: datetime | None = None
_CACHE_TTL_HOURS = 6


async def get_satellite_data() -> dict:
    global _satellite_cache, _satellite_cache_ts

    if _satellite_cache is not None and _satellite_cache_ts is not None:
        age = datetime.now(timezone.utc) - _satellite_cache_ts
        if age.total_seconds() < _CACHE_TTL_HOURS * 3600:
            return _satellite_cache

    # Ejecutar en paralelo — no hay dependencia entre SST y clorofila
    import asyncio
    (sst, sst_src), (chl, chl_src) = await asyncio.gather(get_sst(), get_chlorophyll())
    result = {
        "sst": sst,
        "sst_source": sst_src,
        "chlorophyll": chl,
        "chlorophyll_source": chl_src,
    }

    _satellite_cache = result
    _satellite_cache_ts = datetime.now(timezone.utc)
    return result

