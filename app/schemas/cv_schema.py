from typing import List, Optional
from pydantic import BaseModel, Field

# 1. Importamos tus nuevos esquemas
from app.schemas.experience_schema import ExperienceSchema
from app.schemas.education_schema import EducationSchema
from app.schemas.metadata_schema import PersonalMetadataSchema
from app.schemas.project_schema import ProjectSchema  # <--- Importante
from app.schemas.certification_schema import CertificationSchema  # <--- Importante


class CVDataSchema(BaseModel):
    contact: dict = Field(default_factory=lambda: {"name": "Usuario"})
    metadata: PersonalMetadataSchema = Field(default_factory=PersonalMetadataSchema)
    summary: str = ""
    experience: List[ExperienceSchema] = Field(default_factory=list)
    education: List[EducationSchema] = Field(default_factory=list)
    certifications: List[CertificationSchema] = Field(default_factory=list)
    projects: List[ProjectSchema] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)





class GenerateCVRequest(BaseModel):
    cv_json: CVDataSchema
    offer_text: Optional[str] = None
    optimize: bool = True
    format: str = "pdf"
    photo_base64: Optional[str] = None
    theme_color: str = "CORPORATE_BLUE"
    font_family: str = "INTER"