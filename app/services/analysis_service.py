from app.domain.cv_model import CVProfile
from app.domain.cv_analysis import analyze_bullet_quality
from app.infrastructure.nlp.skills_detector import (
    compare_cv_vs_offer,
    detect_skills,
    analyze_experience_quality,
    AnalysisResponse)
from fastapi import HTTPException
from app.schemas.analysis_schema import (
    AnalyzeOfferRequest,
    BulletQualityRequest
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
        offer_skills = detect_skills(req.offer_text)

        # Preparamos el contenedor con tipos explícitos para evitar el warning
        result: dict[str, any] = {
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
            cv_skills = detect_skills(cv_text)

            # 3. Cruzar datos (ATS Match)
            comparison = compare_cv_vs_offer(cv_skills, offer_skills)

            # 4. Calidad de redacción (Nueva lógica de verbos)
            writing_advice = analyze_experience_quality(cv_text)

            # 5. Construcción del Contrato de Respuesta
            # Usamos dict() para asegurar que sea serializable sin problemas
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

        # Retornamos el diccionario completo.
        # FastAPI se encarga de convertirlo a JSON automáticamente.
        return result

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

    def analyze_bullets(self, req: BulletQualityRequest):
        results = []
        for bullet in req.bullets:
            quality = analyze_bullet_quality(bullet)
            results.append({"bullet": bullet, **quality})
        avg_score = sum(r["score"] for r in results) / max(len(results), 1)
        return {"results": results, "average_score": round(avg_score, 1)}





