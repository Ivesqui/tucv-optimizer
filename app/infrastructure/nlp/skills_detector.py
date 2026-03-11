"""
infrastructure/nlp/skills_detector.py

Detecta habilidades técnicas y blandas de una oferta laboral
usando diccionarios curados + regex. Sin IA externa.

Mejoras production-ready:
    - Tipado completo con TypedDict
    - Precompilación de regex al importar
    - Seniority: devuelve todos los niveles detectados
    - ATS score seguro (sin división por cero)
    - compare_cv_vs_offer: recomendaciones desacopladas
    - Constantes de ponderación nombradas
    - Docstrings completos
    - Logging en lugar de fallos silenciosos
    - _score_to_grade puro con tabla de umbrales explícita
    - Normalización avanzada para VB.NET, VB Net, VBNet, etc.
"""

from __future__ import annotations

import logging
import re
from typing import TypedDict

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Constantes de ponderación ATS
# ─────────────────────────────────────────────

WEIGHT_TECH: float = 70.0
WEIGHT_SOFT: float = 30.0
assert WEIGHT_TECH + WEIGHT_SOFT == 100.0, "Los pesos deben sumar 100"

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
# Diccionarios de skills
# ─────────────────────────────────────────────

TECH_SKILLS: dict[str, list[str]] = {
    "languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
        "kotlin", "swift", "php", "ruby", "scala", "r", "matlab", "bash", "shell",
        "sql", "html", "css", "dart", "elixir", "haskell", "perl",
        "vb.net", "vb", "visual basic",
    ],
    "frameworks": [
        "react", "angular", "vue", "nextjs", "nuxtjs", "svelte", "django", "flask",
        "fastapi", "spring", "springboot", "express", "nestjs", "laravel", "rails",
        "dotnet", ".net", "asp.net", "strapi", "gatsby", "remix", "astro", "vb.net",
    ],
    "databases": [
        "postgresql", "mysql", "mongodb", "redis", "sqlite", "oracle", "cassandra",
        "dynamodb", "elasticsearch", "neo4j", "firebase", "supabase", "cockroachdb",
        "mariadb", "bigquery", "snowflake", "dbt",
    ],
    "cloud": [
        "aws", "azure", "gcp", "google cloud", "heroku", "digitalocean", "vercel",
        "netlify", "cloudflare", "linode", "vultr", "oci",
    ],
    "devops": [
        "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins",
        "github actions", "gitlab ci", "circleci", "travis ci", "helm",
        "prometheus", "grafana", "nginx", "apache", "linux", "unix",
    ],
    "data_ml": [
        "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
        "scikit-learn", "pandas", "numpy", "spark", "hadoop", "airflow", "mlflow",
        "huggingface", "langchain", "nlp", "computer vision", "llm",
    ],
    "tools": [
        "git", "github", "gitlab", "bitbucket", "jira", "confluence", "notion",
        "figma", "postman", "swagger", "graphql", "rest", "grpc", "kafka",
        "rabbitmq", "celery", "websocket", "oauth", "jwt",
    ],
    "methodologies": [
        "agile", "scrum", "kanban", "tdd", "bdd", "ci/cd", "devops", "gitflow",
        "microservices", "monorepo", "solid", "design patterns",
        "clean architecture", "ddd", "event driven",
    ],
}

SOFT_SKILLS: list[str] = [
    # Español
    "comunicación", "liderazgo", "trabajo en equipo", "resolución de problemas",
    "pensamiento crítico", "adaptabilidad", "creatividad", "gestión del tiempo",
    "proactividad", "autonomía", "orientación a resultados", "colaboración",
    # Inglés
    "communication", "leadership", "teamwork", "problem solving",
    "critical thinking", "adaptability", "creativity", "time management",
    "proactive", "autonomous", "results oriented", "collaboration",
    "analytical", "detail oriented", "fast learner", "self motivated",
]

EXPERIENCE_PATTERNS: list[str] = [
    r"(\d+)\+?\s*años?\s*de\s*experiencia",
    r"(\d+)\+?\s*years?\s*of\s*experience",
    r"experiencia\s*de\s*(\d+)\+?\s*años?",
    r"(\d+)\+?\s*yrs?\s*experience",
    r"minimum\s*(\d+)\s*years?",
    r"mínimo\s*(\d+)\s*años?",
]

