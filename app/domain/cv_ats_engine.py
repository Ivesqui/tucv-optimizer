from typing import TypedDict

# Reglas de negocio (Ponderaciones)
WEIGHT_TECH = 70.0
WEIGHT_SOFT = 30.0

class CompareResult(TypedDict):
    ats_score: float
    grade: str
    matching_tech: list[str]
    missing_tech: list[str]
    matching_soft: list[str]
    missing_soft: list[str]
    recommendations: list[str]

def _score_to_grade(score: float) -> str:
    """Convierte el puntaje numérico en una letra (Regla de negocio)."""
    if score >= 80: return "A"
    if score >= 65: return "B"
    if score >= 50: return "C"
    if score >= 35: return "D"
    return "F"

def compare_cv_vs_offer(cv_raw: dict, offer_raw: dict) -> CompareResult:
    """Calcula el match matemático entre el CV y la Vacante."""
    cv_tech = set(cv_raw["all_tech_flat"])
    offer_tech = set(offer_raw["all_tech_flat"])
    cv_soft = set(cv_raw["soft_skills"])
    offer_soft = set(offer_raw["soft_skills"])

    matching_tech = cv_tech & offer_tech
    missing_tech = offer_tech - cv_tech
    matching_soft = cv_soft & offer_soft
    missing_soft = offer_soft - cv_soft

    # Cálculo del Score
    t_score = (len(matching_tech) / max(len(offer_tech), 1)) * WEIGHT_TECH
    s_score = (len(matching_soft) / max(len(offer_soft), 1)) * WEIGHT_SOFT
    ats_score = round(t_score + s_score, 1)

    # Generar recomendaciones
    recs = []
    if missing_tech:
        recs.append(f"Agrega estas skills técnicas: {', '.join(list(missing_tech)[:5])}")
    if ats_score < 65:
        recs.append("📈 Tu score es bajo, intenta incluir más palabras clave de la oferta.")

    return {
        "ats_score": ats_score,
        "grade": _score_to_grade(ats_score),
        "matching_tech": sorted(list(matching_tech)),
        "missing_tech": sorted(list(missing_tech)),
        "matching_soft": sorted(list(matching_soft)),
        "missing_soft": sorted(list(missing_soft)),
        "recommendations": recs
    }