from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.schemas.cv_schema import (
    AnalyzeOfferRequest,
    GenerateCVRequest,
    BulletQualityRequest
)

from app.infrastructure.nlp.skills_detector import detect_skills, compare_cv_vs_offer
from app.models.cv_model import CVProfile, optimize_cv, analyze_bullet_quality
from app.infrastructure.exporters.pdf_generator import ATSPDFGenerator, generate_html_cv, FPDF_AVAILABLE

router = APIRouter(prefix="/cv", tags=["CV"])

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

def _calculate_years(profile: CVProfile) -> str:
    if not profile.experience:
        return "0"
    # Aproximación simple
    return str(len(profile.experience) * 2) + "+"

# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def root():
    """Sirve la UI."""
    ui_path = Path(__file__).parent.parent / "ui" / "index.html"
    if ui_path.exists():
        return HTMLResponse(ui_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>CV Optimizer API ✅</h1><p>Ver /docs para la API.</p>")


@router.post("/analyze-offer")
async def analyze_offer(req: AnalyzeOfferRequest):
    """
    Analiza una oferta laboral y extrae skills, seniority, experiencia requerida.
    Si se pasa cv_json, calcula el ATS score y recomienda mejoras.
    """
    if not req.offer_text.strip():
        raise HTTPException(400, "offer_text no puede estar vacío")

    offer_skills = detect_skills(req.offer_text)
    result = {"offer_skills": offer_skills}

    if req.cv_json:
        try:
            profile = CVProfile.from_dict(req.cv_json)
        except Exception as e:
            raise HTTPException(400, f"cv_json inválido: {e}")
        cv_text = profile.to_plain_text()
        cv_skills = detect_skills(cv_text)
        comparison = compare_cv_vs_offer(cv_skills, offer_skills)
        result["cv_skills"] = cv_skills
        result["comparison"] = comparison

    return JSONResponse(result)


@router.post("/generate-cv")
async def generate_cv(req: GenerateCVRequest):
    """
    Genera el CV en el formato solicitado (html, pdf, json).
    Si se pasa offer_text + optimize=True, optimiza el CV antes de generar.
    """
    try:
        profile = CVProfile.from_dict(req.cv_json)
    except Exception as e:
        raise HTTPException(400, f"cv_json inválido: {e}")

    optimization_notes = {}

    # Optimización automática si hay oferta
    if req.offer_text and req.optimize:
        offer_skills = detect_skills(req.offer_text)
        cv_text = profile.to_plain_text()
        cv_skills = detect_skills(cv_text)
        comparison = compare_cv_vs_offer(cv_skills, offer_skills)
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
        }

    # Generar output
    if req.format == "json":
        return JSONResponse({
            "cv": profile.to_dict(),
            "optimization": optimization_notes,
        })

    elif req.format == "html":
        html = generate_html_cv(profile, photo_base64=req.photo_base64 or "")
        filename = f"cv_{profile.contact.name.replace(' ', '_')}.html"
        output_path = OUTPUT_DIR / filename
        output_path.write_text(html, encoding="utf-8")
        return JSONResponse({
            "html": html,
            "filename": filename,
            "optimization": optimization_notes,
        })

    elif req.format == "pdf":
        if not FPDF_AVAILABLE:
            raise HTTPException(500, "fpdf2 no instalado. Ejecuta: pip install fpdf2")
        filename = f"cv_{profile.contact.name.replace(' ', '_')}.pdf"
        output_path = str(OUTPUT_DIR / filename)

        # Guardar foto temporal si existe
        photo_tmp = None
        if req.photo_base64:
            import base64, tempfile
            try:
                header, b64data = req.photo_base64.split(",", 1)
                ext = "jpg" if "jpeg" in header else "png"
                img_bytes = base64.b64decode(b64data)
                photo_tmp = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False)
                photo_tmp.write(img_bytes)
                photo_tmp.close()
                profile.photo_path = photo_tmp.name
            except Exception:
                pass

        try:
            gen = ATSPDFGenerator(profile)
            gen.generate(output_path)
        except Exception as e:
            raise HTTPException(500, f"Error generando PDF: {e}")
        finally:
            if photo_tmp:
                import os as _os
                try: _os.unlink(photo_tmp.name)
                except: pass

        return FileResponse(output_path, media_type="application/pdf", filename=filename)

    raise HTTPException(400, "format debe ser: html | pdf | json")


@router.post("/analyze-bullets")
async def analyze_bullets(req: BulletQualityRequest):
    """Evalúa la calidad de los bullets del CV."""
    results = []
    for bullet in req.bullets:
        quality = analyze_bullet_quality(bullet)
        results.append({"bullet": bullet, **quality})
    avg_score = sum(r["score"] for r in results) / max(len(results), 1)
    return {"results": results, "average_score": round(avg_score, 1)}


@router.get("/export-json/{filename}")
async def export_json(filename: str):
    """Descarga el JSON del CV guardado."""
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Archivo no encontrado")
    return FileResponse(str(path), media_type="application/json", filename=filename)


@router.get("/linkedin-autofill")
async def linkedin_autofill_format(cv_json: str):
    """
    Retorna el CV en formato estructurado listo para autofill en formularios.
    Incluye campos mapeados a los formularios de LinkedIn, HiringRoom, Workday.
    """
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
            "field": latest_edu.field if latest_edu else "",
            "end_date": latest_edu.end_date if latest_edu else "",
        },
        "skills_text": ", ".join(profile.skills[:15]),
        "summary": profile.summary,
        "experience_years": _calculate_years(profile),
    })
