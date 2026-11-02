/* CropGuard frontend – 02-scanner.js
   Ultra-Tech Multi-Stage Leaf Scanner + Model Switcher
   Stages:
     0 – RGB Capture (top-to-bottom laser sweep)
     1 – Normalise μ/σ  (grid overlay reveal left-to-right)
     2 – Leaf Segmentation (mask reveal + bbox)
     3 – Patch Division (ViT token grid, animated cell scan)
     4 – Pixel/Sub-patch Traversal (raster snake with neon spark trail)
     5 – Attention Heatmap Synthesis (dissolve overlay)
     6 – Lesion Radar Pinning (concentric rings at infection centres)
     idle – Ambient holographic animation (concentric rings + floating sparks)
*/

const cvr = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim() || '#3df5a0';
const cl  = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
let _idle = true;

/* ── Utility ──────────────────────────────────────────────────────────────── */
function rr(x, y, w, h, r) {
  cx.beginPath();
  if (cx.roundRect) cx.roundRect(x, y, w, h, r);
  else cx.rect(x, y, w, h);
}

/* ── Floating spark particles ─────────────────────────────────────────────── */
const _sparks = Array.from({ length: 28 }, () => ({
  x: Math.random() * W,
  y: Math.random() * W,
  speed: 0.2 + Math.random() * 0.7,
  size: 0.8 + Math.random() * 2.4,
  phase: Math.random() * Math.PI * 2,
  alpha: 0.2 + Math.random() * 0.65,
  hue: 140 + Math.random() * 40,
}));

function drawSparks() {
  cx.save();
  for (const p of _sparks) {
    p.y -= p.speed;
    p.x += Math.sin(p.phase + p.y * 0.038) * 0.4;
    if (p.y < 0) { p.y = W; p.x = Math.random() * W; }
    cx.beginPath();
    cx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    cx.fillStyle = `hsla(${p.hue},100%,72%,${p.alpha})`;
    cx.shadowColor = '#3df5a0';
    cx.shadowBlur = 10;
    cx.fill();
  }
  cx.restore();
}

/* ── Concentric Holographic Base Disc ─────────────────────────────────────── */
function drawHoloRings(now) {
  const cx0 = W / 2;

  cx.save();

  /* Base energy disc pedestal at the bottom */
  const baseY = W * 0.85, rxB = W * 0.44, ryB = W * 0.115;
  const gBase = cx.createRadialGradient(cx0, baseY, 0, cx0, baseY, rxB);
  gBase.addColorStop(0,   'rgba(61,245,160,0.42)');
  gBase.addColorStop(0.5, 'rgba(34,197,94,0.16)');
  gBase.addColorStop(1,   'rgba(0,0,0,0)');
  cx.fillStyle = gBase;
  cx.beginPath(); cx.ellipse(cx0, baseY, rxB, ryB, 0, 0, Math.PI * 2); cx.fill();
  cx.beginPath(); cx.ellipse(cx0, baseY, rxB, ryB, 0, 0, Math.PI * 2);
  cx.strokeStyle = '#3df5a0'; cx.lineWidth = 2.2;
  cx.shadowColor = '#3df5a0'; cx.shadowBlur = 18; cx.stroke();
  cx.beginPath(); cx.ellipse(cx0, baseY, rxB * 0.68, ryB * 0.68, 0, 0, Math.PI * 2);
  cx.strokeStyle = 'rgba(61,245,160,0.55)'; cx.lineWidth = 1.2; cx.stroke();

  cx.restore();
}

