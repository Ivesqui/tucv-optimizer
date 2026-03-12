"""
infrastructure/exporters/pdf_generator.py
Genera un PDF ATS-friendly a partir de CVProfile con soporte para textos largos.
"""

from __future__ import annotations
import logging
import os
from typing import List, Optional
from app.domain.cv_model import CVProfile

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Constantes de diseño ATS
# ─────────────────────────────────────────────
MARGIN: float = 15.0
FONT_NAME: str = "DejaVu"
PHOTO_SIZE: float = 28.0
MAX_SKILLS_DISPLAY: int = 24
MAX_SOFT_SKILLS_DISPLAY: int = 10

COLOR_PRIMARY = (20, 20, 20)
COLOR_ACCENT = (30, 100, 200)
COLOR_GRAY = (100, 100, 100)
COLOR_LINE = (200, 200, 200)

_LABELS: dict[str, dict[str, str]] = {
    "es": {
        "summary": "Perfil Profesional",
        "skills": "Habilidades Técnicas",
        "soft_skills_prefix": "Soft skills",
        "experience": "Experiencia Profesional",
        "education": "Educación",
        "present": "Presente",
        "stack_prefix": "Stack",
        "study_in": "en",
    },
    "en": {
        "summary": "Professional Profile",
        "skills": "Technical Skills",
        "soft_skills_prefix": "Soft skills",
        "experience": "Work Experience",
        "education": "Education",
        "present": "Present",
        "stack_prefix": "Stack",
        "study_in": "in",
    },
}

def _sanitize_text(text: Optional[str]) -> str:
    if not text: return ""
    return text.replace("–", "-").replace("—", "-").replace("•", "-")

def _safe_join(items: List[Optional[str]], sep: str = "  ·  ") -> str:
    return sep.join(_sanitize_text(i) for i in items if i)

