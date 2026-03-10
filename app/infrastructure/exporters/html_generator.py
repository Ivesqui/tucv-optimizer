from app.domain.cv_model import CVProfile


def generate_html_cv(profile: CVProfile, photo_base64: str = "") -> str:
    """
    Genera una versión HTML simple del CV.
    Pensada para preview web o exportación.
    """

    c = profile.contact

    photo_html = ""
    if photo_base64:
        photo_html = f"""
        <img src="{photo_base64}" 
             style="width:120px;height:120px;border-radius:50%;object-fit:cover;">
        """

    skills = ", ".join(profile.skills)

    experience_html = ""
    for exp in profile.experience:
        bullets = "".join(f"<li>{b}</li>" for b in exp.bullets)

        experience_html += f"""
        <div style="margin-bottom:15px">
            <strong>{exp.position}</strong> — {exp.company}<br>
            <small>{exp.start_date} - {exp.end_date or "Present"}</small>
            <ul>
                {bullets}
            </ul>
        </div>
        """

    education_html = ""
    for edu in profile.education:
        education_html += f"""
        <div>
            <strong>{edu.degree}</strong> - {edu.institution}<br>
            <small>{edu.start_date} - {edu.end_date}</small>
        </div>
        """

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{c.name} CV</title>
    </head>

    <body style="font-family:Arial;max-width:800px;margin:auto">

        <div style="display:flex;gap:20px;align-items:center">
            {photo_html}

            <div>
                <h1>{c.name}</h1>
                <p>
                {c.email} | {c.phone} | {c.location}<br>
                {c.linkedin}
                </p>
            </div>
        </div>

        <hr>

        <h2>Summary</h2>
        <p>{profile.summary}</p>

        <h2>Skills</h2>
        <p>{skills}</p>

        <h2>Experience</h2>
        {experience_html}

        <h2>Education</h2>
        {education_html}

    </body>
    </html>
    """

    return html