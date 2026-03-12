from app.infrastructure.nlp.skills_detector import detect_skills
from app.domain.cv_ats_engine import compare_cv_vs_offer
from app.domain.cv_analysis import analyze_experience_quality


def run_stress_tests():
    print("🧪 INICIANDO STRESS TEST DE TUCV-OPTIMIZER\n")

    # --- CASO 1: El CV "Vago" (Poca información) ---
    print("🚩 CASO 1: CV con muy poco contenido")
    cv_vago = "Hago cosas en la computadora. Uso Python."
    res_vago = analyze_experience_quality(cv_vago)
    print(f"Score Redacción: {res_vago['score_redaccion']} (Esperado: Bajo)")
    print(f"Sugerencias: {res_vago['sugerencias'][:2]}\n")

    # --- CASO 2: El CV de un "Super Senior" (Detección de experiencia) ---
    print("🚩 CASO 2: Detección de Seniority y Años")
    oferta_sr = "Buscamos Lead Developer con 8 años de experiencia en AWS."
    cv_sr = "Soy Senior Developer con 10 años de experiencia liderando equipos en AWS y Docker."

    det_oferta = detect_skills(oferta_sr)
    det_cv = detect_skills(cv_sr)

    print(f"Años detectados en oferta: {det_oferta.get('years_required')}")
    print(f"Seniority detectado en CV: {det_cv.get('seniority')}\n")

    # --- CASO 3: Mix de Idiomas y Caracteres (Normalización) ---
    print("🚩 CASO 3: Resiliencia a caracteres y formato")
    cv_sucio = """
    * OPTIMICÉ (con tilde) procesos de CI/CD...
    - Desarrollo en C#, .NET y Node.js!!!
    - Manejo de bases de datos (PostgreSQL/MongoDB).
    """
    det_sucio = detect_skills(cv_sucio)
    print(f"Skills detectadas en texto sucio: {det_sucio['all_tech_flat']}\n")

    # --- CASO 4: Match Perfecto vs Match Nulo ---
    print("🚩 CASO 4: Comparación de extremos")
    oferta_tech = "Java, Spring Boot, Microservicios"
    cv_python = "Python, FastAPI, Django"

    match = compare_cv_vs_offer(detect_skills(cv_python), detect_skills(oferta_tech))
    print(f"Score entre Python y Java: {match['ats_score']}% (Esperado: 0 o muy bajo)")


if __name__ == "__main__":
    run_stress_tests()