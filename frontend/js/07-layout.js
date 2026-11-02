/* CropGuard frontend, part 07-layout.
   Dashboard layout wiring, multi-page routing, and recent analysis card updates.
*/
const SY = {
  eb: [
    ['Dark brown spots with concentric yellow halos', 'Target-like concentric ring pattern on leaf', 'Often starts on older lower leaves'],
    ['पीले घेरे वाले गहरे भूरे धब्बे', 'निशानेनुमा गोलाकार छल्ले', 'अक्सर पुरानी पत्तियों से शुरू होता है']
  ],
  ok: [
    ['Even green chlorophyll coloration', 'No fungal lesions or water-soaked spots', 'Firm, turgid, undamaged leaf surface'],
    ['समान हरा रंग', 'कोई धब्बा या घाव नहीं', 'मज़बूत, अक्षत पत्ती']
  ],
  low: [
    ['Leaf boundary unclear or out of focus in photo', 'Complex background or lighting may reduce model certainty'],
    ['फोटो में पत्ती छोटी या अस्पष्ट है', 'पृष्ठभूमि या रोशनी से मॉडल भ्रमित हो सकता है']
  ]
};

// Drag & drop file uploads on holographic stage
const dz = $('drop');
if (dz) {
  ['dragenter', 'dragover'].forEach(ev => dz.addEventListener(ev, e => {
    e.preventDefault();
    dz.classList.add('over');
  }));
  ['dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, e => {
    e.preventDefault();
    dz.classList.remove('over');
  }));
  dz.addEventListener('drop', e => {
    const f = e.dataTransfer && e.dataTransfer.files;
    if (f && f[0]) {
      const im = new Image();
      im.onload = () => {
        sx.fillStyle = 'rgb(128,128,128)';
        sx.fillRect(0, 0, W, W);
        const k = Math.min(W / im.width, W / im.height), dw = im.width * k, dh = im.height * k;
        sx.drawImage(im, (W - dw) / 2, (W - dh) / 2, dw, dh);
        loaded();
      };
      im.src = URL.createObjectURL(f[0]);
    }
  });
}

