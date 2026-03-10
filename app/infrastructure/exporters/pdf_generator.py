"""
infrastructure/exporters/pdf_generator.py

Genera un PDF ATS-friendly a partir de CVProfile.

Requisitos:
    pip install fpdf2

Mejoras production-ready sobre la versión original:
    - i18n: etiquetas de sección configurables por idioma
    - Logging en lugar de `except: pass` silenciosos
    - Guard contra llamadas múltiples a generate()
    - Cálculos de layout sin truncado int() innecesario
    - _safe_html eliminada (era código muerto)
    - chunk_size como constante nombrada
    - inst_col / date_col movidos al constructor (DRY)
    - Tipado completo (-> bytes, parámetros anotados)
    - Docstrings en métodos públicos y privados clave
    - Separación de responsabilidades: _render_bullet, _render_stack
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:  # pragma: no cover
    FPDF_AVAILABLE = False

from app.domain.cv_model import CVProfile

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Constantes de diseño ATS
# ─────────────────────────────────────────────

MARGIN: float = 15.0
FONT_NAME: str = "Helvetica"
PHOTO_SIZE: float = 28.0
SKILLS_CHUNK_SIZE: int = 6
MAX_SKILLS_DISPLAY: int = 24
MAX_SOFT_SKILLS_DISPLAY: int = 10

COLOR_PRIMARY = (20, 20, 20)
COLOR_ACCENT = (30, 100, 200)
COLOR_GRAY = (100, 100, 100)
COLOR_LINE = (200, 200, 200)

# ─────────────────────────────────────────────
# i18n: etiquetas de sección por idioma
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# Utilidades de módulo
# ─────────────────────────────────────────────

def _safe_join(items: List[Optional[str]], sep: str = "  ·  ") -> str:
    """Une ítems no-vacíos con el separador indicado."""
    return sep.join(i for i in items if i)


# ─────────────────────────────────────────────
# Generador PDF
# ─────────────────────────────────────────────

class ATSPDFGenerator:
    """
    Genera un CV en PDF ATS-friendly.

    Características ATS:
        ✔ Texto lineal sin columnas flotantes
        ✔ Headings claros y jerarquizados
        ✔ Sin tablas complejas
        ✔ Fuentes estándar (Helvetica)

    Args:
        profile:  Datos del candidato.
        lang:     Código de idioma para etiquetas de sección ('es' | 'en').
                  Se puede extender agregando entradas a _LABELS.

    Raises:
        ImportError:    Si fpdf2 no está instalado.
        ValueError:     Si el idioma solicitado no está soportado.
    """

    def __init__(self, profile: CVProfile, lang: str = "es") -> None:
        if not FPDF_AVAILABLE:
            raise ImportError(
                "fpdf2 no está instalado. Ejecuta: pip install fpdf2"
            )

        if lang not in _LABELS:
            raise ValueError(
                f"Idioma '{lang}' no soportado. Opciones: {list(_LABELS)}"
            )

        self.profile = profile
        self.lang = lang
        self._labels = _LABELS[lang]
        self._generated = False

        self._pdf = FPDF(format="A4")
        self._pdf.set_margins(MARGIN, MARGIN, MARGIN)
        self._pdf.set_auto_page_break(auto=True, margin=MARGIN)
        self._pdf.add_page()

        self._page_width: float = self._pdf.w - 2 * MARGIN
        self._col_main: float = self._page_width * 0.70
        self._col_side: float = self._page_width * 0.30

    # ─────────────────────────────
    # Helpers de estilo
    # ─────────────────────────────

    def _set_font(self, style: str = "", size: float = 10) -> None:
        self._pdf.set_font(FONT_NAME, style=style, size=size)

    def _set_color(self, rgb: tuple[int, int, int]) -> None:
        self._pdf.set_text_color(*rgb)

    # ─────────────────────────────
    # Sección con línea decorativa
    # ─────────────────────────────

    def _section_line(self, title: str) -> None:
        """Imprime el título de sección con subrayado en COLOR_LINE."""
        self._pdf.ln(3)
        self._set_font("B", 11)
        self._set_color(COLOR_ACCENT)
        self._pdf.cell(0, 6, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self._pdf.set_draw_color(*COLOR_LINE)
        self._pdf.line(
            MARGIN,
            self._pdf.get_y(),
            self._pdf.w - MARGIN,
            self._pdf.get_y(),
        )
        self._pdf.ln(2)
        self._set_color(COLOR_PRIMARY)

    # ─────────────────────────────
    # Header
    # ─────────────────────────────

    def _add_header(self) -> None:
        """Encabezado: nombre, datos de contacto y foto (opcional)."""
        c = self.profile.contact
        photo_path: Optional[str] = getattr(self.profile, "photo_path", None)

        if photo_path:
            if not os.path.exists(photo_path):
                logger.warning(
                    "Foto no encontrada en '%s'; se omite del PDF.", photo_path
                )
            else:
                self._render_header_with_photo(c, photo_path)
                self._pdf.ln(2)
                return

        self._render_header_centered(c)
        self._pdf.ln(2)

    def _render_header_with_photo(self, c, photo_path: str) -> None:
        text_x = MARGIN + PHOTO_SIZE + 5
        text_w = self._pdf.w - text_x - MARGIN
        y_start = self._pdf.get_y()

        try:
            self._pdf.image(
                photo_path, x=MARGIN, y=y_start, w=PHOTO_SIZE, h=PHOTO_SIZE
            )
        except Exception:
            logger.exception(
                "No se pudo insertar la foto '%s'. Se continúa sin ella.",
                photo_path,
            )

        self._pdf.set_xy(text_x, y_start + 4)
        self._set_font("B", 18)
        self._set_color(COLOR_PRIMARY)
        self._pdf.cell(text_w, 8, c.name, new_x="LMARGIN", new_y="NEXT")

        self._pdf.set_x(text_x)
        self._set_font("", 9)
        self._set_color(COLOR_GRAY)
        contact_parts = [p for p in [c.email, c.phone, c.location] if p]
        self._pdf.cell(
            text_w, 5, _safe_join(contact_parts, "  |  "),
            new_x="LMARGIN", new_y="NEXT",
        )

        links = [p for p in [c.linkedin, c.github, c.portfolio] if p]
        if links:
            self._pdf.set_x(text_x)
            self._pdf.cell(
                text_w, 5, _safe_join(links, "  |  "),
                new_x="LMARGIN", new_y="NEXT",
            )

        if self._pdf.get_y() < y_start + PHOTO_SIZE + 2:
            self._pdf.set_y(y_start + PHOTO_SIZE + 2)

    def _render_header_centered(self, c) -> None:
        self._set_font("B", 20)
        self._set_color(COLOR_PRIMARY)
        self._pdf.cell(0, 10, c.name, new_x="LMARGIN", new_y="NEXT", align="C")

        self._set_font("", 9)
        self._set_color(COLOR_GRAY)
        contact_parts = [
            c.email, c.phone, c.location, c.linkedin, c.github, c.portfolio,
        ]
        self._pdf.cell(
            0, 5, _safe_join(contact_parts, "  |  "),
            new_x="LMARGIN", new_y="NEXT", align="C",
        )

    # ─────────────────────────────
    # Resumen / Summary
    # ─────────────────────────────

    def _add_summary(self) -> None:
        if not self.profile.summary:
            return
        self._section_line(self._labels["summary"])
        self._set_font("", 10)
        self._pdf.multi_cell(self._page_width, 5, self.profile.summary)

    # ─────────────────────────────
    # Habilidades / Skills
    # ─────────────────────────────

    def _add_skills(self) -> None:
        if not self.profile.skills:
            return

        self._section_line(self._labels["skills"])
        self._set_font("", 10)

        skills = self.profile.skills[:MAX_SKILLS_DISPLAY]
        chunks = [
            skills[i: i + SKILLS_CHUNK_SIZE]
            for i in range(0, len(skills), SKILLS_CHUNK_SIZE)
        ]
        for chunk in chunks:
            self._pdf.cell(0, 5, _safe_join(chunk), new_x="LMARGIN", new_y="NEXT")

        if self.profile.soft_skills:
            prefix = self._labels["soft_skills_prefix"]
            self._set_font("I", 9)
            self._set_color(COLOR_GRAY)
            self._pdf.cell(
                0,
                5,
                f"{prefix}: " + _safe_join(
                    self.profile.soft_skills[:MAX_SOFT_SKILLS_DISPLAY]
                ),
                new_x="LMARGIN",
                new_y="NEXT",
            )
            self._set_color(COLOR_PRIMARY)

        self._pdf.ln(1)

    # ─────────────────────────────
    # Experiencia / Experience
    # ─────────────────────────────

    def _add_experience(self) -> None:
        if not self.profile.experience:
            return

        self._section_line(self._labels["experience"])

        for exp in self.profile.experience:
            present_label = self._labels["present"]
            date_range = f"{exp.start_date} – {exp.end_date or present_label}"

            # Empresa + fecha en la misma línea
            self._set_font("B", 10)
            self._set_color(COLOR_PRIMARY)
            self._pdf.cell(self._col_main, 5, exp.company)

            self._set_font("", 9)
            self._set_color(COLOR_GRAY)
            self._pdf.cell(
                self._col_side, 5, date_range,
                new_x="LMARGIN", new_y="NEXT", align="R",
            )

            # Cargo + ubicación
            self._set_font("B", 10)
            self._set_color(COLOR_ACCENT)
            loc_suffix = f"  —  {exp.location}" if exp.location else ""
            self._pdf.cell(
                0, 5, exp.position + loc_suffix,
                new_x="LMARGIN", new_y="NEXT",
            )

            self._set_color(COLOR_PRIMARY)

            # Bullets
            self._set_font("", 9.5)
            for bullet in exp.bullets:
                self._render_bullet(bullet)

            # Stack
            if exp.skills_used:
                self._render_stack(exp.skills_used)

            self._pdf.ln(2)

    def _render_bullet(self, text: str) -> None:
        self._pdf.cell(5, 5, "\u2022")
        self._pdf.multi_cell(self._page_width - 5, 5, text)

    def _render_stack(self, skills: List[str]) -> None:
        prefix = self._labels["stack_prefix"]
        self._set_font("I", 8.5)
        self._set_color(COLOR_GRAY)
        self._pdf.cell(
            0, 4, f"{prefix}: " + ", ".join(skills),
            new_x="LMARGIN", new_y="NEXT",
        )
        self._set_color(COLOR_PRIMARY)

    # ─────────────────────────────
    # Educación / Education
    # ─────────────────────────────

    def _add_education(self) -> None:
        if not self.profile.education:
            return

        self._section_line(self._labels["education"])

        for edu in self.profile.education:
            # Institución + fecha
            self._set_font("B", 10)
            self._set_color(COLOR_PRIMARY)
            self._pdf.cell(self._col_main, 5, edu.institution)

            self._set_font("", 9)
            self._set_color(COLOR_GRAY)
            self._pdf.cell(
                self._col_side,
                5,
                f"{edu.start_date} – {edu.end_date}",
                new_x="LMARGIN",
                new_y="NEXT",
                align="R",
            )

            # Título
            self._set_color(COLOR_PRIMARY)
            self._set_font("", 10)
            study_in = self._labels["study_in"]
            degree_line = (
                f"{edu.degree} {study_in} {edu.field_of_study}"
                if edu.field_of_study
                else edu.degree
            )
            self._pdf.cell(0, 5, degree_line, new_x="LMARGIN", new_y="NEXT")
            self._pdf.ln(1)

    # ─────────────────────────────
    # Punto de entrada público
    # ─────────────────────────────

    def generate(self) -> bytes:
        """
        Renderiza el PDF y devuelve los bytes resultantes.

        Raises:
            RuntimeError: Si se llama más de una vez sobre la misma instancia.
                          Para regenerar, crea una nueva instancia de ATSPDFGenerator.
        """
        if self._generated:
            raise RuntimeError(
                "generate() ya fue llamado. Crea una nueva instancia para "
                "regenerar el PDF."
            )

        self._add_header()
        self._add_summary()
        self._add_skills()
        self._add_experience()
        self._add_education()

        self._generated = True
        return bytes(self._pdf.output())
