from pydantic import BaseModel, Field
from typing import List

class ExperienceSchema(BaseModel):
    company: str = "Empresa no especificada"
    position: str = "Cargo no especificado"
    start_date: str = ""
    end_date: str = "Presente"
    bullets: List[str] = Field(default_factory=list)
    skills_used: List[str] = Field(default_factory=list)