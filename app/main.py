"""
app/main.py
CV Optimizer API
uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.routers.cv_router import router as cv_router

app = FastAPI(
    title="CV Optimizer API",
    description="Analiza ofertas, calcula ATS score y genera CVs optimizados",
    version="1.0.0",
)

# CORS (para frontend web)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers

app.include_router(cv_router, prefix="/api")

# Global error handler


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


app.mount("/web", StaticFiles(directory="web"), name="web")


@app.get("/")
def home():
    return FileResponse("web/index.html")