/* ── Corner HUD brackets + "AI Powered" chip ─────────────────────────────── */
function brackets(k = 1) {
  const a = cvr('--acc');
  const o = 6 + (1 - cl(k)) * 14;
  const L = 22;
  cx.save();
  cx.strokeStyle = a; cx.lineWidth = 2.4; cx.shadowColor = a; cx.shadowBlur = 12; cx.lineCap = 'square';
  [[o, o, 1, 1], [W - o, o, -1, 1], [o, W - o, 1, -1], [W - o, W - o, -1, -1]].forEach(([x, y, p, q]) => {
    cx.beginPath(); cx.moveTo(x + p * L, y); cx.lineTo(x, y); cx.lineTo(x, y + q * L); cx.stroke();
    cx.beginPath(); cx.arc(x + p * 5, y + q * 5, 1.4, 0, Math.PI * 2);
    cx.fillStyle = '#fff'; cx.fill();
  });
  /* Center crosshair */
  const hw = W / 2;
  cx.lineWidth = 1; cx.strokeStyle = 'rgba(61,245,160,0.35)';
  cx.beginPath(); cx.moveTo(hw - 10, hw); cx.lineTo(hw + 10, hw);
  cx.moveTo(hw, hw - 10); cx.lineTo(hw, hw + 10); cx.stroke();
  /* AI Powered chip */
  const bx = W - 70, by = 12;
  rr(bx, by, 58, 28, 7); cx.fillStyle = 'rgba(4,14,10,0.88)'; cx.shadowColor = a; cx.shadowBlur = 8; cx.fill();
  cx.strokeStyle = 'rgba(61,245,160,0.7)'; cx.lineWidth = 1.4; cx.stroke();
  cx.strokeStyle = '#3df5a0'; cx.lineWidth = 1;
  [by + 7, by + 13, by + 19].forEach(py => {
    cx.beginPath(); cx.moveTo(bx - 3, py); cx.lineTo(bx, py); cx.stroke();
    cx.beginPath(); cx.moveTo(bx + 58, py); cx.lineTo(bx + 61, py); cx.stroke();
  });
  cx.font = '700 9.5px system-ui, sans-serif'; cx.fillStyle = '#3df5a0'; cx.textAlign = 'center';
  cx.fillText('AI', bx + 29, by + 13);
  cx.font = '600 7.5px system-ui, sans-serif'; cx.fillStyle = '#e6fff1';
  cx.fillText('Powered', bx + 29, by + 22);
  cx.restore();
}

/* ── High-intensity laser scanline ───────────────────────────────────────── */
function beam(y, dir = 1) {
  const a = cvr('--acc');
  const trail = 56 * dir;
  const y0 = y - trail;
  const g = cx.createLinearGradient(0, y0, 0, y);
  g.addColorStop(0,    'rgba(61,245,160,0)');
  g.addColorStop(0.6,  'rgba(61,245,160,0.14)');
  g.addColorStop(1,    'rgba(61,245,160,0.44)');
  cx.save();
  cx.fillStyle = g; cx.fillRect(0, Math.min(y0, y), W, 56);
  /* White core */
  cx.fillStyle = '#fff'; cx.shadowColor = a; cx.shadowBlur = 20; cx.fillRect(0, y - 1, W, 2.5);
  /* Neon edge */
  cx.fillStyle = a; cx.fillRect(0, y + 1, W, 1); cx.restore();
}

/* ── Bounding box around leaf ROI ────────────────────────────────────────── */
function bbox(al) {
  if (!A) return;
  const [x0, y0, x1, y1] = A.bb;
  cx.save(); cx.globalAlpha = al;
  cx.strokeStyle = 'rgba(61,245,160,0.95)'; cx.lineWidth = 1.8;
  cx.shadowColor = '#3df5a0'; cx.shadowBlur = 8; cx.setLineDash([5, 4]);
  cx.strokeRect(x0, y0, x1 - x0, y1 - y0); cx.restore();
}

/* ── Status chip ─────────────────────────────────────────────────────────── */
function chip(x, y, s) {
  cx.save(); cx.font = '600 10.5px system-ui, sans-serif';
  const w = cx.measureText(s).width + 16;
  x = cl(x, 4, W - w - 4); y = cl(y, 4, W - 20);
  rr(x, y, w, 18, 9); cx.fillStyle = 'rgba(4,16,10,0.88)';
  cx.shadowColor = 'rgba(61,245,160,0.45)'; cx.shadowBlur = 6; cx.fill();
  cx.strokeStyle = 'rgba(61,245,160,0.55)'; cx.lineWidth = 1; cx.stroke();
  cx.fillStyle = '#e6fff1'; cx.textAlign = 'left'; cx.fillText(s, x + 8, y + 12.5);
  cx.restore();
}

