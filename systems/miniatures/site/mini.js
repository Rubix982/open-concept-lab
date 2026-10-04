// Systems in Miniature — shared page kit.
//
// Every simulation is Go (sims/), compiled to mini.wasm; a page calls
// run(name, params) and gets back the same JSON the terminal runner prints.
// The rest of this file is small UI pieces the pages share.

export const SERIES = [
  ["cache-router", "Routing for a shared prompt cache"],
  ["batching", "Continuous batching"],
  ["disagg", "Splitting prompt reading from writing"],
  ["straggler", "The one slow GPU"],
  ["double-charge", "The agent that charged twice"],
  ["herd", "A hundred agents, one rate limit"],
  ["local-first", "Local-first sync"],
];

// ---- the simulations
let ready;
function load() {
  ready ||= new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = "wasm_exec.js";
    s.onerror = () => reject(new Error("could not load wasm_exec.js"));
    s.onload = async () => {
      try {
        const go = new Go();
        addEventListener("mini-ready", () => resolve(), { once: true });
        // ?wasm=other.wasm loads a development build instead
        const file = new URLSearchParams(location.search).get("wasm") || "mini.wasm";
        let inst;
        try {
          inst = await WebAssembly.instantiateStreaming(fetch(file), go.importObject);
        } catch {
          // servers that don't send application/wasm
          const buf = await (await fetch(file)).arrayBuffer();
          inst = await WebAssembly.instantiate(buf, go.importObject);
        }
        go.run(inst.instance);
      } catch (e) { reject(e); }
    };
    document.head.appendChild(s);
  });
  return ready;
}

/** Run a simulation by name; params override its defaults. */
export async function run(name, params = {}) {
  await load();
  const out = JSON.parse(globalThis.miniRun(name, JSON.stringify(params)));
  if (out && out.error) throw new Error(out.error);
  return out;
}

// ---- page frame
/** Fill <nav class="series"> with the series links. */
export function series(current) {
  const nav = document.querySelector("nav.series");
  if (!nav) return;
  const i = SERIES.findIndex(([n]) => n === current);
  const prev = SERIES[i - 1], next = SERIES[i + 1];
  nav.innerHTML = `<a class="home" href="index.html">Systems in Miniature</a>
    <span class="steps">${SERIES.map(([n, t], k) => `<a href="${n}.html" title="${esc(t)}"${n === current ? ' aria-current="page"' : ""}>${k + 1}</a>`).join("")}</span>
    <span class="pn">${prev ? `<a href="${prev[0]}.html">← ${esc(prev[1])}</a>` : ""}${next ? `<a href="${next[0]}.html">${esc(next[1])} →</a>` : ""}</span>`;
}

export function fail(el, e) {
  el.innerHTML = `<div class="err">The simulation didn't load: ${esc(e.message || e)}. Serve this folder over HTTP (for example <code>python3 -m http.server</code>) rather than opening the file directly.</div>`;
  console.error(e);
}

// ---- formatting
export const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
export const fmt = {
  ms: (s) => s >= 10 ? `${s.toFixed(1)} s` : s >= 1 ? `${s.toFixed(2)} s` : `${Math.round(s * 1000)} ms`,
  pct: (x, d = 0) => `${(x * 100).toFixed(d)}%`,
  num: (x, d = 0) => x.toLocaleString(undefined, { maximumFractionDigits: d, minimumFractionDigits: d }),
  x: (x) => `${x.toFixed(x >= 10 ? 0 : 1)}×`,
};

