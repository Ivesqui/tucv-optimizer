// ─── State ────────────────────────────────────────────────────────────────
const API_CV = 'http://localhost:8000/api/cv';
const API_ANALYSIS = 'http://localhost:8000/api/analysis';
let experiences = [];
let education = [];
let certifications = [];
let projects = [];
let expCount = 0;
let eduCount = 0;
let projCount = 0;
let photoBase64 = '';
let currentThemeColor = "CORPORATE_BLUE";

// ─── Photo upload ──────────────────────────────────────────────────────────
function handlePhotoUpload(input) {
  const file = input.files[0];
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) { showToast('La foto debe pesar menos de 5MB'); return; }

  const reader = new FileReader();
  reader.onload = (e) => {
    photoBase64 = e.target.result;
    const img = document.getElementById('photo-img');
    const icon = document.getElementById('photo-icon');
    img.src = photoBase64;
    img.style.display = 'block';
    icon.style.display = 'none';
    document.getElementById('clear-photo-btn').style.display = 'inline-flex';
    showToast('Foto cargada ✓');
  };
  reader.readAsDataURL(file);
}

function clearPhoto() {
  photoBase64 = '';
  document.getElementById('photo-img').style.display = 'none';
  document.getElementById('photo-img').src = '';
  document.getElementById('photo-icon').style.display = 'block';
  document.getElementById('photo-input').value = '';
  document.getElementById('clear-photo-btn').style.display = 'none';
  showToast('Foto eliminada');
}

document.addEventListener('click', (e) => {
  if (e.target.classList.contains('color-dot')) {
    document.querySelectorAll('.color-dot').forEach(dot => dot.classList.remove('active'));
    e.target.classList.add('active');
    currentThemeColor = e.target.dataset.color;
    showToast(`Color seleccionado: ${currentThemeColor.replace('_', ' ')}`);
  }
});

// ─── Pestañas ─────────────────────────────────────────────────────────────────
function switchTab(id, btn) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
  if (btn) btn.classList.add('active');
  if (id === 'export') updateJSONPreview();
}

// ─── Construir CV JSON ─────────────────────────────────────────────────────────
function buildCVJson() {
  const skills = document.getElementById('skills-input').value.split(',').map(s => s.trim()).filter(Boolean);
  const softSkills = document.getElementById('soft-skills-input').value.split(',').map(s => s.trim()).filter(Boolean);
  const languages = document.getElementById('languages-input').value.split(',').map(s => s.trim()).filter(Boolean);

  return {
    contact: {
      name: document.getElementById('name').value,
      email: document.getElementById('email').value,
      phone: document.getElementById('phone').value,
      location: document.getElementById('location').value,
      linkedin: document.getElementById('linkedin').value,
      github: document.getElementById('github').value,
      portfolio: '',
    },
    metadata: {
      id_number: document.getElementById('metadata-id')?.value || "",
      nationality: "Ecuatoriana",
      gender: document.getElementById('metadata-gender')?.value || "No especificado",
      marital_status: "Soltero/a",
      province: document.getElementById('metadata-province')?.value || "",
      canton: document.getElementById('metadata-canton')?.value || ""
    },
    summary: document.getElementById('summary').value,
    skills, soft_skills: softSkills, languages,
    experience: experiences,
    education: education,
    projects: projects,
    certifications: [],
  };
}

function updateJSONPreview() {
  document.getElementById('json-preview').textContent = JSON.stringify(buildCVJson(), null, 2);
}

function copyJSON() {
  navigator.clipboard.writeText(JSON.stringify(buildCVJson(), null, 2));
  showToast('JSON copiado ✓');
}

// Funcion Agregar Experiencia
function addExperience() {
  experiences.push({ company:'', position:'', start_date:'', end_date:'', location:'', bullets:[''], skills_used:[] });
  renderExperiences();
}

