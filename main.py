import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers.webhook import router
from config import MEDIA_DIR
from services.water_quality import refresh_cache, daily_refresh_loop

logger = logging.getLogger(__name__)

Path(MEDIA_DIR).mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Al iniciar: cargar caché de calidad del agua y arrancar loop diario
    logger.info("CienRayas iniciando — cargando datos de calidad del agua IDEAM...")
    try:
        await refresh_cache()
    except Exception as e:
        logger.warning(f"Caché inicial de calidad del agua falló: {e}")

    task = asyncio.create_task(daily_refresh_loop())
    yield
    task.cancel()


app = FastAPI(
    title="CienRayas",
    version="1.1.0",
    docs_url="/docs",
    lifespan=lifespan,
)

# Servir las imágenes de mapas generados para WhatsApp
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "bot": "CienRayas v1.1 — Ciénaga Grande"}


@app.get("/ping")
def ping():
    """UptimeRobot llama aquí cada 10 min para evitar que Render duerma el servicio."""
    return "pong"
