"""
api/main.py — FastAPI Backend
CV Optimizer API: análisis de ofertas, scoring ATS, generación de PDF

Instalar: pip install fastapi uvicorn fpdf2 python-multipart
Ejecutar:  uvicorn api.main:app --reload --port 8000
"""

from app.routers import cv_router

# Permite importar desde la raíz del proyecto

try:
    from fastapi import FastAPI, HTTPException, Request

    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles

except ImportError:
    raise ImportError("Instala FastAPI: pip install fastapi uvicorn python-multipart")


# App

app = FastAPI(
    title="CV Optimizer API",
    description="Analiza ofertas, calcula ATS score y genera CVs optimizados",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(cv_router.router)


