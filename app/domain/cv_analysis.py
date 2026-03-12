import re
from app.infrastructure.nlp.skills_detector import (
    _weak_verbs_raw,
    _verbs_raw)

def analyze_bullet_quality(bullet: str) -> dict:
    """Evalúa la calidad de un bullet point usando los diccionarios cargados."""
    issues = []
    score = 100

    # Extraemos las listas planas de los diccionarios
    all_strong_verbs = []
    for category in _verbs_raw.values():
        all_strong_verbs.extend([v.lower() for v in category])

    all_weak_verbs = [v.lower() for v in _weak_verbs_raw.get("verbos_debiles", [])]

    words = bullet.strip().split()
    if not words:
        return {"score": 0, "issues": ["Bullet vacío"]}

    # Verificación de verbos
    first_word = words[0].lower()
    has_impact_verb = first_word in all_strong_verbs
    has_weak_verb = any(v in bullet.lower() for v in all_weak_verbs)

    if not has_impact_verb:
        issues.append("Usa un verbo de impacto al inicio (Desarrollé, Implementé, Optimicé...)")
        score -= 20

    if has_weak_verb:
        issues.append("Evita verbos débiles. Sé más directo.")
        score -= 15

    # Métricas y Longitud (Tu lógica original está perfecta)
    if not bool(re.search(r"\d+\s*%|\d+x|\$[\d,]+|\d+\s*(usuarios|clientes|ms)", bullet.lower())):
        issues.append("Agrega métricas cuantificables.")
        score -= 20

    if len(bullet) < 40:
        issues.append("Bullet muy corto.")
        score -= 15
    elif len(bullet) > 200:
        issues.append("Bullet muy largo.")
        score -= 10

    return {
        "original_bullet": bullet,
        "impact_score": score / 10,  # Convertimos 100 base a 10.0 base
        "feedback": " | ".join(issues) if issues else "¡Excelente bullet!",
        "suggestions": ["Prueba usar métricas", "Empieza con un verbo"] if not has_metric else []
    }

