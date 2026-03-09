"""
skills_detector.py
Detecta habilidades técnicas y blandas de una oferta laboral
usando diccionarios curados + regex. Sin IA externa.
"""

import re
from collections import Counter

# ─── Diccionarios de skills por categoría ────────────────────────────────────

TECH_SKILLS = {
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
        "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins", "github actions",
        "gitlab ci", "circleci", "travis ci", "helm", "prometheus", "grafana",
        "nginx", "apache", "linux", "unix",
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
        "microservices", "monorepo", "solid", "design patterns", "clean architecture",
        "ddd", "event driven",
    ],
}

SOFT_SKILLS = [
    "comunicación", "liderazgo", "trabajo en equipo", "resolución de problemas",
    "pensamiento crítico", "adaptabilidad", "creatividad", "gestión del tiempo",
    "proactividad", "autonomía", "orientación a resultados", "colaboración",
    "communication", "leadership", "teamwork", "problem solving", "critical thinking",
    "adaptability", "creativity", "time management", "proactive", "autonomous",
    "results oriented", "collaboration", "analytical", "detail oriented",
    "fast learner", "self motivated",
]

EXPERIENCE_PATTERNS = [
    r"(\d+)\+?\s*años?\s*de\s*experiencia",
    r"(\d+)\+?\s*years?\s*of\s*experience",
    r"experiencia\s*de\s*(\d+)\+?\s*años?",
    r"(\d+)\+?\s*yrs?\s*experience",
    r"minimum\s*(\d+)\s*years?",
    r"mínimo\s*(\d+)\s*años?",
]

EDUCATION_KEYWORDS = [
    "licenciatura", "ingeniería", "bachelor", "máster", "master", "mba",
    "doctorado", "phd", "técnico", "tecnólogo", "certificación", "certification",
    "bootcamp", "university", "universidad",
]

SENIORITY_MAP = {
    "junior": ["junior", "jr", "entry level", "entry-level", "trainee", "intern", "practicante"],
    "mid": ["mid", "semi senior", "semi-senior", "ssr", "intermediate", "associate"],
    "senior": ["senior", "sr", "lead", "staff", "principal", "architect", "tech lead"],
    "manager": ["manager", "head", "director", "vp", "chief", "cto", "cpo"],
}


def _clean_text(text: str) -> str:
    return text.lower().strip()


def detect_skills(text: str) -> dict:
    """
    Analiza un texto (oferta laboral o CV) y retorna todas las skills detectadas.
    """
    clean = _clean_text(text)

    found_tech = {}
    for category, skills in TECH_SKILLS.items():
        matches = []
        for skill in skills:
            # word boundary para evitar falsos positivos
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, clean):
                matches.append(skill)
        if matches:
            found_tech[category] = matches

    found_soft = [s for s in SOFT_SKILLS if re.search(r"\b" + re.escape(s) + r"\b", clean)]

    # Años de experiencia requeridos
    years_required = None
    for pat in EXPERIENCE_PATTERNS:
        m = re.search(pat, clean)
        if m:
            years_required = int(m.group(1))
            break

    # Nivel de seniority
    seniority = None
    for level, keywords in SENIORITY_MAP.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\b", clean) for kw in keywords):
            seniority = level
            break

    # Educación
    education = [kw for kw in EDUCATION_KEYWORDS if kw in clean]

    # Todas las skills técnicas como lista plana
    all_tech_flat = [s for skills in found_tech.values() for s in skills]

    return {
        "tech_skills": found_tech,
        "soft_skills": found_soft,
        "all_tech_flat": all_tech_flat,
        "years_required": years_required,
        "seniority": seniority,
        "education_keywords": education,
        "total_skills_found": len(all_tech_flat) + len(found_soft),
    }


def compare_cv_vs_offer(cv_skills: dict, offer_skills: dict) -> dict:
    """
    Compara las skills del CV vs la oferta y calcula el ATS score.
    """
    cv_tech = set(cv_skills.get("all_tech_flat", []))
    offer_tech = set(offer_skills.get("all_tech_flat", []))

    cv_soft = set(cv_skills.get("soft_skills", []))
    offer_soft = set(offer_skills.get("soft_skills", []))

    matching_tech = cv_tech & offer_tech
    missing_tech = offer_tech - cv_tech
    extra_tech = cv_tech - offer_tech

    matching_soft = cv_soft & offer_soft
    missing_soft = offer_soft - cv_soft

    # ATS Score: ponderado (tech 70%, soft 30%)
    tech_score = (len(matching_tech) / max(len(offer_tech), 1)) * 70
    soft_score = (len(matching_soft) / max(len(offer_soft), 1)) * 30
    ats_score = round(tech_score + soft_score, 1)

    # Recomendaciones automáticas
    recommendations = []
    if missing_tech:
        top_missing = list(missing_tech)[:5]
        recommendations.append(f"Agrega estas skills al CV: {', '.join(top_missing)}")
    if missing_soft:
        recommendations.append(f"Menciona estas soft skills: {', '.join(list(missing_soft)[:3])}")
    if ats_score < 40:
        recommendations.append("⚠️ Score bajo. Personaliza el CV para esta oferta específica.")
    elif ats_score < 65:
        recommendations.append("📈 Score medio. Incorpora más keywords de la oferta.")
    else:
        recommendations.append("✅ Buen match. Asegura que el CV use las mismas palabras exactas de la oferta.")

    return {
        "ats_score": ats_score,
        "matching_tech": list(matching_tech),
        "missing_tech": list(missing_tech),
        "extra_tech": list(extra_tech),
        "matching_soft": list(matching_soft),
        "missing_soft": list(missing_soft),
        "recommendations": recommendations,
        "grade": _score_to_grade(ats_score),
    }


def _score_to_grade(score: float) -> str:
    if score >= 80:
        return "A"
    elif score >= 65:
        return "B"
    elif score >= 50:
        return "C"
    elif score >= 35:
        return "D"
    return "F"
