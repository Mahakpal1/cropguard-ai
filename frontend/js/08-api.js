/* CropGuard frontend, part 08-api. Backend integration.
   When the API is reachable, its result replaces the in-browser simulated classifier (segmentation/severity still animate as before).
   If the API is missing or fails, the page falls back to demo mode and says so in the header chip.
   API base URL: ?api=http://host:8000/api/v1 in the page address, or window.CROPGUARD_API, or same-origin /api/v1. */
let API = (new URLSearchParams(location.search).get('api') || window.CROPGUARD_API || localStorage.getItem('cropguard_api_url') || '/api/v1').replace(/\/$/, '');
let apiInfo = null, apiRes = null, apiHeat = null, pendingFile = null, origFile = null;

function getApiCandidates() {
  const fromParam = new URLSearchParams(location.search).get('api');
  const fromWindow = window.CROPGUARD_API;
  const fromStorage = localStorage.getItem('cropguard_api_url');
  const candidates = [fromParam, fromWindow, fromStorage, API, '/api/v1', 'http://127.0.0.1:8000/api/v1', 'http://localhost:8000/api/v1'];
  return candidates.filter(Boolean).map(u => String(u).replace(/\/$/, ''));
}

async function probeApi() {
  const list = getApiCandidates();
  const seen = new Set();
  for (const url of list) {
    if (seen.has(url)) continue;
    seen.add(url);
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 2000);
      const r = await fetch(url + '/health', { cache: 'no-store', signal: ctrl.signal });
      clearTimeout(timer);
      if (r.ok) {
        API = url;
        try { localStorage.setItem('cropguard_api_url', url); } catch (_) {}
        apiInfo = await r.json();
        paintBackend();
        return url;
      }
    } catch (_) {}
  }
  return null;
}

/* keep the ORIGINAL photo (not the 224-px preview) for the server; capture phase runs before the page's own handlers */
document.addEventListener('change', e => { if (e.target.matches && e.target.matches('#file, #file2')) pendingFile = e.target.files[0] || null; }, true);
document.addEventListener('drop', e => { const f = e.dataTransfer && e.dataTransfer.files; if (f && f[0] && e.target.closest && e.target.closest('#drop')) pendingFile = f[0]; }, true);
{ const _ld = loaded; loaded = function () { origFile = pendingFile; pendingFile = null; _ld(); }; }

function paintBackend() {
  const chip = document.querySelector('.demo') || $('demoChip');
  const dot = $('modelDot');
  if (dot) dot.className = 'model-status-dot online';
  if (!apiInfo || !chip) return;
  const m = apiInfo.model;
  GATE = m.threshold;
  const gv = $('gateVal'); if (gv) gv.textContent = Math.round(GATE * 100) + '%';
  if (m.simulated) {
    chip.innerHTML = '<i style="color:#f59e0b">●</i> Backend connected · simulated';
  } else {
    chip.innerHTML = '<i style="color:#22c55e">●</i> Live AI model · ' + m.name;
    [3, 4].forEach(i => { const t = document.querySelector('#n' + i + ' .tg'); if (t) { t.className = 'tg live'; t.textContent = 'LIVE'; } });
    const b = document.querySelector('#n4 b'); if (b) b.textContent = 'Occlusion map';
  }
}

async function apiHealth() {
  const found = await probeApi();
  if (!found) {
    apiInfo = null;
    const chip = document.querySelector('.demo') || $('demoChip');
    const dot = $('modelDot');
    if (dot) dot.className = 'model-status-dot offline';
    if (chip) chip.innerHTML = '<i style="color:#ef4444">●</i> AI Server Offline (Run backend on port 8000)';
  }
}

