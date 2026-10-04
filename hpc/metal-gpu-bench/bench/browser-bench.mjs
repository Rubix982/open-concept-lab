#!/usr/bin/env node
// Measure the page's own browser engines (WebGPU vs JavaScript) once, and
// save them as results/browser-<date>.json for export.py to bake in.
//
//   CHROME=/path/to/chrome node browser-bench.mjs
//
// Launches Chrome headless with WebGPU on, opens site/index.html from disk,
// calls window.LiveBench.measureAll() (see site/live.js) and records the
// best steady-state rate of each engine at each size. Needs Node 22+.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const candidates = [
  process.env.CHROME,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ...(() => {
    const cache = path.join(os.homedir(), "Library/Caches/ms-playwright");
    try { return fs.readdirSync(cache).filter((d) => d.startsWith("chromium_headless_shell")).sort().reverse()
      .map((d) => path.join(cache, d, "chrome-headless-shell-mac-arm64/chrome-headless-shell")); } catch { return []; }
  })(),
].filter(Boolean);
const chrome = candidates.find((c) => fs.existsSync(c));
if (!chrome) { console.error("no Chrome found; set CHROME=/path/to/chrome"); process.exit(1); }

const port = 9400 + Math.floor(Math.random() * 400);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "gpu-bench-"));
const proc = spawn(chrome, ["--headless", "--enable-unsafe-webgpu", "--use-angle=metal", "--hide-scrollbars",
  `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
try {
  let tabs;
  for (let i = 0; i < 50 && !tabs; i++) { try { tabs = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); } catch { await wait(200); } }
  const version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
  const ws = new WebSocket(tabs.find((t) => t.type === "page").webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pend = {};
  ws.onmessage = (m) => { const d = JSON.parse(m.data); if (pend[d.id]) { pend[d.id](d.result); delete pend[d.id]; } };
  const send = (method, params = {}) => new Promise((r) => { pend[++id] = r; ws.send(JSON.stringify({ id, method, params })); });
  await send("Page.navigate", { url: "file://" + path.join(root, "site/index.html") });
  await wait(2000);
  console.log("measuring the engines (about a minute)…");
  const r = await send("Runtime.evaluate", { expression: "LiveBench.measureAll({ seconds: 2 })", awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || "measure failed");
  const m = r.result.value;
  console.log("measuring the hero's kernels at full size (about two minutes)…");
  const h = await send("Runtime.evaluate", { expression: "HeroBench.measure({ seconds: 3 })", awaitPromise: true, returnByValue: true });
  if (h.exceptionDetails) throw new Error(h.exceptionDetails.exception?.description || "hero measure failed");
  const hero = h.result.value;
  if (!m.webgpu) console.log("note: WebGPU was not available, so only the JavaScript engine was measured");
  const date = new Date().toISOString().slice(0, 10);
  const out = {
    date,
    browser: version.Browser.replace("HeadlessChrome", "Chrome (headless)"),
    loadAverage1m: os.loadavg()[0],
    method: `Best steady-state rate of each engine over about 2 seconds, measured once in ${version.Browser.replace("HeadlessChrome", "headless Chrome")} on this Mac, with no drawing. WebGPU: compute dispatches timed until the GPU reports them done. JavaScript: one core, in a worker. Rates are force calculations (N × (N − 1) per step) or cell updates per second. The JavaScript engine wasn't run above 4,096 bodies; one step would take seconds.`,
    nbody: m.nbody, stencil: m.stencil, webgpu: m.webgpu,
    hero, heroMethod: "The page's top animation at full size, compute only: the galaxy kernel tiles 256 bodies at a time through workgroup memory (unlike the plain kernel above), and the heat kernel is the stencil with three held-hot sources. Best rate over about 3 seconds after a warm-up. CPU: the same JavaScript on one core, where a step takes under two seconds; above 16,384 bodies it wasn't run.",
  };
  const file = path.join(root, "results", `browser-${date}.json`);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(out, null, 1));
  for (const g of hero.galaxy || []) console.log(`galaxy ${g.n}`.padEnd(16), "WebGPU", (g.gpuRate / 1e9).toFixed(1), "G/s", g.gpuStepsPerSec.toFixed(1), "steps/s", g.cpuRate ? `JS ${(g.cpuRate / 1e9).toFixed(3)} G/s` : "");
  for (const g of hero.heat || []) console.log(`heat ${g.size}²`.padEnd(16), "WebGPU", (g.gpuRate / 1e9).toFixed(1), "G/s", g.gpuStepsPerSec.toFixed(0), "steps/s", `JS ${(g.cpuRate / 1e9).toFixed(3)} G/s`);
  for (const row of [...m.nbody, ...m.stencil]) console.log(row.label.padEnd(16), "WebGPU", (row.gpu / 1e9).toFixed(2), "G/s  JS", row.cpu ? (row.cpu / 1e9).toFixed(3) + " G/s" : "–");
  console.log("wrote", path.relative(root, file), "— then: python3 export.py");
  ws.close();
} finally {
  proc.kill();
}