SENIORITY_MAP: dict[str, list[str]] = {
    "junior":  ["junior", "jr", "entry level", "entry-level", "trainee", "intern", "practicante"],
    "mid":     ["mid", "semi senior", "semi-senior", "ssr", "intermediate", "associate"],
    "senior":  ["senior", "sr", "lead", "staff", "principal", "architect", "tech lead"],
    "manager": ["manager", "head", "director", "vp", "chief", "cto", "cpo"],
}

EDUCATION_KEYWORDS: list[str] = [
    "licenciatura", "ingeniería", "bachelor", "máster", "master", "mba",
    "doctorado", "phd", "técnico", "tecnólogo", "certificación", "certification",
    "bootcamp", "university", "universidad",
]

# ─────────────────────────────────────────────
# Precompilación regex
# ─────────────────────────────────────────────

def _compile_word_pattern(term: str) -> re.Pattern[str]:
    """Compila patrón de palabra completa para term, normalizando puntos y guiones"""
    term_norm = term.lower().replace(".", r"\.?").replace("-", r"\-?")
    return re.compile(r"\b" + re.escape(term_norm) + r"\b", re.IGNORECASE)

_TECH_PATTERNS = {cat: [(s, _compile_word_pattern(s)) for s in skills] for cat, skills in TECH_SKILLS.items()}
_SOFT_PATTERNS = [(s, _compile_word_pattern(s)) for s in SOFT_SKILLS]
_SENIORITY_PATTERNS = {lvl: [(kw, _compile_word_pattern(kw)) for kw in kws] for lvl, kws in SENIORITY_MAP.items()}
_EXPERIENCE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in EXPERIENCE_PATTERNS]

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
# Helpers
# ─────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Minúsculas + trim + reemplazo de separadores por espacio"""
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
        recs.append(f"Agrega estas skills al CV: {', '.join(sorted(missing_tech)[:TOP_MISSING_TECH])}")
    if missing_soft:
        recs.append(f"Menciona estas soft skills: {', '.join(sorted(missing_soft)[:TOP_MISSING_SOFT])}")
    if ats_score < 40:
        recs.append("⚠️ Score bajo. Personaliza el CV para esta oferta específica.")
    elif ats_score < 65:
        recs.append("📈 Score medio. Incorpora más keywords de la oferta.")
    else:
        recs.append("✅ Buen match. Asegura que el CV use las mismas palabras exactas de la oferta.")
    return recs

# ─────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────

def detect_skills(text: str) -> DetectSkillsResult:
    if not text.strip():
        logger.warning("Texto vacío recibido en detect_skills")
        return DetectSkillsResult({}, [], [], None, [], [], 0)

    normalized = _normalize(text)
    tech_skills: dict[str, list[str]] = {cat: [s for s, p in pats if p.search(normalized)] for cat, pats in _TECH_PATTERNS.items() if any(p.search(normalized) for _, p in pats)}
    soft_skills = [s for s, p in _SOFT_PATTERNS if p.search(normalized)]

    years_required = None
    for p in _EXPERIENCE_PATTERNS:
        m = p.search(normalized)
        if m:
            years_required = int(m.group(1))
            break

    seniority = [lvl for lvl, pats in _SENIORITY_PATTERNS.items() if any(p.search(normalized) for _, p in pats)]
    education_keywords = [kw for kw in EDUCATION_KEYWORDS if kw in normalized]
    all_tech_flat = [s for skills in tech_skills.values() for s in skills]

    return DetectSkillsResult(
        tech_skills=tech_skills,
        soft_skills=soft_skills,
        all_tech_flat=all_tech_flat,
        years_required=years_required,
        seniority=seniority,
        education_keywords=education_keywords,
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

    tech_score = (len(matching_tech) / max(len(offer_tech), 1)) * WEIGHT_TECH
    soft_score = (len(matching_soft) / max(len(offer_soft), 1)) * WEIGHT_SOFT
    ats_score = round(tech_score + soft_score, 1)

    return CompareResult(
        ats_score=ats_score,
        grade=_score_to_grade(ats_score),
        matching_tech=sorted(matching_tech),
        missing_tech=sorted(missing_tech),
        extra_tech=sorted(extra_tech),
        matching_soft=sorted(matching_soft),
        missing_soft=sorted(missing_soft),
        recommendations=_build_recommendations(missing_tech, missing_soft, ats_score)
    )