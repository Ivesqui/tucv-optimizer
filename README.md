# 🚀 TuCV Optimizer (CV Optimizer — ATS Pro)

**TuCV Optimizer** es un motor local-first diseñado para transformar CVs genéricos en herramientas de alto impacto para procesos de selección. Utiliza análisis de datos y reglas de reclutamiento (ATS) para optimizar la narrativa y el emparejamiento técnico sin depender de APIs externas costosas.

> **Filosofía:** Privacidad total y cero costos recurrentes. Todo el poder del NLP mediante diccionarios curados, motores de reglas locales y una arquitectura limpia.

---

## ✨ Novedades de la Versión 2.0 (Marzo 2026)

* **Refactorización Narrativa Inteligente:** Motor que detecta verbos débiles (*hice, encargué, trabajé*) y los reemplaza por verbos de acción (*lideré, optimicé, desarrollé*) con **detección de contexto** para mantener la gramática y capitalización correcta.
* **Arquitectura Clean:** Reestructuración total siguiendo patrones de diseño (Domain, Infrastructure, Service, Router) para facilitar la escalabilidad.
* **Motor PDF Profesional:** Generación de documentos ATS-friendly con alineación dinámica de bullets y sangría inteligente para los stacks tecnológicos.
* **Slugify Seguro:** Generación de nombres de archivos sanitizados (ej: `cv_8a2b1f_christian_estupinan.pdf`) para compatibilidad universal.

---

## 🛠️ Instalación rápida

```bash
# 1. Clonar el proyecto
git clone [https://github.com/Ivesqui/tucv-optimizer.git](https://github.com/Ivesqui/tucv-optimizer.git)
cd tucv-optimizer

# 2. Crear y activar entorno virtual
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/Mac:
# source .venv/bin/activate

# 3. Instalar dependencias
pip install fastapi uvicorn fpdf2 python-multipart requests
```

---

## 🏗️ Arquitectura del Sistema

El proyecto implementa una separación de responsabilidades clara para permitir el crecimiento del motor de optimización:

```text
app/
├── core/knowledge/     # Diccionarios JSON de verbos fuertes, débiles y skills.
├── domain/             # Lógica de negocio pura (CVProfile, optimize_cv).
├── infrastructure/     # Implementaciones técnicas (PDF Generator, Skill Detector).
├── services/           # Orquestador de lógica (CVService).
├── routers/            # Definición de endpoints FastAPI (/api/cv/...).
└── schemas/            # Validaciones Pydantic para la integridad de datos.

---

## 📊 Sistema de Scoring ATS

| Componente | Peso | Lógica |
|------------|------|--------|
| **Hard Skills** | 70% | Match directo de tecnologías requeridas vs. detectadas en el texto. |
| **Soft Skills** | 30% | Presencia de competencias blandas clave en la narrativa profesional. |

---

## 📁 Formato de Datos (JSON)

```json
{
  "contact": {
    "name": "Christian Estupiñán",
    "email": "tu@email.com",
    "location": "Ecuador"
  },
  "summary": "Resumen profesional de alto impacto...",
  "skills": ["Python", "FastAPI", "PostgreSQL"],
  "experience": [
    {
      "company": "Tech Ecuador",
      "position": "Backend Developer",
      "bullets": ["Lideré la migración de microservicios"],
      "skills_used": ["Python", "Docker"]
    }
  ]
}