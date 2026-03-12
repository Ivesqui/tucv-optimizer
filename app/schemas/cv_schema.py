from typing import List, Optional
from pydantic import BaseModel, Field

# Importamos tus nuevos esquemas
from app.schemas.experience_schema import ExperienceSchema
from app.schemas.education_schema import EducationSchema

class CVDataSchema(BaseModel):
    # Ahora cv_json ya no es un Dict[str, Any] genérico
    # Definimos la estructura interna que el frontend debe enviar
    contact: dict = Field(default_factory=lambda: {"name": "Usuario"})
    summary: str = ""
    experience: List[ExperienceSchema] = Field(default_factory=list)
    education: List[EducationSchema] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)

class GenerateCVRequest(BaseModel):
    # Aquí integramos la validación profunda
    cv_json: CVDataSchema
    offer_text: Optional[str] = None
    optimize: bool = True
    format: str = "html"
    photo_base64: Optional[str] = None