// ---- colours
const cache = new Map();
let themeKey = "";
/** A CSS custom property's value, e.g. token("--ink"). */
export function token(name) {
  const k = document.documentElement.dataset.theme + matchMedia("(prefers-color-scheme: dark)").matches;
  if (k !== themeKey) { cache.clear(); themeKey = k; }
  if (!cache.has(name)) cache.set(name, getComputedStyle(document.documentElement).getPropertyValue(name).trim());
  return cache.get(name);
}
/** Categorical colour i (wraps after ten). */
export const cat = (i) => token(`--c${((i % 10) + 10) % 10}`);
/** A colour with alpha, from a hex token. */
export function alpha(hex, a) {
  const h = hex.replace("#", "");
  const n = parseInt(h.length === 3 ? h.replace(/./g, "$&$&") : h, 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}

// ---- controls
/** A labelled range slider. Returns {el, value}. */
export function slider(parent, { label, min, max, step = 1, value, format = (v) => v, onInput }) {
  const el = document.createElement("label");
  el.className = "ctl";
  el.innerHTML = `<span class="lab"><span>${esc(label)}</span><span class="val"></span></span><input type="range" min="${min}" max="${max}" step="${step}" value="${value}">`;
  const input = el.querySelector("input"), val = el.querySelector(".val");
  const show = () => (val.textContent = format(+input.value));
  show();
  let timer;
  input.addEventListener("input", () => { show(); clearTimeout(timer); timer = setTimeout(() => onInput(+input.value), 120); });
  parent.appendChild(el);
  return { el, get value() { return +input.value; }, set value(v) { input.value = v; show(); } };
}

/** A row of mutually exclusive buttons. options: [[value, label], ...]. */
export function segmented(parent, { label, options, value, onChange }) {
  const el = document.createElement("div");
  el.className = "ctl";
  el.innerHTML = `${label ? `<span class="lab"><span>${esc(label)}</span></span>` : ""}<span class="seg" role="group">${options.map(([v, l]) => `<button type="button" data-v="${esc(v)}">${esc(l)}</button>`).join("")}</span>`;
  const set = (v) => { value = v; el.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.v === String(v))); };
  set(value);
  el.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) { set(b.dataset.v); onChange(b.dataset.v); } });
  parent.appendChild(el);
  return { el, get value() { return value; }, set value(v) { set(v); } };
}

// ---- canvas
/** A canvas that fills its container's width at a fixed CSS height and keeps
 *  itself sharp; call .draw() to repaint with draw(ctx, w, h). */