async function apiPredict() {
  if (!apiInfo) await probeApi();
  const blob = origFile || await new Promise(r => src.toBlob(r, 'image/jpeg', 0.92));
  const fd = new FormData(); fd.append('file', blob, origFile ? origFile.name : 'leaf.jpg');

  const list = getApiCandidates();
  const seen = new Set();
  let lastErr = null;

  for (const ep of list) {
    if (seen.has(ep)) continue;
    seen.add(ep);
    try {
      const r = await fetch(ep + '/predict?explain=false', { method: 'POST', body: fd });
      if (r.ok) {
        API = ep;
        try { localStorage.setItem('cropguard_api_url', ep); } catch (_) {}
        const j = await r.json();
        apiHeat = null;
        if (j.heatmap) {
          const im = new Image();
          await new Promise((ok, no) => { im.onload = ok; im.onerror = no; im.src = 'data:image/png;base64,' + j.heatmap.png_base64; });
          const c = document.createElement('canvas'); c.width = c.height = W;
          c.getContext('2d').drawImage(im, 0, 0, W, W);
          apiHeat = c;
        }
        apiRes = j;
        apiInfo = { model: j.model };
        paintBackend();
        return j;
      }
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr || new Error('No backend reached');
}

/* heatmap from the server replaces the local proxy */
{ const _an = analyse; analyse = function () { const a = _an(); if (apiRes && apiHeat) a.heat = apiHeat; return a; }; }

/* server result -> the object the existing UI already understands */
{
  const _cl = classify;
  const TITLE = {
    low_confidence: ['Unsure \u2013 please retake the photo', 'पक्का नहीं \u2013 कृपया फोटो दोबारा लें'],
    unsupported_crop: ['Unsupported crop', 'असमर्थित फसल'],
    no_leaf: ['No clear leaf found', 'पत्ती साफ़ नहीं दिखी']
  };
  classify = function (a) {
    const j = apiRes;
    if (!j) {
      KB.offline = {
        n: ['AI Server Offline · Reconnect Backend', 'एआई सर्वर ऑफलाइन · बैकएंड कनेक्ट करें'],
        do: [
          ['Start the backend: run "uvicorn backend.app.main:app --port 8000" in project folder', 'Ensure your Python environment is active with dependencies installed', 'Once running, re-click Analyse Leaf to scan with AI'],
          ['प्रोजेक्ट फोल्डर में कमांड चलाएं: uvicorn backend.app.main:app --port 8000', 'जाँचें कि पोर्ट 8000 पर सर्वर चल रहा है', 'सर्वर शुरू होने के बाद दोबारा जांच करें']
        ],
        av: [
          ['Do not use offline mock for actual agricultural treatment decisions'],
          ['ऑफलाइन डेमो पर वास्तविक रासायनिक छिड़काव का निर्णय न लें']
        ],
        pr: [
          ['Connect backend to enable full 38-class leaf AI scanning across 14 crops'],
          ['वास्तविक एआई जांच के लिए बैकएंड कनेक्ट होना अनिवार्य है']
        ],
        sci: ''
      };
      SY.offline = [
        ['AI model server is not responding at http://127.0.0.1:8000 or /api/v1', 'Live AI classification across 38 crop disease classes requires the backend server'],
        ['बैकएंड एपीआई सर्वर से कनेक्शन नहीं बन पा रहा है', 'सटीक 38-क्लास एआई जांच के लिए बैकएंड चालू होना आवश्यक है']
      ];
      return {
        k: 'offline',
        c: 0.0,
        t3: [['AI Server Offline (Connect :8000)', 0.0]]
      };
    }
    a.pct = j.severity.affected_pct;
    const t3 = j.top3.map(x => [x.display.en, x.p]);
    const adv = j.advice;
    if (j.status !== 'ok') {
      const pc = x => Math.round(x * 100) + '%';
      const cand = j.top3.map(x => [x.display.en + ' (' + pc(x.p) + ')', x.display.hi + ' (' + pc(x.p) + ')']);
      let title = TITLE[j.status], note = [adv.en.symptoms, adv.hi.symptoms];
      if (j.status === 'low_confidence' && cand.length) {
        title = ['Not sure \u00b7 most likely ' + cand[0][0], 'पक्का नहीं \u00b7 सबसे संभावित ' + cand[0][1]];
        note = [adv.en.symptoms.concat(['Possible: ' + cand.map(c => c[0]).join(', ')]), adv.hi.symptoms.concat(['संभावित: ' + cand.map(c => c[1]).join(', ')])];
      } else if (j.status === 'unsupported_crop' && j.crop_id) {
        title = ['Crop not supported yet: ' + j.crop_id.name, 'यह फसल अभी समर्थित नहीं: ' + j.crop_id.name];
      }
      KB.low.n = title;
      KB.low.do = [adv.en.do_now, adv.hi.do_now]; KB.low.av = [adv.en.avoid, adv.hi.avoid]; KB.low.pr = [adv.en.prevent, adv.hi.prevent];
      KB.low.sci = '';
      SY.low = note;
      return { k: 'low', c: j.confidence, t3: t3.length ? t3 : [['\u2013', 0]] };
    }
    const id = j.class_id;
    KB[id] = { n: [j.display.en, j.display.hi], do: [adv.en.do_now, adv.hi.do_now], av: [adv.en.avoid, adv.hi.avoid],
               pr: [adv.en.prevent, adv.hi.prevent], sci: j.scientific_name ? '(' + j.scientific_name + ')' : '' };
    SY[id] = [adv.en.symptoms, adv.hi.symptoms];
    return { k: id, c: j.confidence, t3 };
  };
}

/* say how trustworthy the advice text is (reviewed / draft / generic) & render metadata badges */
{
  const _sh = show;
  show = function () {
    _sh();
    const tb = $('tierBadge'), cp = $('cropPill'), fb = $('fbBox');
    if (apiRes && apiRes.status === 'ok') {
      const t = { reviewed: 'advice: expert-reviewed', draft: 'advice: draft, awaiting expert review', none: 'advice: generic (no reviewed entry for this disease)' }[apiRes.advice_tier];
      $('gate').textContent += ' \u00b7 ' + t;

      if (tb) {
        tb.hidden = false;
        tb.className = 'tier-badge ' + (apiRes.advice_tier || 'none');
        const labels = { reviewed: '✓ Reviewed Advisory', draft: '⚡ Draft Advisory', none: 'ℹ Generic Advisory' };
        tb.textContent = labels[apiRes.advice_tier] || 'Advisory';
      }
      if (cp && apiRes.crop_id) {
        cp.hidden = false;
        cp.textContent = '🌿 ' + apiRes.crop_id.name + ' (' + Math.round(apiRes.crop_id.p * 100) + '%)';
      }
      if (fb) {
        fb.hidden = false;
        $('fbBtns').hidden = false;
        $('fbForm').hidden = true;
        $('fbDone').hidden = true;
      }
    } else if (apiRes) {
      $('gate').textContent = {
        low_confidence: 'result not reliable enough: below the confidence or margin gate',
        unsupported_crop: 'crop not recognised or not supported',
        no_leaf: 'no clear leaf found',
        unreliable_drift: 'attention drifted off leaf onto background (unreliable diagnosis - retake photo closer to leaf)',
      }[apiRes.status] || 'prediction uncertain';
      if (tb) tb.hidden = true;
      if (cp && apiRes.crop_id) {
        cp.hidden = false;
        cp.textContent = '🌿 ' + apiRes.crop_id.name + ' (' + Math.round(apiRes.crop_id.p * 100) + '%)';
      }
      if (fb) {
        fb.hidden = false;
        $('fbBtns').hidden = false;
        $('fbForm').hidden = true;
        $('fbDone').hidden = true;
      }
    } else {
      if (tb) tb.hidden = true;
      if (cp) cp.hidden = true;
      if (fb) fb.hidden = true;
    }

    /* Phase 6: Separated crop / disease confidence bars */
    const breakdown = $('confidenceBreakdown');
    if (breakdown) {
      if (apiRes && apiRes.crop_confidence != null && apiRes.disease_confidence != null) {
        breakdown.style.display = '';
        const cp2 = Math.round(apiRes.crop_confidence * 100);
        const dp  = Math.round(apiRes.disease_confidence * 100);
        const cb = $('cropConfBar'),    cv = $('cropConfVal');
        const db = $('diseaseConfBar'), dv = $('diseaseConfVal');
        if (cb) cb.style.width = cp2 + '%';
        if (cv) cv.textContent = cp2 + '%';
        if (db) db.style.width = dp + '%';
        if (dv) dv.textContent = dp + '%';
      } else {
        breakdown.style.display = 'none';
      }
    }

    /* Phase 6: Leaf-overlap grounding badge */
    const gBadge = $('groundingBadge');
    if (gBadge) {
      if (apiRes && apiRes.leaf_overlap_score != null) {
        gBadge.style.display = '';
        const pct      = Math.round(apiRes.leaf_overlap_score * 100);
        const grounded = apiRes.is_grounded;
        gBadge.className = 'grounding-badge ' + (grounded ? 'grounded' : 'drifted');
        gBadge.textContent = (grounded ? '\uD83C\uDF3F Grounded' : '\u26A0 Background Drift')
                             + ' \u00b7 Attention on leaf: ' + pct + '%';
        gBadge.title = apiRes.explainability_note || '';
      } else {
        gBadge.style.display = 'none';
      }
    }

    /* Phase 6: Top-2 alternative (shown when UNCERTAIN_CROP or low_confidence) */
    const top2el = $('top2Alt');
    if (top2el) {
      if (apiRes && apiRes.top2_crop) {
        top2el.style.display = '';
        top2el.textContent = 'Alt: ' + apiRes.top2_crop + ' \u00b7 ' + (apiRes.top2_disease || '')
                             + ' (' + Math.round((apiRes.top2_confidence || 0) * 100) + '%)';
      } else {
        top2el.style.display = 'none';
      }
    }

    if (typeof updateCropHealthAnalytics === 'function') {
      try { updateCropHealthAnalytics(); } catch (_) {}
    }
  };
}

/* Phase 4: Feedback and active learning submission handlers */
async function loadClassesForFeedback() {
  try {
    const r = await fetch(API + '/classes');
    if (!r.ok) return;
    const data = await r.json();
    const sel = $('fbSelect');
    if (!sel || !data.classes) return;
    sel.innerHTML = '<option value="">Select actual disease...</option>';
    data.classes.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = (c.crop ? c.crop.en : '') + ' - ' + (c.disease ? c.disease.en : c.id);
      sel.appendChild(opt);
    });
  } catch (_) {}
}

