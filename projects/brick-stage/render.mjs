#!/usr/bin/env node
// node render.mjs <story> [--fps 60] [--size 1920x1080] [--from 0] [--to <ms>] [--out file.mp4] [--subs] [--no-audio]
//
// A story to video, frame by frame — no screen recording. Each frame is drawn
// at an exact moment (the player is a pure function of time), photographed
// whole by a headless Chrome so captions, callouts and bubbles come out as on
// screen, and streamed into ffmpeg as H.264. Slow machines just take longer;
// the video is the same. For quick drafts: --fps 30 --size 1280x720.
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { spawn } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const flag = (k, d) => { const i = args.indexOf(`--${k}`); return i >= 0 ? args.splice(i, 2)[1] : d; };
const fps = +flag("fps", 60), [W, H] = flag("size", "1920x1080").split("x").map(Number);
const from = +flag("from", 0), toArg = flag("to"), outArg = flag("out");
const burnSubs = args.includes("--subs"); if (burnSubs) args.splice(args.indexOf("--subs"), 1);
const silent = args.includes("--no-audio"); if (silent) args.splice(args.indexOf("--no-audio"), 1);
const name = args[0];
if (!name) { console.log("usage: node render.mjs <story> [--fps 60] [--size 1920x1080] [--from ms] [--to ms] [--out file.mp4]"); process.exit(1); }
const page = path.join(here, "out", name, "index.html");
await fs.access(page).catch(() => { console.log(`no out/${name}/index.html — run node build.mjs ${name} first`); process.exit(1); });
const out = outArg || path.join(here, "out", name, `${name}.mp4`);

// ---- a headless Chrome we can drive over the DevTools protocol
const shells = (await fs.readdir(path.join(os.homedir(), "Library/Caches/ms-playwright")).catch(() => []))
  .filter((d) => d.startsWith("chromium_headless_shell")).sort().reverse()
  .map((d) => path.join(os.homedir(), "Library/Caches/ms-playwright", d, "chrome-headless-shell-mac-arm64/chrome-headless-shell"));
let chromePath = null;
for (const c of [process.env.CHROME, ...shells, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"].filter(Boolean)) {
  try { await fs.access(c); chromePath = c; break; } catch {}
}
if (!chromePath) { console.log("no headless Chrome found (set CHROME=/path/to/chrome)"); process.exit(1); }
const port = 9300 + Math.floor(Math.random() * 600);
const chrome = spawn(chromePath, ["--headless", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--hide-scrollbars",
  `--remote-debugging-port=${port}`, `--window-size=${W},${H}`, `--user-data-dir=${path.join(os.tmpdir(), `brick-render-${port}`)}`, "about:blank"], { stdio: "ignore" });
const cleanup = () => { try { chrome.kill(); } catch {} };
process.on("exit", cleanup);

let target;
for (let i = 0; i < 100 && !target; i++) {
  await new Promise((r) => setTimeout(r, 100));
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t) => t.type === "page"); } catch {}
}
if (!target) { console.log("couldn't reach headless Chrome"); process.exit(1); }
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

await send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: false });
await send("Page.navigate", { url: `${pathToFileURL(page).href}?render${burnSubs ? "&subs" : ""}` });
for (let i = 0; i < 300; i++) {                        // wait for three.js to load from the CDN and the scene to build
  if (await evaluate("typeof window.__renderAt === 'function'").catch(() => false)) break;
  await new Promise((r) => setTimeout(r, 100));
}
const duration = await evaluate("window.__duration");
const to = Math.min(toArg ? +toArg : duration, duration);
const frames = Math.max(1, Math.round(((to - from) / 1000) * fps));

// ---- frames into ffmpeg
const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-i", "-",
  "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-movflags", "+faststart", out], { stdio: ["pipe", "inherit", "inherit"] });
const started = Date.now();
for (let f = 0; f < frames; f++) {
  await evaluate(`window.__renderAt(${from + (f * 1000) / fps})`);
  const { data } = await send("Page.captureScreenshot", { format: "jpeg", quality: 95, fromSurface: true });
  if (!ff.stdin.write(Buffer.from(data, "base64"))) await new Promise((r) => ff.stdin.once("drain", r));
  if (f % fps === 0 || f === frames - 1) {
    const done = (f + 1) / frames, el = (Date.now() - started) / 1000;
    process.stdout.write(`\r  ${name}: frame ${f + 1}/${frames} · ${(done * 100).toFixed(0)}% · ${el.toFixed(0)} s elapsed · ~${(el / done - el).toFixed(0)} s to go   `);
  }
}
ff.stdin.end();
await new Promise((r) => ff.on("close", r));
// the soundtrack: every sound the story makes, rendered offline by the page's
// own synth, then laid under the video
if (!silent) {
  const b64 = await evaluate(`window.__renderAudio(${from}, ${to})`);
  const wav = out.replace(/\.mp4$/, ".wav"), tmp = out.replace(/\.mp4$/, ".video.mp4");
  await fs.writeFile(wav, Buffer.from(b64, "base64"));
  await fs.rename(out, tmp);
  await new Promise((r, j) => spawn("ffmpeg", ["-y", "-loglevel", "error", "-i", tmp, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], { stdio: "inherit" }).on("close", (c) => (c ? j(new Error("ffmpeg mux failed")) : r())));
  await fs.rm(tmp); await fs.rm(wav);
}
// narration as captions YouTube accepts (.srt), timed to the rendered range
const lines = (await evaluate("window.__narration")).filter((n) => n.t + n.dur > from && n.t < to);
if (lines.length) {
  const stamp = (ms) => { ms = Math.max(0, ms - from); const h = Math.floor(ms / 3.6e6), m = Math.floor(ms / 6e4) % 60, s = Math.floor(ms / 1000) % 60; return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")},${String(Math.round(ms % 1000)).padStart(3, "0")}`; };
  const srt = lines.map((n, i) => `${i + 1}\n${stamp(n.t)} --> ${stamp(Math.min(n.t + n.dur, to))}\n${n.text}\n`).join("\n");
  await fs.writeFile(out.replace(/\.mp4$/, ".srt"), srt);
  console.log(`\n  captions → ${path.relative(process.cwd(), out.replace(/\.mp4$/, ".srt"))} (${lines.length} lines${burnSubs ? ", also burned into the video" : ""})`);
}
ws.close(); cleanup();
const mb = ((await fs.stat(out)).size / 1e6).toFixed(1);
console.log(`\n  → ${path.relative(process.cwd(), out)} · ${frames} frames · ${W}×${H} @ ${fps} fps · ${((to - from) / 1000).toFixed(1)} s · ${mb} MB · rendered in ${((Date.now() - started) / 1000).toFixed(0)} s`);