function renderExperiences() {
  const list = document.getElementById('experience-list');
  list.innerHTML = experiences.map((exp, i) => `
    <div class="exp-entry">
      <div class="exp-header">
        <div class="exp-num">${i+1}</div>
        <strong style="font-size:13px">${exp.company || 'Nueva empresa'}</strong>
        <button class="btn btn-secondary" style="margin-left:auto; padding:4px 10px; font-size:11px" onclick="removeExp(${i})">✕</button>
      </div>
      <div class="form-grid">
        <div class="form-group"><label>Empresa</label><input value="${exp.company}" oninput="experiences[${i}].company=this.value"></div>
        <div class="form-group"><label>Cargo</label><input value="${exp.position}" oninput="experiences[${i}].position=this.value"></div>
        <div class="form-group"><label>Inicio</label><input value="${exp.start_date}" oninput="experiences[${i}].start_date=this.value"></div>
        <div class="form-group"><label>Fin</label><input value="${exp.end_date}" oninput="experiences[${i}].end_date=this.value"></div>
        <div class="form-group full"><label>Logros</label>
          <textarea rows="4" oninput="experiences[${i}].bullets=this.value.split('\\n').filter(Boolean)">${exp.bullets.join('\n')}</textarea>
        </div>
        <div class="form-group full"><label>Skills</label>
          <input value="${exp.skills_used.join(', ')}" oninput="experiences[${i}].skills_used=this.value.split(',').map(s=>s.trim()).filter(Boolean)">
        </div>
      </div>
    </div>
  `).join('');
}

// Boton (x) / remover Experiencia
function removeExp(i) {
    experiences.splice(i, 1);
    renderExperiences(); }

// Función Agregar Educación
function addEducation() {
  education.push({
    institution:'',
    degree:'',
    start_date:'',
    end_date:''
    });
    renderEducation();
}

// Renderizar Educación al HTML
function renderEducation() {
  const list = document.getElementById('education-list');
  if (!list) return;
  list.innerHTML = education.map((edu, i) => `
    <div class="exp-entry">
      <div class="exp-header">
        <div class="exp-num">${i+1}</div>
        <strong style="font-size:13px">${edu.institution || 'Nueva Institución'}</strong>
        <button class="btn btn-secondary" style="margin-left:auto; padding:4px 10px; font-size:11px" onclick="removeEdu(${i})">✕</button>
      </div>
      <div class="form-grid">
        <div class="form-group full"><label>Institución</label><input value="${edu.institution}" oninput="education[${i}].institution=this.value"></div>
        <div class="form-group"><label>Título</label><input value="${edu.degree}" oninput="education[${i}].degree=this.value"></div>
        <div class="form-group"><label>Inicio</label><input value="${edu.start_date}" oninput="education[${i}].start_date=this.value"></div>
        <div class="form-group"><label>Fin</label><input value="${edu.end_date}" oninput="education[${i}].end_date=this.value"></div>
      </div>
    </div>
  `).join('');
}
// Boton (x) / remover Educación
function removeEdu(i) {
    education.splice(i, 1);
    renderEducation();
}

// Función Agregar Proyecto
function addProject() {
  projects.push({
    title: '',
    description: '',
    link: '',
    tech_stack: []
  });
  renderProjects();
}

// Renderizar Proyecto al HTML

function renderProjects() {
  const list = document.getElementById('projects-list');
  if (!list) return;
  list.innerHTML = projects.map((proj, i) => `
    <div class="exp-entry">
      <div class="exp-header">
        <div class="exp-num">${i+1}</div>
        <strong style="font-size:13px">${proj.title || 'Nuevo Proyecto'}</strong>
        <button class="btn btn-secondary" style="margin-left:auto; padding:4px 10px; font-size:11px" onclick="removeProj(${i})">✕</button>
      </div>
      <div class="form-grid">
        <div class="form-group"><label>Nombre del Proyecto</label><input value="${proj.title}" oninput="projects[${i}].name=this.value"></div>
        <div class="form-group"><label>Link (URL)</label><input value="${proj.link}" oninput="projects[${i}].link=this.value"></div>
        <div class="form-group full"><label>Descripción</label>
          <textarea rows="3" oninput="projects[${i}].description=this.value">${proj.description}</textarea>
        </div>
        <div class="form-group full"><label>Tecnologías (separadas por coma)</label>
          <input value="${proj.tech_stack.join(', ')}" oninput="projects[${i}].tech_stack=this.value.split(',').map(s=>s.trim()).filter(Boolean)">
        </div>
      </div>
    </div>
  `).join('');
}

// Boton (x) / remover proyecto

