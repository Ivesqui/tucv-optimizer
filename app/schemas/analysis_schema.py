from pydantic import BaseModel
from typing import Optional, List

class AnalyzeOfferRequest(BaseModel):
    offer_text: str
    cv_json: Optional[dict] = None

class BulletQualityRequest(BaseModel):
    bullets: List[str]

class BulletAnalysisResponse(BaseModel):
    original_bullet: str
    impact_score: float  # De 0.0 a 10.0
    feedback: str
    suggestions: List[str]