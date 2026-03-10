from typing import Optional, List
from pydantic import BaseModel


class AnalyzeOfferRequest(BaseModel):
    offer_text: str
    cv_json: Optional[dict] = None


class GenerateCVRequest(BaseModel):
    cv_json: dict
    offer_text: Optional[str] = None
    optimize: bool = True
    format: str = "html"
    photo_base64: Optional[str] = None

class BulletQualityRequest(BaseModel):
    bullets: List[str]
