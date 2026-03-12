import logging
from typing import TypedDict
from app.core.knowledge.db_loader import (
    _TECH_PATTERNS, _SOFT_PATTERNS, _EXPERIENCE_PATTERNS,
    _SENIORITY_PATTERNS, _EDUCATION_KEYWORDS, clean_text
)

logger = logging.getLogger(__name__)

class RawDetectionResult(TypedDict):
    tech_skills: dict[str, list[str]]
    soft_skills: list[str]
    all_tech_flat: list[str]
    years_required: int | None
    seniority: list[str]
    education_keywords: list[str]


def detect_skills(text: str) -> RawDetectionResult:
    """Extrae información cruda del texto usando los patrones pre-compilados en db_loader."""

    # CORRECCIÓN AQUÍ: Devolvemos un diccionario con las llaves correctas
    if not text or not text.strip():
        return {
            "tech_skills": {},
            "soft_skills": [],
            "all_tech_flat": [],
            "years_required": None,
            "seniority": [],
            "education_keywords": []
        }

    normalized = clean_text(text)

    # 1. Detectar Tech Skills
    tech_skills = {}
    for cat, pats in _TECH_PATTERNS.items():
        found = [name for name, p in pats if p.search(normalized)]
        if found:
            tech_skills[cat] = found

    # 2. Detectar Soft Skills
    soft_skills = list(set([name for name, p in _SOFT_PATTERNS if p.search(normalized)]))

    # 3. Detectar Experiencia (Años)
    years_required = None
    for p in _EXPERIENCE_PATTERNS:
        m = p.search(normalized)
        if m:
            try:
                years_required = int(m.group(1))
            except (ValueError, IndexError):
                continue
            break

    # 4. Seniority y Educación
    seniority = [lvl for lvl, pats in _SENIORITY_PATTERNS.items() if any(p.search(normalized) for _, p in pats)]
    education_found = [kw for kw in _EDUCATION_KEYWORDS if kw.lower() in normalized]

    # Esta parte ya la tenías bien, es un diccionario literal
    return {
        "tech_skills": tech_skills,
        "soft_skills": soft_skills,
        "all_tech_flat": [s for skills in tech_skills.values() for s in skills],
        "years_required": years_required,
        "seniority": seniority,
        "education_keywords": education_found
    }