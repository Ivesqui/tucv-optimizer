from app.domain.cv_model import CVProfile


def generate_html_cv(profile: CVProfile, photo_base64: str = "") -> str:

    c = profile.contact

    # FOTO
    photo_html = ""
    if photo_base64:
        photo_html = f"""
        <div style="text-align:center;margin-bottom:10px">
            <img src="{photo_base64}" style="width:110px;height:110px;border-radius:50%;object-fit:cover">
        </div>
        """

    # SKILLS
    skills = " · ".join(profile.skills)

    # SOFT SKILLS
    soft_skills = ""
    if profile.soft_skills:
        soft_skills = f"""
        <p class="soft">
        Soft skills: {" · ".join(profile.soft_skills)}
        </p>
        """

    # LANGUAGES
    languages_html = ""
    if profile.languages:
        languages_html = f"""
        <section>
        <h2>Idiomas</h2>
        <p>{" · ".join(profile.languages)}</p>
        </section>
        """

    # EXPERIENCE
    experience_html = ""

    for exp in profile.experience:

        bullets = "".join(f"<li>{b}</li>" for b in exp.bullets if b)

        experience_html += f"""
        <div class="entry">

            <div class="row">
                <span class="org">{exp.company}</span>
                <span class="date">{exp.start_date} – {exp.end_date or "Presente"}</span>
            </div>

            <div class="role">{exp.position}</div>

            <ul>
            {bullets}
            </ul>

        </div>
        """

        # EDUCATION
        education_html = ""
        for edu in profile.education:
            # Añadimos la lógica para mostrar el campo de estudio si existe
            estudios = f" en {edu.field_of_study}" if edu.field_of_study else ""

            education_html += f"""
            <div class="entry">
                <div class="row">
                    <span class="org">{edu.institution}</span>
                    <span class="date">{edu.start_date} – {edu.end_date}</span>
                </div>
                <div class="role">{edu.degree}{estudios}</div>
            </div>
            """

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">

<title>CV - {c.name}</title>

<style>

body{{
font-family:Arial,sans-serif;
font-size:10.5pt;
max-width:800px;
margin:0 auto;
padding:30px 40px;
color:#111;
line-height:1.5
}}

h1{{
font-size:22pt;
margin-bottom:4px;
text-align:center
}}

.contact{{
font-size:9pt;
color:#555;
margin-bottom:14px;
text-align:center
}}

h2{{
font-size:11pt;
text-transform:uppercase;
letter-spacing:.06em;
color:#1a4db3;
border-bottom:1px solid #ccc;
padding-bottom:2px;
margin:14px 0 8px
}}

.entry{{
margin-bottom:10px
}}

.row{{
display:flex;
justify-content:space-between;
align-items:center
}}

.org{{
font-weight:bold
}}

.date{{
font-size:9pt;
color:#555
}}

.role{{
color:#1a4db3;
font-weight:bold;
margin:2px 0
}}

ul{{
padding-left:14px;
margin:4px 0
}}

li{{
margin-bottom:2px
}}

.soft{{
font-style:italic;
font-size:9pt;
color:#555
}}

@media print{{
body{{padding:15px 20px}}
.entry{{page-break-inside:avoid}}
}}

</style>

</head>

<body>

{photo_html}

<h1>{c.name}</h1>

<div class="contact">
{c.email} | {c.phone} | {c.location} | {c.linkedin} | {c.github}
</div>


<section>

<h2>Perfil Profesional</h2>

<p>{profile.summary}</p>

</section>


<section>

<h2>Habilidades Técnicas</h2>

<p>{skills}</p>

{soft_skills}

</section>


<section>

<h2>Experiencia</h2>

{experience_html}

</section>


<section>

<h2>Educación</h2>

{education_html}

</section>

{languages_html}

</body>
</html>
"""

    return html