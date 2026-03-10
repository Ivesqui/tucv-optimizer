# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.routers.cv_router import router as cv_router  # tu cv_router.py
import inspect
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

# ─── Carpeta SPA / Archivos estáticos ───────────────────────────────────
web_path = Path(__file__).resolve().parent.parent / "web"
app.mount("/web", StaticFiles(directory=web_path), name="web")

# ─── Ruta principal SPA ─────────────────────────────────────────────────
@app.get("/", response_class=FileResponse)
async def serve_index():
    """Devuelve index.html principal del SPA"""
    return FileResponse(web_path / "index.html")

# ─── Fallback para rutas internas del SPA ───────────────────────────────
@app.get("/{full_path:path}", response_class=FileResponse)
async def serve_spa(full_path: str):
    """
    Para que cualquier ruta interna desconocida del navegador
    devuelva index.html y el SPA maneje el routing.
    """
    return FileResponse(web_path / "index.html")
"""
print("\n--- ROUTES LOADED ---")
for route in app.routes:
    try:
        print(route.path)
    except:
        pass
"""
# ─── Run en desarrollo:
# uvicorn app.main:app --reload


