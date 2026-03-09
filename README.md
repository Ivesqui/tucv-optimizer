# 📄 CV Optimizer — ATS Pro



---

## 🚀 Instalación rápida

```bash
# 1. Clonar / copiar el proyecto
cd cv_optimizer

# 2. Instalar dependencias mínimas
pip install fastapi uvicorn fpdf2 python-multipart

# 3. (Opcional) Para análisis NLP avanzado
pip install spacy scikit-learn
python -m spacy download es_core_news_sm
```

---

## 🎯 Cómo usar

### Opción A: Interfaz Web (recomendada)

```bash
# Iniciar el servidor
uvicorn api.main:app --reload --port 8000

# Abrir en el navegador
open http://localhost:8000
```

### Opción B: CLI (sin servidor)

```bash
# Analizar CV vs oferta
python cli.py analyze --cv example_cv.json --offer "Buscamos Python dev con Docker y AWS, 3+ años"

# Generar CV en HTML (ATS-friendly, abre en navegador y Ctrl+P → PDF)
python cli.py generate --cv example_cv.json --format html

# Generar PDF directo (requiere fpdf2)
python cli.py generate --cv example_cv.json --format pdf

# Generar con optimización para oferta específica
python cli.py generate --cv example_cv.json --format html --offer "texto de la oferta"

# Evaluar calidad de bullets
python cli.py bullets --cv example_cv.json

# Exportar JSON para autofill
python cli.py generate --cv example_cv.json --format autofill
```

### Opción C: API REST directa

```bash
# Analizar oferta + calcular score ATS
curl -X POST http://localhost:8000/analyze-offer \
  -H "Content-Type: application/json" \
  -d '{
    "offer_text": "Buscamos Senior Python dev con FastAPI, PostgreSQL, Docker y AWS. 4+ años.",
    "cv_json": { ...tu CV aquí... }
  }'

# Generar CV en HTML
curl -X POST http://localhost:8000/generate-cv \
  -H "Content-Type: application/json" \
  -d '{"cv_json": {...}, "format": "html", "optimize": true, "offer_text": "..."}'

# Generar PDF
curl -X POST http://localhost:8000/generate-cv \
  -H "Content-Type: application/json" \
  -d '{"cv_json": {...}, "format": "pdf"}' \
  --output mi_cv.pdf
```

---

## 🏗️ Arquitectura

```
cv_optimizer/
├── api/
│   └── main.py          # FastAPI: endpoints REST
├── core/
│   ├── skills_detector.py  # NLP: detección de skills y scoring ATS
│   ├── cv_model.py         # Modelo de datos + optimizador automático
│   └── pdf_generator.py    # Generador PDF ATS-friendly + HTML fallback
├── ui/
│   └── index.html          # Interfaz web (sin frameworks, vanilla JS)
├── cli.py                  # CLI standalone con colores
├── example_cv.json         # CV de ejemplo para probar
└── README.md
```

### Flujo de datos

```
Oferta laboral (texto)
        ↓
skills_detector.detect_skills()
        ↓
Comparador CV vs oferta
        ↓
ATS Score (0-100) + Grado (A-F)
        ↓
optimize_cv() — promueve skills detectadas
        ↓
ATSPDFGenerator / generate_html_cv()
        ↓
PDF / HTML / JSON descargable
```

---

## 📊 Cómo funciona el ATS Score

| Componente | Peso | Cómo se calcula |
|------------|------|-----------------|
| Skills técnicas | 70% | `matching_tech / offer_tech × 70` |
| Soft skills | 30% | `matching_soft / offer_soft × 30` |

| Score | Grado | Interpretación |
|-------|-------|----------------|
| 80–100 | A | Excelente match |
| 65–79 | B | Buen match |
| 50–64 | C | Match moderado |
| 35–49 | D | Match bajo |
| 0–34 | F | Personalizar CV |

---

## 🔌 Integración con formularios (Autofill)

El endpoint `/linkedin-autofill` retorna los campos del CV mapeados a los formularios más comunes:

```json
{
  "personal": {
    "first_name": "Ana",
    "last_name": "García López",
    "email": "ana@email.com",
    "phone": "+57 300 123 4567",
    "location": "Bogotá, Colombia",
    "linkedin_url": "linkedin.com/in/anagarcia"
  },
  "current_role": {
    "title": "Senior Software Engineer",
    "company": "Bancolombia"
  },
  "education": {
    "school": "Universidad de los Andes",
    "degree": "Ingeniería de Sistemas"
  },
  "skills_text": "Python, React, PostgreSQL, Docker, AWS...",
  "summary": "..."
}
```

Puedes usar este JSON con extensiones de Chrome como **Autofill** o **Form Filler** para llenar formularios automáticamente.

---

## 📁 Formato del CV (JSON)

```json
{
  "contact": {
    "name": "Tu Nombre",
    "email": "tu@email.com",
    "phone": "+57 300 000 0000",
    "location": "Ciudad, País",
    "linkedin": "linkedin.com/in/tunombre",
    "github": "github.com/tunombre"
  },
  "summary": "Resumen profesional de 2-4 oraciones...",
  "skills": ["Python", "React", "Docker", "AWS"],
  "soft_skills": ["Liderazgo", "Trabajo en equipo"],
  "languages": ["Español (Nativo)", "Inglés (B2)"],
  "experience": [
    {
      "company": "Empresa",
      "position": "Cargo",
      "start_date": "Ene 2022",
      "end_date": "Presente",
      "location": "Ciudad",
      "bullets": [
        "Logro cuantificado con verbo de acción y métricas",
        "Implementé X que resultó en Y% de mejora"
      ],
      "skills_used": ["Python", "PostgreSQL"]
    }
  ],
  "education": [
    {
      "institution": "Universidad",
      "degree": "Ingeniería en Sistemas",
      "field": "Computación",
      "start_date": "2015",
      "end_date": "2020"
    }
  ],
  "projects": [
    {
      "name": "Nombre del proyecto",
      "description": "Descripción breve",
      "tech_stack": ["React", "Node.js"],
      "url": "github.com/user/repo",
      "highlights": ["Logro 1", "Logro 2"]
    }
  ],
  "certifications": [
    {
      "name": "AWS Solutions Architect",
      "issuer": "Amazon",
      "date": "2023"
    }
  ]
}
```

---

## 🛠️ Extensiones futuras

- [ ] Extensión Chrome para autofill automático en LinkedIn/HiringRoom
- [ ] Soporte multiidioma (EN/ES/PT)
- [ ] Parser de PDF para importar CVs existentes
- [ ] Templates de CV adicionales
- [ ] Modo batch: analizar múltiples ofertas a la vez
- [ ] Historial de aplicaciones (SQLite local)

---

## 📦 Dependencias

| Librería | Uso | Instalación |
|----------|-----|-------------|
| `fastapi` | API REST | `pip install fastapi uvicorn` |
| `fpdf2` | Generación PDF | `pip install fpdf2` |
| `python-multipart` | Upload de archivos | `pip install python-multipart` |

> **Sin spaCy, sin OpenAI, sin costos recurrentes.** Todo el análisis NLP se hace con diccionarios curados y regex.
