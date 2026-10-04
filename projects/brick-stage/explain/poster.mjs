#!/usr/bin/env node
// node explain/poster.mjs <name> [ms] [--out file.jpg]   → out/<name>/poster.jpg
//
// A still from a built explainer (node explain/build.mjs <name> first), at
// the explainer's own size (1920×1080, 1080×1920, 1080×1080…), photographed
// by headless Chrome through the page's __renderAt, so it matches the video.
// Without ms it picks the moment the longest 3D build is finished and still
// on screen, in the longest stretch where its camera isn't moving; with no 3D
// stage, 40% of the way through.
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const outAt = args.indexOf("--out"), outArg = outAt >= 0 ? args.splice(outAt, 2)[1] : null;
const [name, msArg] = args;
if (!name) { console.log("usage: node explain/poster.mjs <name> [ms] [--out file.jpg]"); process.exit(1); }
const page = path.join(here, "..", "out", name, "index.html");
await fs.access(page).catch(() => { console.log(`no out/${name}/index.html — run node explain/build.mjs ${name} first`); process.exit(1); });
const out = outArg || path.join(here, "..", "out", name, "poster.jpg");

// ---- headless Chrome over the DevTools protocol (as render.mjs)
const cache = path.join(os.homedir(), "Library/Caches/ms-playwright");
const shells = (await fs.readdir(cache).catch(() => [])).filter((d) => d.startsWith("chromium_headless_shell")).sort().reverse()
  .map((d) => path.join(cache, d, "chrome-headless-shell-mac-arm64/chrome-headless-shell"));
let chromePath = null;
for (const c of [process.env.CHROME, ...shells, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"].filter(Boolean)) {
  try { await fs.access(c); chromePath = c; break; } catch {}
}
if (!chromePath) { console.log("no headless Chrome found (set CHROME=/path/to/chrome)"); process.exit(1); }
const port = 9700 + Math.floor(Math.random() * 200);
const profile = await fs.mkdtemp(path.join(os.tmpdir(), "explain-poster-"));
const chrome = spawn(chromePath, ["--headless", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--hide-scrollbars",
  `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "--window-size=1920,1080", "about:blank"], { stdio: "ignore" });
const done = async (code) => { try { chrome.kill(); } catch {} await fs.rm(profile, { recursive: true, force: true }).catch(() => {}); process.exit(code); };

let target;
for (let i = 0; i < 100 && !target; i++) {
  await new Promise((r) => setTimeout(r, 100));
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t) => t.type === "page"); } catch {}
}
if (!target) { console.log("couldn't reach headless Chrome"); await done(1); }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
let nextId = 1;
const pending = new Map();
ws.onmessage = (m) => { const msg = JSON.parse(m.data); if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); } };
const send = (method, params = {}) => new Promise((resolve, reject) => {
  const id = nextId++;
  pending.set(id, (msg) => (msg.error ? reject(new Error(`${method}: ${msg.error.message}`)) : resolve(msg.result)));
  ws.send(JSON.stringify({ id, method, params }));
});
const evaluate = async (expr) => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result.value;

await send("Page.enable");
await send("Page.navigate", { url: pathToFileURL(page).href + "?paused" });
for (let i = 0; i < 200; i++) {
  await new Promise((r) => setTimeout(r, 100));
  if (await evaluate("typeof window.__renderAt === 'function'").catch(() => false)) break;
}
const meta = await evaluate("({ w: window.TIMELINE.meta.w, h: window.TIMELINE.meta.h, dur: window.__duration })");
await send("Emulation.setDeviceMetricsOverride", { width: meta.w, height: meta.h, deviceScaleFactor: 1, mobile: false });

// the default moment: the longest 3D build, finished and still on screen
const ms = msArg != null ? +msArg : await evaluate(`(() => {
  const TL = window.TIMELINE, best = { len: -1, t: TL.meta.duration * 0.4 };
  for (const o of TL.objects.filter((o) => o.type === "stage3d")) {
    const tw = TL.tweens.filter((x) => x.id === o.id);
    const built = tw.find((x) => x.prop === "reveal"), len = built ? built.t1 - built.t0 : 0;
    const exit = tw.filter((x) => x.prop === "opacity" && x.to === 0 && x.t0 >= (built?.t1 ?? 0)).map((x) => x.t0)[0] ?? TL.meta.duration;
    if (len <= best.len) continue;
    // the longest stretch in that window where the camera isn't moving
    const moves = tw.filter((x) => ["az", "el", "dist", "focusK", "tx", "ty", "tz"].includes(x.prop) && x.t1 - x.t0 > 1).map((x) => [x.t0, x.t1]).sort((a, b) => a[0] - b[0]);
    let from = built.t1, still = [built.t1, built.t1];
    const end = Math.min(exit, TL.meta.duration);
    for (const [a, b] of [...moves, [end, end]]) { if (a > from && Math.min(a, end) - from > still[1] - still[0]) still = [from, Math.min(a, end)]; from = Math.max(from, b); }
    best.len = len; best.t = still[1] - still[0] > 400 ? (still[0] + still[1]) / 2 : (built.t1 + end) / 2;
  }
  return Math.round(best.t);
})()`);
await evaluate(`window.__renderAt(${ms})`);
await new Promise((r) => setTimeout(r, 150));
const shot = await send("Page.captureScreenshot", { format: "jpeg", quality: 88, clip: { x: 0, y: 0, width: meta.w, height: meta.h, scale: 1 } });
await fs.writeFile(out, Buffer.from(shot.data, "base64"));
console.log(`${path.relative(process.cwd(), out)} · ${meta.w}×${meta.h} at ${(ms / 1000).toFixed(1)} s`);
ws.close();
await done(0);
