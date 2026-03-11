from app.infrastructure.nlp.skills_detector import compare_cv_vs_offer, detect_skills, analyze_experience_quality, \
    AnalysisResponse


def get_full_cv_analysis(cv_text: str, offer_text: str) -> AnalysisResponse:
    # 1. Detectar skills en ambos textos
    cv_data = detect_skills(cv_text)
    offer_data = detect_skills(offer_text)

    # 2. Comparar CV vs Oferta (ATS Match)
    comparison = compare_cv_vs_offer(cv_data, offer_data)

    # 3. Analizar calidad de redacción (Verbos)
    writing_quality = analyze_experience_quality(cv_text)

    # 4. Unir todo en un solo objeto JSON
    return {
        "match_details": comparison,
        "skills_detected": cv_data,
        "writing_advice": writing_quality,
        "meta": {
            "engine_version": "2.0-universal",
            "industry_detected": list(cv_data["tech_skills"].keys())[0] if cv_data["tech_skills"] else "General"
        }
    }