async function sendFeedback(payload) {
  try {
    const r = await fetch(API + '/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (r.ok) {
      $('fbBtns').hidden = true;
      $('fbForm').hidden = true;
      $('fbDone').hidden = false;
    }
  } catch (err) {
    console.warn('Feedback submit failed:', err);
  }
}

if ($('fbYes')) {
  $('fbYes').onclick = () => {
    if (!apiRes) return;
    sendFeedback({ scan_id: apiRes.id, is_correct: true });
  };
}
if ($('fbNo')) {
  $('fbNo').onclick = () => {
    $('fbForm').hidden = false;
  };
}
if ($('fbSubmit')) {
  $('fbSubmit').onclick = () => {
    if (!apiRes) return;
    const sel = $('fbSelect');
    const notes = $('fbNotes');
    sendFeedback({
      scan_id: apiRes.id,
      is_correct: false,
      corrected_class_id: sel ? sel.value || null : null,
      notes: notes ? notes.value || null : null
    });
  };
}

loadClassesForFeedback();

/* call the API in parallel with the visual animation */
{
  const _prev = (typeof window.runPipeline === 'function') ? window.runPipeline : (typeof run === 'function' ? run : null);
  run = async function () {
    if (busy) return;
    // Reset API state for this scan
    apiRes = null;
    apiHeat = null;

    // If image not ready, load sample first
    if (!ready) { sample(); await sl(200); }

    // Fire API predict in parallel (ALWAYS try backend even if initial probe was pending)
    const p = apiPredict().catch(e => {
      console.warn('Backend predict unreachable:', e);
      return null;
    });

    // Run the full 8-stage visual animation pipeline
    const animRunner = typeof _prev === 'function' ? _prev : (typeof window.runPipeline === 'function' ? window.runPipeline : null);
    let animErr = null;
    const animPromise = animRunner ? animRunner().catch(e => { animErr = e; console.error('Animation pipeline error:', e); }) : Promise.resolve();

    // Wait for API result concurrently while animation runs
    try {
      const j = await p;
      if (j) {
        apiRes = j;
        // Re-analyse with server heatmap overlay if available
        if (typeof analyse === 'function') A = analyse();
        if (typeof classify === 'function') R = classify(A);
      }
    } catch (e) {
      console.warn('API result error:', e);
    }

    // Now wait for the animation to fully complete
    await animPromise;

    // Final show() re-renders diagnosis with best available data
    if (!animErr && typeof show === 'function') show();
  };
  window.runPipeline = run;
  const rb = $('run');
  if (rb) rb.onclick = run;
}

