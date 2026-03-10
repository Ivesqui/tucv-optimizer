"""
pdf_generator.py
Genera un PDF ATS-friendly a partir del CVProfile.
Usa ReportLab o fpdf2 si está disponible, o genera HTML→PDF como fallback.

Ejecutar: pip install fpdf2
"""

import os

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

from app.models.cv_model import CVProfile


# ─── Constantes de diseño ATS ────────────────────────────────────────────────

MARGIN = 15          # mm
FONT_NAME = "Helvetica"
COLOR_PRIMARY = (20, 20, 20)
COLOR_ACCENT = (30, 100, 200)
COLOR_GRAY = (100, 100, 100)
COLOR_LINE = (200, 200, 200)


class ATSPDFGenerator:
    """
    Genera CV en PDF con formato ATS-compatible:
    - Sin tablas complejas (los parsers ATS las odian)
    - Sin columnas múltiples
    - Texto lineal, headings claros
    - Fuente estándar
    """

    def __init__(self, profile: CVProfile):
        self.profile = profile
        if not FPDF_AVAILABLE:
            raise ImportError("Instala fpdf2: pip install fpdf2")
        self.pdf = FPDF(format="A4")
        self.pdf.set_margins(MARGIN, MARGIN, MARGIN)
        self.pdf.set_auto_page_break(auto=True, margin=MARGIN)
        self.pdf.add_page()
        self.page_width = int(self.pdf.w - 2 * MARGIN)
        self.col_main = int(self.page_width * 0.7)
        self.col_side = int(self.page_width * 0.3)

    def _set_font(self, style="", size=10):
        self.pdf.set_font(FONT_NAME, style=style, size=size)

    def _set_color(self, rgb):
        self.pdf.set_text_color(*rgb)

    def _section_line(self, title: str):
        """Encabezado de sección con línea separadora."""
        self.pdf.ln(3)
        self._set_font("B", 11)
        self._set_color(COLOR_ACCENT)
        self.pdf.cell(0, 6, title.upper(), ln=True)
        self.pdf.set_draw_color(*COLOR_LINE)
        self.pdf.line(MARGIN, self.pdf.get_y(), self.pdf.w - MARGIN, self.pdf.get_y())
        self.pdf.ln(2)
        self._set_color(COLOR_PRIMARY)

    def _add_header(self):
        c = self.profile.contact
        photo_path = getattr(self.profile, 'photo_path', None)

        if photo_path and os.path.exists(photo_path):
            # Layout con foto: foto a la izquierda, datos a la derecha
            PHOTO_SIZE = 28  # mm
            TEXT_X = MARGIN + PHOTO_SIZE + 5
            TEXT_W = int(self.pdf.w - TEXT_X - MARGIN)

            # Foto circular (fpdf2 no tiene clip oval nativo, usamos imagen cuadrada)
            try:
                self.pdf.image(photo_path, x=MARGIN, y=self.pdf.get_y(), w=PHOTO_SIZE, h=PHOTO_SIZE)
            except Exception:
                pass  # Si falla la imagen, continúa sin foto

            y_start = self.pdf.get_y()
            self.pdf.set_xy(TEXT_X, y_start + 4)
            self._set_font("B", 18)
            self._set_color(COLOR_PRIMARY)
            self.pdf.cell(TEXT_W, 8, c.name, ln=True)

            self.pdf.set_x(TEXT_X)
            self._set_font("", 9)
            self._set_color(COLOR_GRAY)
            contact_parts = [p for p in [c.email, c.phone, c.location] if p]
            self.pdf.cell(TEXT_W, 5, "  |  ".join(contact_parts), ln=True)

            if c.linkedin or c.github or c.portfolio:
                self.pdf.set_x(TEXT_X)
                links = [p for p in [c.linkedin, c.github, c.portfolio] if p]
                self.pdf.cell(TEXT_W, 5, "  |  ".join(links), ln=True)

            # Asegurar que continuamos debajo de la foto
            if self.pdf.get_y() < y_start + PHOTO_SIZE + 2:
                self.pdf.set_y(y_start + PHOTO_SIZE + 2)
        else:
            # Layout clásico centrado sin foto
            self._set_font("B", 20)
            self._set_color(COLOR_PRIMARY)
            self.pdf.cell(0, 10, c.name, ln=True, align="C")

            self._set_font("", 9)
            self._set_color(COLOR_GRAY)
            contact_parts = [p for p in [c.email, c.phone, c.location] if p]
            if c.linkedin:
                contact_parts.append(c.linkedin)
            if c.github:
                contact_parts.append(c.github)
            if c.portfolio:
                contact_parts.append(c.portfolio)
            self.pdf.cell(0, 5, "  |  ".join(contact_parts), ln=True, align="C")

        self.pdf.ln(2)

    def _add_summary(self):
        if not self.profile.summary:
            return
        self._section_line("Perfil Profesional")
        self._set_font("", 10)
        self._set_color(COLOR_PRIMARY)
        self.pdf.multi_cell(self.page_width, 5, self.profile.summary)
        self.pdf.ln(1)

    def _add_skills(self):
        if not self.profile.skills:
            return
        self._section_line("Habilidades Técnicas")
        self._set_font("", 10)
        # Agrupar en líneas de max 6 skills
        chunk_size = 6
        chunks = [self.profile.skills[i:i+chunk_size] for i in range(0, len(self.profile.skills), chunk_size)]
        for chunk in chunks:
            self.pdf.cell(0, 5, "  ·  ".join(chunk), ln=True)
        if self.profile.soft_skills:
            self._set_font("I", 9)
            self._set_color(COLOR_GRAY)
            self.pdf.cell(0, 5, "Soft skills: " + "  ·  ".join(self.profile.soft_skills), ln=True)
            self._set_color(COLOR_PRIMARY)
        self.pdf.ln(1)

    def _add_experience(self):
        if not self.profile.experience:
            return
        self._section_line("Experiencia Profesional")
        for exp in self.profile.experience:
            # Empresa + fechas
            self._set_font("B", 10)
            date_range = f"{exp.start_date} – {exp.end_date or 'Presente'}"
            self.pdf.cell(self.col_main, 5, exp.company, ln=False)
            self._set_font("", 9)
            self._set_color(COLOR_GRAY)
            self.pdf.cell(self.col_side, 5, date_range, ln=True, align="R")

            # Cargo
            self._set_font("B", 10)
            self._set_color(COLOR_ACCENT)
            loc = f"  —  {exp.location}" if exp.location else ""
            self.pdf.cell(0, 5, exp.position + loc, ln=True)
            self._set_color(COLOR_PRIMARY)

            # Bullets
            self._set_font("", 9.5)
            for bullet in exp.bullets:
                self.pdf.cell(5, 5, "•", ln=False)
                self.pdf.multi_cell(int(self.page_width - 5), 5, bullet)

            # Skills usadas
            if exp.skills_used:
                self._set_font("I", 8.5)
                self._set_color(COLOR_GRAY)
                self.pdf.cell(0, 4, "Stack: " + ", ".join(exp.skills_used), ln=True)
                self._set_color(COLOR_PRIMARY)

            self.pdf.ln(2)

    def _add_education(self):
        if not self.profile.education:
            return
        self._section_line("Educación")
        for edu in self.profile.education:
            self._set_font("B", 10)
            inst_col = int(self.page_width * 0.7)
            date_col = int(self.page_width * 0.3)
            self.pdf.cell(inst_col, 5, edu.institution, ln=False)
            self._set_font("", 9)
            self._set_color(COLOR_GRAY)
            self.pdf.cell(date_col, 5, f"{edu.start_date} – {edu.end_date}", ln=True, align="R")
            self._set_color(COLOR_PRIMARY)
            self._set_font("", 10)
            degree_line = f"{edu.degree}" + (f" en {edu.field_of_study}" if edu.field_of_study else "")
            self.pdf.cell(0, 5, degree_line, ln=True)
            self.pdf.ln(1)

    def _add_projects(self):
        if not self.profile.projects:
            return
        self._section_line("Proyectos Destacados")
        for proj in self.profile.projects:
            self._set_font("B", 10)
            self.pdf.cell(0, 5, proj.name, ln=True)
            self._set_font("", 9.5)
            self.pdf.multi_cell(int(self.page_width), 5, proj.description)
            if proj.tech_stack:
                self._set_font("I", 8.5)
                self._set_color(COLOR_GRAY)
                self.pdf.cell(0, 4, "Tech: " + ", ".join(proj.tech_stack), ln=True)
                self._set_color(COLOR_PRIMARY)
            for h in proj.highlights:
                self._set_font("", 9)
                self.pdf.cell(5, 4, "•", ln=False)
                self.pdf.multi_cell(int(self.page_width - 5), 4, h)
            if proj.url:
                self._set_font("", 8.5)
                self._set_color(COLOR_ACCENT)
                self.pdf.cell(0, 4, proj.url, ln=True)
                self._set_color(COLOR_PRIMARY)
            self.pdf.ln(2)

    def _add_certifications(self):
        if not self.profile.certifications:
            return
        self._section_line("Certificaciones")
        for cert in self.profile.certifications:
            self._set_font("", 10)
            line = f"{cert.name}  —  {cert.issuer}"
            if cert.date:
                line += f"  ({cert.date})"
            self.pdf.cell(0, 5, line, ln=True)
        self.pdf.ln(1)

    def _add_languages(self):
        if not self.profile.languages:
            return
        self._section_line("Idiomas")
        self._set_font("", 10)
        self.pdf.cell(0, 5, "  ·  ".join(self.profile.languages), ln=True)

    def generate(self) -> bytes:
        """Genera el PDF y devuelve los bytes."""
        self._add_header()
        self._add_summary()
        self._add_skills()
        self._add_experience()
        self._add_projects()
        self._add_education()
        self._add_certifications()
        self._add_languages()
        return bytes(self.pdf.output())