/* ── Disease lesion hotspot detection ────────────────────────────────────── */
function pts() {
  if (A && A._p) return A._p;
  if (!A || !A.les) return [];
  const d = A.les.getContext('2d').getImageData(0, 0, W, W).data;
  const N = 14, c = W / N, cnt = Array(N * N).fill(0);
  for (let i = 0; i < W * W; i++) {
    if (d[i * 4 + 3]) cnt[((i / W / c) | 0) * N + (((i % W) / c) | 0)]++;
  }
  const tot = cnt.reduce((a, b) => a + b, 0) || 1, out = [];
  cnt.map((v, i) => [v, i]).sort((a, b) => b[0] - a[0]).forEach(([v, i]) => {
    if (v < 50 || out.length >= 4) return;
    const x = (i % N + 0.5) * c, y = ((i / N | 0) + 0.5) * c;
    if (out.every(p => Math.hypot(p.x - x, p.y - y) > 42)) out.push({ x, y, s: Math.round(v / tot * 100) });
  });
  return (A._p = out);
}

/* ── Lesion radar rings + HUD leader lines ───────────────────────────────── */
function drawPts(k) {
  const a = cvr('--acc'), now = performance.now();
  pts().forEach((p, n) => {
    const u = cl((k - 0.12 * n) / 0.3);
    if (u <= 0) return;
    cx.save(); cx.globalAlpha = u;
    const r = 5 + ((now / 60 + n * 6) % 18);
    cx.strokeStyle = `rgba(61,245,160,${Math.max(0, 1 - (r - 5) / 18) * 0.88})`;
    cx.lineWidth = 1.6;
    cx.beginPath(); cx.arc(p.x, p.y, r, 0, Math.PI * 2); cx.stroke();
    /* Second expanding ring (offset) */
    const r2 = 5 + ((now / 40 + n * 8 + 9) % 18);
    cx.strokeStyle = `rgba(255,180,0,${Math.max(0, 1 - (r2 - 5) / 18) * 0.5})`;
    cx.lineWidth = 1;
    cx.beginPath(); cx.arc(p.x, p.y, r2, 0, Math.PI * 2); cx.stroke();
    /* Core dot */
    cx.fillStyle = a; cx.shadowColor = a; cx.shadowBlur = 10;
    cx.beginPath(); cx.arc(p.x, p.y, 3.8, 0, Math.PI * 2); cx.fill(); cx.shadowBlur = 0;
    /* Leader line */
    cx.strokeStyle = 'rgba(255,255,255,0.82)'; cx.lineWidth = 1.2;
    cx.beginPath(); cx.moveTo(p.x + 3, p.y - 3); cx.lineTo(p.x + 16, p.y - 18); cx.lineTo(p.x + 28, p.y - 18); cx.stroke();
    chip(p.x + 28, p.y - 27, `L${n + 1} · ${p.s}%`);
    cx.restore();
  });
}

/* ══════════════════════════════════════════════════════════════════
   STAGE 4 – Raster pixel traversal with neon spark trail
   (a high-speed snake cursor scanning every cell in a 24×24 grid)
   ══════════════════════════════════════════════════════════════════ */
const _GRID = 24;
const _CELL = W / _GRID;
const _TOTAL = _GRID * _GRID;

/* Zigzag (boustrophedon) index → pixel coords */
function _cellPos(k) {
  const row = (k / _GRID) | 0;
  const col = row % 2 === 0 ? k % _GRID : _GRID - 1 - (k % _GRID);
  return { x: col * _CELL + _CELL / 2, y: row * _CELL + _CELL / 2 };
}

const _trail = [];   // [{x,y,age}] — neon green spark trail

