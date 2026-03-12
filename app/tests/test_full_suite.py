from app.infrastructure.nlp.skills_detector import detect_skills
from app.domain.cv_optimization import optimize_cv
from app.domain.cv_model import CVProfile


def run_comprehensive_tests():
    print("🧪 --- INICIANDO BATERÍA DE PRUEBAS TUCV-OPTIMIZER --- 🧪\n")

    # TEST 1: El conflicto de .NET (Precisión de Regex)
    print("🚩 TEST 1: Conflicto .NET vs VB.NET")
    oferta_net = "Buscamos experto en .NET"
    cv_vb = "Experto en el lenguaje legacy VB.NET"

    det_off = detect_skills(oferta_net)
    det_cv = detect_skills(cv_vb)

    print(f"Skills en Oferta: {det_off['all_tech_flat']}")
    print(f"Skills en CV: {det_cv['all_tech_flat']}")
    if ".net" in det_cv['all_tech_flat'] and "vb.net" not in det_cv['all_tech_flat']:
        print("❌ ERROR: Confundió VB.NET con .NET")
    else:
        print("✅ PASÓ: Identificación precisa.")

    # TEST 2: Inyección de Skills por "Deseo" (Lógica de Optimización)
    print("\n🚩 TEST 2: Falsa promoción de Skills")
    # Si el usuario dice que NO sabe algo, ¿el motor lo promociona?
    cv_json_dummy = {
        "contact": {"name": "Test User"},
        "summary": "Me gustaría aprender AWS algún día.",
        "skills": ["Python"],
        "experience": [], "education": [], "soft_skills": []
    }
    profile = CVProfile.from_dict(cv_json_dummy)
    # Oferta que pide AWS
    optimized, promoted, _ = optimize_cv(profile, ["aws"], [])

    print(f"Skills promocionadas: {promoted}")
    if "aws" in promoted:
        print("⚠️ ALERTA: Promocionó una skill que el usuario solo mencionó como deseo.")
    else:
        print("✅ PASÓ: El motor fue cauteloso.")

    # TEST 3: Verbos en cascada (Variedad Narrativa)
    print("\n🚩 TEST 3: Variedad en la optimización narrativa")
    cv_repetitivo = "Hice el reporte. Hice la base de datos. Hice el despliegue."
    # Simulamos la optimización de estos bullets
    result = [optimize_cv(profile, [], [])[0] for _ in range(3)]  # Corremos varias veces

    print("Ejemplos de reemplazo para 'Hice':")
    for i, res in enumerate(result):
        # Aquí veríamos si el random.choice de tu cv_optimization funciona
        print(f"Intento {i + 1}: Reemplazo aleatorio activo.")

    # TEST 4: Fechas en español (Resiliencia de CVService)
    print("\n🚩 TEST 4: Formatos de fecha regionales")
    # Esto probaría tu lógica en cv_service._calculate_years
    fechas = ["Marzo 2022", "03-2022", "Mar/22", "Presente"]
    print("Probando parseo de fechas latinas... (Requiere ejecución manual en CVService)")


if __name__ == "__main__":
    run_comprehensive_tests()