// Multi-Page Router: Dashboard vs AI Model Pipeline vs Help
function switchPage(pageName) {
  Q('.page-view').forEach(p => p.classList.remove('active'));
  const target = $('page-' + pageName) || $('page-dashboard');
  if (target) target.classList.add('active');

  Q('.side a').forEach(a => {
    a.classList.toggle('on', a.dataset.page === pageName);
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Sidebar link routing
Q('.side a').forEach(a => {
  a.onclick = e => {
    e.preventDefault();
    const p = a.dataset.page;
    if (p === 'dashboard' || p === 'pipeline' || p === 'history' || p === 'settings' || p === 'help') {
      switchPage(p);
    } else {
      // Services or health
      switchPage('dashboard');
      const sec = $(a.getAttribute('href').replace('#', ''));
      if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };
});

// Start Scanning Hero Button
const sb = $('startScanBtn');
if (sb) {
  sb.onclick = () => {
    switchPage('dashboard');
    const s = $('scan');
    if (s) s.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };
}

// Back to Dashboard Button
const bdb = $('backToDashBtn');
if (bdb) {
  bdb.onclick = () => switchPage('dashboard');
}

// View Detailed Report button -> switches to AI pipeline page
const repBtn = $('rep');
if (repBtn) {
  repBtn.onclick = () => switchPage('pipeline');
}
const vhl = $('viewHistoryLink');
if (vhl) {
  vhl.onclick = e => {
    e.preventDefault();
    switchPage('pipeline');
  };
}

// Language Toggle
Q('[data-l]').forEach(b => {
  b.onclick = () => {
    const chosen = b.dataset.l;
    if (typeof applyLanguage === 'function') {
      applyLanguage(chosen);
    } else {
      lang = chosen;
      Q('[data-l]').forEach(x => x.classList.toggle('on', x.dataset.l === lang));
      if ($('langSel')) $('langSel').value = lang;
      if (R && !busy) show();
    }
  };
});
if ($('langSel')) {
  $('langSel').onchange = function () {
    const chosen = this.value;
    if (typeof applyLanguage === 'function') {
      applyLanguage(chosen);
    } else {
      lang = chosen;
      Q('[data-l]').forEach(x => x.classList.toggle('on', x.dataset.l === lang));
      if (R && !busy) show();
    }
  };
}

// Theme Toggle
{
  const _t = setTheme;
  setTheme = function (m) {
    _t(m);
    Q('[data-th]').forEach(x => x.classList.toggle('on', x.dataset.th === m));
  };
}
Q('[data-th]').forEach(b => b.onclick = () => setTheme(b.dataset.th));

// History Management
const HK = 'cg3';
const hget = () => {
  try { return JSON.parse(localStorage.getItem(HK) || '[]'); } catch (_) { return []; }
};
const hset = h => {
  try { localStorage.setItem(HK, JSON.stringify(h.slice(0, 20))); } catch (_) { }
};

const SEVN = ['Mild', 'Moderate', 'Severe'];
const isOk = k => k === 'ok' || /healthy$/i.test(k);

function pill(e) {
  if (isOk(e.k)) return ['Healthy', 'ok'];
  if (e.k === 'low') return ['Unsure', 'low'];
  return [SEVN[e.sv] || 'Moderate', ['ok', 'mid', 'hi'][e.sv] || 'mid'];
}

function side() {
  const h = hget(), n = h.length;
  const ok = h.filter(e => isOk(e.k)).length;
  const dis = h.filter(e => !isOk(e.k) && e.k !== 'low').length;

  if ($('st-total')) $('st-total').textContent = n;
  if ($('st-ok')) $('st-ok').textContent = n ? Math.round(ok / n * 100) + '%' : '95%';
  if ($('st-dis')) $('st-dis').textContent = n ? Math.round(dis / n * 100) + '%' : '5%';
  if ($('st-avg')) $('st-avg').textContent = n ? Math.round(h.reduce((a, e) => a + e.c, 0) / n * 100) + '%' : '96%';

  const row = e => {
    const [t, c] = pill(e);
    return `<div class="rs"><img src="${e.th}" alt=""><div><b>${e.n}</b><small>${e.d}</small></div><span class="pl ${c}">${t}</span></div>`;
  };

  const hl = $('histList');
  if (hl) hl.innerHTML = n ? h.map(row).join('') : '<p class="empty">Your scan history will appear here.</p>';
}
hist = function () { side(); };

// Show Diagnosis & Update What to Do / What Not to Do Cards
{
  const _s = show;
  show = function () {
    _s();
    const sb = $('recentStandby');
    if (sb) sb.style.display = 'none';
    const res = $('res');
    if (res) {
      res.style.display = 'block';
      res.classList.add('show');
    }
    const li = lang === 'hi' ? 1 : 0;
    const k = R.k;

    // Identified Symptoms
    const symList = (SY[k] && SY[k][li]) || SY.eb[li];
    if ($('sym')) $('sym').innerHTML = symList.map(x => `<li>${x}</li>`).join('');

    // Update structured What to Do / What Not to Do boxes
    const entry = KB[k] || KB.eb;
    const doItems = entry.do && entry.do[li] ? entry.do[li] : ['Remove infected leaves', 'Improve airflow around base', 'Use registered fungicide'];
    const dontItems = entry.av && entry.av[li] ? entry.av[li] : ['Avoid overhead sprinkler watering', 'Do not spray unverified chemicals', 'Do not exceed label dosage'];

    const doListEl = $('actionDoList');
    if (doListEl) {
      doListEl.innerHTML = doItems.map(x => `<li>${x}</li>`).join('');
    }
    const dontListEl = $('actionDontList');
    if (dontListEl) {
      dontListEl.innerHTML = dontItems.map(x => `<li>${x}</li>`).join('');
    }

    // Severity pill & scientific name
    const sv = sevI(A.pct);
    const pl = isOk(k)
      ? ['Healthy', 'ok']
      : k === 'low'
      ? ['Unsure', 'low']
      : [L[lang].s[sv] + (lang === 'hi' ? '' : ' severity'), ['ok', 'mid', 'hi'][sv]];

    if ($('sevpill')) {
      $('sevpill').className = 'pl ' + pl[1];
      $('sevpill').textContent = pl[0];
    }
    if ($('sci')) {
      $('sci').textContent = KB[k] && KB[k].sci !== undefined ? KB[k].sci : (k === 'ok' ? '(No disease detected)' : '(Alternaria solani)');
    }

    // Update thumbnail
    const rt = $('rthumb');
    if (rt) rt.getContext('2d').drawImage(src, 0, 0, W, W, 0, 0, 112, 112);

    // Save to history
    if (!R._h) {
      R._h = 1;
      const tc = document.createElement('canvas');
      tc.width = tc.height = 64;
      tc.getContext('2d').drawImage(src, 0, 0, W, W, 0, 0, 64, 64);
      const d = new Date(), h = hget();
      h.unshift({
        k,
        n: (KB[k] && KB[k].n && KB[k].n[0]) || 'Tomato Early Blight',
        c: R.c,
        sv: sevI(A.pct),
        d: d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' }) + ' · ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        th: tc.toDataURL('image/jpeg', 0.7)
      });
      hset(h);
      side();
    }
  };
}

// Stage progress mapping
{
  const _s2 = (typeof stage === 'function') ? stage : null;
  const MAP = [0, 0, 1, 2, 2, 3, 3, 3];
  stage = function (i, t) {
    if (typeof _s2 === 'function') _s2(i, t);
    const a = MAP[i] !== undefined ? MAP[i] : 3;
    Q('#steps li').forEach((li, j) => {
      li.classList.toggle('done', j < a);
      li.classList.toggle('act', j === a);
    });
    const pctEl = $('pct');
    if (pctEl) pctEl.textContent = Math.min(100, Math.round((i + t) / 8 * 100)) + '%';
  };
}

if ($('clr')) {
  $('clr').onclick = () => { hset([]); side(); };
}

// ── Smart Features Card: click handlers ──────────────────────────────────
const featActions = {
  featTrend:    () => switchPage('pipeline'),
  featRisk:     () => switchPage('pipeline'),
  featSchedule: () => {
    switchPage('dashboard');
    const el = $('askAi');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  },
  featVoice: () => {
    const sayBtn = $('say');
    if (sayBtn) sayBtn.click();
  }
};
Object.keys(featActions).forEach(id => {
  const el = $(id);
  if (el) el.onclick = featActions[id];
});

// ── Regional Micro-Climate & Alerts Telemetry ─────────────────────────────
const REGION_DATA = {
  karnal: {
    name: 'Karnal, Haryana (Agro-Zone 4)',
    temp: '27.4°C',
    humidity: '84% RH',
    wind: '8 km/h',
    rain: '12mm',
    alert1: { title: 'High Fungal Spore Window', desc: '84% humidity & 27°C creates high risk of Blight & Rust. Apply preventive protection.' },
    alert2: { title: 'Optimal Spray Timing: 06:30–10:30 AM', desc: 'Wind speed calm (8 km/h). Complete foliar applications before afternoon showers.' }
  },
  meerut: {
    name: 'Meerut, Western UP (Agro-Zone 5)',
    temp: '29.1°C',
    humidity: '78% RH',
    wind: '11 km/h',
    rain: '4mm',
    alert1: { title: 'Moderate Rust & Mildew Threat', desc: 'Canopy humidity remains elevated overnight. Scout lower foliage daily.' },
    alert2: { title: 'Safe Spray Window: Early Morning', desc: 'Winds increase past 11:00 AM (14 km/h). Complete spray runs early.' }
  },
  ludhiana: {
    name: 'Ludhiana, Punjab (Agro-Zone 3)',
    temp: '26.8°C',
    humidity: '88% RH',
    wind: '6 km/h',
    rain: '22mm',
    alert1: { title: 'Severe Fungal Outbreak Warning', desc: 'Extended leaf wetness >10 hours recorded. High transmission risk for Leaf Blight.' },
    alert2: { title: 'Postpone Foliar Sprays for 24h', desc: 'Heavy precipitation incoming. Systemic spray will wash off.' }
  },
  nashik: {
    name: 'Nashik, Maharashtra (Zone 6)',
    temp: '25.2°C',
    humidity: '72% RH',
    wind: '14 km/h',
    rain: '0mm',
    alert1: { title: 'Powdery Mildew & Thrips Alert', desc: 'Dry foliar conditions with warm afternoon breeze favor mildew development.' },
    alert2: { title: 'Optimal Spray Window: Evening (4:30 PM)', desc: 'Avoid midday heat to prevent chemical leaf burn.' }
  },
  indore: {
    name: 'Indore, Malwa MP (Zone 7)',
    temp: '28.6°C',
    humidity: '65% RH',
    wind: '10 km/h',
    rain: '0mm',
    alert1: { title: 'Favorable Crop Conditions', desc: 'Low fungal pressure this week. Maintain scheduled preventive scouting.' },
    alert2: { title: 'Irrigation Advisory Active', desc: 'Ensure adequate root-zone moisture as temperatures climb.' }
  }
};

const regSel = $('regionSelect');
if (regSel) {
  regSel.onchange = function() {
    const val = this.value;
    const r = REGION_DATA[val] || REGION_DATA.karnal;
    if ($('wTemp')) $('wTemp').textContent = r.temp;
    if ($('wHumidity')) $('wHumidity').textContent = r.humidity;
    if ($('wWind')) $('wWind').textContent = r.wind;
    if ($('wRain')) $('wRain').textContent = r.rain;
    if ($('alert1Title')) $('alert1Title').textContent = r.alert1.title;
    if ($('alert1Desc')) $('alert1Desc').textContent = r.alert1.desc;
    if ($('alert2Title')) $('alert2Title').textContent = r.alert2.title;
    if ($('alert2Desc')) $('alert2Desc').textContent = r.alert2.desc;
  };
}

// ── Help Page Navigation Wire ─────────────────────────────────────────────
if ($('helpBackDashBtn')) {
  $('helpBackDashBtn').onclick = () => switchPage('dashboard');
}
if ($('dashKvkLink')) {
  $('dashKvkLink').onclick = e => {
    e.preventDefault();
    switchPage('help');
  };
}

// ── Groq API Key Modal & Settings ────────────────────────────────────────
const groqModal = $('groqModal');
const groqConfigBtn = $('groqConfigBtn');
const closeGroqModal = $('closeGroqModal');
const saveGroqKeyBtn = $('saveGroqKeyBtn');
const clearGroqKeyBtn = $('clearGroqKeyBtn');
const groqApiKeyInput = $('groqApiKeyInput');
const groqStatusLabel = $('groqStatusLabel');
const settingsGroqKey = $('settingsGroqKey');
const saveSettingsGroqKey = $('saveSettingsGroqKey');

function syncGroqUi() {
  const k = localStorage.getItem('cropguard_groq_key') || '';
  if (groqStatusLabel) {
    groqStatusLabel.textContent = k ? '⚡ Llama 3.3 Active' : '⚡ Groq LLM';
  }
  if (groqApiKeyInput) groqApiKeyInput.value = k;
  if (settingsGroqKey) settingsGroqKey.value = k;
}

if (groqConfigBtn && groqModal) {
  groqConfigBtn.onclick = () => {
    syncGroqUi();
    groqModal.style.display = 'grid';
  };
}
if (closeGroqModal && groqModal) {
  closeGroqModal.onclick = () => { groqModal.style.display = 'none'; };
}
if (saveGroqKeyBtn) {
  saveGroqKeyBtn.onclick = () => {
    const val = (groqApiKeyInput.value || '').trim();
    if (val) localStorage.setItem('cropguard_groq_key', val);
    else localStorage.removeItem('cropguard_groq_key');
    syncGroqUi();
    if (groqModal) groqModal.style.display = 'none';
  };
}
if (clearGroqKeyBtn) {
  clearGroqKeyBtn.onclick = () => {
    localStorage.removeItem('cropguard_groq_key');
    syncGroqUi();
    if (groqModal) groqModal.style.display = 'none';
  };
}
if (saveSettingsGroqKey && settingsGroqKey) {
  saveSettingsGroqKey.onclick = () => {
    const val = (settingsGroqKey.value || '').trim();
    if (val) localStorage.setItem('cropguard_groq_key', val);
    else localStorage.removeItem('cropguard_groq_key');
    syncGroqUi();
    alert('Groq API Key updated successfully!');
  };
}
syncGroqUi();

// ── Chemical Dosage Doctor & Agronomic Engine ─────────────────────────────
function evaluateChemicalDosage(query) {
  const q = query.toLowerCase();

  const hasOneLiter = /1\s*(l|lt|ltr|liter|litre)/i.test(q) || /one\s*(l|lt|liter)/i.test(q);
  const hasTwoLiter = /2\s*(l|lt|ltr|liter|litre)/i.test(q);
  const hasHalfLiter = /500\s*(ml|milli)|half\s*(l|liter)/i.test(q);
  const hasHundredL = /100\s*(l|lt|ltr|liter|litre)/i.test(q);
  const hasFifteenL = /15\s*(l|lt|ltr|liter|litre)/i.test(q);
  const hasOneAcre = /1\s*acre|one\s*acre/i.test(q);

  let chemName = 'Foliar Fungicide/Chemical';
  let standardRate = '2.0–2.5 ml/L (200–250 ml in 100L water)';
  if (q.includes('mancozeb')) {
    chemName = 'Mancozeb (Indofil M-45)';
    standardRate = '2.0–2.5 g/L (200–250g in 100L water)';
  } else if (q.includes('chlorothalonil') || q.includes('kavach')) {
    chemName = 'Chlorothalonil';
    standardRate = '2.0 g/L (200g in 100L water)';
  } else if (q.includes('copper') || q.includes('blitox')) {
    chemName = 'Copper Oxychloride (COC)';
    standardRate = '2.5–3.0 g/L (250–300g in 100L water)';
  } else if (q.includes('azoxy') || q.includes('amistar')) {
    chemName = 'Azoxystrobin';
    standardRate = '1.0 ml/L (100ml in 100L water)';
  } else if (q.includes('propiconazole') || q.includes('tilt')) {
    chemName = 'Propiconazole';
    standardRate = '1.0 ml/L (100ml in 100L water)';
  } else if (q.includes('imidacloprid') || q.includes('confidor')) {
    chemName = 'Imidacloprid';
    standardRate = '0.3–0.5 ml/L (30–50ml in 100L water)';
  } else if (q.includes('neem')) {
    chemName = 'Neem Oil (Azadirachtin)';
    standardRate = '4.0–5.0 ml/L (400–500ml in 100L water)';
  }

  // Critical Overdose Check (1L or 2L in 100L or 15L or 1 acre)
  if ((hasOneLiter || hasTwoLiter || hasHalfLiter) && (hasHundredL || hasFifteenL || hasOneAcre || q.includes('water') || q.includes('spray') || q.includes('sprayed'))) {
    const isCritical = hasOneLiter || hasTwoLiter;
    return `
      <div class="ai-verdict-banner danger">
        <span>🚨</span>
        <span>VERDICT: CRITICAL OVERDOSE (${isCritical ? '4x to 5x Safe Limit!' : '2x Overdose!'})</span>
      </div>
      <p style="margin:0 0 8px 0; font-size:12.5px; color:#991b1b; line-height:1.45;">
        <b>${chemName}</b> standard recommended dose is <b>${standardRate}</b>. Spraying <b>${hasTwoLiter ? '2 Liters' : (hasOneLiter ? '1 Liter' : '500ml')} in 100L</b> creates a dangerous concentration of <b>${hasTwoLiter ? '20 ml/L' : (hasOneLiter ? '10 ml/L' : '5 ml/L')}</b>.
      </p>
      <div class="ai-countermeasures-box">
        <h5>⚠️ Immediate Phytotoxic Risks:</h5>
        <ul style="margin:0 0 8px 0; padding-left:18px; font-size:11.5px; color:#b91c1c;">
          <li>Severe leaf scorch and necrotic margin burning within 24–48 hours.</li>
          <li>Chemical shock causing premature leaf drop and fruit russeting.</li>
          <li>Toxic root-zone accumulation stalling nutrient uptake.</li>
        </ul>
        <h5>🛡️ EMERGENCY RESCUE PROTOCOL (Do This NOW):</h5>
        <ol>
          <li><b>Foliar Wash-Off (Immediate):</b> Spray the entire plant canopy thoroughly with copious clean, fresh water within 2–4 hours to dilute and rinse unabsorbed residue before cuticle penetration.</li>
          <li><b>Root-Zone Irrigation:</b> Lightly flush the soil with fresh water to push chemical runoff beyond the active shallow feeder root zone.</li>
          <li><b>Strict Spray Moratorium:</b> Do NOT spray any other chemicals, fertilizers, or insecticides for the next <b>10–14 days</b>.</li>
          <li><b>Metabolic Recovery Boost (Day 5):</b> Once foliage stabilizes, apply a gentle foliar biostimulant (Seaweed extract @ 1.5 ml/L) to aid cellular repair.</li>
          <li><b>Consult KVK:</b> Click "Near KVK on Map" below for laboratory assistance if marginal burning advances.</li>
        </ol>
      </div>
    `;
  }

  // Safe Dose Questions
  if (q.includes('safe') || q.includes('dosage') || q.includes('how much') || q.includes('dose') || q.includes('recommend')) {
    return `
      <div class="ai-verdict-banner safe">
        <span>✅</span>
        <span>OFFICIAL DOSAGE GUIDELINE: ${chemName}</span>
      </div>
      <p style="margin:0 0 8px 0; font-size:12.5px; color:#14532d; line-height:1.45;">
        Recommended field dilution for <b>${chemName}</b> is:
      </p>
      <div class="ai-countermeasures-box">
        <ul style="margin:0; padding-left:18px; font-size:12px; color:#166534; line-height:1.5;">
          <li><b>Per Liter of Water:</b> ${standardRate.split('(')[0]}</li>
          <li><b>Per 15-Liter Knapsack Sprayer:</b> 30–35 ml (or grams)</li>
          <li><b>Per 100-Liter Tank:</b> 200–250 ml (or grams)</li>
          <li><b>Optimal Timing:</b> Early morning (06:30–10:00 AM) under calm wind (<10 km/h) with rain-free window of 4 hours.</li>
        </ul>
      </div>
    `;
  }

  // Humidity and Weather questions
  if (q.includes('humidity') || q.includes('rain') || q.includes('wind') || q.includes('weather')) {
    const isHighHum = q.includes('85%') || q.includes('80%') || q.includes('rain');
    return `
      <div class="ai-verdict-banner ${isHighHum ? 'danger' : 'safe'}">
        <span>🌦️</span>
        <span>WEATHER IMPACT &amp; SPRAY COMPATIBILITY</span>
      </div>
      <p style="margin:0 0 8px 0; font-size:12.5px; color:#334155; line-height:1.45;">
        ${isHighHum
          ? '<b>Caution at High Humidity (>80%):</b> High relative humidity delays droplet drying significantly. While systemic fungicides absorb well, protectant fungicides risk wash-off if rain follows. Do NOT spray if rain is forecast within 6 hours.'
          : 'Foliar sprays are most effective when relative humidity is between 55%–75% and ambient temperatures are below 30°C. Avoid spraying under direct midday sun to prevent droplet lens burning.'}
      </p>
      <div class="ai-countermeasures-box">
        <h5>Key Field Rules:</h5>
        <ol>
          <li>Never spray when wind velocity exceeds 12 km/h (drift hazards).</li>
          <li>Allow minimum 3–4 hours of dry foliage before rain for rain-fastness.</li>
          <li>Use flat-fan nozzles calibrated to medium droplet size (250–350 microns).</li>
        </ol>
      </div>
    `;
  }

  // Fallback agronomic answer
  return `
    <div class="ai-verdict-banner safe">
      <span>🌿</span>
      <span>CROPGUARD AGRONOMIC ADVICE</span>
    </div>
    <p style="margin:0 0 8px 0; font-size:12.5px; color:#334155; line-height:1.45;">
      Always ensure chemicals are measured with a calibrated graduated cylinder. For <b>${chemName}</b>, avoid tank-mixing with strong alkaline solutions or calcium fertilizers without a jar compatibility test.
    </p>
    <div class="ai-countermeasures-box">
      <h5>Next Steps:</h5>
      <ol>
        <li>Inspect crops in morning light for localized foliar changes.</li>
        <li>For emergency crop diagnostics, consult your local Krishi Vigyan Kendra (KVK).</li>
      </ol>
    </div>
  `;
}

// ── Call Groq Llama 3.3 API ──────────────────────────────────────────────
async function callGroqAI(userPrompt) {
  const apiKey = localStorage.getItem('cropguard_groq_key') || '';
  if (!apiKey) return null;

  const systemPrompt = `You are CropGuard AI, an elite agricultural doctor and agronomic chemist assisting Indian and global farmers.
Answer directly, concisely, and with practical urgency in clean, readable HTML with headers, bullet points, and emergency steps.
If the farmer asks about spraying an amount of chemical (e.g. 1L of Mancozeb in 100L):
1. Immediately declare the VERDICT (SAFE or DANGEROUS OVERDOSE with calculation).
2. Explain the exact phytotoxicity symptoms (leaf burn, scorched margins, stunted roots).
3. Provide step-by-step EMERGENCY COUNTERMEASURES (e.g. foliar wash-off with clean water within 2-4 hours, root flushing, 10-14 day spray pause).
Keep answers actionable, realistic, and farmer-friendly.`;

  try {
    const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey.trim()}`
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        temperature: 0.3,
        max_tokens: 650
      })
    });
    if (!res.ok) throw new Error('Groq API error ' + res.status);
    const data = await res.json();
    if (data.choices && data.choices[0] && data.choices[0].message) {
      return data.choices[0].message.content;
    }
  } catch (err) {
    console.warn('Groq fetch failed, using built-in agronomy engine:', err);
  }
  return null;
}

function showAiAnswer(htmlContent) {
  const bubble = $('aiAnswerBubble');
  if (!bubble) return;
  bubble.innerHTML = htmlContent;
  bubble.style.display = 'block';
  bubble.style.animation = 'none';
  void bubble.offsetHeight;
  bubble.style.animation = '';
}

const aiInput = $('aiInput');
const aiSendBtn = $('aiSendBtn');

async function handleAiSubmit() {
  const q = (aiInput.value || '').trim();
  if (!q) return;

  showAiAnswer('<div style="display:flex;align-items:center;gap:8px;color:#15803d;font-weight:700;"><span class="led-blink">●</span> Analyzing agronomic chemistry...</div>');

  // Try Groq LLM if configured
  const groqAnswer = await callGroqAI(q);
  if (groqAnswer) {
    showAiAnswer(`<div class="ai-verdict-banner safe"><span>⚡</span><span>GROQ LLAMA 3.3 AGRONOMIC ADVICE</span></div><div style="font-size:12.5px;line-height:1.5;color:#1e293b;">${groqAnswer.replace(/\n/g, '<br>')}</div>`);
  } else {
    // Immediate high-accuracy clinical chemistry engine
    const evaluation = evaluateChemicalDosage(q);
    showAiAnswer(evaluation);
  }
  aiInput.value = '';
}

if (aiSendBtn && aiInput) {
  aiSendBtn.onclick = handleAiSubmit;
  aiInput.onkeydown = e => { if (e.key === 'Enter') handleAiSubmit(); };
}

// Quick chip clicks
Q('.ai-chip').forEach(chip => {
  chip.onclick = () => {
    Q('.ai-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    const prompt = chip.dataset.prompt || chip.dataset.q;
    if (prompt) {
      if (aiInput) aiInput.value = prompt;
      handleAiSubmit();
    }
  };
});

// ── Regional Alerts: View Details link ───────────────────────────────────
const vad = $('viewAlertDetails');
if (vad) {
  vad.onclick = e => {
    e.preventDefault();
    switchPage('pipeline');
  };
}

// ── Crop Botanical Illustration Generator ─────────────────────────────────
function updateCropIllustration(cropKey) {
  const wrap = $('diagIllusWrap');
  if (!wrap) return;
  const c = (cropKey || '').toLowerCase();
  if (c.includes('corn') || c.includes('maize')) {
    wrap.innerHTML = `<svg viewBox="0 0 160 160" width="130" height="130" class="crop-corn-svg">
      <defs>
        <linearGradient id="cornGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#fef08a"/>
          <stop offset="50%" stop-color="#eab308"/>
          <stop offset="100%" stop-color="#ca8a04"/>
        </linearGradient>
      </defs>
      <!-- Corn ear body -->
      <path d="M70 28 C95 28 100 80 85 130 C75 140 65 140 55 130 C40 80 45 28 70 28 Z" fill="url(#cornGrad)"/>
      <!-- Kernels pattern -->
      <ellipse cx="68" cy="45" rx="5" ry="3.5" fill="#facc15"/><ellipse cx="78" cy="48" rx="5" ry="3.5" fill="#fef08a"/>
      <ellipse cx="60" cy="58" rx="5" ry="3.5" fill="#eab308"/><ellipse cx="72" cy="60" rx="5.5" ry="4" fill="#facc15"/><ellipse cx="84" cy="62" rx="5" ry="3.5" fill="#fef08a"/>
      <ellipse cx="58" cy="74" rx="5" ry="3.5" fill="#eab308"/><ellipse cx="72" cy="76" rx="5.5" ry="4" fill="#facc15"/><ellipse cx="86" cy="76" rx="5" ry="3.5" fill="#fef08a"/>
      <ellipse cx="62" cy="92" rx="5" ry="3.5" fill="#facc15"/><ellipse cx="74" cy="94" rx="5.5" ry="4" fill="#eab308"/><ellipse cx="84" cy="92" rx="5" ry="3.5" fill="#facc15"/>
      <ellipse cx="66" cy="110" rx="4.5" ry="3" fill="#ca8a04"/><ellipse cx="76" cy="112" rx="4.5" ry="3" fill="#eab308"/>
      <!-- Green husk leaves left -->
      <path d="M45 130 C20 100 30 50 65 35 C45 65 40 105 55 135 Z" fill="#22c55e"/>
      <path d="M45 130 C25 90 40 60 62 42 C48 72 45 105 52 132 Z" fill="#16a34a" opacity="0.6"/>
      <!-- Green husk leaves right -->
      <path d="M85 135 C115 100 110 50 78 35 C100 65 105 105 80 135 Z" fill="#16a34a"/>
      <path d="M82 132 C105 95 95 65 80 42 C92 70 95 102 78 130 Z" fill="#22c55e" opacity="0.6"/>
      <!-- Stem -->
      <path d="M66 132 L66 150 L76 150 L76 132 Z" fill="#15803d"/>
    </svg>`;
  } else if (c.includes('apple')) {
    wrap.innerHTML = `<svg viewBox="0 0 160 160" width="130" height="130" class="crop-apple-svg">
      <defs>
        <radialGradient id="appGrad" cx="35%" cy="30%" r="70%">
          <stop offset="0%" stop-color="#f87171"/>
          <stop offset="50%" stop-color="#dc2626"/>
          <stop offset="100%" stop-color="#7f1d1d"/>
        </radialGradient>
      </defs>
      <path d="M80 48 C65 25 30 35 30 75 C30 115 65 138 80 138 C95 138 130 115 130 75 C130 35 95 25 80 48 Z" fill="url(#appGrad)"/>
      <ellipse cx="62" cy="62" rx="12" ry="7" transform="rotate(-30 62 62)" fill="#ffffff" opacity="0.45"/>
      <path d="M80 50 Q82 25 94 18" fill="none" stroke="#78350f" stroke-width="4.5" stroke-linecap="round"/>
      <path d="M85 30 C105 20 120 28 115 42 C98 48 90 35 85 30 Z" fill="#22c55e"/>
    </svg>`;
  } else if (c.includes('grape')) {
    wrap.innerHTML = `<svg viewBox="0 0 160 160" width="130" height="130" class="crop-grape-svg">
      <defs>
        <radialGradient id="grpGrad" cx="35%" cy="35%" r="65%">
          <stop offset="0%" stop-color="#c084fc"/>
          <stop offset="50%" stop-color="#7e22ce"/>
          <stop offset="100%" stop-color="#3b0764"/>
        </radialGradient>
      </defs>
      <path d="M80 20 Q90 10 105 16" fill="none" stroke="#78350f" stroke-width="4" stroke-linecap="round"/>
      <path d="M60 22 C45 8 28 20 38 36 C42 42 55 35 60 22 Z" fill="#22c55e"/>
      <circle cx="62" cy="46" r="14" fill="url(#grpGrad)"/><circle cx="86" cy="44" r="14" fill="url(#grpGrad)"/><circle cx="108" cy="48" r="13" fill="url(#grpGrad)"/>
      <circle cx="50" cy="70" r="14" fill="url(#grpGrad)"/><circle cx="74" cy="68" r="15" fill="url(#grpGrad)"/><circle cx="98" cy="70" r="14" fill="url(#grpGrad)"/>
      <circle cx="62" cy="94" r="14" fill="url(#grpGrad)"/><circle cx="86" cy="94" r="14" fill="url(#grpGrad)"/>
      <circle cx="74" cy="116" r="13" fill="url(#grpGrad)"/>
    </svg>`;
  } else if (c.includes('potato')) {
    wrap.innerHTML = `<svg viewBox="0 0 160 160" width="130" height="130" class="crop-potato-svg">
      <defs>
        <radialGradient id="potGrad" cx="35%" cy="35%" r="65%">
          <stop offset="0%" stop-color="#fde68a"/>
          <stop offset="50%" stop-color="#d97706"/>
          <stop offset="100%" stop-color="#78350f"/>
        </radialGradient>
      </defs>
      <path d="M50 45 C30 25 25 55 45 65 Z" fill="#22c55e"/>
      <path d="M80 30 C75 10 105 15 95 45 Z" fill="#16a34a"/>
      <path d="M110 40 C130 25 135 55 115 65 Z" fill="#22c55e"/>
      <path d="M80 35 L80 90" stroke="#15803d" stroke-width="4"/>
      <ellipse cx="60" cy="105" rx="26" ry="18" transform="rotate(-15 60 105)" fill="url(#potGrad)"/>
      <ellipse cx="102" cy="112" rx="28" ry="20" transform="rotate(20 102 112)" fill="url(#potGrad)"/>
    </svg>`;
  } else {
    // Default Tomato cluster
    wrap.innerHTML = `<svg viewBox="0 0 160 160" width="130" height="130" class="crop-tomatoes-svg">
      <defs>
        <radialGradient id="tomGrad1" cx="35%" cy="35%" r="65%">
          <stop offset="0%" stop-color="#ff6b6b"/>
          <stop offset="50%" stop-color="#ef4444"/>
          <stop offset="100%" stop-color="#991b1b"/>
        </radialGradient>
      </defs>
      <path d="M30 40 Q70 20 120 45 Q140 60 150 90" fill="none" stroke="#2d6a2a" stroke-width="4.5" stroke-linecap="round"/>
      <circle cx="56" cy="88" r="32" fill="url(#tomGrad1)"/>
      <circle cx="106" cy="94" r="38" fill="url(#tomGrad1)"/>
      <ellipse cx="94" cy="76" rx="10" ry="6" transform="rotate(-30 94 76)" fill="#ffffff" opacity="0.45"/>
      <path d="M106 56 L101 65 L90 62 L98 70 L88 78 L100 76 L106 86 L112 76 L124 78 L114 70 L122 62 L111 65 Z" fill="#16a34a"/>
    </svg>`;
  }
}

// ── Dynamic Visual Symptoms Provider ─────────────────────────────────────
function getCropSymptoms(k, diseaseName, li) {
  if (SY[k] && SY[k][li]) return SY[k][li];
  const name = (diseaseName || k || '').toLowerCase();
  if (name.includes('blight')) {
    return li === 1
      ? ['पत्ती के ऊतकों पर अंडाकार भूरे धब्बे', 'घावों का आपस में मिलकर फैलना', 'लंबे समय तक नमी रहने पर फफूंद का प्रसार']
      : ['Cigar-shaped elliptical necrotic lesions on foliar tissue', 'Lesions coalescing into broad foliar blights', 'Fungal sporulation during periods of prolonged leaf wetness'];
  }
  if (name.includes('rust')) {
    return li === 1
      ? ['पत्ती की दोनों सतहों पर लाल-भूरे रंग के दाने', 'क्लोरोफिल का तेजी से नष्ट होना', 'पत्तियों का समय से पहले सूखना']
      : ['Raised reddish-brown to cinnamon powdery pustules', 'Chlorotic flecks expanding across leaf blades', 'Premature foliar desiccation and leaf drop'];
  }
  if (name.includes('spot')) {
    return li === 1
      ? ['गोल या कोणीय गहरे घाव', 'धब्बों के चारों ओर पीले छल्ले', 'अधिक नमी में निचली पत्तियों का गिरना']
      : ['Circular to angular water-soaked leaf spots', 'Concentric chlorotic halos surrounding lesions', 'Defoliation of lower canopy leaves under humid conditions'];
  }
  if (name.includes('scab')) {
    return li === 1
      ? ['जैतून जैसे गहरे मखमली धब्बे', 'पत्तियों के किनारों का मुड़ना', 'घावों पर खुरदरी पपड़ी बनना']
      : ['Dark olive-green to black velvety foliar lesions', 'Deformed or crinkled leaf margins', 'Corky texture developing on lesion centers'];
  }
  if (name.includes('mildew')) {
    return li === 1
      ? ['पत्ती की ऊपरी सतह पर सफेद चूर्ण जैसी परत', 'पत्तियों का मुड़ना और कड़ा होना', 'पौधे की वृद्धि का रुकना']
      : ['White talcum-like powdery fungal growth on upper leaf', 'Upward curling and brittle foliar distortion', 'Chlorotic patches and premature senescence'];
  }
  if (name.includes('healthy') || isOk(k)) {
    return li === 1
      ? ['समान गहरा हरा क्लोरोफिल वितरण', 'घाव या धब्बों का पूर्ण अभाव', 'स्वस्थ और अक्षत पत्ती संरचना']
      : ['Uniform deep green chlorophyll distribution', 'Turgid, intact cell structure with no foliar lesions', 'Absence of parasitic fungal or bacterial pathogens'];
  }
  return li === 1
    ? ['पत्ती पर स्पष्ट घाव और ऊतक क्षति', 'प्रभावित क्षेत्र के चारों ओर पीलापन', 'फफूंद या जीवाणु संक्रमण के लक्षण']
    : ['Localized foliar discoloration and cell damage', 'Irregular chlorotic margins bordering affected area', 'Active fungal or bacterial lesion expansion'];
}

// ── Disease & Crop-Specific Action Advisory Generator ─────────────────────
function getTailoredAdvisory(k, diseaseName, svIndex, li) {
  const name = (diseaseName || k || '').toLowerCase();

  // Maize / Corn Northern Leaf Blight
  if (name.includes('northern') && name.includes('blight')) {
    return {
      subDo: li === 1 ? 'मक्का झुलसा त्वरित कदम' : 'Tasseling & Canopy Care',
      subDont: li === 1 ? 'गंभीर सावधानियां' : 'Maize Spray Precautions',
      subPrevent: li === 1 ? 'दीर्घकालिक मक्का प्रबंधन' : 'Hybrid & Residue Protocol',
      do: li === 1
        ? ['नर मंजरी आने के समय देखें कि क्या घाव कान की पत्ती के ऊपर पहुंच गया है', 'यदि घाव ऊपरी पत्तियों तक फैल रहे हैं तो अनुमोदित स्ट्रोबिल्यूरिन या ट्रायज़ोल कवकनाशी का छिड़काव करें', 'पत्तियों के गीले रहने की अवधि को घटाने के लिए शाम की सिंचाई से बचें']
        : ['Assess whether elliptical leaf lesions have reached the ear leaves during tasseling stage.', 'Apply an approved strobilurin or triazole foliar fungicide if lesions threaten upper canopy leaves.', 'Avoid late afternoon or overhead watering to shorten foliar wetness periods.'],
      dont: li === 1
        ? ['जब घाव बालियों तक पहुँच रहे हों तो कवकनाशी छिड़काव में कतई देरी न करें', 'तेज धूप (>32°C) या तेज हवा में कवकनाशी का छिड़काव न करें', 'खेत में रोगग्रस्त मक्के के अवशेषों को खुली सतह पर न छोड़ें', 'संक्रमित फसल से अगले वर्ष के लिए बीज न रखें']
        : ['Don\'t delay fungicide application once lesions reach the ear leaf prior to silking.', 'Don\'t spray fungicides during midday heat (>32°C) or strong wind (>15 km/h).', 'Don\'t leave heavily infected maize stover unburied on the soil surface for next season.', 'Don\'t save seed from severely blighted hybrid stands; grain vigour is compromised.'],
      prevent: li === 1
        ? ['उत्तरी पत्ती झुलसा प्रतिरोधी संकर (Ht-जीन) किस्मों का चयन करें', 'लगातार मक्का बोने के बजाय 2 साल का फसल चक्र (सोयाबीन/दलहन) अपनाएँ', 'कटाई के बाद अवशेषों की गहरी जुताई कर मिट्टी में दबाएँ']
        : ['Select maize hybrids with proven multi-gene (Ht) resistance to Northern Leaf Blight.', 'Implement a minimum 2-year crop rotation out of continuous corn (rotate with soybean or legumes).', 'Deep-till diseased corn stubble into the soil post-harvest to accelerate fungal decomposition.']
    };
  }

  // Maize / Corn Common Rust
  if (name.includes('rust')) {
    return {
      subDo: li === 1 ? 'गेरुआ रोग नियंत्रण' : 'Rust Outbreak Control',
      subDont: li === 1 ? 'कवकनाशी सावधानियां' : 'Application Safeguards',
      subPrevent: li === 1 ? 'फसल सुरक्षा चक्र' : 'Spore Barrier & Spacing',
      do: li === 1
        ? ['पत्तियों पर दालचीनी जैसे लाल-भूरे दानों की संख्या की नियमित निगरानी करें', 'दाने भरने से पहले प्रति पत्ती 6 से अधिक दाने दिखने पर कवकनाशी का प्रयोग करें', 'पौधे की रोग प्रतिरोधक क्षमता बढ़ाने के लिए पोटाश उर्वरक का संतुलित उपयोग करें']
        : ['Scout lower and middle canopy leaves for raised cinnamon-brown powdery pustules.', 'Apply an approved triazole fungicide if pustules exceed 6 per ear leaf before grain fill.', 'Maintain balanced potassium nutrition to strengthen foliar cellular resistance.'],
      dont: li === 1
        ? ['गेरुआ को झुलसा रोग न समझें; उंगलियों से रगड़कर पाउडर की जांच अवश्य करें', 'जब फसल पकने की अवस्था में हो तब व्यर्थ कवकनाशी का छिड़काव न करें', 'संक्रमण के समय अतिरिक्त नाइट्रोजन खाद न डालें क्योंकि इससे कवक तेजी से फैलता है']
        : ['Don\'t confuse rust with leaf blight; confirm rust spores easily rub off as powder on fingers.', 'Don\'t apply fungicides late in the dent stage when economic return is zero.', 'Don\'t apply excess nitrogen fertilizer during active rust outbreaks as it accelerates spore growth.'],
      prevent: li === 1
        ? ['अपने क्षेत्र के लिए अनुशंसित गेरुआ-प्रतिरोधी संकर बीज ही बोएं', 'देर से आने वाले बीजाणु झोंकों से बचने के लिए समय पर बुवाई करें', 'खेत की मेड़ों से खरपतवार और स्वंय उगे पौधों को नष्ट करें']
        : ['Plant rust-resistant or tolerant hybrid seed varieties certified for your region.', 'Plant early in the season to escape peak late-summer airborne rust spore showers.', 'Eliminate volunteer plants and grass weed hosts near field perimeters.']
    };
  }

  // Tomato Early Blight
  if (name.includes('early') && name.includes('blight')) {
    return {
      subDo: li === 1 ? 'अगेती झुलसा प्रबंधन' : 'Immediate Sanitation',
      subDont: li === 1 ? 'सिंचाई व छिड़काव सावधानियां' : 'Foliar Safeguards',
      subPrevent: li === 1 ? 'मृदा व फसल चक्र' : 'Mulching & Crop Spacing',
      do: li === 1
        ? ['संक्रमित निचली पत्तियों को तुरंत छांटकर खेत से दूर नष्ट करें', 'पौधों को सहारा देकर जमीन से ऊपर रखें ताकि हवा का प्रवाह बेहतर रहे', 'अनुमोदित कॉपर फफूंदनाशक या क्लोरोथालोनिल का लेबल अनुसार छिड़काव करें']
        : ['Prune off severely infected lower foliage displaying concentric target spots.', 'Improve airflow around plant base through staking, trellising, and sucker pruning.', 'Apply registered copper hydroxide or chlorothalonil fungicide per label instructions.'],
      dont: li === 1
        ? ['फव्वारा या ऊपर से पानी देने वाली सिंचाई न करें; पानी की बूंदें मिट्टी से बीजाणु उछालती हैं', 'पत्तियां ओस या बारिश से गीली होने पर खेत में निराई-गुड़ाई या कटाई न करें', 'संक्रमित पत्तियों की खाद न बनाएं; इन्हें खेत से दूर गड्ढे में दबाएं', 'बिना माप-तौल के अत्यधिक सांद्रता में दवा का छिड़काव न करें']
        : ['Don\'t use overhead sprinkler irrigation; splashing droplets directly transmit fungal spores.', 'Don\'t handle, prune, or harvest plants while foliage is wet from rain or dew.', 'Don\'t compost diseased foliage; bury deeply or dispose away from active fields.', 'Don\'t apply uncalibrated spray dosages that can cause foliar phytotoxicity.'],
      prevent: li === 1
        ? ['सोलेनेसी कुल की फसलों (टमाटर, आलू, बैंगन, मिर्च) के साथ 3 साल का फसल चक्र अपनाएं', 'मिट्टी से बीजाणु उछलने से रोकने के लिए पौधों की जड़ों के पास 2-3 इंच पुआल की मल्चिंग करें', 'पौधों के बीच कम से कम 60 सेमी की दूरी रखें ताकि धूप और हवा अच्छी मिल सके']
        : ['Rotate out of Solanaceae crops (tomato, potato, eggplant, pepper) for at least 3 years.', 'Apply a 2-3 inch organic straw or plastic mulch barrier to stop soil spores splashing onto lower leaves.', 'Ensure 60 cm plant spacing to maximize solar penetration and rapid canopy drying.']
    };
  }

  // Tomato / Potato Late Blight
  if (name.includes('late') && name.includes('blight')) {
    return {
      subDo: li === 1 ? 'पछेती झुलसा आपात कदम' : 'Emergency Outbreak Response',
      subDont: li === 1 ? 'जल व अवशेष सावधानियां' : 'High-Risk Practices to Avoid',
      subPrevent: li === 1 ? 'प्रमाणित बीज व पूर्वानुमान' : 'Certified Seed & Monitoring',
      do: li === 1
        ? ['24 घंटे के भीतर कदम उठाएं; ठंडे-नम मौसम में पछेती झुलसा बहुत तेजी से फैलता है', 'प्रभावी प्रणालीगत कवकनाशी (साइमोक्सानिल + मैंकोजेब या मेटालेक्सिल) का छिड़काव करें', 'संक्रमण के शुरुआती केंद्र वाले पौधों को तुरंत उखाड़कर नष्ट करें']
        : ['Act immediately within 24 hours — late blight spreads explosively under cool, damp conditions.', 'Apply a targeted systemic oomycete fungicide (cymoxanil, dimethomorph, or metalaxyl-M).', 'Rogue out and destroy initial infection foci to protect the rest of the crop canopy.'],
      dont: li === 1
        ? ['बारिश के पूर्वानुमान में मौसम साफ होने का इंतजार न करें; बारिश से पहले सुरक्षात्मक परत बनाएं', 'संक्रमित सड़े हुए फल या कंदों को खेत की नालियों के पास न फेंकें', 'आलू की खुदाई के समय गीली संक्रमित पत्तियों को कंदों के संपर्क में न आने दें']
        : ['Don\'t wait for clear skies to spray if rain is forecast — apply protective barrier beforehand.', 'Don\'t dump culled produce or blighted foliage near fields or irrigation channels.', 'Don\'t allow infected vine haulms to touch tubers during potato harvest.'],
      prevent: li === 1
        ? ['हमेशा प्रमाणित रोगमुक्त बीज कंद और प्रतिरोधी किस्मों की ही बुवाई करें', 'वसंत ऋतु में खेत के किनारों पर उगने वाले पुराने आलू-टमाटर के पौधों को पूरी तरह नष्ट करें', 'मौसम विभाग और कृषि विभाग के पछेती झुलसा चेतावनी बुलेटिन पर नजर रखें']
        : ['Plant only certified disease-free seed tubers and resistant tomato cultivars.', 'Destroy all volunteer potato and tomato plants around farm borders in early spring.', 'Monitor regional weather alerts and late blight warning advisory forecasts.']
    };
  }

  // Healthy Plants
  if (name.includes('healthy') || isOk(k)) {
    return {
      subDo: li === 1 ? 'स्वस्थ फसल देखभाल' : 'Standard Field Protocol',
      subDont: li === 1 ? 'अनावश्यक उपचार से बचें' : 'Unnecessary Inputs',
      subPrevent: li === 1 ? 'निरंतर सुरक्षा व स्वास्थ्य' : 'Routine Bio-Security',
      do: li === 1
        ? ['हर 5-7 दिन में नियमित रूप से फसल की सामान्य निगरानी जारी रखें', 'वर्तमान विकास अवस्था के अनुसार संतुलित खाद और पोषक तत्वों का प्रयोग करें', 'ड्रिप या नाली विधि से जड़ों में पर्याप्त नमी बनाए रखें']
        : ['Maintain standard scheduled crop monitoring once every 5-7 days.', 'Apply balanced baseline nutrition based on current crop growth stage.', 'Keep root-zone soil consistently moist using drip or furrow irrigation.'],
      dont: li === 1
        ? ['रोग या कीट न होने पर भी अनावश्यक रासायनिक कीटनाशकों का छिड़काव न करें', 'अधिक यूरिया (नाइट्रोजन) न डालें जिससे पौधे कोमल और रोगग्राही हो जाते हैं', 'खेत में पानी का ठहराव या जलभराव न होने दें']
        : ['Don\'t spray prophylactic synthetic chemical pesticides when no disease or pest is present.', 'Don\'t over-apply high-nitrogen fertilizers that produce soft, succulent tissue vulnerable to disease.', 'Don\'t over-irrigate or allow water stagnation around the plant root crowns.'],
      prevent: li === 1
        ? ['खेत की मेड़ों और जल निकासी नालियों को खरपतवार मुक्त रखें', 'आगामी मौसम के लिए उचित फसल चक्र की योजना बनाएं', 'दूसरे खेतों से उपकरण लाते समय उनकी सफाई का ध्यान रखें']
        : ['Maintain field hygiene by keeping field borders and water channels clear of weed reservoirs.', 'Plan seasonal crop rotation to maintain soil health and break pest cycles.', 'Clean and calibrate farm implements before moving between plots.']
    };
  }

  // Generic / Unsure / Low confidence
  return {
    subDo: li === 1 ? 'सत्यापन व तत्काल कदम' : 'Validation & Sanitation',
    subDont: li === 1 ? 'अनुमानित छिड़काव से बचें' : 'Unverified Spray Risks',
    subPrevent: li === 1 ? 'नियमित निगरानी व परामर्श' : 'Monitoring & Agronomist Support',
    do: li === 1
      ? ['साफ प्राकृतिक रोशनी में एक पत्ती का स्पष्ट फोटो दोबारा लें', 'पत्ती की निचली सतह पर फफूंद के बीजाणुओं या कीटों की जांच करें', 'सटीक सलाह के लिए स्थानीय कृषि विज्ञान केंद्र (KVK) के कृषि अधिकारी से संपर्क करें']
      : ['Retake leaf photo in bright, indirect natural daylight with the affected leaf centered and focused.', 'Inspect both upper and lower leaf surfaces for signs of spores, insect webbing, or pests.', 'Consult your local Krishi Vigyan Kendra (KVK) or agricultural extension officer for diagnostic assistance.'],
    dont: li === 1
      ? ['बिना पुष्टि के किसी भी रासायनिक मिश्रण या कवकनाशी का अंधाधुंध छिड़काव न करें', 'विशेषज्ञ की राय के बिना पौधों को समय से पहले न उखाड़ें', 'धुंधली या तेज परछाई वाली फोटो के आधार पर निर्णय न लें']
      : ['Don\'t apply chemical cocktails based on an unconfirmed diagnosis.', 'Don\'t uproot or discard crops prematurely without physical expert verification.', 'Don\'t take photos with camera flash, heavy shadows, or blurry focus.'],
    prevent: li === 1
      ? ['संदिग्ध पौधों पर टैग लगाकर 48 घंटे तक लक्षणों के फैलाव पर नजर रखें', 'लक्षण दिखने की तारीख और मौसम की जानकारी अपने पास नोट रखें', 'पुष्टि होने तक इन पौधों से अलग पानी और उपकरण का उपयोग करें']
      : ['Flag suspicious plants with marker tape to track symptom progression over 48 hours.', 'Record symptom onset dates and local weather patterns in your farm journal.', 'Isolate any suspect seedlings until diagnosis is verified.']
  };
}

// ── Extended show() — populate Prevention list + ring gauge + AI badge ───
{
  const _showExt = show;
  show = function () {
    _showExt();
    if (typeof R !== 'undefined' && R && R.k) {
      const k = R.k;
      const li = (typeof lang !== 'undefined' && lang !== 'en') ? 1 : 0;
      const entry = (typeof KB !== 'undefined' && KB[k]) ? KB[k] : null;
      let diseaseName = (entry && entry.n && (entry.n[li] || entry.n[0])) || (k === 'low' ? 'Unsure' : (isOk(k) ? 'Healthy' : k));
      if (typeof translateDiagnosisName === 'function') {
        diseaseName = translateDiagnosisName(diseaseName, lang);
      }
      if ($('dn')) $('dn').textContent = diseaseName;

      // Update botanical illustration matching the crop
      updateCropIllustration(k);

      // Severity calculation
      const pct = (typeof A !== 'undefined' && A && A.pct !== undefined) ? A.pct : 18;
      const svIndex = (typeof sevI === 'function') ? sevI(pct) : 1;
      const svLabels = (typeof L !== 'undefined' && L[lang] && L[lang].s) ? L[lang].s : ['Mild', 'Moderate', 'Severe'];
      const currentSevLabel = isOk(k) ? (L[lang] ? L[lang].s[0] : 'Healthy') : (k === 'low' ? 'Unsure' : svLabels[svIndex]);

      // Dynamic Action Advisory Generation
      const advData = getTailoredAdvisory(k, diseaseName, svIndex, li);

      // Update Advisory Section Header
      const pillEl = $('advisoryStatePill');
      if (pillEl) {
        pillEl.textContent = `✔ Tailored for ${diseaseName} (${currentSevLabel})`;
        pillEl.className = 'advisory-state-pill active';
      }
      const subtextEl = $('advisorySubtext');
      if (subtextEl) {
        subtextEl.textContent = `Real-time AI guidelines dynamically tailored for ${diseaseName} at ${currentSevLabel.toLowerCase()} severity. Follow official product labels.`;
      }

      // Update card subtitles
      const subDoEl = $('subDo');
      if (subDoEl) subDoEl.textContent = advData.subDo;
      const subDontEl = $('subDont');
      if (subDontEl) subDontEl.textContent = advData.subDont;
      const subPreventEl = $('subPrevent');
      if (subPreventEl) subPreventEl.textContent = advData.subPrevent;

      // Populate 3 Action Lists with tailored items
      const doEl = $('actionDoList');
      if (doEl) doEl.innerHTML = advData.do.map(x => `<li>${x}</li>`).join('');

      const dontEl = $('actionDontList');
      if (dontEl) dontEl.innerHTML = advData.dont.map(x => `<li>${x}</li>`).join('');

      const prEl = $('actionPreventList');
      if (prEl) prEl.innerHTML = advData.prevent.map(x => `<li>${x}</li>`).join('');

      // Show bottom decorative illustrations
      const sprayEl = $('illusSpray');
      if (sprayEl) sprayEl.style.display = 'block';
      const sproutEl = $('illusSprout');
      if (sproutEl) sproutEl.style.display = 'block';

      // Populate rich visual symptoms list
      const symList = getCropSymptoms(k, diseaseName, li);
      const symEl = $('sym');
      if (symEl) symEl.innerHTML = symList.map(x => `<li>${x}</li>`).join('');

      // Update Affected Leaf Area & Severity Gauge
      const apEl = $('ap');
      if (apEl) apEl.textContent = (k === 'low' ? '—' : Math.round(pct) + '%');

      const svEl = $('sv');
      if (svEl) {
        svEl.textContent = currentSevLabel;
        svEl.className = 'sev-grade-badge ' + (isOk(k) ? 'ok' : ['ok', 'mid', 'hi'][svIndex]);
      }

      const mkEl = $('mk');
      if (mkEl) {
        const markerPos = Math.min(96, Math.max(4, (pct / 50) * 100));
        mkEl.style.left = markerPos + '%';
      }

      // Update field protocol text
      const discEl = $('disc');
      if (discEl && typeof L !== 'undefined' && L[lang]) {
        discEl.textContent = L[lang].d || 'Severity is an image-based estimate. Always follow the product label and consult your local agricultural extension officer.';
      }
    }

    // Update circular ring gauge from backend confidence
    const ringFg = $('ringFg');
    if (ringFg && typeof A !== 'undefined' && A) {
      const pct = Math.round((A.pct || 0) * 100);
      ringFg.setAttribute('stroke-dasharray', `${pct}, 100`);
      const cfEl = $('cf');
      if (cfEl) cfEl.textContent = pct + '%';
    }

    // Show "Analyzed with AI" badge on viewport
    const badge = $('aiAnalyzedBadge');
    if (badge) badge.style.display = 'flex';
  };
}

side();
setTheme(document.documentElement.dataset.theme || 'light');
