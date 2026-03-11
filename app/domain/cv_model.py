"""
domain/cv_model.py
Modelo de datos del CV + lógica de optimización automática.
"""

from dataclasses import dataclass, field as dc_field, asdict
from typing import List, Tuple
import json
import copy
import re
# Importamos los diccionarios cargados en el motor
from app.infrastructure.nlp.skills_detector import _weak_verbs_raw, _verbs_raw

field = dc_field  # alias para no romper el código existente
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


def _smart_replace(text: str, weak_list: list, strong_list: list) -> str:
    if not text:
        return text

    updated_text = text
    for weak in weak_list:
        # Buscamos el verbo débil (palabra completa, ignorando mayúsculas)
        pattern = re.compile(rf"\b{weak}\b", re.IGNORECASE)
        match = pattern.search(updated_text)

        if match:
            replacement = strong_list[0] if strong_list else "lideré"

            # Lógica de capitalización:
            # Si el match está al inicio del texto, Capitalize.
            # Si no, mantenemos minúscula para que fluya en la frase.
            if match.start() == 0:
                replacement = replacement.capitalize()
            else:
                replacement = replacement.lower()

            # Reemplazamos solo la primera ocurrencia para evitar sobre-optimización
            updated_text = pattern.sub(replacement, updated_text, count=1)
            break

    return updated_text


def optimize_cv(
        profile: CVProfile,
        missing_tech: List[str],
        missing_soft: List[str]
) -> Tuple[CVProfile, List[str], List[str]]:
    optimized = copy.deepcopy(profile)

    # 1. Cargar diccionarios
    weak_list = _weak_verbs_raw.get("verbos_debiles", [])
    strong_list = _verbs_raw.get("liderazgo", []) + _verbs_raw.get("operativo", [])

    # 2. OPTIMIZACIÓN NARRATIVA: Summary
    if optimized.summary:
        optimized.summary = _smart_replace(optimized.summary, weak_list, strong_list)

    # 3. OPTIMIZACIÓN NARRATIVA: Experiencia (Bullets)
    for exp in optimized.experience:
        optimized_bullets = []
        for bullet in exp.bullets:
            optimized_bullets.append(_smart_replace(bullet, weak_list, strong_list))
        exp.bullets = optimized_bullets

    # 4. PROMOCIÓN DE SKILLS (Tu lógica original)
    existing_lower = {s.lower() for s in optimized.skills}
    all_text_lower = optimized.to_plain_text().lower()

    skills_to_promote = []
    for skill in missing_tech:
        if skill.lower() in all_text_lower and skill.lower() not in existing_lower:
            skills_to_promote.append(skill)

    if skills_to_promote:
        optimized.skills.extend(skills_to_promote)

    # 5. SUGERENCIA DE SOFT SKILLS
    existing_soft_lower = {s.lower() for s in optimized.soft_skills}
    soft_to_add = [s for s in missing_soft if s.lower() not in existing_soft_lower][:3]

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


# app/domain/cv_model.py

def improve_bullet_narrative(bullet: str, weak_verbs: list, strong_verbs: list) -> str:
    """
    Busca verbos débiles en un bullet y los reemplaza por uno de alto impacto.
    """
    new_bullet = bullet
    # Limpieza básica para evitar reemplazar partes de palabras
    for weak in weak_verbs:
        pattern = re.compile(rf"\b{weak}\b", re.IGNORECASE)
        if pattern.search(new_bullet):
            # Tomamos un verbo fuerte aleatorio o el primero de la lista
            replacement = strong_verbs[0] if strong_verbs else "Lideré"
            # Reemplazamos y capitalizamos si es el inicio de la frase
            new_bullet = pattern.sub(replacement.capitalize(), new_bullet)
            break  # Solo reemplazamos el primero para no saturar

    return new_bullet


