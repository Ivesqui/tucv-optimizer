from app.infrastructure.nlp.skills_detector import detect_skills
from app.domain.cv_ats_engine import compare_cv_vs_offer
from app.domain.cv_analysis import analyze_experience_quality

# 1. Simulamos una oferta y un CV
oferta_texto = "Buscamos desarrollador Python con experiencia en FastAPI y PostgreSQL. Soft skills: Liderazgo."
cv_texto = "Desarrollador Backend Senior. Optimicé el mantenimiento de 15 bases de datos PostgreSQL reduciendo la latencia en un 20%. Lideré el despliegue de microservicios usando Python y fastapi."

print("🚀 Iniciando prueba de TuCv-Optimizer...")

# 2. Probar el Músculo (Detección)
print("\n--- PASO 1: Detección ---")
oferta_data = detect_skills(oferta_texto)
cv_data = detect_skills(cv_texto)
print(f"Skills en Oferta: {oferta_data['all_tech_flat']}")
print(f"Skills en CV: {cv_data['all_tech_flat']}")

# 3. Probar el Cerebro (ATS Match)
print("\n--- PASO 2: Match ATS ---")
resultado_ats = compare_cv_vs_offer(cv_data, oferta_data)
print(f"Score: {resultado_ats['ats_score']} | Grado: {resultado_ats['grade']}")
print(f"Faltan: {resultado_ats['missing_tech']}")

# 4. Probar la Redacción (Verbos/JSON)
print("\n--- PASO 3: Redacción ---")
redaccion = analyze_experience_quality(cv_texto)
print(f"Score Redacción: {redaccion['score_redaccion']}")
print(f"Sugerencias: {redaccion['sugerencias']}")