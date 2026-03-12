import re
import random
from app.core.knowledge.db_loader import (
    VERBS_DB, METRICS_DB, WEAK_TO_STRONG_MAP_CLEAN,
    ALL_STRONG_VERBS, ALL_WEAK_VERBS, clean_text
)


def get_smart_suggestions(bullet_text: str, first_word_clean: str, has_metric: bool) -> list:
    suggestions = []
    text_normalized = clean_text(bullet_text)

    # 1. Sugerencia de Verbos con Random Sample
    if first_word_clean in WEAK_TO_STRONG_MAP_CLEAN:
        category = WEAK_TO_STRONG_MAP_CLEAN[first_word_clean]
        all_verbs = VERBS_DB.get(category, [])
        # Seleccionamos 3 aleatorios para variar la experiencia del usuario
        examples = random.sample(all_verbs, min(len(all_verbs), 3))
        suggestions.append(
            f"En lugar de '{first_word_clean}', usa verbos de {category}: {', '.join(examples)}."
        )

    # 2. Detección de Infinitivos (Ej: "Optimizar" vs "Optimicé")
    if first_word_clean.endswith(('ar', 'er', 'ir')):
        suggestions.append("Usa la primera persona del pasado (ej. 'Optimicé' en lugar de 'Optimizar').")

    # 3. Métricas Contextuales
    if not has_metric:
        for domain, data in METRICS_DB.items():
            if any(clean_text(k) in text_normalized for k in data.get("keywords", [])):
                suggestions.append(data.get("suggestion"))
                break
        else:
            suggestions.append("Agrega métricas (%, $, #) para validar este logro.")

    return suggestions


def analyze_bullet_quality(bullet: str) -> dict:
    bullet_clean = bullet.strip()
    if not bullet_clean: return {"score": 0, "issues": ["Bullet vacío"]}

    words = bullet_clean.split()
    # Primera palabra normalizada (sin tildes ni signos)
    first_word_raw = re.sub(r'[^\w]', '', words[0])
    first_word_clean = clean_text(first_word_raw)

    # Validaciones
    has_impact_verb = first_word_clean in ALL_STRONG_VERBS
    has_weak_verb = any(re.search(rf"\b{v}\b", clean_text(bullet_clean)) for v in ALL_WEAK_VERBS)

    metric_pattern = r"\d+\s*%|\d+x|\$[\d,]+|\d+\s*(usuarios|clientes|ms|segundos|peticiones|servidores)"
    has_metric = bool(re.search(metric_pattern, bullet_clean.lower()))

    issues = []
    score = 100

    if not has_impact_verb:
        issues.append(f"Inicia con un verbo de impacto (detectado: '{first_word_raw}')")
        score -= 25
    if has_weak_verb:
        issues.append("Evita verbos débiles o frases pasivas.")
        score -= 15
    if not has_metric:
        issues.append("Falta una métrica cuantificable.")
        score -= 20

    # Longitud
    length = len(bullet_clean)
    if length < 40:
        score -= 15
    elif length > 220:
        score -= 10

    return {
        "original_bullet": bullet_clean,
        "impact_score": max(0, score / 10),
        "feedback": issues if issues else ["¡Excelente bullet!"],
        "suggestions": get_smart_suggestions(bullet_clean, first_word_clean, has_metric)
    }


def analyze_experience_quality(text: str) -> dict:
    """
    Toma el bloque de texto completo del CV, lo divide en bullets
    y usa analyze_bullet_quality para cada uno.
    """
    if not text or len(text.strip()) < 5:
        return {"score_redaccion": 0, "detalles_por_bullet": [], "sugerencias": ["El CV parece estar vacío."]}

    # 1. Separar por líneas (bullets)
    bullets = [b.strip() for b in text.split('\n') if len(b.strip()) > 5]

    all_bullet_results = []
    total_impact_score = 0
    feedback_consolidado = []
    sugerencias_unificadas = []

    for b in bullets:
        analysis = analyze_bullet_quality(b)
        all_bullet_results.append(analysis)
        total_impact_score += analysis["impact_score"]

        # Si el bullet es mejorable, guardamos el feedback
        if analysis["impact_score"] < 10:
            feedback_consolidado.extend(analysis["feedback"])
            sugerencias_unificadas.extend(analysis["suggestions"])

    # Calculamos promedio sobre 100 para la UI
    avg_score = (total_impact_score / len(bullets)) * 10 if bullets else 0

    return {
        "score_redaccion": round(avg_score, 1),
        "detalles_por_bullet": all_bullet_results,
        "puntos_a_mejorar": list(set(feedback_consolidado))[:5],
        "sugerencias": list(set(sugerencias_unificadas))[:3]
    }