"""
domain/cv_model.py
Modelo de datos del CV + lógica de optimización automática.
"""

from dataclasses import dataclass, field as dc_field, asdict
field = dc_field  # alias para no romper el código existente
from typing import List, Tuple
import json
import re



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
    start_date: str = ""        # "2022-03" o "Mar 2022"
    end_date: str = ""          # "Presente" o "2024-01"
    location: str = ""
    bullets: List[str] = dc_field(default_factory=list)   # logros / responsabilidades
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
    issuer: str = ""
    date: str = ""
    url: str = ""


@dataclass
class CVProfile:
    contact: ContactInfo = dc_field(default_factory=ContactInfo)
    summary: str = ""
    experience: List[WorkExperience] = dc_field(default_factory=list)
    education: List[Education] = dc_field(default_factory=list)
    projects: List[Project] = dc_field(default_factory=list)
    certifications: List[Certification] = dc_field(default_factory=list)
    skills: List[str] = dc_field(default_factory=list)          # skills técnicas
    languages: List[str] = dc_field(default_factory=list)       # idiomas
    soft_skills: List[str] = dc_field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_plain_text(self) -> str:
        """Genera texto plano del CV para análisis NLP."""
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
        return cls(
            contact=contact,
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


# ─── Optimizador de CV ────────────────────────────────────────────────────────

# Verbos de impacto para bullets ATS
IMPACT_VERBS = [
    "Desarrollé", "Implementé", "Lideré", "Optimicé", "Diseñé",
    "Construí", "Automaticé", "Reduje", "Aumenté", "Mejoré",
    "Migré", "Refactoricé", "Integré", "Desplegué", "Coordiné",
    "Entregué", "Escalé", "Monitoreé", "Documenté", "Colaboré",
]

WEAK_VERBS = [
    "hice", "trabajé", "ayudé", "participé", "estuve encargado",
    "fui responsable", "me encargué", "colaboré en", "apoyé",
    "was responsible", "helped", "assisted", "worked on", "participated",
]


def optimize_cv(
        profile: CVProfile,
        missing_tech: List[str],
        missing_soft: List[str]) \
        -> Tuple[CVProfile, List[str], List[str]]:
    """
    Optimiza el CV automáticamente:
    1. Agrega skills faltantes si el usuario las tiene
    2. Mejora el summary con keywords de la oferta
    3. Sugiere agregar soft skills
    """
    import copy
    optimized = copy.deepcopy(profile)

    # Normalizar skills existentes a minúsculas para comparar
    existing_lower = {s.lower() for s in optimized.skills}

    # No agregamos skills que el usuario no mencionó — solo las destacamos
    # en el resumen si ya existen en experiencia/proyectos
    all_text_lower = optimized.to_plain_text().lower()

    # Skills que están en experiencia pero no en la sección Skills
    skills_to_promote = []
    for skill in missing_tech:
        if skill.lower() in all_text_lower and skill.lower() not in existing_lower:
            skills_to_promote.append(skill)

    if skills_to_promote:
        optimized.skills.extend(skills_to_promote)

    # Agregar soft skills que no estén listadas
    existing_soft_lower = {s.lower() for s in optimized.soft_skills}
    soft_to_add = [s for s in missing_soft if s.lower() not in existing_soft_lower][:3]
    # Solo las agregamos si hay base en el perfil (no inventamos)
    # En MVP real, el usuario confirma

    return optimized, skills_to_promote, soft_to_add


def analyze_bullet_quality(bullet: str) -> dict:
    """Evalúa la calidad de un bullet point."""
    issues = []
    score = 100

    # ¿Empieza con verbo de impacto?
    words = bullet.strip().split()
    if not words:
        return {"score": 0, "issues": ["Bullet vacío"]}

    first_word = words[0].lower()
    has_impact_verb = any(v.lower() in first_word for v in IMPACT_VERBS)
    has_weak_verb = any(v.lower() in bullet.lower() for v in WEAK_VERBS)

    if not has_impact_verb:
        issues.append("Usa un verbo de impacto al inicio (Desarrollé, Implementé, Optimicé...)")
        score -= 20

    if has_weak_verb:
        issues.append("Evita verbos débiles. Sé más directo y cuantitativo.")
        score -= 15

    # ¿Tiene métricas?
    has_metric = bool(re.search(r"\d+\s*%|\d+x|\$[\d,]+|\d+\s*(usuarios|users|clientes|requests|ms|gb|tb)", bullet.lower()))
    if not has_metric:
        issues.append("Agrega métricas: %, $, tiempo, usuarios afectados, etc.")
        score -= 20

    # Longitud
    if len(bullet) < 40:
        issues.append("Bullet muy corto. Agrega contexto y resultado.")
        score -= 15
    elif len(bullet) > 200:
        issues.append("Bullet muy largo. Divide en 2 o acórtalo.")
        score -= 10

    return {"score": max(0, score), "issues": issues}
