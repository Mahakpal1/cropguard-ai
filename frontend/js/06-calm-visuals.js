/* CropGuard frontend, part 06-calm-visuals. Scripts share one global scope and MUST load in numeric order. */
/* Palettes for tiles/overlays and smooth post-run scrolling */
function recolor(c, fn) {
  const x = c.getContext('2d'), im = x.getImageData(0, 0, W, W), d = im.data;
  for (let i = 0; i < d.length; i += 4) {
    const o = fn(d[i], d[i + 1], d[i + 2], d[i + 3]);
    d[i] = o[0]; d[i + 1] = o[1]; d[i + 2] = o[2];
  }
  x.putImageData(im, 0, 0);
  return c;
}

const BG = [34, 44, 40];
const TINT = [[212, 128, 116], [122, 176, 134], [124, 154, 206]];
const mixc = (t, c) => BG.map((b, i) => Math.round(b + (c[i] - b) * t));

const _an = analyse;
analyse = function () {
  const a = _an();
  a.ch = a.ch.map((c, k) => recolor(c, (r, g, b) => mixc([r, g, b][k] / 255, TINT[k])));
  a.fl = a.fl.map(c => recolor(c, (r, g) => mixc(g / 255, [172, 206, 188])));
  recolor(a.mask, (r, g, b, al) => g > 100 ? [128, 184, 150] : [r, g, b]);
  recolor(a.les, () => [208, 112, 102]);
  recolor(a.heat, (r, g, b, al) => {
    const t = Math.min(1, al / 140), c0 = [236, 205, 120], c1 = [204, 98, 88];
    return c0.map((v, i) => Math.round(v + (c1[i] - v) * t));
  });
  return a;
};

const hx = (h, a) => {
  h = h.replace('#', '');
  if (h.length === 3) h = h.split('').map(c => c + c).join('');
  return 'rgba(' + parseInt(h.slice(0, 2), 16) + ',' + parseInt(h.slice(2, 4), 16) + ',' + parseInt(h.slice(4, 6), 16) + ',' + a + ')';
};

setTheme(document.documentElement.dataset.theme || 'light');
