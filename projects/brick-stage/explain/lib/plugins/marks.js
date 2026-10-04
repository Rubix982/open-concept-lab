// Math, code and emphasis for the blueprint layer.
//   math       LaTeX via MathJax 3 (SVG), drawn as an image that writes itself on
//   code       a code panel: line numbers, small syntax highlighter, focus bar
//   counter    a number that ticks from one value to another
//   underline, circle, brace, strike, highlight, arrowTo
//              marks that draw themselves on, around a box {x, y, w, h}, a 3D
//              anchor (resolved by the core into x, y), or another object of
//              this plugin: anchor { id, fx, fy } (a point in its bounds, 0..1)
//              or { id, line } (a line of a code panel).
(function () {
"use strict";
const { C, color, MONO, SANS, clamp, EASE, glow, noGlow, partial, smooth, arrowHead, hash, roundRect } = BP;
const BOUNDS = (BP.BOUNDS ||= {}); // id → { x, y, w, h, lines? } as last drawn

// ---- where a mark goes: its own box, or a box/point from another object
function target(p) {
  const a = p.anchor;
  if (a && a.id != null && BOUNDS[a.id]) {
    const b = BOUNDS[a.id];
    if (a.line != null && b.lines) {
      const l = b.lines[a.line]; if (l) return { x: l.x + l.w / 2 + (a.dx || 0), y: l.y + l.h / 2 + (a.dy || 0), w: p.w ?? l.w, h: p.h ?? l.h };
    }
    if (a.fx != null) return { x: b.x + b.w * a.fx + (a.dx || 0), y: b.y + b.h * (a.fy ?? 0.5) + (a.dy || 0), w: p.w ?? 40, h: p.h ?? 40 };
    return { x: b.x + b.w / 2 + (a.dx || 0), y: b.y + b.h / 2 + (a.dy || 0), w: p.w ?? b.w, h: p.h ?? b.h };
  }
  return { x: p.x, y: p.y, w: p.w ?? 120, h: p.h ?? 40 };
}

// ---- math: pre-rendered to images before the player starts
const MATH = (BP.MATH = new Map()); // key → { img, w, h } or { fail: true }
const mathKey = (p) => `${p.tex}|${p.size}|${p.color}`;
function loadMathJax() {
  if (window.MathJax?.tex2svg) return Promise.resolve(true);
  return new Promise((resolve) => {
    window.MathJax = { svg: { fontCache: "none" }, startup: { typeset: false }, options: { enableMenu: false } };
    const s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js";
    s.onload = () => (window.MathJax.startup?.promise || Promise.resolve()).then(() => resolve(true), () => resolve(false));
    s.onerror = () => resolve(false);
    document.head.appendChild(s);
    setTimeout(() => resolve(Boolean(window.MathJax?.tex2svg)), 12000);
  });
}
async function renderMath(p) {
  const key = mathKey(p);
  if (MATH.has(key)) return;
  try {
    // the promise form waits for extensions MathJax loads on demand (\color...)
    const node = await window.MathJax.tex2svgPromise(p.tex, { display: true }), svg = node.querySelector("svg");
    const vb = svg.getAttribute("viewBox").split(/\s+/).map(Number);
    const w = (vb[2] / 1000) * p.size, h = (vb[3] / 1000) * p.size;
    svg.setAttribute("width", w); svg.setAttribute("height", h);
    svg.setAttribute("color", color(p.color));
    svg.style.color = color(p.color);
    let src = new XMLSerializer().serializeToString(svg).replace(/currentColor/g, color(p.color));
    const img = new Image();
    return new Promise((resolve) => {
      img.onload = () => { MATH.set(key, { img, w, h }); resolve(); };
      img.onerror = () => { console.error("math image failed"); MATH.set(key, { fail: true }); resolve(); };
      img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(src);
    });
  } catch (e) { console.error("math render failed:", String(e)); MATH.set(key, { fail: true }); }
}
const mathObjs = BP.TL.objects.filter((o) => o.type === "math");
if (mathObjs.length) BP.ready.push(async () => {
  const ok = await loadMathJax();
  for (const o of mathObjs) {
    // every colour the object is ever given, so a colour change needs no render
    const colors = new Set([o.props.color, ...BP.TL.tweens.filter((t) => t.id === o.id && t.prop === "color").map((t) => t.to)]);
    for (const c of colors) {
      const p = { ...o.props, color: c };
      if (ok) await renderMath(p); else { console.error("MathJax did not load"); MATH.set(mathKey(p), { fail: true }); }
    }
  }
});

BP.register("math", (ctx, p, t, obj) => {
  const m = MATH.get(mathKey(p));
  const k = clamp(p.reveal);
  if (!m || m.fail) { // offline: the TeX itself
    ctx.font = `500 ${Math.round(p.size * 0.6)}px ${MONO}`; ctx.fillStyle = color(p.color); ctx.textBaseline = "middle";
    ctx.textAlign = p.align; const s = p.tex.slice(0, Math.ceil(p.tex.length * k)); ctx.fillText(s, p.x, p.y);
    const w = ctx.measureText(p.tex).width; BOUNDS[obj.id] = { x: p.align === "center" ? p.x - w / 2 : p.x, y: p.y - p.size * 0.4, w, h: p.size * 0.8 };
    return;
  }
  const x = p.align === "center" ? p.x - m.w / 2 : p.align === "right" ? p.x - m.w : p.x, y = p.y - m.h / 2;
  BOUNDS[obj.id] = { x, y, w: m.w, h: m.h };
  const edge = 46, rx = (m.w + edge) * EASE.inout(k) - edge; // the reveal front, with a soft leading edge
  if (p.color !== "ink" && p.color !== "dim") glow(ctx, color(p.color), 10); else glow(ctx, "rgba(160,190,255,0.3)", 8);
  if (rx > 0) ctx.drawImage(m.img, 0, 0, m.img.width, m.img.height, x, y, Math.min(rx, m.w), m.h);
  noGlow(ctx);
  const sx = m.img.width / m.w;
  for (let i = 0; i < 6; i++) { // fade across the edge in slices
    const a = rx + (i * edge) / 6, b = a + edge / 6;
    if (b <= 0 || a >= m.w) continue;
    const a0 = Math.max(0, a), b0 = Math.min(m.w, b);
    ctx.globalAlpha = ctx._alpha * (1 - (i + 0.5) / 6);
    ctx.drawImage(m.img, a0 * sx, 0, (b0 - a0) * sx, m.img.height, x + a0, y, b0 - a0, m.h);
  }
  ctx.globalAlpha = ctx._alpha;
  if (k > 0 && k < 1) { // the pen
    const px = x + clamp(rx, 0, m.w);
    ctx.strokeStyle = C.accent; ctx.lineWidth = 2; glow(ctx, C.accent, 12);
    ctx.beginPath(); ctx.moveTo(px, y + 4); ctx.lineTo(px, y + m.h - 4); ctx.stroke(); noGlow(ctx);
  }
});

// ---- code: a tiny tokenizer per language
const KW = {
  go: "break case chan const continue default defer else fallthrough for func go goto if import interface map package range return select struct switch type var nil true false",
  js: "async await break case catch class const continue default delete do else export extends false finally for from function if import in instanceof let new null of return super switch this throw true try typeof undefined var void while yield",
  python: "and as assert async await break class continue def del elif else except False finally for from global if import in is lambda None nonlocal not or pass raise return True try while with yield",
};
const TYPES = { go: "int int64 uint64 float64 string bool byte error any", js: "", python: "int float str bool list dict set tuple" };
function tokenize(line, lang) {
  const kw = new Set((KW[lang] || KW.js).split(" ")), types = new Set((TYPES[lang] || "").split(" ").filter(Boolean));
  const comment = lang === "python" ? "#" : "//";
  const out = [];
  const re = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`[^`]*`)|(\d+(?:\.\d+)?)|([A-Za-z_][A-Za-z0-9_]*)|(\s+)|(.)/g;
  const ci = line.indexOf(comment);
  // a comment marker outside a string starts a comment (good enough for samples)
  let code = line, rest = "";
  if (ci >= 0 && (line.slice(0, ci).split('"').length % 2 === 1)) { code = line.slice(0, ci); rest = line.slice(ci); }
  let m;
  while ((m = re.exec(code))) {
    const [tok, str, num, word] = m;
    let kind = "plain";
    if (str) kind = "string"; else if (num) kind = "number";
    else if (word) kind = kw.has(word) ? "keyword" : types.has(word) ? "type" : code[re.lastIndex] === "(" ? "call" : "plain";
    else if (/[{}()[\]]/.test(tok)) kind = "punct";
    out.push([tok, kind]);
  }
  if (rest) out.push([rest, "comment"]);
  return out;
}
const TOK_COLOR = { keyword: () => C.cyan, string: () => C.green, number: () => C.gold, comment: () => C.dim, type: () => C.violet, call: () => C.ink, punct: () => C.dim, plain: () => C.ink };

BP.register("code", (ctx, p, t, obj) => {
  const lines = (obj._lines ||= p.source.split("\n").map((l) => tokenize(l, p.lang)));
  const n = lines.length, lh = p.size * 1.55, padX = 22, gutter = p.size * 2.6, top = 46;
  ctx.font = `400 ${p.size}px ${MONO}`;
  const charW = ctx.measureText("M").width;
  const longest = Math.max(...p.source.split("\n").map((l) => l.length));
  const w = p.w ?? Math.max(360, gutter + padX * 2 + longest * charW), h = top + n * lh + 18;
  const x = p.x, y = p.y, k = clamp(p.reveal);
  // frame draws on, then the title tab
  ctx.strokeStyle = C.faint; ctx.lineWidth = 1.5;
  partial(ctx, [[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]], clamp(k * 3));
  if (k > 0.15) {
    ctx.fillStyle = "rgba(10,20,52,0.55)"; ctx.fillRect(x + 1, y + 1, w - 2, h - 2);
    ctx.strokeStyle = C.faint; ctx.beginPath(); ctx.moveTo(x, y + top - 12); ctx.lineTo(x + w, y + top - 12); ctx.stroke();
    ctx.font = `500 14px ${MONO}`; ctx.fillStyle = C.dim; ctx.textBaseline = "middle"; ctx.textAlign = "left";
    ctx.fillText(p.title || "", x + padX, y + (top - 12) / 2);
    ctx.fillStyle = C.faint; for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.arc(x + w - 22 - i * 16, y + (top - 12) / 2, 4, 0, Math.PI * 2); ctx.fill(); }
  }
  const linesBounds = [];
  for (let i = 0; i < n; i++) linesBounds.push({ x: x + gutter, y: y + top + i * lh - 2, w: Math.max(40, p.source.split("\n")[i].length * charW + 12), h: lh });
  BOUNDS[obj.id] = { x, y, w, h, lines: [null, ...linesBounds] }; // lines are 1-based
  // focus bar, moving smoothly to focusAt
  const focus = new Set(p.focus || []);
  if (focus.size && p.focusAt > 0) {
    const fy = y + top + (p.focusAt - 1) * lh - 2, fh = lh * (p.focusSpan || 1);
    ctx.fillStyle = "rgba(124,200,255,0.08)"; ctx.fillRect(x + 1, fy, w - 2, fh);
    ctx.fillStyle = C.accent; glow(ctx, C.accent, 8); ctx.fillRect(x + 1, fy, 3, fh); noGlow(ctx);
  }
  // lines type on, one after another
  const typed = k * 1.15 * n;
  ctx.textBaseline = "middle"; ctx.textAlign = "left";
  for (let i = 0; i < n; i++) {
    const shown = clamp(typed - i); if (shown <= 0) break;
    const ly = y + top + i * lh + lh / 2 - 2, dim = focus.size && !focus.has(i + 1);
    ctx.font = `400 ${p.size * 0.85}px ${MONO}`; ctx.fillStyle = C.faint; ctx.textAlign = "right";
    ctx.globalAlpha = ctx._alpha * (dim ? 0.5 : 1);
    ctx.fillText(String(i + 1), x + gutter - 14, ly);
    ctx.textAlign = "left"; ctx.font = `400 ${p.size}px ${MONO}`;
    const total = lines[i].reduce((a, [s]) => a + s.length, 0), upto = Math.ceil(total * shown);
    let cx = x + gutter, used = 0;
    ctx.globalAlpha = ctx._alpha * (dim ? 0.32 : 1);
    for (const [s, kind] of lines[i]) {
      if (used >= upto) break;
      const part = s.slice(0, upto - used); used += s.length;
      ctx.fillStyle = TOK_COLOR[kind]();
      ctx.fillText(part, cx, ly); cx += ctx.measureText(part).width;
    }
    if (shown < 1 && Math.floor(t / 250) % 2 === 0) { ctx.fillStyle = C.ink; ctx.fillRect(cx + 2, ly - p.size * 0.5, p.size * 0.5, p.size); }
  }
  ctx.globalAlpha = ctx._alpha;
});

// ---- counter
const FORMATS = {
  int: (v) => Math.round(v).toLocaleString("en-US"),
  comma: (v) => Math.round(v).toLocaleString("en-US"),
  ms: (v) => (v >= 1000 ? `${(v / 1000).toFixed(2)} s` : `${Math.round(v)} ms`),
  pct: (v) => `${(v * 100).toFixed(v < 0.1 ? 1 : 0)}%`,
  x: (v) => `${v.toFixed(v < 10 ? 1 : 0)}×`,
  s: (v) => `${v.toFixed(1)} s`,
  fixed1: (v) => v.toFixed(1), fixed2: (v) => v.toFixed(2),
};
BP.register("counter", (ctx, p, t, obj) => {
  const f = FORMATS[p.format] || FORMATS.int, text = (p.prefix || "") + f(p.value) + (p.suffix || "");
  ctx.globalAlpha = ctx._alpha * clamp(p.reveal * 12);
  ctx.font = `600 ${p.size}px ${MONO}`; ctx.textBaseline = "middle"; ctx.textAlign = p.align;
  const c = color(p.color); ctx.fillStyle = c; glow(ctx, c, p.color === "ink" ? 6 : 14);
  ctx.fillText(text, p.x, p.y); noGlow(ctx);
  const w = ctx.measureText(text).width, x0 = p.align === "center" ? p.x - w / 2 : p.align === "right" ? p.x - w : p.x;
  BOUNDS[obj.id] = { x: x0, y: p.y - p.size * 0.55, w, h: p.size * 1.1 };
  if (p.label) { ctx.font = `500 ${Math.round(p.size * 0.32)}px ${SANS}`; ctx.fillStyle = C.dim; ctx.fillText(p.label, p.x, p.y + p.size * 0.85); }
  ctx.globalAlpha = ctx._alpha;
});

// ---- marks
const markColor = (p) => color(p.color || "accent");
BP.register("underline", (ctx, p, t, obj) => {
  const b = target(p), c = markColor(p), y = b.y + b.h / 2 + (p.gap ?? 6);
  const pts = []; for (let i = 0; i <= 24; i++) { const u = i / 24; pts.push([b.x - b.w / 2 + u * b.w, y + (p.wavy ? Math.sin(u * Math.PI * 6) * 3 : (hash(i + obj.id.length * 31) - 0.5) * 1.6)]); }
  ctx.strokeStyle = c; ctx.lineWidth = p.width ?? 3; ctx.lineCap = "round"; glow(ctx, c, 10);
  partial(ctx, pts, clamp(p.reveal)); noGlow(ctx);
});
BP.register("strike", (ctx, p) => {
  const b = target(p), c = markColor(p);
  ctx.strokeStyle = c; ctx.lineWidth = p.width ?? 3; ctx.lineCap = "round"; glow(ctx, c, 10);
  partial(ctx, [[b.x - b.w / 2 - 6, b.y + 3], [b.x + b.w / 2 + 6, b.y - 3]], clamp(p.reveal)); noGlow(ctx);
});
BP.register("circle", (ctx, p, t, obj) => {
  const b = target(p), c = markColor(p), pad = p.pad ?? 10;
  const rx = b.w / 2 + pad, ry = b.h / 2 + pad, seed = obj.id.split("").reduce((a, ch) => a + ch.charCodeAt(0), 0);
  const pts = [], turns = 1.08, N = 90, a0 = -Math.PI * 0.62;
  for (let i = 0; i <= N; i++) { // a slightly irregular hand-drawn loop, a little past full
    const u = i / N, a = a0 + u * Math.PI * 2 * turns, wob = 1 + (hash(seed + Math.floor(u * 7)) - 0.5) * 0.07 + Math.sin(u * 9 + seed) * 0.02;
    pts.push([b.x + Math.cos(a) * rx * wob, b.y + Math.sin(a) * ry * wob * (1 + u * 0.04)]);
  }
  ctx.strokeStyle = c; ctx.lineWidth = p.width ?? 3; ctx.lineCap = "round"; glow(ctx, c, 12);
  partial(ctx, pts, EASE.inout(clamp(p.reveal))); noGlow(ctx);
});
BP.register("highlight", (ctx, p) => {
  const b = target(p), c = markColor(p), k = EASE.out(clamp(p.reveal)), pad = p.pad ?? 6;
  ctx.globalAlpha = ctx._alpha * (p.alpha ?? 0.2); ctx.fillStyle = c;
  ctx.fillRect(b.x - b.w / 2 - pad, b.y - b.h / 2 - pad, (b.w + pad * 2) * k, b.h + pad * 2);
  ctx.globalAlpha = ctx._alpha;
});
BP.register("brace", (ctx, p) => {
  // a curly brace along one side of the box: below (default), above, left or right
  const b = target(p), c = markColor(p), side = p.side || "below", d = p.depth ?? 16, gap = p.gap ?? 8;
  const horiz = side === "below" || side === "above", s = side === "below" || side === "right" ? 1 : -1;
  const L = horiz ? b.w : b.h, base = horiz ? b.y + s * (b.h / 2 + gap) : b.x + s * (b.w / 2 + gap);
  const pt = (u, v) => (horiz ? [b.x - b.w / 2 + u * L, base + s * v] : [base + s * v, b.y - b.h / 2 + u * L]);
  // a curly brace: curl out from each end, run straight, curl into the point
  const q = (a, b, cc, n) => { const out = []; for (let i = 0; i <= n; i++) { const u = i / n; out.push([(1 - u) ** 2 * a[0] + 2 * (1 - u) * u * b[0] + u * u * cc[0], (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * b[1] + u * u * cc[1]]); } return out; };
  const e = Math.min(0.08, (d * 1.2) / L), h = d / 2;
  const pts = [
    ...q([0, 0], [0, h], [e, h], 12), ...q([e, h], [0.25, h], [0.5 - e, h], 12),
    ...q([0.5 - e, h], [0.5, h], [0.5, d], 10), ...q([0.5, d], [0.5, h], [0.5 + e, h], 10),
    ...q([0.5 + e, h], [0.75, h], [1 - e, h], 12), ...q([1 - e, h], [1, h], [1, 0], 12),
  ].map(([u, v]) => pt(u, v));
  ctx.strokeStyle = c; ctx.lineWidth = p.width ?? 2.5; ctx.lineJoin = "round"; glow(ctx, c, 10);
  partial(ctx, pts, EASE.inout(clamp(p.reveal * 1.2))); noGlow(ctx);
  if (p.label && p.reveal > 0.5) {
    const [lx, ly] = pt(0.5, d + 14);
    ctx.globalAlpha = ctx._alpha * clamp((p.reveal - 0.5) * 3);
    ctx.font = `500 ${p.size ?? 22}px ${SANS}`; ctx.fillStyle = c; ctx.textBaseline = horiz ? (s > 0 ? "top" : "bottom") : "middle";
    ctx.textAlign = horiz ? "center" : s > 0 ? "left" : "right"; glow(ctx, c, 6);
    ctx.fillText(p.label, lx, ly); noGlow(ctx); ctx.globalAlpha = ctx._alpha;
  }
});
BP.register("arrowTo", (ctx, p) => {
  // from a fixed point (fx, fy) to the target, bending to one side, with a label at the start
  const b = target(p), c = markColor(p), to = [b.x + (p.tdx || 0), b.y + (p.tdy || 0)];
  const mid = [(p.fx + to[0]) / 2, (p.fy + to[1]) / 2], dx = to[0] - p.fx, dy = to[1] - p.fy, bend = p.bend ?? 0.25;
  const ctrl = [mid[0] - dy * bend, mid[1] + dx * bend];
  const pts = []; for (let i = 0; i <= 40; i++) { const u = i / 40; pts.push([(1 - u) ** 2 * p.fx + 2 * (1 - u) * u * ctrl[0] + u * u * to[0], (1 - u) ** 2 * p.fy + 2 * (1 - u) * u * ctrl[1] + u * u * to[1]]); }
  // stop short of the target so the head doesn't sit on it
  const end = pts.length - 3;
  ctx.strokeStyle = c; ctx.lineWidth = p.width ?? 2.5; ctx.lineCap = "round"; glow(ctx, c, 10);
  const { tip, dir } = partial(ctx, pts.slice(0, end), EASE.inout(clamp(p.reveal * 1.25)));
  if (p.reveal > 0.05) arrowHead(ctx, tip, dir, 13);
  noGlow(ctx);
  if (p.label) {
    ctx.globalAlpha = ctx._alpha * clamp(p.reveal * 4);
    ctx.font = `500 ${p.size ?? 22}px ${SANS}`; ctx.fillStyle = c; ctx.textBaseline = "middle"; ctx.textAlign = p.labelAlign || (dx >= 0 ? "right" : "left");
    ctx.fillText(p.label, p.fx + (dx >= 0 ? -12 : 12), p.fy); ctx.globalAlpha = ctx._alpha;
  }
});
})();
