from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers.webhook import router
from config import MEDIA_DIR

Path(MEDIA_DIR).mkdir(exist_ok=True)

app = FastAPI(title="CienRayas", version="1.0.0", docs_url="/docs")

# Servir las imágenes de mapas generados para WhatsApp
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "bot": "CienRayas v1.0 — Ciénaga Grande"}


@app.get("/ping")
def ping():
    """UptimeRobot llama aquí cada 10 min para evitar que Render duerma el servicio."""
    return "pong"
