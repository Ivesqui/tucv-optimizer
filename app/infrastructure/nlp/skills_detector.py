"""
infrastructure/nlp/skills_detector.py

Motor universal de detección de habilidades y reglas ATS.
Carga dinámica desde archivos JSON en core/knowledge/.
"""

from __future__ import annotations
import logging
import re
import json
from typing import TypedDict
from pathlib import Path

logger = logging.getLogger(__name__)

# Ruta dinámica para encontrar tus JSONs
KNOWLEDGE_PATH = Path(__file__).parent.parent.parent / "core" / "knowledge"

# ─────────────────────────────────────────────
# Constantes de ponderación ATS
# ─────────────────────────────────────────────

WEIGHT_TECH: float = 70.0
WEIGHT_SOFT: float = 30.0
TOP_MISSING_TECH: int = 5
TOP_MISSING_SOFT: int = 3

_GRADE_THRESHOLDS: list[tuple[float, str]] = [
    (80.0, "A"),
    (65.0, "B"),
    (50.0, "C"),
    (35.0, "D"),
    (0.0,  "F"),
]

# ─────────────────────────────────────────────
# Helpers de Carga y Compilación
# ─────────────────────────────────────────────

def _load_json(filename: str) -> dict | list:
    """Carga segura de archivos JSON desde la base de conocimientos"""
    path = KNOWLEDGE_PATH / filename
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando {filename}: {e}")
        return {} if "db" in filename or "rules" in filename else []

def _compile_word_pattern(term: str) -> re.Pattern[str]:
    """Compila patrón de palabra completa, normalizando puntos y guiones"""
    term_norm = term.lower().replace(".", r"\.?").replace("-", r"\-?")
    return re.compile(r"\b" + re.escape(term_norm) + r"\b", re.IGNORECASE)

# ─────────────────────────────────────────────
# Inicialización de Datos (Precompilación)
# ─────────────────────────────────────────────

# 1. Cargar Datos Raw
_tech_raw = _load_json("skills_db.json")
_soft_raw = _load_json("soft_skills_db.json")
_rules_raw = _load_json("rules_db.json")
_verbs_raw = _load_json("action_verbs_db.json")
_weak_verbs_raw = _load_json("weak_verbs_db.json")

# 2. Precompilar Patrones (Optimización de performance)
_TECH_PATTERNS = {
    cat: [(s, _compile_word_pattern(s)) for s in skills]
    for cat, skills in _tech_raw.items()
}

# Aplanamos las soft skills para el motor de búsqueda
_all_soft_list = [s for sublist in _soft_raw.values() for s in sublist]
_SOFT_PATTERNS = [(s, _compile_word_pattern(s)) for s in _all_soft_list]

_SENIORITY_PATTERNS = {
    lvl: [(kw, _compile_word_pattern(kw)) for kw in kws]
    for lvl, kws in _rules_raw.get("seniority_map", {}).items()
}

_EXPERIENCE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in _rules_raw.get("experience_patterns", [])
]

_EDUCATION_KEYWORDS = _rules_raw.get("education_keywords", [])

# ─────────────────────────────────────────────
# TypedDicts
# ─────────────────────────────────────────────

class DetectSkillsResult(TypedDict):
    tech_skills: dict[str, list[str]]
    soft_skills: list[str]
    all_tech_flat: list[str]
    years_required: int | None
    seniority: list[str]
    education_keywords: list[str]
    total_skills_found: int

class CompareResult(TypedDict):
    ats_score: float
    grade: str
    matching_tech: list[str]
    missing_tech: list[str]
    extra_tech: list[str]
    matching_soft: list[str]
    missing_soft: list[str]
    recommendations: list[str]

