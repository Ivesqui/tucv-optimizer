from pydantic import BaseModel, Field
from typing import Optional

class CertificationSchema(BaseModel):
    name: str = Field(default="")
    issuer: str = Field(default="")
    issue_date: Optional[str] = None
    expiration_date: Optional[str] = None
    credential_id: Optional[str] = None
    url: Optional[str] = None