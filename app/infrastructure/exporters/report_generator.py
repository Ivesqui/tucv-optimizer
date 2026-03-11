def generate_analysis_report_html(analysis_data: dict) -> str:
    """
    Genera una interfaz de DASHBOARD para que el usuario vea
    qué debe corregir ANTES de generar su PDF final.
    """
    score = analysis_data["writing_advice"]["score_redaccion"]
    sugerencias = analysis_data["writing_advice"]["sugerencias"]
    missing = analysis_data["match_details"]["missing_tech"]

    return f"""
    <div class="analysis-container">
        <h2>Diagnóstico de tu CV</h2>
        <div class="score-card">Fuerza de Redacción: {score}%</div>

        <div class="alert-box">
            <h3>Palabras que te faltan para el ATS:</h3>
            <p>{", ".join(missing)}</p>
        </div>

        <div class="tips-box">
            <h3>Consejos de Verbos de Acción:</h3>
            <ul>{"".join(f"<li>{s}</li>" for s in sugerencias)}</ul>
        </div>
    </div>
    """