"""Point d'entrée FastAPI de FUTURA."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app import models  # noqa: F401  (enregistre les tables auprès de Base)
from app.seed import seed_users
from app.routers import parcours, users, wellbeing

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
LABOS_DIR = os.path.join(BASE_DIR, "labos")

Base.metadata.create_all(bind=engine)
seed_users()

app = FastAPI(
    title="FUTURA API",
    description="Backend pour la plateforme de mentorat Maryse & Laeticia",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parcours.router)
app.include_router(users.router)
app.include_router(wellbeing.router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/labos", StaticFiles(directory=LABOS_DIR), name="labos")


@app.get("/", include_in_schema=False)
def read_root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    """Le service worker est servi à la racine pour contrôler toute l'app."""
    return FileResponse(
        os.path.join(STATIC_DIR, "sw.js"), media_type="application/javascript"
    )


@app.get("/health", include_in_schema=False)
def health_check():
    return {"status": "ok"}
