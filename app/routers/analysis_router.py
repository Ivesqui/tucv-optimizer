from fastapi import APIRouter, Depends
from app.schemas.analysis_schema import (
    AnalyzeOfferRequest,
    BulletQualityRequest,
    BulletAnalysisResponse)
from app.services.analysis_service import AnalysisService
from app.dependencies import get_cv_analysis
from typing import List

router = APIRouter(tags=["ANALYSIS"])

@router.post("/analyze-offer")
async def analyze_offer(req: AnalyzeOfferRequest, service: AnalysisService = Depends(get_cv_analysis)):
    return service.analyze_offer(req)

@router.post("/analyze-bullets", response_model=List[BulletAnalysisResponse])
async def analyze_bullets(
    request: BulletQualityRequest,
    service: AnalysisService = Depends(get_cv_analysis)
    ):
    data = service.analyze_bullets(request)
    return data.get("results")