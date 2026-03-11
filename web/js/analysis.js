    // ─── State ────────────────────────────────────────────────────────────────
    const API = 'http://localhost:8000/api/cv';
    let experiences = [];
    let education = [];
    let projects = [];
    let expCount = 0;
    let eduCount = 0;
    let projCount = 0;
    let photoBase64 = '';  // foto en base64 con prefijo data:image/...

    // ─── Photo upload ──────────────────────────────────────────────────────────
    function handlePhotoUpload(input) {
      const file = input.files[0];
      if (!file) return;
      if (file.size > 5 * 1024 * 1024) { showToast('La foto debe pesar menos de 5MB'); return; }

      const reader = new FileReader();
      reader.onload = (e) => {
        photoBase64 = e.target.result;  // data:image/jpeg;base64,...
        // Mostrar preview
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
      const skills = document.getElementById('skills-input').value
        .split(',').map(s => s.trim()).filter(Boolean);
      const softSkills = document.getElementById('soft-skills-input').value
        .split(',').map(s => s.trim()).filter(Boolean);
      const languages = document.getElementById('languages-input').value
        .split(',').map(s => s.trim()).filter(Boolean);

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
      document.getElementById('json-preview').textContent =
        JSON.stringify(buildCVJson(), null, 2);
    }

    function copyJSON() {
      navigator.clipboard.writeText(JSON.stringify(buildCVJson(), null, 2));
      showToast('JSON copiado ✓');
    }

    // ─── Experiencia ────────────────────────────────────────────────────────────
    function addExperience() {
      expCount++;
      const idx = experiences.length;
      experiences.push({ company:'', position:'', start_date:'', end_date:'', location:'', bullets:[''], skills_used:[] });
      renderExperiences();
    }

    function renderExperiences() {
      const list = document.getElementById('experience-list');
      list.innerHTML = experiences.map((exp, i) => `
        <div class="exp-entry">
          <div class="exp-header">
            <div class="exp-num">${i+1}</div>
            <strong style="font-size:13px">${exp.company || 'Nueva empresa'} — ${exp.position || 'Cargo'}</strong>
            <button class="btn btn-secondary" style="margin-left:auto; padding:4px 10px; font-size:11px" onclick="removeExp(${i})">✕</button>
          </div>
          <div class="form-grid">
            <div class="form-group"><label>Empresa</label><input value="${exp.company}" oninput="experiences[${i}].company=this.value;renderExperiences()" placeholder="Google"></div>
            <div class="form-group"><label>Cargo</label><input value="${exp.position}" oninput="experiences[${i}].position=this.value;renderExperiences()" placeholder="Senior Software Engineer"></div>
            <div class="form-group"><label>Inicio</label><input value="${exp.start_date}" oninput="experiences[${i}].start_date=this.value" placeholder="Mar 2022"></div>
            <div class="form-group"><label>Fin</label><input value="${exp.end_date}" oninput="experiences[${i}].end_date=this.value" placeholder="Presente"></div>
            <div class="form-group full"><label>Logros y responsabilidades (uno por línea)</label>
              <textarea rows="4" oninput="experiences[${i}].bullets=this.value.split('\\n').filter(Boolean)" placeholder="Implementé un sistema de cache que redujo la latencia en 40%&#10;Lideré un equipo de 4 devs en la migración a microservicios&#10;Reduje el tiempo de deploy de 2h a 8min con GitHub Actions">${exp.bullets.join('\n')}</textarea>
            </div>
            <div class="form-group full"><label>Skills usadas (separadas por coma)</label>
              <input value="${exp.skills_used.join(', ')}" oninput="experiences[${i}].skills_used=this.value.split(',').map(s=>s.trim()).filter(Boolean)" placeholder="Python, FastAPI, PostgreSQL, Redis">
            </div>
          </div>
        </div>
      `).join('');
    }

    function removeExp(i) { experiences.splice(i, 1); renderExperiences(); }

    // ─── Educación ─────────────────────────────────────────────────────────────
    function addEducation() {
      education.push({ institution:'', degree:'', field:'', start_date:'', end_date:'', gpa:'', highlights:[] });
      renderEducation();
    }

    function renderEducation() {
      document.getElementById('education-list').innerHTML = education.map((edu, i) => `
        <div class="exp-entry" style="margin-bottom:8px">
          <div class="form-grid">
            <div class="form-group"><label>Institución</label><input value="${edu.institution}" oninput="education[${i}].institution=this.value" placeholder="Universidad Nacional"></div>
            <div class="form-group"><label>Título</label><input value="${edu.degree}" oninput="education[${i}].degree=this.value" placeholder="Ingeniería en Sistemas"></div>
            <div class="form-group"><label>Inicio</label><input value="${edu.start_date}" oninput="education[${i}].start_date=this.value" placeholder="2016"></div>
            <div class="form-group"><label>Fin</label><input value="${edu.end_date}" oninput="education[${i}].end_date=this.value" placeholder="2021"></div>
          </div>
          <button class="btn btn-secondary" style="padding:4px 10px; font-size:11px; margin-top:6px" onclick="education.splice(${i},1);renderEducation()">✕ Eliminar</button>
        </div>
      `).join('');
    }

    // ─── Projectos ──────────────────────────────────────────────────────────────
    function addProject() {
      projects.push({ name:'', description:'', tech_stack:[], url:'', highlights:[] });
      renderProjects();
    }

    function renderProjects() {
      document.getElementById('projects-list').innerHTML = projects.map((proj, i) => `
        <div class="exp-entry" style="margin-bottom:8px">
          <div class="form-grid">
            <div class="form-group"><label>Nombre</label><input value="${proj.name}" oninput="projects[${i}].name=this.value" placeholder="API de pagos con Stripe"></div>
            <div class="form-group"><label>URL</label><input value="${proj.url}" oninput="projects[${i}].url=this.value" placeholder="github.com/user/repo"></div>
            <div class="form-group full"><label>Descripción</label><input value="${proj.description}" oninput="projects[${i}].description=this.value" placeholder="Sistema de pagos en tiempo real con webhooks y retries automáticos"></div>
            <div class="form-group full"><label>Tech stack (coma)</label><input value="${proj.tech_stack.join(', ')}" oninput="projects[${i}].tech_stack=this.value.split(',').map(s=>s.trim()).filter(Boolean)" placeholder="Node.js, Stripe API, PostgreSQL, Redis"></div>
          </div>
          <button class="btn btn-secondary" style="padding:4px 10px; font-size:11px; margin-top:6px" onclick="projects.splice(${i},1);renderProjects()">✕ Eliminar</button>
        </div>
      `).join('');
    }

   // ─── Analizar Oferta ─────────────────────────────────────────────────────────
async function analyzeOffer() {
  const offerText = document.getElementById('offer-text').value.trim();
  if (!offerText) {
    showToast('Pega una oferta laboral primero');
    return;
  }

  const resultsDiv = document.getElementById('analysis-results');
  resultsDiv.innerHTML = `
    <div class="card" style="text-align:center; padding:40px">
      <div class="spinner"></div>
      <div style="margin-top:12px; color:var(--muted); font-size:13px">Analizando oferta...</div>
    </div>
  `;

  try {
    const res = await fetch(`${API}/analyze-offer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
    offer_text: document.getElementById('offer-text').value,
    cv_json: buildCVJson()
    })
  });

    if (!res.ok) throw new Error(await res.text());

    const data = await res.json();

    // Logging profesional
    console.info("✅ Datos recibidos del backend:", data);

    // Renderizamos la UI
    renderAnalysis(data);
  } catch (err) {
    console.error("❌ Error analizando la oferta:", err);
    renderAnalysisLocal(offerText);
  }
}

// ─── Renderizado principal ───────────────────────────────────────────────
function renderAnalysis(data) {
  const resultsDiv = document.getElementById('analysis-results');

  // Si no hay ATS (servidor no iniciado), mostrar análisis local
  if (!data.comparison) {
    const found = data.offer_skills?.all_tech_flat || [];
    resultsDiv.innerHTML = `
      <div class="card">
        <div class="card-title"><span>⚡</span> Análisis Local (sin servidor)</div>
        <p style="font-size:12px;color:var(--muted);margin-bottom:12px">
          Para el score ATS completo, inicia el servidor FastAPI.
        </p>
        <div class="card-title" style="margin-top:8px"><span>🔍</span> Skills detectadas en la oferta</div>
        <div class="tags">
          ${found.map(s=>`<span class="tag tag-neutral">${s}</span>`).join('')}
        </div>
        <div style="margin-top:12px; font-size:13px; color:var(--muted)">
          Inicia el servidor:
          <code style="font-family:var(--mono); background:var(--surface2); padding:2px 6px; border-radius:4px">
            uvicorn app.main:app --reload
          </code>
        </div>
      </div>
    `;
    return;
  }

function renderAnalysisLocal(offerText) {
  const resultsDiv = document.getElementById('analysis-results');
  const found = ['python','docker','sql','postgresql','git','fastapi']; // ejemplo
  resultsDiv.innerHTML = `
    <div class="card">
      <div class="card-title"><span>⚡</span> Análisis Local (sin servidor)</div>
      <p style="font-size:12px;color:var(--muted);margin-bottom:12px">
        Para el score ATS completo, inicia el servidor FastAPI.
      </p>
      <div class="card-title" style="margin-top:8px"><span>🔍</span> Skills detectadas en la oferta</div>
      <div class="tags">
        ${found.map(s=>`<span class="tag tag-neutral">${s}</span>`).join('')}
      </div>
      <div style="margin-top:12px; font-size:13px; color:var(--muted)">
        Inicia el servidor:
        <code style="font-family:var(--mono); background:var(--surface2); padding:2px 6px; border-radius:4px">
          uvicorn app.main:app --reload
        </code>
      </div>
    </div>
  `;
}

  // Si hay ATS completo
  const comp = data.comparison;
  const offerSkills = data.offer_skills?.all_tech_flat || [];
  const cvSkills = data.cv_skills?.all_tech_flat || [];

  const scoreColor = comp.ats_score >= 65 ? 'var(--green)' :
                     comp.ats_score >= 40 ? 'var(--yellow)' :
                     'var(--red)';

  const gradeColors = { A:'var(--green)', B:'#86efac', C:'var(--yellow)', D:'#fb923c', F:'var(--red)' };
  const gradeColor = gradeColors[comp.grade] || 'var(--muted)';

  resultsDiv.innerHTML = `
    <div class="card" style="text-align:center">
      <div class="card-title"><span>📊</span> ATS Score</div>
      <div class="grade-badge" style="background:${gradeColor}22; color:${gradeColor}">${comp.grade}</div>
      <div style="font-size:24px; font-weight:600; color:${scoreColor}; margin-bottom:12px">
        ${comp.ats_score}%
      </div>

      <div style="text-align:left; margin-top:12px">
        <strong>Skills de la oferta:</strong> ${offerSkills.join(', ')}
      </div>
      <div style="text-align:left; margin-top:4px">
        <strong>Skills en tu CV:</strong> ${cvSkills.join(', ')}
      </div>
      <div style="text-align:left; margin-top:8px">
        <strong>Skills que coinciden:</strong> ${comp.matching_tech.join(', ') || 'Ninguna'}
      </div>
      <div style="text-align:left; margin-top:4px; color:var(--red)">
        <strong>Skills faltantes:</strong> ${comp.missing_tech.join(', ') || 'Ninguna'}
      </div>

      <div style="text-align:left; margin-top:12px; font-size:13px; color:var(--muted)">
        <strong>Recomendaciones:</strong>
        <ul>
          ${comp.recommendations.map(r=>`<li>${r}</li>`).join('')}
        </ul>
      </div>
    </div>
  `;
}

    // ─── Export ────────────────────────────────────────────────────────────────
    async function exportCV(format) {
      const cvJson = buildCVJson();
      const offerText = document.getElementById('offer-text').value;
      try {
        const res = await fetch(`${API}/generate-cv`, {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ cv_json: cvJson, offer_text: offerText, optimize: true, format, photo_base64: photoBase64 }),
        });
        if (!res.ok) throw new Error(await res.text());

        if (format === 'pdf') {
          const blob = await res.blob();
          downloadBlob(blob, `cv_${cvJson.contact.name.replace(/ /g,'_')}.pdf`, 'application/pdf');
        } else {
          const data = await res.json();
          if (format === 'html') {
            const blob = new Blob([data.html], {type:'text/html'});
            downloadBlob(blob, `cv_${cvJson.contact.name.replace(/ /g,'_')}.html`, 'text/html');
          } else {
            const blob = new Blob([JSON.stringify(data.cv, null, 2)], {type:'application/json'});
            downloadBlob(blob, `cv_${cvJson.contact.name.replace(/ /g,'_')}.json`, 'application/json');
          }
        }
        showToast('Descarga iniciada ✓');
      } catch {
        // Fallback local para HTML y JSON
        if (format === 'html') {
          const html = generateHTMLLocal(cvJson, photoBase64);
          const blob = new Blob([html], {type:'text/html'});
          downloadBlob(blob, `cv_${(cvJson.contact.name||'cv').replace(/ /g,'_')}.html`, 'text/html');
          showToast('HTML generado localmente ✓');
        } else if (format === 'json') {
          const blob = new Blob([JSON.stringify(cvJson, null, 2)], {type:'application/json'});
          downloadBlob(blob, `cv_${(cvJson.contact.name||'cv').replace(/ /g,'_')}.json`, 'application/json');
          showToast('JSON exportado ✓');
        } else {
          showToast('Para PDF, inicia el servidor FastAPI + instala fpdf2');
        }
      }
    }

    function downloadBlob(blob, name, type) {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = name; a.click();
    }

    function generateHTMLLocal(cv, photo = '') {
      const c = cv.contact;
      const contacts = [c.email,c.phone,c.location,c.linkedin,c.github].filter(Boolean).join(' | ');
      const photoBlock = photo
        ? `<img src="${photo}" style="width:90px;height:90px;border-radius:50%;object-fit:cover;border:2px solid #ddd;flex-shrink:0" alt="Foto">`
        : '';
      const headerStyle = photo
        ? 'display:flex;align-items:center;gap:20px;margin-bottom:14px'
        : 'margin-bottom:14px';
      const nameStyle = photo ? 'text-align:left' : 'text-align:center';
      const contactStyle = photo ? 'text-align:left' : 'text-align:center';

      const expHtml = cv.experience.map(e => `
        <div class="entry">
          <div class="row"><span class="org">${e.company}</span><span class="date">${e.start_date} – ${e.end_date||'Presente'}</span></div>
          <div class="role">${e.position}${e.location?' — '+e.location:''}</div>
          <ul>${e.bullets.map(b=>`<li>${b}</li>`).join('')}</ul>
          ${e.skills_used.length?`<div class="stack">Stack: ${e.skills_used.join(', ')}</div>`:''}
        </div>`).join('');
      const eduHtml = cv.education.map(e => `
        <div class="entry">
          <div class="row"><span class="org">${e.institution}</span><span class="date">${e.start_date} – ${e.end_date}</span></div>
          <div class="role">${e.degree}${e.field_of_study?' en '+e.field_of_study:''}</div>
        </div>`).join('');
      const projHtml = cv.projects.map(p => `
        <div class="entry">
          <div class="role">${p.name}</div>
          <p>${p.description}</p>
          ${p.tech_stack.length?`<div class="stack">Tech: ${p.tech_stack.join(', ')}</div>`:''}
        </div>`).join('');

      return `<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>CV - ${c.name}</title>
    <style>
    body{font-family:Arial,sans-serif;font-size:10.5pt;max-width:800px;margin:0 auto;padding:30px 40px;color:#111;line-height:1.5}
    h1{font-size:22pt;margin-bottom:3px;${nameStyle?'text-align:'+nameStyle:'text-align:center'}}
    .contact{font-size:9pt;color:#555;margin-bottom:14px;${contactStyle?'text-align:'+contactStyle:'text-align:center'}}
    h2{font-size:11pt;text-transform:uppercase;letter-spacing:.06em;color:#1a4db3;border-bottom:1px solid #ccc;padding-bottom:2px;margin:14px 0 8px}
    .entry{margin-bottom:10px}.row{display:flex;justify-content:space-between}
    .org{font-weight:bold}.date{font-size:9pt;color:#555}
    .role{color:#1a4db3;font-weight:bold;margin:2px 0}
    ul{padding-left:14px;margin:4px 0}li{margin-bottom:2px}
    .stack{font-size:9pt;color:#555;font-style:italic}
    @media print{body{padding:15px 20px}.entry{page-break-inside:avoid}}
    </style></head><body>
    <div style="${headerStyle}">
      ${photoBlock}
      <div>
        <h1 style="${nameStyle}">${c.name}</h1>
        <div class="contact" style="${contactStyle}">${contacts}</div>
      </div>
    </div>
    ${cv.summary?`<section><h2>Perfil Profesional</h2><p>${cv.summary}</p></section>`:''}
    <section><h2>Habilidades Técnicas</h2><p>${cv.skills.join(' · ')}</p>${cv.soft_skills.length?`<p style="font-style:italic;font-size:9pt;color:#555">Soft skills: ${cv.soft_skills.join(' · ')}</p>`:''}</section>
    ${expHtml?`<section><h2>Experiencia</h2>${expHtml}</section>`:''}
    ${projHtml?`<section><h2>Proyectos</h2>${projHtml}</section>`:''}
    ${eduHtml?`<section><h2>Educación</h2>${eduHtml}</section>`:''}
    ${cv.languages.length?`<section><h2>Idiomas</h2><p>${cv.languages.join(' · ')}</p></section>`:''}
    </body></html>`;
    }

    async function getAutofill() {
      const cv = buildCVJson();
      const autofill = {
        "// Campos para LinkedIn / HiringRoom / Workday": "",
        personal: {
          first_name: cv.contact.name.split(' ')[0] || '',
          last_name: cv.contact.name.split(' ').slice(1).join(' ') || '',
          email: cv.contact.email,
          phone: cv.contact.phone,
          location: cv.contact.location,
          linkedin_url: cv.contact.linkedin,
        },
        current_role: cv.experience[0] ? {
          title: cv.experience[0].position,
          company: cv.experience[0].company,
          start_date: cv.experience[0].start_date,
        } : {},
        education: cv.education[0] ? {
          school: cv.education[0].institution,
          degree: cv.education[0].degree,
          end_date: cv.education[0].end_date,
        } : {},
        skills_text: cv.skills.slice(0,15).join(', '),
        summary: cv.summary,
      };
      document.getElementById('autofill-box').textContent = JSON.stringify(autofill, null, 2);
      showToast('Autofill generado ✓');
    }

    async function analyzeBullets() {
      const text = document.getElementById('bullets-input').value.trim();
      if (!text) return;
      const bullets = text.split('\n').filter(Boolean);

      // Análisis local sin servidor
      const results = bullets.map(b => {
        let score = 100; const issues = [];
        const impactVerbs = ['implementé','desarrollé','lideré','optimicé','diseñé','construí','automaticé','reduje','aumenté','mejoré','migré','integré','desplegué','entregué','escalé'];
        const weakVerbs = ['fui responsable','me encargué','trabajé','ayudé','participé','was responsible','helped','assisted'];
        const firstWord = b.split(' ')[0].toLowerCase();
        if (!impactVerbs.some(v => firstWord.includes(v))) { issues.push('Usa un verbo de impacto (Implementé, Lideré, Optimicé...)'); score -= 20; }
        if (weakVerbs.some(v => b.toLowerCase().includes(v))) { issues.push('Evita verbos débiles'); score -= 15; }
        if (!/\d+\s*%|\d+x|\$[\d,]+|\d+\s*(usuarios|ms|gb|clientes)/.test(b.toLowerCase())) { issues.push('Agrega métricas: %, $, usuarios, tiempo'); score -= 20; }
        if (b.length < 40) { issues.push('Muy corto. Agrega contexto y resultado'); score -= 15; }
        return { bullet: b, score: Math.max(0, score), issues };
      });

      document.getElementById('bullets-results').innerHTML = results.map(r => {
        const color = r.score >= 70 ? 'var(--green)' : r.score >= 45 ? 'var(--yellow)' : 'var(--red)';
        return `<div class="bullet-row">
          <div class="bullet-score" style="background:${color}22;color:${color}">${r.score}</div>
          <div>
            <div style="font-size:13px;margin-bottom:3px">${r.bullet}</div>
            ${r.issues.map(i=>`<div style="font-size:11px;color:var(--muted)">→ ${i}</div>`).join('')}
          </div>
        </div>`;
      }).join('');
    }

    // ─── Toast ─────────────────────────────────────────────────────────────────
    function showToast(msg) {
      const t = document.createElement('div');
      t.textContent = msg;
      Object.assign(t.style, {
        position:'fixed', bottom:'20px', right:'20px', zIndex:9999,
        background:'var(--surface2)', border:'1px solid var(--green)', color:'var(--green)',
        padding:'10px 16px', borderRadius:'8px', fontSize:'13px', fontFamily:'var(--mono)',
        boxShadow:'0 4px 20px rgba(0,0,0,.4)', transition:'opacity .3s',
      });
      document.body.appendChild(t);
      setTimeout(() => { t.style.opacity='0'; setTimeout(()=>t.remove(), 300); }, 2500);
    }

    // ─── Init ──────────────────────────────────────────────────────────────────
    addExperience();
    addEducation();
    window.switchTab = switchTab;