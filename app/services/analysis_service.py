from typing import Any, cast
from app.domain.cv_model import CVProfile
from app.domain.cv_analysis import analyze_bullet_quality, analyze_experience_quality
from app.infrastructure.nlp.skills_detector import detect_skills
from app.domain.cv_ats_engine import compare_cv_vs_offer
from fastapi import HTTPException
from app.schemas.analysis_schema import (
    AnalyzeOfferRequest,
    BulletQualityRequest,
    AnalysisResponse
)

class AnalysisService:
    # ───────────────────────────────
    # Analyze Offer
    # ───────────────────────────────
    def analyze_offer(self, req: AnalyzeOfferRequest):
        """
        Analiza la oferta y realiza el diagnóstico completo (ATS + Redacción).
        """
        if not req.offer_text.strip():
            raise HTTPException(400, "offer_text no puede estar vacío")

        # 1. Procesar Oferta
        # detect_skills retorna RawDetectionResult; casteamos a dict para compatibilidad
        offer_skills = cast(dict[str, Any], detect_skills(req.offer_text))

        result: dict[str, Any] = {
            "offer_skills": offer_skills,
            "cv_analysis": None
        }

        if req.cv_json:
            try:
                profile = CVProfile.from_dict(req.cv_json)
            except Exception as e:
                raise HTTPException(400, f"cv_json inválido: {e}")

            # 2. Procesar CV
            cv_text = profile.to_plain_text()
            cv_skills = cast(dict[str, Any], detect_skills(cv_text))

            # 3. Cruzar datos (ATS Match)
            comparison = cast(dict[str, Any], compare_cv_vs_offer(cv_skills, offer_skills))

            # 4. Calidad de redacción (Nueva lógica de verbos)
            writing_advice = analyze_experience_quality(cv_text)

            # 5. Construcción del Contrato de Respuesta
            analysis_payload: AnalysisResponse = {
                "match_details": comparison,
                "skills_detected": cv_skills,
                "writing_advice": writing_advice,
                "meta": {
                    "engine_version": "2.0-universal",
                    "industry_detected": next(iter(cv_skills.get("tech_skills", {}).keys()), "General")
                }
            }

            result["cv_analysis"] = analysis_payload

        return result

    def get_full_cv_analysis(self, cv_text: str, offer_text: str) -> AnalysisResponse:
        """
        Analiza calidad y match ATS en un solo paso.
        """
        # 1. Detectar skills en ambos textos
        cv_data = cast(dict[str, Any], detect_skills(cv_text))
        offer_data = cast(dict[str, Any], detect_skills(offer_text))

        # 2. Comparar CV vs Oferta (ATS Match)
        comparison = cast(dict[str, Any], compare_cv_vs_offer(cv_data, offer_data))

        # 3. Analizar calidad de redacción (Verbos)
        writing_quality = analyze_experience_quality(cv_text)

        # 4. Unir todo en un solo objeto según el esquema
        return {
            "match_details": comparison,
            "skills_detected": cv_data,
            "writing_advice": writing_quality,
            "meta": {
                "engine_version": "2.0-universal",
                "industry_detected": list(cv_data.get("tech_skills", {}).keys())[0] if cv_data.get("tech_skills") else "General"
            }
        }

    def analyze_bullets(self, req: BulletQualityRequest):
        """
        Analiza una lista de bullets individuales.
        """
        results = []
        for bullet in req.bullets:
            quality = analyze_bullet_quality(bullet)
            results.append({
                "bullet": bullet,
                "score": quality["impact_score"],
                **{k: v for k, v in quality.items() if k != "impact_score"}
            })

        avg_score = sum(r["score"] for r in results) / max(len(results), 1)
        return {"results": results, "average_score": round(avg_score, 1)}




