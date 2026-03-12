// ─── State ────────────────────────────────────────────────────────────────
const API_CV = 'http://localhost:8000/api/cv';
const API_ANALYSIS = 'http://localhost:8000/api/analysis';
let experiences = [];
let education = [];
let projects = [];
let expCount = 0;
let eduCount = 0;
let projCount = 0;
let photoBase64 = '';

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

// ─── Experiencia ────────────────────────────────────────────────────────────
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

function removeExp(i) { experiences.splice(i, 1); renderExperiences(); }

// ─── Educación y Proyectos (Omitidos por brevedad, mantenlos igual) ─────────
function addEducation() { education.push({ institution:'', degree:'', start_date:'', end_date:'' }); renderEducation(); }
function renderEducation() { /* tu código actual */ }
function addProject() { projects.push({ name:'', description:'', tech_stack:[] }); renderProjects(); }
function renderProjects() { /* tu código actual */ }

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
async function exportCV(format) { /* tu código de exportar */ }
function downloadBlob(blob, name, type) { /* tu código */ }
function generateHTMLLocal(cv, photo = '') { /* tu código */ }
async function getAutofill() { /* tu código */ }
async function analyzeBullets() { /* tu código */ }
function showToast(msg) { /* tu código */ }

// ─── Init ──────────────────────────────────────────────────────────────────
addExperience();
addEducation();
window.switchTab = switchTab;