# ─── Fallback: HTML ATS ──────────────────────────────────────────────────────

def generate_html_cv(profile: CVProfile, photo_base64: str = "") -> str:
    """
    Genera un CV en HTML limpio, ATS-friendly y bien formateado.
    photo_base64: imagen en base64 (data:image/jpeg;base64,...)
    Puede imprimirse como PDF desde el navegador (Ctrl+P).
    """
    c = profile.contact
    contact_parts = [p for p in [c.email, c.phone, c.location, c.linkedin, c.github, c.portfolio] if p]

    exp_html = ""
    for exp in profile.experience:
        bullets_html = "".join(f"<li>{b}</li>" for b in exp.bullets)
        stack = f'<div class="stack">Stack: {", ".join(exp.skills_used)}</div>' if exp.skills_used else ""
        exp_html += f"""
        <div class="entry">
          <div class="entry-header">
            <span class="org">{exp.company}</span>
            <span class="date">{exp.start_date} – {exp.end_date or "Presente"}</span>
          </div>
          <div class="role">{exp.position}{" — " + exp.location if exp.location else ""}</div>
          <ul>{bullets_html}</ul>
          {stack}
        </div>"""

    proj_html = ""
    for proj in profile.projects:
        highlights = "".join(f"<li>{h}</li>" for h in proj.highlights)
        tech = f'<div class="stack">Tech: {", ".join(proj.tech_stack)}</div>' if proj.tech_stack else ""
        url = f'<div class="stack"><a href="{proj.url}">{proj.url}</a></div>' if proj.url else ""
        proj_html += f"""
        <div class="entry">
          <div class="role">{proj.name}</div>
          <p>{proj.description}</p>
          {tech}
          <ul>{highlights}</ul>
          {url}
        </div>"""

    edu_html = ""
    for edu in profile.education:
        degree = f"{edu.degree}" + (f" en {edu.field_of_study}" if edu.field_of_study else "")
        edu_html += f"""
        <div class="entry">
          <div class="entry-header">
            <span class="org">{edu.institution}</span>
            <span class="date">{edu.start_date} – {edu.end_date}</span>
          </div>
          <div class="role">{degree}</div>
        </div>"""

    cert_html = ""
    for cert in profile.certifications:
        cert_html += f'<div class="cert">{cert.name} — {cert.issuer} ({cert.date})</div>'

    skills_str = "  ·  ".join(profile.skills or [])
    soft_str = "  ·  ".join(profile.soft_skills or [])
    langs_str = "  ·  ".join(profile.languages or [])

    summary_section = f'<section><h2>Perfil Profesional</h2><p>{profile.summary}</p></section>' if profile.summary else ""
    proj_section = f'<section><h2>Proyectos Destacados</h2>{proj_html}</section>' if proj_html else ""
    cert_section = f'<section><h2>Certificaciones</h2>{cert_html}</section>' if cert_html else ""
    lang_section = f'<section><h2>Idiomas</h2><p>{langs_str}</p></section>' if langs_str else ""

    photo_html = ""
    if photo_base64:
        photo_html = f'<img src="{photo_base64}" class="photo" alt="Foto de perfil">'

    photo_header_style = ""
    if photo_base64:
        photo_header_style = """
  .header-wrap { display: flex; align-items: center; gap: 20px; margin-bottom: 14px; }
  .photo { width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 2px solid #ddd; flex-shrink: 0; }
  .header-text { flex: 1; }
  .header-text h1 { text-align: left; }
  .contact-line { text-align: left; }
"""
    else:
        photo_header_style = """
  .header-wrap { margin-bottom: 14px; }
"""

    header_block = f"""
  <div class="header-wrap">
    {photo_html}
    <div class="header-text">
      <h1>{c.name}</h1>
      <div class="contact-line">{" &nbsp;|&nbsp; ".join(contact_parts)}</div>
    </div>
  </div>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>CV - {c.name}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&family=Source+Sans+3:wght@400;600&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Source Sans 3', Arial, sans-serif;
    font-size: 10.5pt;
    color: #111;
    max-width: 800px;
    margin: 0 auto;
    padding: 30px 40px;
    line-height: 1.5;
  }}
  h1 {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 22pt; }}
  .contact-line {{ font-size: 9pt; color: #555; margin: 4px 0 0; }}
  h2 {{
    font-size: 10.5pt; text-transform: uppercase; letter-spacing: 0.08em;
    color: #1a4db3; border-bottom: 1px solid #ccc;
    padding-bottom: 2px; margin: 14px 0 8px;
  }}
  .entry {{ margin-bottom: 10px; }}
  .entry-header {{ display: flex; justify-content: space-between; }}
  .org {{ font-weight: 600; }}
  .date {{ font-size: 9pt; color: #555; }}
  .role {{ font-weight: 600; color: #1a4db3; margin: 1px 0; }}
  ul {{ padding-left: 14px; margin: 4px 0; }}
  li {{ margin-bottom: 2px; }}
  .stack {{ font-size: 9pt; color: #555; font-style: italic; margin-top: 2px; }}
  .cert {{ margin-bottom: 3px; }}
  {photo_header_style}
  @media print {{
    body {{ padding: 15px 20px; }}
    h2 {{ page-break-after: avoid; }}
    .entry {{ page-break-inside: avoid; }}
    .photo {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}
</style>
</head>
<body>
  {header_block}
  {summary_section}
  <section>
    <h2>Habilidades Técnicas</h2>
    <p>{skills_str}</p>
    {"<p class='stack'>Soft skills: " + soft_str + "</p>" if soft_str else ""}
  </section>
  <section><h2>Experiencia Profesional</h2>{exp_html}</section>
  {proj_section}
  <section><h2>Educación</h2>{edu_html}</section>
  {cert_section}
  {lang_section}
</body>
</html>"""
