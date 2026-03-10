from typing import Optional, List
from pydantic import BaseModel
from typing import Dict, Any

class AnalyzeOfferRequest(BaseModel):
    offer_text: str
    cv_json: Optional[dict] = None


class GenerateCVRequest(BaseModel):
    cv_json: Dict[str, Any]
    offer_text: Optional[str] = None
    optimize: bool = True
    format: str = "html"
    photo_base64: Optional[str] = None

class BulletQualityRequest(BaseModel):
    bullets: List[str]
