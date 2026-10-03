// From any RGB colour to the nearest LEGO colour, by perceptual (CIE Lab)
// distance — plain RGB distance turns light greys pink. Used to colour shapes
// that come from scans, downloads and AI-made models.
import fs from "node:fs";
import zlib from "node:zlib";
import { COLORS } from "./parts.mjs";

// Match against one consistent reference: Rebrickable's RGB for each colour
// (our COLORS hex values are tuned for drawing, and mixing the two skews the
// match). Falls back to COLORS where the catalogue isn't downloaded yet.
let REF = null;
function refHex(code) {
  if (!REF) {
    REF = {};
    try {
      const f = new URL("../.cache/rebrickable/colors.csv.gz", import.meta.url);
      for (const l of zlib.gunzipSync(fs.readFileSync(f)).toString().split("\n").slice(1)) {
        const [id, , rgb] = l.split(","); if (rgb) REF[id] = `#${rgb}`;
      }
    } catch {}
  }
  return REF[code] || COLORS[code][2];
}

export function lab([r, g, b]) {
  const c = [r, g, b].map((v) => v / 255).map((v) => (v > 0.04045 ? ((v + 0.055) / 1.055) ** 2.4 : v / 12.92));
  const [x, y, z] = [[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]].map((m, i) => (m[0] * c[0] + m[1] * c[1] + m[2] * c[2]) / [0.9505, 1, 1.089][i]);
  const f = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
  return [116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))];
}
const hexRgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));

// `codes` limits the choice (e.g. to keep a model to a few colours).
export function nearestColour(rgb, codes = Object.keys(COLORS).map(Number)) {
  const want = lab(rgb);
  let best = codes[0], bestD = Infinity;
  for (const c of codes) {
    const l = lab(hexRgb(refHex(c))), d = Math.hypot(l[0] - want[0], l[1] - want[1], l[2] - want[2]);
    if (d < bestD) { bestD = d; best = c; }
  }
  return best;
}

// Per-triangle RGB (Uint8Array, 3 per triangle) to LEGO codes, cached by colour.
export function toLegoColours(rgb, codes) {
  const out = new Array(rgb.length / 3), cache = new Map();
  for (let i = 0; i < out.length; i++) {
    const key = (rgb[i * 3] << 16) | (rgb[i * 3 + 1] << 8) | rgb[i * 3 + 2];
    if (!cache.has(key)) cache.set(key, nearestColour([rgb[i * 3], rgb[i * 3 + 1], rgb[i * 3 + 2]], codes));
    out[i] = cache.get(key);
  }
  return out;
}

// For models whose colours have lighting baked in (AI-made and scanned
// models): first group the triangle colours into k clusters (k-means in Lab),
// so a yellow duck's hundreds of shades become one yellow, then give each
// cluster its nearest LEGO colour. Matching shade by shade instead sends the
// shadowed shades to browns.
export function clusterToLego(rgb, k = 6, codes) {
  const n = rgb.length / 3, labs = new Array(n);
  for (let i = 0; i < n; i++) labs[i] = lab([rgb[i * 3], rgb[i * 3 + 1], rgb[i * 3 + 2]]);
  // Cluster on colour with the shading divided out: shadow scales lightness
  // and saturation together, so a/(L+20), b/(L+20) stay put while L drops.
  // Lightness still counts a little, so black and white stay apart.
  const feat = (p) => [p[0] * 0.3, (p[1] / (p[0] + 20)) * 100, (p[2] / (p[0] + 20)) * 100];
  const step = Math.max(1, Math.floor(n / 20000)), idx = [];
  for (let i = 0; i < n; i += step) idx.push(i);
  const F = idx.map((i) => feat(labs[i]));
  let seed = 7;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const d2 = (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2;
  const cents = [F[Math.floor(rnd() * F.length)]];
  while (cents.length < Math.min(k, F.length)) {                       // k-means++ start
    const w = F.map((p) => Math.min(...cents.map((c) => d2(p, c)))), total = w.reduce((a, b) => a + b, 0);
    let r = rnd() * total, i = 0; while ((r -= w[i]) > 0 && i < w.length - 1) i++;
    cents.push(F[i]);
  }
  const nearest = (f) => { let b = 0, bd = Infinity; cents.forEach((c, j) => { const d = d2(f, c); if (d < bd) { bd = d; b = j; } }); return b; };
  for (let round = 0; round < 15; round++) {                           // Lloyd's rounds
    const sum = cents.map(() => [0, 0, 0, 0]);
    for (const f of F) { const j = nearest(f); sum[j][0] += f[0]; sum[j][1] += f[1]; sum[j][2] += f[2]; sum[j][3]++; }
    sum.forEach((s, j) => { if (s[3]) cents[j] = [s[0] / s[3], s[1] / s[3], s[2] / s[3]]; });
  }
  // each cluster's colour as lit: the mean of its brightest quarter
  const members = cents.map(() => []);
  idx.forEach((i, m) => members[nearest(F[m])].push(labs[i]));
  const legoOf = members.map((ms) => {
    if (!ms.length) return null;
    const top = [...ms].sort((a, b) => b[0] - a[0]).slice(0, Math.max(1, Math.ceil(ms.length / 4)));
    return nearestLab([0, 1, 2].map((q) => top.reduce((s, p) => s + p[q], 0) / top.length), codes);
  });
  return labs.map((p) => legoOf[nearest(feat(p))]);
}
function nearestLab(want, codes = Object.keys(COLORS).map(Number)) {
  let best = codes[0], bestD = Infinity;
  for (const c of codes) {
    const l = lab(hexRgb(refHex(c))), d = Math.hypot(l[0] - want[0], l[1] - want[1], l[2] - want[2]);
    if (d < bestD) { bestD = d; best = c; }
  }
  return best;
}