function removeProj(i) {
    projects.splice(i, 1);
    renderProjects(); }

// Función Agregar Certificación o curso

function addCertification() {
    certifications.push({
    name: '',
    issuer: '',
    issue_date: '',
    expiration_date: '',
    credential_id: '',
    url: ''
  });
  renderCertifications();
}
// Renderizar Certificación al HTML
function renderCertifications() {
  const list = document.getElementById('certifications-list');
  if (!list) return;
  list.innerHTML = certifications.map((cert, i) => `
    <div class="exp-entry">
      <div class="exp-header">
        <div class="exp-num">${i+1}</div>
        <strong style="font-size:13px">${cert.name || 'Nueva Certificación'}</strong>
        <button class="btn btn-secondary" style="margin-left:auto; padding:4px 10px; font-size:11px" onclick="removeCert(${i})">✕</button>
      </div>
      <div class="form-grid">
        <div class="form-group full"><label>Nombre del Certificado</label><input value="${cert.name}" oninput="certifications[${i}].name=this.value"></div>
        <div class="form-group"><label>Emisor</label><input value="${cert.issuer}" oninput="certifications[${i}].issuer=this.value"></div>
        <div class="form-group"><label>ID Credencial</label><input value="${cert.credential_id}" oninput="certifications[${i}].credential_id=this.value"></div>
        <div class="form-group"><label>Fecha</label><input value="${cert.issue_date}" oninput="certifications[${i}].issue_date=this.value"></div>
        <div class="form-group"><label>URL Verificación</label><input value="${cert.url}" oninput="certifications[${i}].url=this.value"></div>
      </div>
    </div>
  `).join('');
}
// Boton (x) / remover Certificación
function removeCert(i) {
    certifications.splice(i, 1);
    renderCertifications();
    }

// ─── Analizar Oferta ─────────────────────────────────────────────────────────
async function analyzeOffer() {
  const offerText = document.getElementById('offer-text').value.trim();
  if (!offerText) { showToast('Pega una oferta laboral primero'); return; }

  const resultsDiv = document.getElementById('analysis-results');
  resultsDiv.innerHTML = `<div class="card" style="text-align:center; padding:40px"><div class="spinner"></div><p>Analizando oferta...</p></div>`;

  try {
    const res = await fetch(`${API_ANALYSIS}/analyze-offer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ offer_text: offerText, cv_json: buildCVJson() })
    });

    if (!res.ok) throw new Error("Backend offline");
    const data = await res.json();
    renderAnalysis(data);
  } catch (err) {
    console.error(err);
    renderAnalysisLocal(offerText);
  }
}

function renderAnalysis(data) {
  const resultsDiv = document.getElementById('analysis-results');
  const analysis = data.cv_analysis;

  if (!analysis || !analysis.match_details) {
    renderAnalysisLocal(document.getElementById('offer-text').value);
    return;
  }

  const comp = analysis.match_details;
  const scoreColor = comp.ats_score >= 65 ? 'var(--green)' : comp.ats_score >= 40 ? 'var(--yellow)' : 'var(--red)';

  resultsDiv.innerHTML = `
    <div class="card" style="text-align:center">
      <div class="card-title"><span>📊</span> ATS Score</div>
      <div style="font-size:32px; font-weight:700; color:${scoreColor}; margin:10px 0">${comp.ats_score}%</div>
      <div style="text-align:left; border-top:1px solid var(--surface2); padding-top:12px">
        <p><strong>Matches:</strong> ${comp.matching_tech.join(', ') || 'Ninguna'}</p>
        <p style="color:var(--red)"><strong>Faltantes:</strong> ${comp.missing_tech.join(', ') || 'Ninguna'}</p>
        <div style="margin-top:10px">
          <strong>Tips:</strong>
          <ul>${comp.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>
        </div>
      </div>
    </div>
  `;
}

function renderAnalysisLocal(offerText) {
  const resultsDiv = document.getElementById('analysis-results');
  resultsDiv.innerHTML = `
    <div class="card">
      <div class="card-title"><span>⚡</span> Análisis Local</div>
      <p style="font-size:12px;color:var(--muted)">Inicia el servidor para el score completo.</p>
    </div>
  `;
}

// ─── Export y Otros (Mantenlos igual) ───────────────────────────────────────

async function exportCV(format) {
  const cvData = buildCVJson(); // Tu función que recolecta los datos
  const selectedFont = document.getElementById('font-family-select').value;

  // Nombre de archivo limpio
  const rawName = cvData.contact.name || 'mi_cv';
  const filename = rawName.replace(/\s+/g, '_').toLowerCase();

  // --- CASO 1: HTML (Se hace 100% en el navegador) ---
  if (format === 'html') {
    generateHTMLLocal(cvData, currentThemeColor, selectedFont);
    showToast('HTML generado ✓');
    return; // Terminamos aquí, no necesita ir al servidor
  }

  // --- CASO 2: JSON (Se hace 100% en el navegador si solo quieres los datos) ---
  if (format === 'json-local') {
    const blob = new Blob([JSON.stringify(cvData, null, 2)], {type:'application/json'});
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.json`;
    a.click();
    showToast('JSON exportado ✓');
    return;
  }

  // --- CASO 3: PDF (Vamos al servidor para que use fpdf2 con estilos) ---
  showToast('Generando PDF con estilo... 📄');

  try {
    const response = await fetch(`${API_CV}/generate-cv`, { // Usa tu variable de ruta API
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cv_json: cvData,
        format: 'pdf',
        theme_color: currentThemeColor, // Enviamos el ID del color (ej: "DUSTY_ROSE")
        font_family: selectedFont,      // Enviamos el ID de la fuente (ej: "ROBOTO")
        optimize: true,
        offer_text: document.getElementById('offer-text')?.value || ""
      })
    });

    if (!response.ok) throw new Error("Error en el servidor");

    // Recibimos el PDF como un chorro de bytes (Blob)
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cv_${filename}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url); // Limpieza de memoria

    showToast('PDF descargado con éxito ✓');

  } catch (err) {
    console.error("Error al exportar PDF:", err);
    showToast('Error al generar PDF');
  }
}

