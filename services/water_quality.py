"""
Calidad del agua de la Ciénaga Grande de Santa Marta.

Estrategia de datos (en orden de prioridad):
  1. Caché en memoria — válido 24 h (actualización diaria automática)
  2. Estaciones IDEAM DHIME en tiempo real
  3. Valores estacionales calibrados para la CGSM (fallback permanente)

Los parámetros monitoreados son: oxígeno disuelto (mg/L), pH,
salinidad (PSU) y turbidez (NTU).
"""
import httpx
import logging
import asyncio
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Caché en memoria — se actualiza diariamente via tarea de fondo en main.py
# ---------------------------------------------------------------------------
_cache: dict | None = None
_cache_ts: datetime | None = None
_CACHE_TTL_HOURS = 24       # refrescar cada 24 horas

# ---------------------------------------------------------------------------
# Estaciones IDEAM en o cerca de la CGSM
# Fuente: catálogo IDEAM DHIME — Red de Calidad Hídrica
# ---------------------------------------------------------------------------
_IDEAM_STATIONS = [
    {"id": "29037010", "name": "Caño Clarín"},
    {"id": "29037020", "name": "Boca de la Barra"},
    {"id": "29030050", "name": "Río Fundación – desembocadura"},
]

_DHIME_BASE = "https://dhime.ideam.gov.co/ords/DescargarArchivo"
_DATOS_BASE = "https://www.datos.gov.co/resource"

# ---------------------------------------------------------------------------
# Valores estacionales calibrados para la CGSM
# Basado en: monitoreos IDEAM 2015-2023, INVEMAR GEF7-CGSM 2025,
#            y Perdomo et al. sobre gradientes de salinidad estuarina.
#
# Mes → (OD mg/L, pH, salinidad PSU, turbidez NTU, temporada)
# ---------------------------------------------------------------------------
_SEASONAL: dict[int, tuple[float, float, float, float, str]] = {
    1:  (5.0, 8.2, 22.0, 35,  "seca"),
    2:  (4.8, 8.3, 26.0, 28,  "seca"),
    3:  (4.5, 8.4, 28.0, 25,  "seca"),        # pico sequía
    4:  (4.6, 8.3, 25.0, 30,  "seca"),
    5:  (5.5, 7.9, 12.0, 55,  "transición"),  # inicio lluvias
    6:  (6.0, 7.4,  5.0, 80,  "lluvias"),
    7:  (6.2, 7.3,  3.0, 90,  "lluvias"),     # veranillo del Caribe
    8:  (6.0, 7.3,  4.0, 95,  "lluvias"),
    9:  (6.3, 7.2,  3.0, 105, "lluvias"),
    10: (6.5, 7.2,  3.0, 115, "lluvias"),     # pico de lluvias
    11: (5.8, 7.6,  8.0, 70,  "transición"),
    12: (5.2, 8.0, 15.0, 45,  "seca"),
}


def _seasonal_values(month: int) -> dict:
    od, ph, sal, turb, season = _SEASONAL[month]
    return {
        "dissolved_oxygen": od,
        "ph": ph,
        "salinity": sal,
        "turbidity": turb,
        "season": season,
        "source": "referencia estacional IDEAM-CGSM",
        "fallback": True,
    }


async def _try_ideam_dhime(station_id: str) -> dict | None:
    """
    Intenta obtener el último registro de calidad de agua de una estación
    IDEAM vía DHIME. Devuelve None si falla o no hay datos recientes.
    """
    today = datetime.now(timezone.utc)
    since = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    until = today.strftime("%Y-%m-%d")

    url = (
        f"{_DHIME_BASE}/p_descarga_json"
        f"?p_cod_estacion={station_id}"
        f"&p_tipo_serie=CA"   # CA = Calidad de Agua
        f"&p_desde={since}&p_hasta={until}"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
        if r.status_code != 200:
            return None
        data = r.json()
        if not data or not isinstance(data, list):
            return None

        # Extraer último registro con todos los campos
        last = data[-1]
        od   = float(last.get("oxigeno_disuelto") or last.get("od") or 0)
        ph   = float(last.get("ph") or 0)
        sal  = float(last.get("salinidad") or 0)
        turb = float(last.get("turbidez") or 0)

        if od <= 0 and ph <= 0:
            return None

        return {
            "dissolved_oxygen": round(od, 1),
            "ph": round(ph, 1),
            "salinity": round(sal, 1),
            "turbidity": round(turb, 0),
            "season": _season_label(datetime.now().month),
            "source": f"IDEAM DHIME – {station_id}",
            "fallback": False,
        }
    except Exception as e:
        logger.debug(f"IDEAM DHIME {station_id} no disponible: {e}")
        return None


def _season_label(month: int) -> str:
    _, _, _, _, season = _SEASONAL[month]
    return season


async def _fetch_from_ideam() -> dict | None:
    """Intenta todas las estaciones IDEAM; devuelve el primer resultado válido."""
    for station in _IDEAM_STATIONS:
        result = await _try_ideam_dhime(station["id"])
        if result is not None:
            logger.info(f"Calidad agua IDEAM ok — estación {station['name']}")
            return result
    return None


async def refresh_cache() -> dict:
    """
    Fuerza una actualización del caché de calidad del agua.
    Llamado al inicio y cada 24 h por la tarea de fondo en main.py.
    """
    global _cache, _cache_ts

    fresh = await _fetch_from_ideam()
    if fresh is None:
        month = datetime.now().month
        fresh = _seasonal_values(month)
        logger.info(f"Calidad agua — referencia estacional mes {month}")
    else:
        fresh["fallback"] = False

    _cache = fresh
    _cache_ts = datetime.now(timezone.utc)
    return _cache


async def get_water_quality() -> dict:
    """
    Devuelve los parámetros de calidad del agua de la CGSM.
    Usa el caché si es válido (<24 h); si no, refresca en el momento.
    """
    global _cache, _cache_ts

    if _cache is not None and _cache_ts is not None:
        age = datetime.now(timezone.utc) - _cache_ts
        if age.total_seconds() < _CACHE_TTL_HOURS * 3600:
            return _cache

    return await refresh_cache()


async def daily_refresh_loop():
    """
    Tarea de fondo: actualiza el caché de calidad del agua cada 24 h.
    Se inicia desde main.py en el evento de startup de FastAPI.
    """
    while True:
        await asyncio.sleep(_CACHE_TTL_HOURS * 3600)
        logger.info("Actualizando caché de calidad del agua IDEAM...")
        try:
            await refresh_cache()
        except Exception as e:
            logger.error(f"Error en actualización diaria IDEAM: {e}")