# ─────────────────────────────────────────────
# Helpers de Procesamiento
# ─────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Limpieza estándar de texto"""
    text = text.lower().strip()
    text = re.sub(r"[\.\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text

def _score_to_grade(score: float) -> str:
    for thresh, grade in _GRADE_THRESHOLDS:
        if score >= thresh:
            return grade
    return "F"

def _build_recommendations(missing_tech: set[str], missing_soft: set[str], ats_score: float) -> list[str]:
    recs: list[str] = []
    if missing_tech:
        recs.append(f"Agrega estas skills técnicas: {', '.join(sorted(missing_tech)[:TOP_MISSING_TECH])}")
    if missing_soft:
        recs.append(f"Menciona estas habilidades blandas: {', '.join(sorted(missing_soft)[:TOP_MISSING_SOFT])}")

    if ats_score < 40:
        recs.append("⚠️ Score muy bajo. Tu CV no coincide con los requisitos básicos.")
    elif ats_score < 65:
        recs.append("📈 Score aceptable, pero faltan keywords clave de la industria.")
    else:
        recs.append("✅ Excelente match. Tu perfil es muy compatible.")
    return recs

# ─────────────────────────────────────────────
# API Pública
# ─────────────────────────────────────────────

def detect_skills(text: str) -> DetectSkillsResult:
    if not text or not text.strip():
        logger.warning("Texto vacío en detect_skills")
        return DetectSkillsResult({}, [], [], None, [], [], 0)

    normalized = _normalize(text)

    # 1. Detectar Tech Skills por categoría
    tech_skills: dict[str, list[str]] = {}
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
            years_required = int(m.group(1))
            break

    # 4. Detectar Seniority y Educación
    seniority = [lvl for lvl, pats in _SENIORITY_PATTERNS.items() if any(p.search(normalized) for _, p in pats)]
    education_found = [kw for kw in _EDUCATION_KEYWORDS if kw.lower() in normalized]

    all_tech_flat = [s for skills in tech_skills.values() for s in skills]

    return DetectSkillsResult(
        tech_skills=tech_skills,
        soft_skills=soft_skills,
        all_tech_flat=all_tech_flat,
        years_required=years_required,
        seniority=seniority,
        education_keywords=education_found,
        total_skills_found=len(all_tech_flat) + len(soft_skills)
    )

def compare_cv_vs_offer(cv_skills: DetectSkillsResult, offer_skills: DetectSkillsResult) -> CompareResult:
    cv_tech = set(cv_skills["all_tech_flat"])
    offer_tech = set(offer_skills["all_tech_flat"])
    cv_soft = set(cv_skills["soft_skills"])
    offer_soft = set(offer_skills["soft_skills"])

    matching_tech = cv_tech & offer_tech
    missing_tech = offer_tech - cv_tech
    extra_tech = cv_tech - offer_tech
    matching_soft = cv_soft & offer_soft
    missing_soft = offer_soft - cv_soft

    # Score ponderado
    t_score = (len(matching_tech) / max(len(offer_tech), 1)) * WEIGHT_TECH
    s_score = (len(matching_soft) / max(len(offer_soft), 1)) * WEIGHT_SOFT
    ats_score = round(t_score + s_score, 1)

    return CompareResult(
        ats_score=ats_score,
        grade=_score_to_grade(ats_score),
        matching_tech=sorted(list(matching_tech)),
        missing_tech=sorted(list(missing_tech)),
        extra_tech=sorted(list(extra_tech)),
        matching_soft=sorted(list(matching_soft)),
        missing_soft=sorted(list(missing_soft)),
        recommendations=_build_recommendations(missing_tech, missing_soft, ats_score)
    )


def analyze_experience_quality(text: str) -> dict:
    """
    Analiza la calidad de la redacción detectando verbos débiles
    y sugiriendo alternativas poderosas desde los diccionarios JSON.
    """
    if not text:
        return {"score_redaccion": 100, "puntos_a_mejorar": [], "sugerencias": []}

    text_lower = text.lower()

    # 1. Extraer listas de los nuevos JSONs
    weak_list = _weak_verbs_raw.get("verbos_debiles", [])
    passive_list = _weak_verbs_raw.get("frases_pasivas", [])

    # Verbos fuertes para las sugerencias (mezcla de categorías)
    strong_alternatives = (
            _verbs_raw.get("liderazgo", [])[:2] +
            _verbs_raw.get("operativo", [])[:2] +
            _verbs_raw.get("comercial", [])[:2]
    )

    # 2. Encontrar debilidades (con espacio para evitar match parcial)
    found_weak = [v for v in weak_list if f" {v} " in f" {text_lower} "]
    found_passive = [p for p in passive_list if p in text_lower]

    total_issues = found_weak + found_passive

    # 3. Generar score (mínimo 0 para no romper la UI)
    deduction = (len(found_weak) * 8) + (len(found_passive) * 12)
    score = max(0, 100 - deduction)

    # 4. Construir respuesta profesional
    results = {
        "score_redaccion": score,
        "puntos_a_mejorar": total_issues,
        "sugerencias": []
    }

    if total_issues:
        # Tomamos los primeros 3 problemas y les damos una alternativa
        for issue in total_issues[:3]:
            results["sugerencias"].append(
                f"En lugar de usar '{issue}', intenta con verbos de impacto como: {', '.join(strong_alternatives[:3])}."
            )

    return results

class AnalysisResponse(TypedDict):
    match_details: CompareResult        # El score ATS y comparativa
    skills_detected: DetectSkillsResult # Lo que encontró el motor
    writing_advice: dict                # El resultado de analyze_experience_quality
    meta: dict                          # Datos extra (fecha, versión del motor)