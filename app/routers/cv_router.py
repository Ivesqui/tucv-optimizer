from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.dependencies import get_cv_service
from app.services.cv_service import CVService
from app.schemas.cv_schema import (
    AnalyzeOfferRequest,
    GenerateCVRequest,
    BulletQualityRequest,
)

router = APIRouter(prefix="/cv", tags=["CV"])


@router.get("/", response_class=HTMLResponse)
async def root():
    """Sirve la UI."""
    ui_path = Path(__file__).resolve().parents[2] / "web" / "index.html"

    if ui_path.exists():
        return HTMLResponse(ui_path.read_text(encoding="utf-8"))

    return HTMLResponse(
        "<h1>CV Optimizer API ✅</h1><p>Ver /docs para la API.</p>"
    )


@router.post("/analyze-offer")
async def analyze_offer(
    req: AnalyzeOfferRequest,
    service: CVService = Depends(get_cv_service),
):
    return service.analyze_offer(req)


@router.post("/generate-cv")
async def generate_cv(
    req: GenerateCVRequest,
    service: CVService = Depends(get_cv_service),
):
    return service.generate_cv(req)


@router.post("/analyze-bullets")
async def analyze_bullets(
    req: BulletQualityRequest,
    service: CVService = Depends(get_cv_service),
):
    return service.analyze_bullets(req)


@router.get("/export-json/{filename}")
async def export_json(
    filename: str,
    service: CVService = Depends(get_cv_service),
):
    return service.export_json(filename)


@router.get("/linkedin-autofill")
async def linkedin_autofill(
    cv_json: str,
    service: CVService = Depends(get_cv_service),
):
    return service.linkedin_autofill(cv_json)