// ─── Analizador de Bullets ───
async function analyzeBullets() {
  const input = document.getElementById('bullets-input'); // ID corregido del HTML
  const resultsDiv = document.getElementById('bullets-results'); // ID corregido
  const text = input.value.trim();

  if (!text) {
    showToast('Pega tus logros primero');
    return;
  }

  resultsDiv.innerHTML = '<div class="spinner"></div> Analizando calidad...';

  try {
    const res = await fetch(`${API_ANALYSIS}/analyze-bullets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        bullets: text.split('\n').filter(b => b.trim() !== ""),
        target_role: "Software Engineer"
      })
    });

  const data = await res.json();
    // Suponiendo que el router devuelve una lista de resultados
    renderBulletResults(data);
    showToast('Análisis de logros completado ✓');
  } catch (err) {
    resultsDiv.innerHTML = '<p style="color:var(--red)">Error de conexión</p>';
  }
}

// Helper para pintar los resultados de los bullets
function renderBulletResults(results) {
    const div = document.getElementById('bullets-results');

    // Si no hay resultados o la respuesta falló
    if (!results || results.length === 0) {
        div.innerHTML = '<p style="color:var(--muted)">No se encontraron sugerencias.</p>';
        return;
    }

    div.innerHTML = results.map(r => {
        // Determinamos el color basado en el score que ahora sí llega bien
        const statusColor = r.score >= 7.0 ? 'var(--green)' : r.score >= 4.5 ? 'var(--yellow)' : 'var(--red)';

        // Unimos todas las sugerencias de la lista en un solo bloque de texto o lista
        const suggestionsHtml = r.suggestions && r.suggestions.length > 0
            ? r.suggestions.map(s => `<li>${s}</li>`).join('')
            : '<li>Intenta cuantificar este logro con métricas.</li>';

        return `
            <div class="card" style="margin-bottom:12px; border-left:4px solid ${statusColor}; background: var(--surface1)">
                <div style="display:flex; justify-content:space-between; align-items:center">
                    <strong style="font-size:13px">Logro:</strong>
                    <span class="badge" style="background:${statusColor}22; color:${statusColor}">Score: ${r.score}</span>
                </div>
                <p style="font-size:13px; margin: 8px 0; color: var(--text)">${r.bullet}</p>

                <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px; margin-top: 8px">
                    <strong style="font-size:11px; color:var(--muted); text-transform:uppercase">Sugerencias para mejorar:</strong>
                    <ul style="font-size:12px; margin: 5px 0 0 15px; padding:0; color:var(--yellow)">
                        ${suggestionsHtml}
                    </ul>
                </div>
            </div>
        `;
    }).join('');
}

function downloadBlob(blob, name) {
  // Creamos una URL temporal para el objeto blob
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = name; // Nombre del archivo que aparecerá en la carpeta de descargas

  document.body.appendChild(a);
  a.click(); // Forzamos el click para descargar

  // Limpiamos la memoria
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

function showToast(msg) {
  // Crear el elemento si no existe
  let toast = document.getElementById('toast-container');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast-container';
    toast.style.cssText = `
      position: fixed; bottom: 20px; right: 20px;
      background: var(--surface2); border: 1px solid var(--primary);
      color: white; padding: 12px 20px; border-radius: 8px;
      z-index: 10000; font-size: 13px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
      transition: opacity 0.3s;
    `;
    document.body.appendChild(toast);
  }

  toast.textContent = msg;
  toast.style.opacity = '1';

  // Desaparece tras 3 segundos
  setTimeout(() => {
    toast.style.opacity = '0';
  }, 3000);
}


function generateHTMLLocal(cv, photo = '') {
  // Construimos un HTML minimalista que los lectores ATS aman
  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>CV - ${cv.contact.name}</title>
      <style>
        body { font-family: Arial, sans-serif; line-height: 1.5; color: #333; max-width: 800px; margin: 40px auto; }
        h1 { text-align: center; color: #000; }
        .contact { text-align: center; font-size: 0.9em; margin-bottom: 20px; }
        h2 { border-bottom: 1px solid #ccc; color: #222; text-transform: uppercase; font-size: 1.1em; }
        .item { margin-bottom: 15px; }
        .item-header { display: flex; justify-content: space-between; font-weight: bold; }
      </style>
    </head>
    <body>
      <h1>${cv.contact.name}</h1>
      <div class="contact">
        ${cv.contact.email} | ${cv.contact.phone} | ${cv.contact.location}<br>
        ${cv.contact.linkedin} | ${cv.contact.github}
      </div>

      <h2>Perfil Profesional</h2>
      <p>${cv.summary}</p>

      <h2>Experiencia</h2>
      ${cv.experience.map(exp => `
        <div class="item">
          <div class="item-header"><span>${exp.company}</span> <span>${exp.start_date} - ${exp.end_date}</span></div>
          <div><em>${exp.position}</em></div>
          <ul>${exp.bullets.map(b => `<li>${b}</li>`).join('')}</ul>
        </div>
      `).join('')}

      <h2>Formación Académica</h2>
      ${cv.education.map(edu => `
        <div class="item">
          <div class="item-header"><span>${edu.institution}</span> <span>${edu.start_date} - ${edu.end_date}</span></div>
          <div>${edu.degree}</div>
        </div>
      `).join('')}

      <h2>Certificaciones</h2>
      ${cv.certifications.map(cert => `
        <div class="item">
          <div class="item-header"><span>${cert.name}</span> <span>${cert.issue_date}</span></div>
          <div><em>${cert.issuer}</em></div>
        </div>
      `).join('')}

      <h2>Habilidades</h2>
      <p><strong>Técnicas:</strong> ${cv.skills.join(', ')}</p>
      <p><strong>Blandas:</strong> ${cv.soft_skills.join(', ')}</p>

      <h2>Proyectos</h2>
      ${cv.projects.map(proj => `
        <div class="item">
          <div class="item-header"><strong>${proj.name}</strong></div>
          <p>${proj.description}</p>
          <small>Tech: ${proj.tech_stack.join(', ')}</small>
        </div>
      `).join('')}
    </body>
    </html>
  `;

  const blob = new Blob([htmlContent], { type: 'text/html' });
  downloadBlob(blob, `${cv.contact.name.replace(/\s+/g, '_')}_ATSFriendly.html`);
}




// ─── Init ──────────────────────────────────────────────────────────────────
addExperience();
addEducation();
window.switchTab = switchTab;