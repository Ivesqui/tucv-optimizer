# cv_service.py
from pathlib import Path
import base64
import tempfile
import os
from io import BytesIO
from datetime import datetime
import uuid
from fastapi import HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import unicodedata
import re

from app.schemas.cv_schema import (
    AnalyzeOfferRequest,
    GenerateCVRequest,
    BulletQualityRequest,
)

from app.infrastructure.nlp.skills_detector import (
    detect_skills,
    compare_cv_vs_offer,
    analyze_experience_quality,
    AnalysisResponse)
from app.domain.cv_model import CVProfile, optimize_cv, analyze_bullet_quality
from app.infrastructure.exporters.pdf_generator import ATSPDFGenerator, FPDF_AVAILABLE
from app.infrastructure.exporters.html_generator import generate_html_cv


import traceback

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

class CVService:

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

    def load_cv_from_file(self, filename: str) -> CVProfile | None:
        """
        Carga un CV previamente guardado en OUTPUT_DIR como JSON y devuelve un CVProfile.
        """
        if "/" in filename or ".." in filename:
            raise HTTPException(400, "Nombre de archivo inválido")

        path = OUTPUT_DIR / filename
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
            profile = CVProfile.from_json(content)
            return profile
        except Exception as e:
            raise HTTPException(500, f"No se pudo cargar el CV: {e}")

    # ───────────────────────────────
    # Generate CV
    # ───────────────────────────────

    def generate_cv(self, req: GenerateCVRequest):
        try:
            profile = CVProfile.from_dict(req.cv_json)
        except Exception as e:
            raise HTTPException(400, f"cv_json inválido: {e}")

        optimization_notes = {}

        # 1. OPTIMIZACIÓN GLOBAL (Afecta a JSON, HTML y PDF por igual)
        if req.offer_text and req.optimize:
            offer_skills = detect_skills(req.offer_text)
            cv_text = profile.to_plain_text()
            cv_skills = detect_skills(cv_text)
            comparison = compare_cv_vs_offer(cv_skills, offer_skills)

            # Aquí 'profile' se transforma (Verbos + Skills)
            profile, promoted, suggested_soft = optimize_cv(
                profile,
                comparison["missing_tech"],
                comparison["missing_soft"],
            )

            optimization_notes = {
                "ats_score_before": comparison["ats_score"],
                "skills_promoted": promoted,
                "soft_skills_suggested": suggested_soft,
                "recommendations": comparison["recommendations"],
                "narrative_improved": True  # Indicador de que se mejoraron verbos
            }

        # 2. SELECCIÓN DE FORMATO

        # ─ JSON ─
        if req.format == "json":
            return JSONResponse({"cv": profile.to_dict(), "optimization": optimization_notes})

        # ─ HTML ─
        if req.format == "html":
            # Usa el profile ya optimizado
            safe_name = self.slugify_safe(profile.contact.name)
            filename = f"cv_{safe_name}.html"
            html_content = generate_html_cv(profile, photo_base64=req.photo_base64 or "")
            buffer = BytesIO(html_content.encode("utf-8"))

            return StreamingResponse(buffer, media_type="text/html",
                                     headers={"Content-Disposition": f"attachment; filename={filename}"})

        # ─ PDF ─
        if req.format == "pdf":
            if not FPDF_AVAILABLE:
                raise HTTPException(500, "fpdf2 no instalado")

            request_id = str(uuid.uuid4())[:8]
            safe_name = self.slugify_safe(profile.contact.name)[:15]  # Corto para que no sea un link gigante
            filename = f"cv_{request_id}_{safe_name}.pdf"

            # Manejo de Foto (Temporal)
            photo_tmp = None
            if req.photo_base64:
                try:
                    header, b64data = req.photo_base64.split(",", 1)
                    ext = "jpg" if "jpeg" in header else "png"
                    img_bytes = base64.b64decode(b64data)
                    photo_tmp = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False)
                    photo_tmp.write(img_bytes)
                    photo_tmp.close()
                    profile.photo_path = photo_tmp.name  # Inyectamos la ruta para el PDF
                except Exception:
                    pass

            try:
                # IMPORTANTE: Aquí pasamos el 'profile' que ya pasó por optimize_cv
                pdf_bytes = ATSPDFGenerator(profile).generate()
                buffer = BytesIO(pdf_bytes)
            except Exception as e:
                traceback.print_exc()
                raise HTTPException(500, f"Error generando PDF: {e}")
            finally:
                if photo_tmp:
                    try:
                        os.unlink(photo_tmp.name)
                    except Exception:
                        pass

            return StreamingResponse(
                buffer,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        raise HTTPException(400, "format debe ser: html | pdf | json")
    # ───────────────────────────────
    # Analyze Bullets
    # ───────────────────────────────
    def analyze_bullets(self, req: BulletQualityRequest):
        results = []
        for bullet in req.bullets:
            quality = analyze_bullet_quality(bullet)
            results.append({"bullet": bullet, **quality})
        avg_score = sum(r["score"] for r in results) / max(len(results), 1)
        return {"results": results, "average_score": round(avg_score, 1)}

    # ───────────────────────────────
    # Export JSON
    # ───────────────────────────────
    def export_json(self, filename: str):
        if "/" in filename or ".." in filename:
            raise HTTPException(400, "Nombre de archivo inválido")

        path = OUTPUT_DIR / filename
        if not path.exists():
            raise HTTPException(404, "Archivo no encontrado")

        return FileResponse(str(path), media_type="application/json", filename=filename)

    # ───────────────────────────────
    # LinkedIn Autofill
    # ───────────────────────────────
    def linkedin_autofill(self, cv_json: str):
        try:
            profile = CVProfile.from_json(cv_json)
        except Exception as e:
            raise HTTPException(400, str(e))

        c = profile.contact
        latest_exp = profile.experience[0] if profile.experience else None
        latest_edu = profile.education[0] if profile.education else None

        return JSONResponse({
            "# LinkedIn / HiringRoom Autofill": "Copia estos campos en el formulario",
            "personal": {
                "first_name": c.name.split()[0] if c.name else "",
                "last_name": " ".join(c.name.split()[1:]) if c.name else "",
                "email": c.email,
                "phone": c.phone,
                "location": c.location,
                "linkedin_url": c.linkedin,
                "portfolio_url": c.portfolio,
            },
            "current_role": {
                "title": latest_exp.position if latest_exp else "",
                "company": latest_exp.company if latest_exp else "",
                "start_date": latest_exp.start_date if latest_exp else "",
            },
            "education": {
                "school": latest_edu.institution if latest_edu else "",
                "degree": latest_edu.degree if latest_edu else "",
                "field": latest_edu.field_of_study if latest_edu else "",
                "end_date": latest_edu.end_date if latest_edu else "",
            },
            "skills_text": ", ".join(profile.skills[:15]),
            "summary": profile.summary,
            "experience_years": self._calculate_years(profile),
        })

    # ───────────────────────────────
    # Helper
    # ───────────────────────────────
    def _calculate_years(self, profile: CVProfile) -> str:
        if not profile.experience:
            return "0"

        total_months = 0
        now = datetime.now()

        for exp in profile.experience:
            try:
                # 1. Normalizar y parsear fecha de inicio
                start_str = exp.start_date.strip().lower()
                # Intenta formatos comunes: 2022-01 o 01/2022
                if "-" in start_str:
                    start_dt = datetime.strptime(start_str, "%Y-%m")
                else:
                    start_dt = datetime.strptime(start_str, "%m/%Y")

                # 2. Normalizar y parsear fecha de fin
                end_str = exp.end_date.strip().lower() if exp.end_date else "presente"

                if any(x in end_str for x in ["presente", "actual", "present"]):
                    end_dt = now
                elif "-" in end_str:
                    end_dt = datetime.strptime(end_str, "%Y-%m")
                else:
                    end_dt = datetime.strptime(end_str, "%m/%Y")

                # 3. Calcular diferencia en meses
                diff = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
                if diff > 0:
                    total_months += diff
            except Exception:
                # Si el formato no coincide, ignoramos ese bloque para no romper la app
                continue

        years = total_months // 12
        months = total_months % 12

        if years == 0:
            return f"{months} meses"
        return f"{years}.{months // 1} años"

    def slugify_safe(self, text: str) -> str: # Añadido 'self'
        """ Transforma 'Christian Estupiñán' -> 'christian_estupinan' """
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'[^\w\s-]', '', text).strip().lower()
        return re.sub(r'[-\s]+', '_', text)