export function stage(container, height, draw) {
  const canvas = document.createElement("canvas");
  container.appendChild(canvas);
  const ctx = canvas.getContext("2d");
  let w = 0, h = typeof height === "function" ? height(container.clientWidth) : height;
  const size = () => {
    const dpr = window.devicePixelRatio || 1;
    w = container.clientWidth;
    h = typeof height === "function" ? height(w) : height;
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    canvas.style.height = `${h}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  };
  const api = { canvas, ctx, draw() { ctx.clearRect(0, 0, w, h); draw(ctx, w, h); }, get w() { return w; }, get h() { return h; } };
  size();
  new ResizeObserver(() => { size(); api.draw(); }).observe(container);
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => api.draw());
  return api;
}

// ---- replay
/** Play/pause, a scrubber and speed for a simulated clock running 0..duration
 *  seconds. onFrame(t) is called whenever the time changes. */
export class Player {
  constructor(parent, { duration, speed = 1, speeds = [0.25, 1, 4, 16], onFrame, unit = "s" }) {
    this.duration = duration; this.speed = speed; this.t = 0; this.playing = false; this.onFrame = onFrame; this.unit = unit;
    const el = document.createElement("div");
    el.className = "player";
    el.innerHTML = `<button type="button" class="btn play">Play</button><input type="range" min="0" max="1000" value="0" aria-label="Time"><span class="t num"></span><span class="seg" role="group" aria-label="Speed">${speeds.map((s) => `<button type="button" data-s="${s}">${s < 1 ? s : s}×</button>`).join("")}</span>`;
    parent.appendChild(el);
    this.el = el;
    this.btn = el.querySelector(".play");
    this.range = el.querySelector("input");
    this.label = el.querySelector(".t");
    this.btn.addEventListener("click", () => (this.playing ? this.pause() : this.play()));
    this.range.addEventListener("input", () => { this.seek((this.range.value / 1000) * this.duration); });
    const setSpeed = (s) => { this.speed = s; el.querySelectorAll("[data-s]").forEach((b) => b.setAttribute("aria-pressed", +b.dataset.s === s)); };
    setSpeed(speed);
    el.querySelector(".seg").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) setSpeed(+b.dataset.s); });
    this.loop = this.loop.bind(this);
  }
  setDuration(d) { this.duration = d; this.seek(Math.min(this.t, d)); }
  seek(t) {
    this.t = Math.max(0, Math.min(this.duration, t));
    this.range.value = Math.round((this.t / this.duration) * 1000) || 0;
    this.label.textContent = `${this.t.toFixed(1)} / ${this.duration.toFixed(0)} ${this.unit}`;
    this.onFrame(this.t);
  }
  play() {
    if (this.t >= this.duration) this.seek(0);
    this.playing = true; this.btn.textContent = "Pause"; this.last = performance.now();
    requestAnimationFrame(this.loop);
  }
  pause() { this.playing = false; this.btn.textContent = this.t >= this.duration ? "Replay" : "Play"; }
  loop(now) {
    if (!this.playing) return;
    const dt = Math.min(0.1, (now - this.last) / 1000);
    this.last = now;
    this.seek(this.t + dt * this.speed);
    if (this.t >= this.duration) { this.pause(); return; }
    requestAnimationFrame(this.loop);
  }
}

/** Start playing once the panel scrolls into view (and not before). */
export function autoplay(player, el) {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); player.play(); } }, { threshold: 0.3 });
  io.observe(el);
}

// ---- comparison table
/** rows: [{key, label, cells: {...}}], cols: [{key, label, fmt, better: "low"|"high"}].
 *  Marks the best and worst value in each column; onPick(key) on row click. */
export function compare(table, { rows, cols, current, onPick }) {
  const best = {}, worst = {};
  for (const c of cols) {
    if (!c.better) continue;
    const vals = rows.map((r) => r.cells[c.key]);
    const lo = Math.min(...vals), hi = Math.max(...vals);
    best[c.key] = c.better === "low" ? lo : hi;
    worst[c.key] = c.better === "low" ? hi : lo;
  }
  table.innerHTML = `<thead><tr><th></th>${cols.map((c) => `<th>${esc(c.label)}</th>`).join("")}</tr></thead><tbody>${rows.map((r) =>
    `<tr data-k="${esc(r.key)}" class="${r.key === current ? "on" : ""}"><td>${esc(r.label)}</td>${cols.map((c) => {
      const v = r.cells[c.key];
      const cls = c.better && rows.length > 1 && best[c.key] !== worst[c.key] ? (v === best[c.key] ? "best" : v === worst[c.key] ? "worst" : "") : "";
      return `<td class="${cls}">${c.fmt ? c.fmt(v) : v}</td>`;
    }).join("")}</tr>`).join("")}</tbody>`;
  if (onPick) table.querySelectorAll("tbody tr").forEach((tr) => tr.addEventListener("click", () => onPick(tr.dataset.k)));
}

// ---- small chart helpers for canvas
/** Map a value into [a, b] pixels, optionally on a log scale. */
export function scale(d0, d1, r0, r1, log = false) {
  if (log) { const l0 = Math.log10(d0), l1 = Math.log10(d1); return (v) => r0 + ((Math.log10(Math.max(v, d0)) - l0) / (l1 - l0)) * (r1 - r0); }
  return (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
}

/** Axes with ticks; returns nothing, draws into ctx. */
export function axes(ctx, { x, y, xTicks = [], yTicks = [], box, xLabel, yLabel }) {
  ctx.save();
  ctx.font = `11px ${token("--sans") || "sans-serif"}`;
  ctx.fillStyle = token("--faint");
  ctx.strokeStyle = token("--rule");
  ctx.lineWidth = 1;
  for (const [v, l] of yTicks) {
    const py = Math.round(y(v)) + 0.5;
    ctx.beginPath(); ctx.moveTo(box.l, py); ctx.lineTo(box.r, py); ctx.stroke();
    ctx.textAlign = "right"; ctx.textBaseline = "middle"; ctx.fillText(l, box.l - 6, py);
  }
  ctx.textAlign = "center"; ctx.textBaseline = "top";
  for (const [v, l] of xTicks) ctx.fillText(l, x(v), box.b + 6);
  if (xLabel) { ctx.textAlign = "right"; ctx.fillText(xLabel, box.r, box.b + 20); }
  if (yLabel) { ctx.textAlign = "left"; ctx.textBaseline = "bottom"; ctx.fillText(yLabel, box.l, box.t - 6); }
  ctx.restore();
}

/** Linear interpolation and easing for animations. */
export const lerp = (a, b, k) => a + (b - a) * k;
export const ease = (k) => (k < 0 ? 0 : k > 1 ? 1 : k * k * (3 - 2 * k));
