#!/usr/bin/env node
// node explain/build.mjs <script>   → out/<script>/index.html
//
// Compiles explain/scripts/<script>.mjs into a self-contained page: the
// timeline, the blueprint player and the fonts link. It works opened straight
// from disk, and render.mjs turns it into an MP4 like any brick story:
//   node render.mjs <script>
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const name = process.argv[2];
if (!name) { console.log("usage: node explain/build.mjs <script>"); process.exit(1); }
const tl = (await import(pathToFileURL(path.join(here, "scripts", `${name}.mjs`)).href)).default;
const player = await fs.readFile(path.join(here, "lib", "blueprint.js"), "utf8");
const bricksKit = await fs.readFile(path.join(here, "..", "lib", "bricks.js"), "utf8");

// brick stages: every model goes through brick-check, like a story's models
const brickStages = tl.objects.filter((o) => o.type === "stage3d" && o.props.kind === "bricks");
if (brickStages.length) {
  const { check } = await import("../../brick-check/lib/check.mjs");
  const { PARTS, COLORS, footprint } = await import("../../brick-check/lib/parts.mjs");
  const { partMesh } = await import("../../brick-check/tools/ldraw-mesh.mjs");
  const meshIds = new Set();
  for (const o of brickStages) {
    const r = check({ steps: [{ note: o.id, parts: o.props.parts }] });
    const n = o.props.parts.length;
    console.log(`  ${r.ok ? "✓" : "✗"} ${o.id} · ${n} parts${r.ok ? " · buildable" : ": " + [...new Set(r.errors.map((e) => e.rule))].join(", ")}`);
    if (!r.ok) process.exitCode = 1;
    o.props.parts = o.props.parts.map((p) => {
      const f = footprint(p), def = PARTS[p.part];
      if (def.mesh) meshIds.add(p.part);
      return { ...p, w: f.w, d: f.d, h: f.h, kind: def.kind, mesh: Boolean(def.mesh) };
    });
  }
  tl.colors = COLORS;
  tl.meshes = {};
  for (const id of meshIds) tl.meshes[id] = { tri: (await partMesh(id)).tri, center: PARTS[id].center || [0, 0] };
}
// plugins: lib/plugins/*.js are inlined after the core player; a matching
// *.build.mjs may check or extend the timeline and return extra <script>s
const pluginDir = path.join(here, "lib", "plugins");
const pluginFiles = (await fs.readdir(pluginDir).catch(() => [])).sort();
const plugins = [], extraHead = [];
for (const f of pluginFiles.filter((f) => f.endsWith(".js"))) plugins.push(`// ---- plugin: ${f}\n` + (await fs.readFile(path.join(pluginDir, f), "utf8")));
for (const f of pluginFiles.filter((f) => f.endsWith(".build.mjs"))) {
  const mod = await import(pathToFileURL(path.join(pluginDir, f)).href);
  const extra = await mod.build?.(tl, { here, log: (m) => console.log(`  ${m}`) });
  if (extra) extraHead.push(extra);
}
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(tl.meta.title)}</title>
<meta name="description" content="${esc(tl.meta.description || tl.meta.title)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
  :root { color-scheme: dark; }
  html, body { margin: 0; background: #040817; color: #dbe6ff; font: 15px/1.4 "IBM Plex Sans", -apple-system, sans-serif; }
  .screen { container-type: inline-size; position: relative; width: min(100vw, calc((100vh - 56px) * ${tl.meta.w} / ${tl.meta.h})); margin: 0 auto; aspect-ratio: ${tl.meta.w} / ${tl.meta.h}; }
  canvas { display: block; width: 100%; height: 100%; }
  /* captions sit low and light, a subtitle line rather than a box over the scene */
  #caption { position: absolute; left: 50%; bottom: 2.6%; transform: translateX(-50%); max-width: ${tl.meta.w > tl.meta.h ? 72 : 88}%; padding: 0.25em 0.7em; text-align: center;
    font: 500 clamp(12px, ${tl.meta.w > tl.meta.h ? 1.3 : tl.meta.w === tl.meta.h ? 2.2 : 3.4}cqw, 26px)/1.35 "IBM Plex Sans", sans-serif; color: #f2f6ff; background: rgba(4, 9, 28, 0.5); border: 0;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
    transition: opacity 0.25s; pointer-events: none; }
  #controls { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px; width: min(100vw, max(560px, calc((100vh - 56px) * ${tl.meta.w} / ${tl.meta.h}))); margin: 0 auto; padding: 10px 14px; box-sizing: border-box; font-size: 13px; color: #9fb0d6; }
  #controls button { all: unset; cursor: pointer; padding: 5px 10px; border: 1px solid rgba(219, 230, 255, 0.25); color: #dbe6ff; }
  #controls button:hover { border-color: #dbe6ff; }
  #controls button:focus-visible, #controls input:focus-visible { outline: 2px solid #7cc8ff; outline-offset: 1px; }
  #play { min-width: 4em; text-align: center; }
  #scrub { flex: 1 1 200px; accent-color: #ff7a59; }
  #time { font-family: "IBM Plex Mono", monospace; min-width: 8em; }
  .chapters { display: flex; flex-wrap: wrap; gap: 6px; }
  .chapters button { font-size: 12px; }
  label { display: inline-flex; gap: 5px; align-items: center; cursor: pointer; }
  /* render.mjs: the frame fills the window, no controls, captions go to the .srt */
  body.render .screen { width: 100vw; height: 100vh; aspect-ratio: auto; }
  body.render #controls, body.render #caption { display: none; }
</style>
</head>
<body>
<div class="screen"><canvas id="stage" aria-label="${esc(tl.meta.title)}: an animated explainer"></canvas><div id="caption" aria-live="polite"></div></div>
<div id="controls"></div>
<script type="importmap">{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js", "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/" } }</script>
<script>window.TIMELINE = ${JSON.stringify(tl)};</script>
<script>
${bricksKit}
</script>
${extraHead.join("\n")}
<script>
${player}
</script>
${plugins.map((p) => `<script>\n${p}\n</script>`).join("\n")}
<script>BP.start();</script>
</body>
</html>
`;
const outDir = path.join(here, "..", "out", name);
await fs.mkdir(outDir, { recursive: true });
await fs.writeFile(path.join(outDir, "index.html"), html);
console.log(`out/${name}/index.html · ${(tl.meta.duration / 1000).toFixed(1)} s · ${tl.objects.length} objects · ${tl.narration.length} lines · ${(html.length / 1024).toFixed(0)} KB`);