function drawRasterStage(t) {
  /* How many cells have been visited this frame */
  const n = Math.floor(cl(t) * _TOTAL);

  cx.save();

  /* Dark translucent overlay so grid pops */
  cx.fillStyle = 'rgba(0,0,0,0.28)';
  cx.fillRect(0, 0, W, W);

  /* Draw grid lines */
  cx.strokeStyle = 'rgba(61,245,160,0.22)'; cx.lineWidth = 0.7;
  for (let k = 0; k <= _GRID; k++) {
    cx.beginPath(); cx.moveTo(k * _CELL, 0); cx.lineTo(k * _CELL, W); cx.stroke();
    cx.beginPath(); cx.moveTo(0, k * _CELL); cx.lineTo(W, k * _CELL); cx.stroke();
  }

  /* Shade scanned cells */
  for (let k = 0; k < n; k++) {
    const { x, y } = _cellPos(k);
    const age = n - k;
    const al = Math.max(0, 0.22 - age * 0.003);
    cx.fillStyle = `rgba(61,245,160,${al})`;
    cx.fillRect(x - _CELL / 2, y - _CELL / 2, _CELL, _CELL);
  }

  /* Trail sparks: keep last 18 positions */
  if (n > 0 && n <= _TOTAL) {
    const cur = _cellPos(n - 1);
    _trail.push({ x: cur.x, y: cur.y, age: 0 });
  }
  _trail.forEach(p => p.age++);
  while (_trail.length > 18) _trail.shift();

  _trail.forEach(p => {
    const al = Math.max(0, 1 - p.age / 18);
    const r  = Math.max(0.5, 3.5 - p.age * 0.18);
    const hue = 140 + p.age * 3;
    cx.beginPath(); cx.arc(p.x, p.y, r, 0, Math.PI * 2);
    cx.fillStyle = `hsla(${hue},100%,72%,${al})`;
    cx.shadowColor = '#3df5a0'; cx.shadowBlur = 8; cx.fill();
  });

  /* Cursor: current cell highlight */
  if (n > 0 && n <= _TOTAL) {
    const cur = _cellPos(n - 1);
    cx.strokeStyle = '#fff'; cx.lineWidth = 2;
    cx.shadowColor = '#3df5a0'; cx.shadowBlur = 14;
    cx.strokeRect(cur.x - _CELL / 2 + 1, cur.y - _CELL / 2 + 1, _CELL - 2, _CELL - 2);
  }

  cx.restore();
}

/* ══════════════════════════════════════════════════════════════════
   STAGE 3 – Grid patch division (ViT token grid)
   ══════════════════════════════════════════════════════════════════ */
function drawPatchStage(t) {
  const COLS = 7, cw = W / COLS;
  const total = COLS * COLS;
  cx.save();
  cx.fillStyle = 'rgba(0,0,0,0.22)'; cx.fillRect(0, 0, W, W);

  /* Reveal cells one-by-one */
  for (let k = 0; k < total; k++) {
    const al = cl(t * total - k) * 0.32;
    if (al > 0) {
      cx.fillStyle = `rgba(61,245,160,${al})`;
      cx.fillRect((k % COLS) * cw, ((k / COLS) | 0) * cw, cw, cw);
    }
  }

  /* Grid lines */
  cx.strokeStyle = 'rgba(61,245,160,0.48)'; cx.lineWidth = 1;
  for (let k = 0; k <= COLS; k++) {
    cx.beginPath(); cx.moveTo(k * cw, 0); cx.lineTo(k * cw, W); cx.stroke();
    cx.beginPath(); cx.moveTo(0, k * cw); cx.lineTo(W, k * cw); cx.stroke();
  }

  /* Active scanning token */
  const f = Math.min(total - 1, (t * total) | 0);
  cx.strokeStyle = '#fff'; cx.lineWidth = 2;
  cx.shadowColor = '#3df5a0'; cx.shadowBlur = 12;
  cx.strokeRect((f % COLS) * cw + 1, ((f / COLS) | 0) * cw + 1, cw - 2, cw - 2);
  cx.restore();
}

/* ══════════════════════════════════════════════════════════════════
   Main stage animation driver
   ══════════════════════════════════════════════════════════════════ */
