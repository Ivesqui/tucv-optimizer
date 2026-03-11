import requests
import json

# Configuración
ENDPOINT = "http://127.0.0.1:8000/api/cv/generate-cv"

# Datos de prueba con "errores" (verbos débiles y falta de skills)
payload = {
    "offer_text": "Buscamos desarrollador con experiencia en Python y FastAPI.",
    "optimize": True,
    "format": "pdf",  # Puedes cambiar a "json" o "html"
    "cv_json": {
        "contact": {
            "name": "Christian Estupiñán",
            "email": "christian@example.com"
        },
        "summary": "Soy desarrollador y hice varias cosas.",
        "experience": [
            {
                "company": "Tech Ecuador",
                "position": "Junior Dev",
                "start_date": "2023-01",
                "end_date": "presente",
                "bullets": [
                    "Hice una aplicación simple.",
                    "Me encargué de la base de datos."
                ],
                "skills_used": ["Python"]
            }
        ],
        "skills": ["Python"],
        "soft_skills": []
    }
}


def test_optimization():
    print(f"🚀 Enviando petición a {ENDPOINT}...")
    try:
        response = requests.post(ENDPOINT, json=payload)

        if response.status_code == 200:
            # Extraer el nombre del archivo del header
            content_disposition = response.headers.get("Content-Disposition")
            filename = content_disposition.split("filename=")[1] if content_disposition else "cv_descargado.pdf"

            print(f"✅ ¡Éxito! Archivo generado: {filename}")

            # Guardar el archivo localmente para revisar
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"📂 El archivo se ha guardado en tu carpeta actual.")

        else:
            print(f"❌ Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"🔥 Error de conexión: {e}")


if __name__ == "__main__":
    test_optimization()