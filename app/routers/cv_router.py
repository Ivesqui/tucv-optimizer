print(">>> CV ROUTER FILE:", __file__)
# cv_router.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from app.schemas.cv_schema import AnalyzeOfferRequest, GenerateCVRequest, BulletQualityRequest
from app.infrastructure.exporters.pdf_generator import ATSPDFGenerator
from app.services.cv_service import CVService
from app.dependencies import get_cv_service

router = APIRouter(tags=["CV"])

# ───────────────────────────────
# Endpoints
# ───────────────────────────────
@router.post("/analyze-offer")
async def analyze_offer(req: AnalyzeOfferRequest, service: CVService = Depends(get_cv_service)):
    return service.analyze_offer(req)

@router.post("/generate-cv")
async def generate_cv(req: GenerateCVRequest, service: CVService = Depends(get_cv_service)):
    return service.generate_cv(req)

@router.post("/analyze-bullets")
async def analyze_bullets(req: BulletQualityRequest, service: CVService = Depends(get_cv_service)):
    return service.analyze_bullets(req)

@router.get("/export-json/{filename}")
async def export_json(filename: str, service: CVService = Depends(get_cv_service)):
    return service.export_json(filename)

@router.get("/export-pdf/{filename}")
async def export_pdf(filename: str, service: CVService = Depends(get_cv_service)):
    """
    Genera PDF desde un CV guardado en OUTPUT_DIR
    """
    # Carga el CV desde JSON
    cv_profile = service.load_cv_from_file(filename)
    if not cv_profile:
        raise HTTPException(404, "CV no encontrado")

    pdf_bytes = ATSPDFGenerator(cv_profile).generate()
    buffer = BytesIO(pdf_bytes)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
    )

@router.get("/linkedin-autofill")
async def linkedin_autofill(cv_json: str, service: CVService = Depends(get_cv_service)):
    return service.linkedin_autofill(cv_json)