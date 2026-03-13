from pydantic import BaseModel
from typing import Optional, List
from typing import TypedDict, Any

class AnalyzeOfferRequest(BaseModel):
    offer_text: str
    cv_json: Optional[dict] = None

class BulletQualityRequest(BaseModel):
    bullets: List[str]


class BulletAnalysisResponse(BaseModel):
    original_bullet: Optional[str] = None
    bullet: str
    score: float
    impact_score: Optional[float] = 0.0
    feedback: List[str]
    suggestions: List[str]

class AnalysisResponse(TypedDict):
    match_details: dict[str, Any]
    skills_detected: dict[str, Any]
    writing_advice: dict[str, Any]
    meta: dict[str, str]