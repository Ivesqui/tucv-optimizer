"""
infrastructure/nlp/skills_detector.py

Detecta habilidades técnicas y blandas de una oferta laboral
usando diccionarios curados + regex. Sin IA externa.

Mejoras production-ready sobre la versión original:
    - Tipado completo con TypedDict para todos los retornos
    - Precompilación de regex al importar (rendimiento)
    - Seniority: devuelve todos los niveles encontrados, no solo el primero
    - ATS score: división por cero imposible aunque offer_tech/soft estén vacíos
    - compare_cv_vs_offer: recomendaciones desacopladas en _build_recommendations
    - Constantes de ponderación nombradas (WEIGHT_TECH / WEIGHT_SOFT)
    - Docstrings completos con Args / Returns / Raises
    - Logging en lugar de fallos silenciosos
    - _score_to_grade como método puro con tabla de umbrales explícita
    - Nombres internos consistentes (snake_case, sin abreviaciones ambiguas)
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
    ],
    "frameworks": [
        "react", "angular", "vue", "nextjs", "nuxtjs", "svelte", "django", "flask",
        "fastapi", "spring", "springboot", "express", "nestjs", "laravel", "rails",
        "dotnet", ".net", "asp.net", "strapi", "gatsby", "remix", "astro",
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
# Precompilación de patrones regex
# ─────────────────────────────────────────────

def _compile_word_pattern(term: str) -> re.Pattern[str]:
    """Compila un patrón de palabra completa para `term`."""
    return re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)


# Tech skills: {category: [(skill_name, compiled_pattern), ...]}
_TECH_PATTERNS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    category: [
        (skill, _compile_word_pattern(skill))
        for skill in skills
    ]
    for category, skills in TECH_SKILLS.items()
}

# Soft skills: [(skill_name, compiled_pattern), ...]
_SOFT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (skill, _compile_word_pattern(skill)) for skill in SOFT_SKILLS
]

# Seniority: {level: [(keyword, compiled_pattern), ...]}
_SENIORITY_PATTERNS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    level: [
        (kw, _compile_word_pattern(kw)) for kw in keywords
    ]
    for level, keywords in SENIORITY_MAP.items()
}

# Experience: lista de compiled patterns
_EXPERIENCE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in EXPERIENCE_PATTERNS
]


# ─────────────────────────────────────────────
# TypedDicts de retorno
# ─────────────────────────────────────────────

class DetectSkillsResult(TypedDict):
    tech_skills: dict[str, list[str]]
    soft_skills: list[str]
    all_tech_flat: list[str]
    years_required: int | None
    seniority: list[str]           # todos los niveles detectados
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
# Helpers internos
# ─────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Convierte el texto a minúsculas y elimina espacios extremos."""
    return text.lower().strip()


def _score_to_grade(score: float) -> str:
    """
    Convierte un score numérico (0–100) a una letra de calificación.

    Args:
        score: Valor entre 0.0 y 100.0.

    Returns:
        Letra de calificación según _GRADE_THRESHOLDS.
    """
    for threshold, grade in _GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"  # fallback defensivo


def _build_recommendations(
    missing_tech: set[str],
    missing_soft: set[str],
    ats_score: float,
) -> list[str]:
    """
    Genera recomendaciones accionables basadas en el gap de skills.

    Args:
        missing_tech:  Skills técnicas presentes en la oferta pero no en el CV.
        missing_soft:  Soft skills presentes en la oferta pero no en el CV.
        ats_score:     Score ATS calculado (0–100).

    Returns:
        Lista de strings con recomendaciones ordenadas por prioridad.
    """
    recommendations: list[str] = []

    if missing_tech:
        top = sorted(missing_tech)[:TOP_MISSING_TECH]
        recommendations.append(f"Agrega estas skills al CV: {', '.join(top)}")

    if missing_soft:
        top = sorted(missing_soft)[:TOP_MISSING_SOFT]
        recommendations.append(f"Menciona estas soft skills: {', '.join(top)}")

    if ats_score < 40:
        recommendations.append(
            "⚠️ Score bajo. Personaliza el CV para esta oferta específica."
        )
    elif ats_score < 65:
        recommendations.append(
            "📈 Score medio. Incorpora más keywords de la oferta."
        )
    else:
        recommendations.append(
            "✅ Buen match. Asegura que el CV use las mismas palabras exactas de la oferta."
        )

    return recommendations


