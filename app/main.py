from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.routers.analysis_router import router as analysis_router
from app.routers.cv_router import router as cv_router
from app.routers.meta_router import router as metadata_router

# ─── App FastAPI ────────────────────────────────────────────────────────
app = FastAPI(title="CV Optimizer API", version="1.0")

# ─── CORS para pruebas locales ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],  # frontend local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Rutas API ──────────────────────────────────────────────────────────
app.include_router(cv_router, prefix="/api/cv")
app.include_router(analysis_router, prefix="/api/analysis")
app.include_router(metadata_router, prefix="/api/metadata")

# ─── Carpeta SPA / Archivos estáticos ───────────────────────────────────
web_path = Path(__file__).resolve().parent.parent / "web"
# Montamos los archivos estáticos bajo /static para acceder a JS, CSS, imágenes
app.mount("/static", StaticFiles(directory=web_path), name="static")

# ─── Ruta principal SPA ─────────────────────────────────────────────────
@app.get("/", response_class=FileResponse)
async def serve_index():
    """Devuelve index.html principal del SPA"""
    return FileResponse(web_path / "index.html")

# ─── Fallback para rutas internas del SPA ───────────────────────────────
@app.get("/{full_path:path}", response_class=FileResponse)
async def serve_spa(full_path: str):
    """Para que cualquier ruta interna desconocida devuelva index.html"""
    return FileResponse(web_path / "index.html")

# ─── Run en desarrollo:
# uvicorn app.main:app --reload


