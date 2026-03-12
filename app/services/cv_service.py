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

from app.schemas.cv_schema import GenerateCVRequest



from app.infrastructure.nlp.skills_detector import (
    detect_skills,
    )
from app.domain.cv_model import CVProfile
from app.domain.cv_ats_engine import compare_cv_vs_offer
from app.domain.cv_optimization import optimize_cv
from app.infrastructure.exporters.pdf_generator import ATSPDFGenerator, FPDF_AVAILABLE
from app.infrastructure.exporters.html_generator import generate_html_cv


import traceback

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

class CVService:

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

    def generate_cv(self, req: GenerateCVRequest):
        try:
            cv_data_dict = req.cv_json.model_dump()
            profile = CVProfile.from_dict(cv_data_dict)
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

    def _parse_spanish_date(self, date_str: str):
        meses = {
            "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
            "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
            "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
            "ene": "01", "feb": "02", "mar": "03", "abr": "04", "may": "05", "jun": "06",
            "jul": "07", "ago": "08", "sep": "09", "oct": "10", "nov": "11", "dic": "12"
        }
        date_clean = date_str.lower().strip()
        for mes_es, mes_num in meses.items():
            if mes_es in date_clean:
                date_clean = re.sub(rf"{mes_es}\s* de?\s*", f"{mes_num}/", date_clean)
                date_clean = date_clean.replace(mes_es, f"{mes_num}/")
        return date_clean

    def _calculate_years(self, profile: CVProfile) -> str:
        if not profile.experience:
            return "0"

        total_months = 0
        now = datetime.now()

        for exp in profile.experience:
            try:
                # 1. Normalizar y parsear fecha de inicio
                start_str = self._parse_spanish_date(exp.start_date)
                # Intenta formatos comunes: 2022-01 o 01/2022
                if "-" in start_str:
                    start_dt = datetime.strptime(start_str, "%Y-%m")
                else:
                    start_dt = datetime.strptime(start_str, "%m/%Y")

                # 2. Normalizar y parsear fecha de fin
                end_str = self._parse_spanish_date(exp.end_date) if exp.end_date else "presente"

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