# ─────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────

def detect_skills(text: str) -> DetectSkillsResult:
    """
    Analiza un texto (oferta laboral o CV) y retorna todas las skills detectadas.

    Usa patrones precompilados para máximo rendimiento. La detección es
    insensible a mayúsculas y busca palabras completas (word boundary).

    Args:
        text: Texto plano de la oferta o del CV.

    Returns:
        DetectSkillsResult con skills técnicas por categoría, soft skills,
        años de experiencia requeridos, niveles de seniority y keywords
        de educación encontrados.
    """
    if not text or not text.strip():
        logger.warning("detect_skills recibió texto vacío; retornando resultado vacío.")
        return DetectSkillsResult(
            tech_skills={},
            soft_skills=[],
            all_tech_flat=[],
            years_required=None,
            seniority=[],
            education_keywords=[],
            total_skills_found=0,
        )

    normalized = _normalize(text)

    # Skills técnicas por categoría
    tech_skills: dict[str, list[str]] = {}
    for category, patterns in _TECH_PATTERNS.items():
        matches = [skill for skill, pat in patterns if pat.search(normalized)]
        if matches:
            tech_skills[category] = matches

    # Soft skills
    soft_skills = [skill for skill, pat in _SOFT_PATTERNS if pat.search(normalized)]

    # Años de experiencia (primer match gana)
    years_required: int | None = None
    for pat in _EXPERIENCE_PATTERNS:
        match = pat.search(normalized)
        if match:
            years_required = int(match.group(1))
            break

    # Seniority: todos los niveles detectados (una oferta puede pedir "senior" y "lead")
    seniority = [
        level
        for level, patterns in _SENIORITY_PATTERNS.items()
        if any(pat.search(normalized) for _, pat in patterns)
    ]

    # Educación
    education_keywords = [
        kw for kw in EDUCATION_KEYWORDS if kw in normalized
    ]

    all_tech_flat = [s for skills in tech_skills.values() for s in skills]

    return DetectSkillsResult(
        tech_skills=tech_skills,
        soft_skills=soft_skills,
        all_tech_flat=all_tech_flat,
        years_required=years_required,
        seniority=seniority,
        education_keywords=education_keywords,
        total_skills_found=len(all_tech_flat) + len(soft_skills),
    )


def compare_cv_vs_offer(
    cv_skills: DetectSkillsResult,
    offer_skills: DetectSkillsResult,
) -> CompareResult:
    """
    Compara las skills del CV contra las de la oferta y calcula el ATS score.

    La ponderación es: {WEIGHT_TECH}% técnicas + {WEIGHT_SOFT}% blandas.
    Ambas fracciones se normalizan sobre el total de skills de la *oferta*,
    por lo que un CV con skills extras no penaliza el score.

    Args:
        cv_skills:     Resultado de detect_skills() aplicado al CV.
        offer_skills:  Resultado de detect_skills() aplicado a la oferta.

    Returns:
        CompareResult con score ATS, grade, listas de matches/gaps y
        recomendaciones accionables.
    """
    cv_tech = set(cv_skills.get("all_tech_flat", []))
    offer_tech = set(offer_skills.get("all_tech_flat", []))

    cv_soft = set(cv_skills.get("soft_skills", []))
    offer_soft = set(offer_skills.get("soft_skills", []))

    matching_tech = cv_tech & offer_tech
    missing_tech  = offer_tech - cv_tech
    extra_tech    = cv_tech - offer_tech

    matching_soft = cv_soft & offer_soft
    missing_soft  = offer_soft - cv_soft

    # Ponderación; max(..., 1) garantiza que no hay división por cero
    tech_score = (len(matching_tech) / max(len(offer_tech), 1)) * WEIGHT_TECH
    soft_score = (len(matching_soft) / max(len(offer_soft), 1)) * WEIGHT_SOFT
    ats_score  = round(tech_score + soft_score, 1)

    recommendations = _build_recommendations(missing_tech, missing_soft, ats_score)

    return CompareResult(
        ats_score=ats_score,
        grade=_score_to_grade(ats_score),
        matching_tech=sorted(matching_tech),
        missing_tech=sorted(missing_tech),
        extra_tech=sorted(extra_tech),
        matching_soft=sorted(matching_soft),
        missing_soft=sorted(missing_soft),
        recommendations=recommendations,
    )
