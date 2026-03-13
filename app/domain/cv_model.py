"""
domain/cv_model.py
Modelo de datos del CV + lógica de optimización automática.
"""

from dataclasses import dataclass, field as dc_field, asdict
from typing import List
import json

field = dc_field


@dataclass
class PersonalMetadata:
    # Identidad
    id_type: str = ""  # Cédula, Pasaporte
    id_number: str = ""
    birth_date: str = ""  # ISO o formato legible
    gender: str = ""  # Masculino, Femenino, Otro
    marital_status: str = ""  # Soltero, Casado, etc.
    nationality: str = ""
    ethnicity: str = ""  # Para Encuentra Empleo

    # Salud y Acciones Afirmativas
    disability_status: bool = False
    disability_percentage: int = 0
    blood_type: str = ""  # Para Encuentra Empleo
    catastrophic_illness_family: bool = False

    # Legal y Logística
    drivers_license: str = ""  # No, Tipo A, Tipo B, etc.
    owns_vehicle: bool = False
    willing_to_travel: bool = False
    willing_to_relocate: bool = False
    military_service_status: str = ""  # A veces pedido en sector público

    # Ubicación detallada
    province: str = ""
    canton: str = ""
    parish: str = ""  # Parroquia
    address_main_street: str = ""
    address_secondary_street: str = ""
    address_reference: str = ""


@dataclass
class ContactInfo:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""

@dataclass
class WorkExperience:
    company: str = ""
    position: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    bullets: List[str] = dc_field(default_factory=list)
    skills_used: List[str] = dc_field(default_factory=list)

@dataclass
class Education:
    institution: str = ""
    degree: str = ""
    field_of_study: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: str = ""
    highlights: List[str] = dc_field(default_factory=list)

@dataclass
class Project:
    name: str = ""
    description: str = ""
    tech_stack: List[str] = dc_field(default_factory=list)
    url: str = ""
    highlights: List[str] = dc_field(default_factory=list)

@dataclass
class Certification:
    name: str = ""
    issue: str = ""
    date: str = ""
    url: str = ""

@dataclass
class CVProfile:
    contact: ContactInfo = dc_field(default_factory=ContactInfo)
    metadata: PersonalMetadata = dc_field(default_factory=PersonalMetadata)  # NUEVO
    summary: str = ""
    experience: List[WorkExperience] = dc_field(default_factory=list)
    education: List[Education] = dc_field(default_factory=list)
    projects: List[Project] = dc_field(default_factory=list)
    certifications: List[Certification] = dc_field(default_factory=list)
    skills: List[str] = dc_field(default_factory=list)
    languages: List[str] = dc_field(default_factory=list)
    soft_skills: List[str] = dc_field(default_factory=list)


    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_plain_text(self) -> str:
        parts = []
        parts.append(f"{self.contact.name}")
        parts.append(self.summary)
        for exp in self.experience:
            parts.append(f"{exp.position} {exp.company}")
            parts.extend(exp.bullets)
            parts.extend(exp.skills_used)
        for proj in self.projects:
            parts.append(f"{proj.name} {proj.description}")
            parts.extend(proj.tech_stack)
        parts.extend(self.skills)
        parts.extend(self.soft_skills)
        return " ".join(parts)

    @classmethod
    def from_dict(cls, data: dict) -> "CVProfile":
        contact = ContactInfo(**data.get("contact", {}))
        experience = [WorkExperience(**e) for e in data.get("experience", [])]
        education = [Education(**{"field_of_study" if k=="field" else k: v for k,v in e.items()}) for e in data.get("education", [])]
        projects = [Project(**p) for p in data.get("projects", [])]
        certifications = [Certification(**c) for c in data.get("certifications", [])]
        metadata_data = data.get("metadata", {})
        metadata = PersonalMetadata(**metadata_data)
        return cls(
            contact=contact,
            metadata=metadata,
            summary=data.get("summary", ""),
            experience=experience,
            education=education,
            projects=projects,
            certifications=certifications,
            skills=data.get("skills", []),
            languages=data.get("languages", []),
            soft_skills=data.get("soft_skills", []),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "CVProfile":
        return cls.from_dict(json.loads(json_str))

