from typing import Optional
from pydantic import BaseModel
from typing import Dict, Any

class GenerateCVRequest(BaseModel):
    cv_json: Dict[str, Any]
    offer_text: Optional[str] = None
    optimize: bool = True
    format: str = "html"
    photo_base64: Optional[str] = None



