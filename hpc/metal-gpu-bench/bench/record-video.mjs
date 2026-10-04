#!/usr/bin/env node
// Record the page's live WebGPU scenes on this Mac as MP4 clips, for visitors
// whose browser can't run them (no WebGPU): site/media/galaxy.mp4, heat.mp4,
// with a still of each and site/data/clips.js (what the HUD said meanwhile).
//
//   node record-video.mjs            (needs Node 22+, Chrome, ffmpeg)
//
// Opens site/index.html in headless Chrome with WebGPU on, hides the HUD and
// title, and captures the hero with the DevTools screencast. Frames keep their
// real timestamps, so the clip plays at the speed it actually ran.
import { spawn, execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const W = 1280, H = 720;
const scenes = [["galaxy", 24], ["heat", 10]];   // [scene, seconds]

const cache = path.join(os.homedir(), "Library/Caches/ms-playwright");
const chrome = [process.env.CHROME, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ...(fs.existsSync(cache) ? fs.readdirSync(cache).filter((d) => d.startsWith("chromium_headless_shell")).sort().reverse()
    .map((d) => path.join(cache, d, "chrome-headless-shell-mac-arm64/chrome-headless-shell")) : [])].filter(Boolean).find((c) => fs.existsSync(c));
if (!chrome) { console.error("no Chrome found; set CHROME=/path/to/chrome"); process.exit(1); }

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const outDir = path.join(root, "site/media");
fs.mkdirSync(outDir, { recursive: true });

const clips = {};
for (const [scene, seconds] of scenes) {
  const port = 9500 + Math.floor(Math.random() * 400);
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "gpu-rec-"));
  const proc = spawn(chrome, ["--headless", "--enable-unsafe-webgpu", "--use-angle=metal", "--hide-scrollbars",
    `--window-size=${W},${H}`, `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });
  try {
    let tabs;
    for (let i = 0; i < 50 && !tabs; i++) { try { tabs = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); } catch { await wait(200); } }
    const ws = new WebSocket(tabs.find((t) => t.type === "page").webSocketDebuggerUrl);
    await new Promise((r) => (ws.onopen = r));
    let id = 0; const pend = {}; const frames = [];
    ws.onmessage = (m) => {
      const d = JSON.parse(m.data);
      if (d.method === "Page.screencastFrame") {
        frames.push({ t: d.params.metadata.timestamp, data: d.params.data });
        ws.send(JSON.stringify({ id: ++id, method: "Page.screencastFrameAck", params: { sessionId: d.params.sessionId } }));
      }
      if (pend[d.id]) { pend[d.id](d.result); delete pend[d.id]; }
    };
    const send = (method, params = {}) => new Promise((r) => { pend[++id] = r; ws.send(JSON.stringify({ id, method, params })); });
    await send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: false });
    // one chosen encounter (the page picks a random one each visit; ?seed= fixes it)
    await send("Page.navigate", { url: "file://" + path.join(root, "site/index.html") + "?seed=" + (process.env.SEED || 202) + "&bodies=" + (process.env.BODIES || 16384) + "&pace=1" });
    await wait(1500);
    const r = await send("Runtime.evaluate", { returnByValue: true, awaitPromise: true, expression: `(async () => {
      const h = document.getElementById("hero");
      h.style.height = "${H}px"; h.style.maxHeight = "none";
      for (const id of ["heroHud", "heroTabs", "heroHint"]) document.getElementById(id).style.display = "none";
      h.querySelector(".title").style.display = "none";
      for (let i = 0; i < 80 && h.dataset.mode !== "live"; i++) await new Promise((r) => setTimeout(r, 100));
      if ("${scene}" === "heat") document.querySelector('#heroTabs [data-scene=heat]').click();
      await new Promise((r) => setTimeout(r, 600));
      return h.dataset.mode;
    })()` });
    if (r.result.value !== "live") throw new Error(`WebGPU isn't running in this Chrome (mode: ${r.result.value})`);
    await send("Page.startScreencast", { format: "jpeg", quality: 92, maxWidth: W, maxHeight: H, everyNthFrame: 1 });
    await wait(seconds * 1000);
    await send("Page.stopScreencast");
    // what the HUD said during the take: size and rates, for the clip's label
    const hud = await send("Runtime.evaluate", { returnByValue: true, expression: '[...document.querySelectorAll("#heroHud .lines span")].map((s) => s.textContent)' });
    clips[scene] = { lines: hud.result.value, seconds };
    ws.close();
    // write frames with their real durations, then encode
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "gpu-frames-"));
    let list = "";
    frames.forEach((f, i) => {
      const file = path.join(dir, `f${String(i).padStart(5, "0")}.jpg`);
      fs.writeFileSync(file, Buffer.from(f.data, "base64"));
      const dur = i + 1 < frames.length ? frames[i + 1].t - f.t : 1 / 30;
      list += `file '${file}'\nduration ${Math.max(0.001, dur).toFixed(4)}\n`;
    });
    list += `file '${path.join(dir, `f${String(frames.length - 1).padStart(5, "0")}.jpg`)}'\n`;
    fs.writeFileSync(path.join(dir, "list.txt"), list);
    const out = path.join(outDir, `${scene}.mp4`);
    execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", path.join(dir, "list.txt"),
      "-vf", "fps=30,scale=960:540:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "30", "-movflags", "+faststart", "-an", out]);
    // a still for the poster attribute
    execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-sseof", "-3", "-i", out, "-frames:v", "1", "-q:v", "4", path.join(outDir, `${scene}.jpg`)]);
    const span = frames.length > 1 ? frames[frames.length - 1].t - frames[0].t : 0;
    console.log(`${scene}: ${frames.length} frames over ${span.toFixed(1)} s (${(frames.length / span).toFixed(0)} fps captured) → ${path.relative(root, out)} ${(fs.statSync(out).size / 1e6).toFixed(1)} MB`);
    fs.rmSync(dir, { recursive: true, force: true });
  } finally {
    proc.kill();
  }
}

// the labels, as a script the page loads with a plain <script> tag
const version = execFileSync(chrome, ["--version"]).toString().trim();
fs.writeFileSync(path.join(root, "site/data/clips.js"),
  "// Generated by bench/record-video.mjs — don't edit by hand.\n" +
  "window.HERO_CLIPS = " + JSON.stringify({ date: new Date().toISOString().slice(0, 10), browser: version, ...clips }, null, 1) + ";\n");
console.log("wrote site/data/clips.js");