function stage(i, t) {
  const now = performance.now();
  cx.clearRect(0, 0, W, W);
  cx.drawImage(src, 0, 0);

  drawHoloRings(now);
  drawSparks();

  const y    = W * t;
  const dir  = 1;

  /* Helper: reveal m from top to y */
  const rev = (m, al = 1) => {
    cx.save(); cx.beginPath(); cx.rect(0, 0, W, y); cx.clip();
    cx.globalAlpha = al; cx.drawImage(m, 0, 0); cx.restore();
  };
  const lay = (m, al) => { cx.globalAlpha = al; cx.drawImage(m, 0, 0); cx.globalAlpha = 1; };
  const tex = h => {
    cx.fillStyle = 'rgba(255,255,255,0.07)';
    for (let k = 0; k < h; k += 3) cx.fillRect(0, k, W, 1);
  };
  const dim = () => { cx.fillStyle = 'rgba(0,0,0,0.36)'; cx.fillRect(0, y, W, W - y); };

  if (i === 0) {
    /* Stage 0: Top-to-bottom laser beam sweep */
    dim(); tex(y); beam(y, dir);
    brackets(cl(t * 2.5));
    chip(8, W - 26, '① RGB Capture · 384²');

  } else if (i === 1) {
    /* Stage 1: Normalise – reveal grid pattern left to right */
    dim(); tex(y);
    cx.save(); cx.beginPath(); cx.rect(0, 0, W, y); cx.clip();
    cx.strokeStyle = 'rgba(61,245,160,0.38)'; cx.lineWidth = 0.9;
    for (let k = 0; k <= W; k += 16) {
      cx.beginPath(); cx.moveTo(k, 0); cx.lineTo(k, W);
      cx.moveTo(0, k); cx.lineTo(W, k); cx.stroke();
    }
    cx.restore();
    beam(y, dir); brackets(1);
    chip(8, W - 26, '② Normalise μ/σ · ImageNet stats');

  } else if (i === 2) {
    /* Stage 2: Leaf segmentation mask reveal */
    rev(A.mask); beam(y); bbox(t); brackets(1);
    if (t > 0.5) chip(A.bb[0], Math.max(8, A.bb[1] - 22), `Leaf ROI · ${(A.leafFrac * 100).toFixed(0)}%`);
    chip(8, W - 26, '③ Leaf Segmentation');

  } else if (i === 3) {
    /* Stage 3: ViT patch grid */
    lay(A.mask, 0.2); bbox(1);
    drawPatchStage(t);
    brackets(1);
    chip(8, W - 26, '④ ViT Patch Tokens · 7×7');

  } else if (i === 4) {
    /* Stage 4: Raster pixel traversal with neon spark trail */
    if (t === 0 || (t < 0.01 && _trail.length > 0)) _trail.length = 0;  // reset trail at start
    cx.clearRect(0, 0, W, W);
    cx.drawImage(src, 0, 0);
    lay(A.mask, 0.18); bbox(1);
    drawRasterStage(t);
    drawHoloRings(now); drawSparks();
    brackets(1);
    chip(8, W - 26, `⑤ Pixel Scan · ${(t * _TOTAL) | 0}/${_TOTAL} cells`);

  } else if (i === 5) {
    /* Stage 5: Attention heatmap dissolve */
    bbox(1); rev(A.heat); beam(y); brackets(1);
    chip(8, W - 26, '⑥ Attention Heatmap Synthesis');

  } else if (i === 6) {
    /* Stage 6: Lesion radar pinning */
    bbox(1); rev(A.les); beam(y);
    drawPts(cl((t - 0.3) / 0.7));
    brackets(1);
    chip(8, W - 26, `⑦ Lesion Radar · ${A.pct.toFixed(0)}% area`);

  } else {
    /* Stage 7: Lock-on complete */
    bbox(1); lay(A.les, 0.72);
    drawPts(1); brackets(1);
    /* Lock-on concentric glow rings */
    const hw = W / 2;
    const rp = 8 + ((performance.now() / 80) % 30);
    cx.save();
    cx.strokeStyle = `rgba(61,245,160,${Math.max(0, 1 - rp / 30) * 0.8})`;
    cx.lineWidth = 2;
    cx.beginPath(); cx.arc(hw, hw, rp, 0, Math.PI * 2); cx.stroke();
    cx.strokeStyle = `rgba(61,245,160,${Math.max(0, 1 - rp / 30) * 0.4})`;
    cx.beginPath(); cx.arc(hw, hw, rp + 12, 0, Math.PI * 2); cx.stroke();
    cx.restore();
    chip(8, W - 26, '✓ AI Diagnosis Complete');
  }
}

/* ── Idle holographic animation loop ─────────────────────────────────────── */
(function idle() {
  if (busy) _idle = false;
  if (ready && _idle && !busy) {
    const now = performance.now();
    const t   = (now % 4400) / 4400;
    const yv  = W * (0.5 - 0.5 * Math.cos(t * Math.PI * 2));

    cx.clearRect(0, 0, W, W);
    cx.drawImage(src, 0, 0);
    cx.fillStyle = 'rgba(0,8,4,0.14)'; cx.fillRect(0, 0, W, W);

    drawHoloRings(now);
    drawSparks();
    beam(yv, t < 0.5 ? 1 : -1);
    brackets(1);
    chip(8, W - 26, 'STANDBY · Ready to Scan');
  }
  requestAnimationFrame(idle);
})();