apiHealth();

/* ── Model catalogue & live switcher ─────────────────────────────────────── */
const ALL_MODELS = [
  { id: 'dinov2_hierarchical',  label: 'DINOv2 Hierarchical (Research)' },
  { id: 'cropguard38_384',      label: 'ViT-384 Focal (Best ONNX)' },
  { id: 'cropguard38_combined', label: 'Combined 224px (Fast)' },
  { id: 'cropguard38_vit',      label: 'Base ViT 224px' },
  { id: 'cropguard38',          label: 'MobileNet/ResNet' },
  { id: 'cropguard38_recovered',label: 'Recovered ViT' },
  { id: 'community',            label: 'Community Pretrained' },
];

async function loadModelList() {
  const sel = $('modelSel');
  const dot = $('modelDot');
  if (!sel) return;

  let activeModel = sel.value || 'cropguard38_384';
  let availableList = ALL_MODELS.map(m => m.id);

  if (location.protocol !== 'file:' || new URLSearchParams(location.search).get('api') || window.CROPGUARD_API) {
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 4000);
      const r = await fetch(API + '/models', { cache: 'no-store', signal: ctrl.signal });
      clearTimeout(timer);
      if (r.ok) {
        const j = await r.json();
        if (j.active) activeModel = j.active;
        if (j.available && j.available.length) {
          // Merge keeping standard order first, then any custom backend models
          const backendSet = new Set(j.available);
          const ordered = ALL_MODELS.map(m => m.id);
          j.available.forEach(name => { if (!ordered.includes(name)) ordered.push(name); });
          availableList = ordered;
        }
        /* Update header chip */
        const chip = $('demoChip');
        if (chip && j.active_info) {
          const m = j.active_info;
          chip.innerHTML = `<i style="color:#22c55e">●</i> ${m.name}`;
        }
      }
    } catch (err) {
      console.warn('loadModelList info:', err);
    }
  }

  sel.innerHTML = availableList.map(name => {
    const known = ALL_MODELS.find(m => m.id === name);
    const label = known ? known.label : name;
    const active = name === activeModel;
    return `<option value="${name}"${active ? ' selected' : ''}>${label}${active ? ' ✓' : ''}</option>`;
  }).join('');
  sel.value = activeModel;

  if (dot) dot.className = 'model-status-dot';
}

async function switchModel(name) {
  const sel = $('modelSel');
  const dot = $('modelDot');
  if (dot) dot.className = 'model-status-dot switching';
  if (sel) sel.disabled = true;
  try {
    const r = await fetch(`${API}/models/switch?model_name=${encodeURIComponent(name)}`, { method: 'POST' });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: 'Switch failed' }));
      alert(`Model switch failed: ${err.detail || r.status}`);
      return;
    }
    const j = await r.json();
    /* Refresh health to pick up new model metadata */
    await apiHealth();
    /* Refresh model list dropdown */
    await loadModelList();
    console.log('Model switched to:', j.active_info);
  } catch (e) {
    console.warn('Model switch error:', e);
    alert('Could not switch model — is the backend running?');
  } finally {
    if (sel) sel.disabled = false;
    if (dot) dot.className = 'model-status-dot';
  }
}

if ($('modelSel')) {
  $('modelSel').addEventListener('change', e => {
    const name = e.target.value;
    if (name && name !== 'demo') switchModel(name);
  });
}

loadModelList();
