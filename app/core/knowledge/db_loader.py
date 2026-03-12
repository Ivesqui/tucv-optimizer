import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_DIR = BASE_DIR / "core" / "knowledge"

def clean_text(text):
    """Normaliza texto: minúsculas y quita tildes."""
    if not text: return ""
    trans_tab = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    return text.lower().strip().translate(trans_tab)

def load_json(file_name):
    path = KNOWLEDGE_DIR / file_name
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _compile_pattern(term: str):
    """
    Crea un patrón de búsqueda exacto.
    Protege términos con puntos (como .NET) evitando que se detecten dentro de otros (como VB.NET).
    """
    term_norm = re.escape(term.lower())
    # El lookbehind (?<![\w.]) asegura que no haya letras ni puntos antes
    # El lookahead (?![\w.]) asegura que no haya letras ni puntos después
    return re.compile(rf"(?<![\w.]){term_norm}(?![a-zA-Z0-9])", re.IGNORECASE)

# --- CARGA Y PROCESAMIENTO ---
VERBS_DB = load_json("action_verbs_db.json")
METRICS_DB = load_json("metrics_db.json")
WEAK_VERBS_DB = load_json("weak_verbs_db.json")
WEAK_TO_STRONG_MAP = load_json("weak_to_strong_map.json")
_tech_raw = load_json("skills_db.json")
_soft_raw = load_json("soft_skills_db.json")
_rules_raw = load_json("rules_db.json")

WEAK_TO_STRONG_MAP_CLEAN = {clean_text(k): v for k, v in WEAK_TO_STRONG_MAP.items()}
ALL_STRONG_VERBS = [clean_text(v) for sublist in VERBS_DB.values() for v in sublist]
ALL_WEAK_VERBS = [clean_text(v) for v in WEAK_VERBS_DB.get("verbos_debiles", [])]

_TECH_PATTERNS = {
    cat: [(skill, _compile_pattern(skill)) for skill in skills]
    for cat, skills in _tech_raw.items()
}

_all_soft_list = [s for sublist in _soft_raw.values() for s in sublist]
_SOFT_PATTERNS = [(s, _compile_pattern(s)) for s in _all_soft_list]

_EXPERIENCE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _rules_raw.get("experience_patterns", [])]

_SENIORITY_PATTERNS = {
    lvl: [(kw, _compile_pattern(kw)) for kw in kws]
    for lvl, kws in _rules_raw.get("seniority_map", {}).items()
}

_EDUCATION_KEYWORDS = _rules_raw.get("education_keywords", [])