class ATSPDFGenerator:
    def __init__(self, profile: CVProfile, lang: str = "es") -> None:
        if not FPDF_AVAILABLE: raise ImportError("fpdf2 no instalado")
        if lang not in _LABELS: raise ValueError(f"Idioma '{lang}' no soportado")

        self.profile = profile
        self.lang = lang
        self._labels = _LABELS[lang]
        self._generated = False

        self._pdf = FPDF(format="A4")
        self._pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf", uni=True)
        self._pdf.add_font("DejaVu", "B", "fonts/DejaVuSans-Bold.ttf", uni=True)
        self._pdf.add_font("DejaVu", "I", "fonts/DejaVuSans-Oblique.ttf", uni=True)
        self._pdf.add_font("DejaVu", "BI", "fonts/DejaVuSans-BoldOblique.ttf", uni=True)

        self._pdf.set_margins(MARGIN, MARGIN, MARGIN)
        self._pdf.set_auto_page_break(auto=True, margin=MARGIN)
        self._pdf.add_page()

        self._page_width = self._pdf.w - 2 * MARGIN
        self._col_main = self._page_width * 0.70
        self._col_side = self._page_width * 0.30

    def _set_font(self, style: str = "", size: float = 10) -> None:
        self._pdf.set_font(FONT_NAME, style=style, size=size)

    def _set_color(self, rgb):
        self._pdf.set_text_color(*rgb)

    def _section_line(self, title: str):
        self._pdf.ln(3)
        self._set_font("B", 11)
        self._set_color(COLOR_ACCENT)
        self._pdf.cell(0, 6, _sanitize_text(title.upper()), new_x="LMARGIN", new_y="NEXT")
        self._pdf.set_draw_color(*COLOR_LINE)
        self._pdf.line(MARGIN, self._pdf.get_y(), self._pdf.w - MARGIN, self._pdf.get_y())
        self._pdf.ln(2)
        self._set_color(COLOR_PRIMARY)

    # ─────────────────────────────
    # Header Refactorizado (Soporta links largos)
    # ─────────────────────────────
    def _add_header(self):
        c = self.profile.contact
        photo_path: Optional[str] = getattr(self.profile, "photo_path", None)

        if photo_path and os.path.exists(photo_path):
            self._render_header_with_photo(c, photo_path)
        else:
            self._render_header_centered(c)
        self._pdf.ln(2)

    def _render_header_centered(self, c):
        self._set_font("B", 20)
        self._set_color(COLOR_PRIMARY)
        self._pdf.cell(0, 10, _sanitize_text(c.name), new_x="LMARGIN", new_y="NEXT", align="C")

        self._set_font("", 9)
        self._set_color(COLOR_GRAY)
        contact_parts = [c.email, c.phone, c.location, c.linkedin, c.github, c.portfolio]
        # Usamos multi_cell para evitar colapso si hay muchos links
        self._pdf.multi_cell(0, 5, _safe_join(contact_parts, " | "), align="C", new_x="LMARGIN", new_y="NEXT")

    def _render_header_with_photo(self, c, photo_path: str):
        text_x = MARGIN + PHOTO_SIZE + 5
        text_w = self._pdf.w - text_x - MARGIN
        y_start = self._pdf.get_y()

        try:
            self._pdf.image(photo_path, x=MARGIN, y=y_start, w=PHOTO_SIZE, h=PHOTO_SIZE)
        except Exception:
            logger.exception("No se pudo insertar foto")

        self._pdf.set_xy(text_x, y_start + 2)
        self._set_font("B", 18)
        self._set_color(COLOR_PRIMARY)
        self._pdf.cell(text_w, 8, _sanitize_text(c.name), new_x="LMARGIN", new_y="NEXT")

        self._pdf.set_x(text_x)
        self._set_font("", 9)
        self._set_color(COLOR_GRAY)

        contact_parts = [c.email, c.phone, c.location]
        self._pdf.multi_cell(text_w, 5, _safe_join(contact_parts, " | "), new_x="LMARGIN", new_y="NEXT")

        links = [c.linkedin, c.github, c.portfolio]
        if any(links):
            self._pdf.set_x(text_x)
            self._pdf.multi_cell(text_w, 5, _safe_join(links, " | "), new_x="LMARGIN", new_y="NEXT")

        if self._pdf.get_y() < y_start + PHOTO_SIZE + 2:
            self._pdf.set_y(y_start + PHOTO_SIZE + 2)

    # ─────────────────────────────
    # Secciones con multi_cell para resiliencia
    # ─────────────────────────────
    def _add_summary(self):
        if not self.profile.summary: return
        self._section_line(self._labels["summary"])
        self._set_font("", 10)
        self._pdf.multi_cell(0, 5, _sanitize_text(self.profile.summary))

    def _add_skills(self):
        if not self.profile.skills: return
        self._section_line(self._labels["skills"])
        self._set_font("", 10)

        skills_text = _safe_join(self.profile.skills[:MAX_SKILLS_DISPLAY])
        self._pdf.multi_cell(0, 5, skills_text, new_x="LMARGIN", new_y="NEXT")

        if self.profile.soft_skills:
            self._pdf.ln(1)
            self._set_font("I", 9)
            self._set_color(COLOR_GRAY)
            soft_text = f"{self._labels['soft_skills_prefix']}: {', '.join(self.profile.soft_skills[:MAX_SOFT_SKILLS_DISPLAY])}"
            self._pdf.multi_cell(0, 5, _sanitize_text(soft_text), new_x="LMARGIN", new_y="NEXT")
            self._set_color(COLOR_PRIMARY)

    def _add_experience(self):
        if not self.profile.experience: return
        self._section_line(self._labels["experience"])

        for exp in self.profile.experience:
            self._set_font("B", 10)
            self._pdf.cell(self._col_main, 5, _sanitize_text(exp.company))
            self._set_font("", 9)
            self._set_color(COLOR_GRAY)
            date_range = f"{exp.start_date} - {exp.end_date or self._labels['present']}"
            self._pdf.cell(self._col_side, 5, _sanitize_text(date_range), new_x="LMARGIN", new_y="NEXT", align="R")

            self._set_font("B", 10)
            self._set_color(COLOR_ACCENT)
            loc = f" - {exp.location}" if exp.location else ""
            self._pdf.multi_cell(0, 5, _sanitize_text(exp.position + loc), new_x="LMARGIN", new_y="NEXT")

            self._set_color(COLOR_PRIMARY)
            self._set_font("", 9.5)
            for bullet in exp.bullets:
                self._pdf.set_x(MARGIN + 5)
                self._render_bullet(bullet)

            if exp.skills_used:
                self._pdf.set_x(MARGIN + 5)
                self._render_stack(exp.skills_used)
            self._pdf.ln(2)

    def _render_bullet(self, text: str):
        self._pdf.cell(5, 5, "•", ln=0)
        self._pdf.multi_cell(0, 5, _sanitize_text(text), new_x="LMARGIN", new_y="NEXT")

    def _render_stack(self, skills: List[str]):
        self._set_font("I", 8.5)
        self._set_color(COLOR_GRAY)
        text = f"{self._labels['stack_prefix']}: {', '.join(skills)}"
        self._pdf.multi_cell(0, 4, _sanitize_text(text), new_x="LMARGIN", new_y="NEXT")
        self._set_color(COLOR_PRIMARY)

    def _add_education(self):
        if not self.profile.education: return
        self._section_line(self._labels["education"])
        for edu in self.profile.education:
            self._set_font("B", 10)
            self._pdf.cell(self._col_main, 5, _sanitize_text(edu.institution))
            self._set_font("", 9)
            self._set_color(COLOR_GRAY)
            self._pdf.cell(self._col_side, 5, _sanitize_text(f"{edu.start_date} - {edu.end_date}"), new_x="LMARGIN", new_y="NEXT", align="R")

            self._set_color(COLOR_PRIMARY)
            self._set_font("", 10)
            degree = f"{edu.degree} {self._labels['study_in']} {edu.field_of_study}" if edu.field_of_study else edu.degree
            self._pdf.multi_cell(0, 5, _sanitize_text(degree), new_x="LMARGIN", new_y="NEXT")
            self._pdf.ln(1)

    def generate(self) -> bytes:
        if self._generated: raise RuntimeError("generate() ya fue llamado")
        self._add_header()
        self._add_summary()
        self._add_skills()
        self._add_experience()
        self._add_education()
        self._generated = True
        return bytes(self._pdf.output(dest="S"))