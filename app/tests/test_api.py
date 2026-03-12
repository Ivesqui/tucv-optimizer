import requests
import json
import time
from pathlib import Path

# Configuración
BASE_URL = "http://127.0.0.1:8000/api/cv/generate-cv"
OUTPUT_DIR = Path("test_results")
OUTPUT_DIR.mkdir(exist_ok=True)

# Payload enriquecido (el que definimos antes)
PAYLOAD = {
    "offer_text": """
        Buscamos un Software Architecture Lead con más de 10 años de experiencia. 
        Experto en Python (FastAPI/Django), diseño de microservicios con Docker y Kubernetes. 
        Indispensable experiencia en Cloud (AWS/Azure) y CI/CD robusto. 
        Buscamos liderazgo técnico, capacidad de mentoría y gestión de stakeholders.
        Deseable experiencia en el sector bancario o financiero.
    """,
    "optimize": True,
    "format": "pdf",
    "cv_json": {
        "contact": {
            "name": "Christian Estupiñán",
            "email": "christian.pro@example.com",
            "phone": "+593 99 999 9999",
            "location": "Quito, Ecuador",
            "linkedin": "https://linkedin.com/in/christian-senior-dev"
        },
        "summary": "Ingeniero de Software con una década de experiencia construyendo sistemas escalables. He pasado por muchas empresas y siempre hice mi mejor esfuerzo liderando equipos. Me gusta mucho Python y quiero mejorar en Kubernetes.",
        "experience": [
            {
                "company": "Banco Internacional S.A.",
                "position": "Senior Backend Developer / Tech Lead",
                "start_date": "Enero 2021",
                "end_date": "Presente",
                "bullets": [
                    "Hice la migración de un sistema monolítico a microservicios usando Python y FastAPI.",
                    "Me encargué de liderar un equipo de 5 desarrolladores y hice las revisiones de código.",
                    "Reduje el tiempo de respuesta de las transacciones en un 30% optimizando PostgreSQL.",
                    "Implementé el flujo de CI/CD con GitHub Actions para despliegues automáticos."
                ],
                "skills_used": ["Python", "FastAPI", "PostgreSQL", "Docker", "GitHub Actions"]
            },
            {
                "company": "Ecuador Tech Corp",
                "position": "Software Engineer II",
                "start_date": "Marzo 2017",
                "end_date": "Diciembre 2020",
                "bullets": [
                    "Hice el mantenimiento de una plataforma legacy escrita en Django.",
                    "Me encargué de la integración con pasarelas de pago de terceros.",
                    "Ayudé a mejorar la base de datos para manejar 100k usuarios activos.",
                    "Hice scripts en Python para automatizar tareas administrativas."
                ],
                "skills_used": ["Python", "Django", "SQL", "Linux", "AWS"]
            },
            {
                "company": "Desarrollos Rápidos S.A.",
                "position": "Junior & Middle Developer",
                "start_date": "Junio 2014",
                "end_date": "Febrero 2017",
                "bullets": [
                    "Hice aplicaciones web simples con JavaScript y Python.",
                    "Me encargué de corregir bugs reportados por los clientes.",
                    "Hice reportes en Excel y bases de datos SQL para contabilidad."
                ],
                "skills_used": ["JavaScript", "Python", "SQL", "Git"]
            }
        ],
        "education": [
            {
                "institution": "Escuela Politécnica Nacional",
                "degree": "Ingeniería en Sistemas",
                "field_of_study": "Ingeniería de Software",
                "start_date": "2009",
                "end_date": "2014"
            }
        ],
        "skills": ["Python", "SQL", "Git", "PostgreSQL", "FastAPI", "Docker", "AWS", "Linux", "Django", "JavaScript"],
        "soft_skills": [
            "Comunicación efectiva",
            "Resolución de conflictos",
            "Mentoría",
            "Pensamiento analítico",
            "Gestión de tiempo",
            "Liderazgo de equipos"
        ]
    }
}


def run_test(format_type: str):
    print(f"\n--- 🧪 PROBANDO FORMATO: {format_type.upper()} ---")

    current_payload = PAYLOAD.copy()
    current_payload["format"] = format_type

    start_time = time.time()
    try:
        response = requests.post(BASE_URL, json=current_payload)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            print(f"✅ Respuesta recibida en {elapsed:.2f}s")

            if format_type == "json":
                data = response.json()
                # --- VALIDACIONES DE TESIS ---
                opt = data.get("optimization", {})
                print(f"📊 Score ATS Inicial: {opt.get('ats_score_before')}")
                print(f"🛠️ Skills Promocionadas: {opt.get('skills_promoted')}")
                print(f"💡 Soft Skills Sugeridas: {opt.get('soft_skills_suggested')}")

                # Guardar el JSON para inspección
                with open(OUTPUT_DIR / "result_debug.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

            else:
                # Guardar PDF/HTML
                content_disposition = response.headers.get("Content-Disposition")
                filename = content_disposition.split("filename=")[
                    1] if content_disposition else f"cv_test.{format_type}"
                file_path = OUTPUT_DIR / filename

                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"📂 Archivo guardado en: {file_path}")

        else:
            print(f"❌ Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"🔥 Error crítico: {e}")


if __name__ == "__main__":
    print("🚀 INICIANDO BATERÍA DE PRUEBAS DE INTEGRACIÓN")
    # Primero probamos JSON para ver las tripas de la optimización
    run_test("json")
    # Luego generamos el PDF final
    run_test("pdf")
    print("\n✨ Pruebas finalizadas. Revisa la carpeta 'test_results'.")