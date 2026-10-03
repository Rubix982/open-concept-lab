#!/usr/bin/env node
// node build.mjs [story]   check one story's models and stage, write out/<story>/
// node build.mjs --all     build every story in stories/, plus a gallery at out/index.html
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";
import { COLORS } from "../brick-check/lib/parts.mjs";
import { toLDR } from "../brick-check/lib/ldraw.mjs";
import { PARTS } from "../brick-check/lib/parts.mjs";
import { partMesh } from "../brick-check/tools/ldraw-mesh.mjs";
import { availability } from "../brick-check/lib/availability.mjs";
import { physical } from "../brick-check/lib/physical.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const TL = createRequire(import.meta.url)("./lib/timeline.cjs");

export async function buildStory(name, { quiet = false } = {}) {
  const log = quiet ? () => {} : console.log;
  // a query string defeats the module cache, so the dev server always sees the latest story
  const story = (await import(`${pathToFileURL(path.join(here, "stories", `${name}.mjs`))}?v=${Date.now()}`)).default;
  const out = path.join(here, "out", name);
  await fs.mkdir(path.join(out, "models"), { recursive: true });

  let ok = true;
  log(`${story.meta.title} · ${(story.duration / 1000).toFixed(1)} s`);
  for (const [model, r] of Object.entries(story.reports)) {
    ok &&= r.ok;
    log(`  ${r.ok ? "✓" : "✗"} ${model} · ${r.stats?.parts ?? "?"} parts${r.ok ? ` · ${r.stats.studConnections} stud connections` : ""}`);
    for (const e of r.errors) log(`      ✗ ${e.rule}: ${e.msg}`);
    const file = model.replace(/[^a-z0-9-]+/gi, "_");
    await fs.writeFile(path.join(out, "models", `${file}.ldr`), toLDR({ title: model, name: file, steps: [{ note: model, parts: r.parts }] }));
    // real parts in real colours? (Rebrickable), and what it would weigh
    const av = await availability(r.parts);
    r.available = av.ok; r.missing = av.missing.map((l) => `${l.qty}× ${PARTS[l.part].name} in ${l.colorName}`);
    r.physical = physical(r.parts);
    r.inventory = av.lines.map((l) => ({ part: l.part, name: PARTS[l.part].name, color: l.color, colorName: l.colorName, qty: l.qty, element: l.elementIds[0] || null, bl: PARTS[l.part].bl || l.part, exists: l.exists }));
    for (const m of r.missing) log(`      ⚠ not made by LEGO: ${m}`);
    const csv = ["qty,part,name,colour,lego_element_id,bricklink_part", ...r.inventory.map((l) => `${l.qty},${l.part},"${l.name}",${l.colorName},${l.element ?? ""},${l.bl}`)];
    await fs.writeFile(path.join(out, "models", `${file}.csv`), csv.join("\n") + "\n");
  }
  // the stage check: run the whole timeline and look for actors walking into each other
  const stage = TL.stageCollisions(story);
  for (const s of stage) log(`  ⚠ ${s.pair} overlap at ${(s.t / 1000).toFixed(1)} s`);
  if (!stage.length) log("  ✓ stage · no actors overlap");

  // real geometry for every part that isn't a plain box (slopes, round parts)
  const meshIds = [...new Set(Object.values(story.actors).flatMap((a) => (a.parts || []).filter((p) => p.mesh).map((p) => p.part)))];
  const meshes = {};
  for (const id of meshIds) meshes[id] = { tri: (await partMesh(id)).tri, center: PARTS[id].center || [0, 0] };

  const { reports, ...rest } = story;
  const slim = {
    ...rest, stage, colors: COLORS, meshes,
    reports: Object.fromEntries(Object.entries(reports).map(([k, r]) => [k, { ok: r.ok, stats: r.stats, errors: r.errors, actor: r.actor, available: r.available, missing: r.missing, physical: r.physical, inventory: r.inventory }])),
  };
  // function replacers, so a `$` in the story text is never read as a pattern
  const timeline = await fs.readFile(path.join(here, "lib", "timeline.cjs"), "utf8");
  const bricksKit = await fs.readFile(path.join(here, "lib", "bricks.js"), "utf8");
  const minifigKit = await fs.readFile(path.join(here, "lib", "minifig.js"), "utf8");
  const page = (await fs.readFile(path.join(here, "lib", "player.html"), "utf8"))
    .replace("__TITLE__", () => story.meta.title)
    .replace("__TIMELINE__", () => timeline)
    .replace("__BRICKS__", () => bricksKit)
    .replace("__MINIFIG__", () => minifigKit)
    .replace("__STORY__", () => JSON.stringify(slim));
  await fs.writeFile(path.join(out, "index.html"), page);
  log(`  wrote out/${name}/`);
  return { name, story, ok, stage };
}

async function gallery(results) {
  const card = ({ name, story, ok, stage }) => `
    <a class="card" href="${name}/index.html">
      <span class="k">${(story.duration / 1000).toFixed(0)} s · ${Object.keys(story.reports).length} models</span>
      <span class="t">${story.meta.title}</span>
      <span class="s">${ok ? "✓ every model buildable" : "✗ a model can't be built"}${stage.length ? ` · ⚠ ${stage.length} stage overlap${stage.length > 1 ? "s" : ""}` : ""}</span>
    </a>`;
  await fs.writeFile(path.join(here, "out", "index.html"), `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Brick Stage</title>
<style>
  :root { --bg: #f1f0ec; --ink: #1d1d1b; --muted: #6f6e68; --accent: #e8711c; --card: #fff; --line: #dcdad3; }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #161614; --ink: #ecebe6; --muted: #a3a29b; --card: #20201d; --line: #34332f; } }
  :root[data-theme="dark"] { --bg: #161614; --ink: #ecebe6; --muted: #a3a29b; --card: #20201d; --line: #34332f; }
  body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.45 "Helvetica Neue", Helvetica, Arial, system-ui, sans-serif; }
  main { max-width: 900px; margin: 0 auto; padding: 48px 16px; }
  h1 { font-weight: 300; font-size: 40px; margin: 0 0 6px; } p { color: var(--muted); margin: 0 0 28px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
  .card { display: flex; flex-direction: column; gap: 6px; background: var(--card); border: 1px solid var(--line); border-left: 3px solid var(--accent);
    border-radius: 8px; padding: 16px 18px; color: inherit; text-decoration: none; }
  .card:hover, .card:focus-visible { border-color: var(--accent); outline: none; }
  .k { font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--accent); font-weight: 700; }
  .t { font-size: 22px; font-weight: 300; } .s { font-size: 13px; color: var(--muted); }
</style></head><body><main>
<h1>Brick Stage</h1>
<p>Stories told with LEGO models that assemble themselves. Every model is checked as really buildable.</p>
<div class="grid">${results.map(card).join("")}</div>
</main></body></html>
`);
  console.log(`gallery · out/index.html (${results.length} stories)`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const arg = process.argv[2] || "little-builder";
  if (arg === "--all") {
    const names = (await fs.readdir(path.join(here, "stories"))).filter((f) => f.endsWith(".mjs") && !f.startsWith("_")).map((f) => f.slice(0, -4)).sort();
    const results = [];
    for (const n of names) results.push(await buildStory(n));
    await gallery(results);
    process.exit(results.every((r) => r.ok) ? 0 : 1);
  } else {
    const r = await buildStory(arg);
    if (!r.ok) { console.log("  some models can't be built as written — fix them before sharing"); process.exit(1); }
  }
}
