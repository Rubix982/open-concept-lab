#!/usr/bin/env node
// node cinema/render.mjs [--size 1920x1080] [--fps 60] [--secs 40] [--bodies 65536] [--steps 1] [--slow 1] [--seed 11] [--out file.mp4]
//   --slow k   the same story over k× the time: --secs 60 --slow 1.875 stretches the 32 s cut to a minute
//
// Renders cinema/index.html to an MP4, frame by frame: headless Chrome with
// WebGPU (on Metal), the page advanced one exact frame at a time
// (window.__frame(i)), each frame photographed and piped into ffmpeg. No
// screen recording, so a slow machine only takes longer; the video is the same.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const flag = (k, d) => { const i = args.indexOf(`--${k}`); return i >= 0 ? args[i + 1] : d; };
const [W, H] = flag("size", "1920x1080").split("x").map(Number);
const fps = +flag("fps", 60), secs = +flag("secs", 40), bodies = +flag("bodies", 65536), steps = +flag("steps", 1), seed = +flag("seed", 11), slow = +flag("slow", 1);
const out = path.resolve(flag("out", path.join(here, "out", `galaxies-${W}x${H}.mp4`)));
fs.mkdirSync(path.dirname(out), { recursive: true });

const cache = path.join(os.homedir(), "Library/Caches/ms-playwright");
const chrome = [process.env.CHROME, ...(fs.existsSync(cache) ? fs.readdirSync(cache).filter((d) => d.startsWith("chromium_headless_shell")).sort().reverse()
  .map((d) => path.join(cache, d, "chrome-headless-shell-mac-arm64/chrome-headless-shell")) : []), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
  .filter(Boolean).find((c) => fs.existsSync(c));
if (!chrome) { console.log("no Chrome found (set CHROME=/path/to/chrome)"); process.exit(1); }

const port = 9600 + Math.floor(Math.random() * 300), profile = fs.mkdtempSync(path.join(os.tmpdir(), "cinema-"));
const proc = spawn(chrome, ["--headless", "--enable-unsafe-webgpu", "--use-angle=metal", "--hide-scrollbars", "--force-device-scale-factor=1",
  `--window-size=${W},${H}`, `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
let tab;
for (let i = 0; i < 80 && !tab; i++) { await wait(150); tab = await fetch(`http://127.0.0.1:${port}/json`).then((r) => r.json()).then((l) => l.find((t) => t.type === "page")).catch(() => null); }
const ws = new WebSocket(tab.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } };
const send = (method, params = {}) => new Promise((r) => { pend.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });
const evaluate = async (expression) => {
  const d = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (d.result?.exceptionDetails) throw new Error(d.result.exceptionDetails.exception?.description || "page error");
  return d.result?.result?.value;
};

await send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: false });
const url = pathToFileURL(path.join(here, "index.html")).href + `?render&bodies=${bodies}&steps=${steps}&seed=${seed}&fps=${fps}&secs=${secs}&slow=${slow}`;
await send("Page.navigate", { url });
for (let i = 0; i < 200; i++) { if (await evaluate("window.__ready === true || !!window.__error").catch(() => false)) break; await wait(150); }
const err = await evaluate("window.__error || null");
if (err) { console.log(`the page can't run: ${err}`); proc.kill(); process.exit(1); }
const info = await evaluate("window.__info");
console.log(`${info.N.toLocaleString()} bodies · ${info.STEPS} steps a frame · ${info.FRAMES} frames · ${info.W}×${info.H} @ ${fps} fps → ${path.relative(process.cwd(), out)}`);

const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-i", "-",
  "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], { stdio: ["pipe", "inherit", "inherit"] });
const t0 = Date.now();
for (let i = 0; i < info.FRAMES; i++) {
  await evaluate(`window.__frame(${i})`);
  const shot = await send("Page.captureScreenshot", { format: "png" });
  if (!ff.stdin.write(Buffer.from(shot.result.data, "base64"))) await new Promise((r) => ff.stdin.once("drain", r));
  if (i % 60 === 0 || i === info.FRAMES - 1) {
    const el = (Date.now() - t0) / 1000, left = (el / (i + 1)) * (info.FRAMES - i - 1);
    process.stdout.write(`\r  frame ${i + 1}/${info.FRAMES} · ${el.toFixed(0)} s · ~${left.toFixed(0)} s left   `);
  }
}
ff.stdin.end();
await new Promise((r) => ff.on("close", r));
ws.close(); proc.kill();
// let Chrome finish writing its profile before removing it
await Promise.race([new Promise((r) => proc.once("exit", r)), wait(3000)]);
try { fs.rmSync(profile, { recursive: true, force: true }); } catch {}
console.log(`\n  done in ${((Date.now() - t0) / 1000).toFixed(0)} s → ${out}`);
