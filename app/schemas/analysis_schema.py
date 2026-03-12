from pydantic import BaseModel
from typing import Optional, List
from typing import TypedDict, Any

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

class AnalysisResponse(TypedDict):
    match_details: dict[str, Any]      # El resultado de compare_cv_vs_offer
    skills_detected: dict[str, Any]    # El resultado de detect_skills
    writing_advice: dict[str, Any]     # El resultado de analyze_experience_quality
    meta: dict[str, str]               # Versión, industria, etc.