#!/usr/bin/env node
// node showcase.mjs <file> "Title" [--height 48] [--up y|z] [--colours 8] [--credit "…"] [--name slug]
//
// From any 3D file (GLB/glTF, OBJ, STL, PLY, MagicaVoxel .vox) to a brick
// model and a story, in one go:
//   load → nearest LEGO colours → brickify → only parts LEGO makes → check →
//   sections at the narrow points → an editable story → animation, booklet, poster
// The story it writes (stories/<name>.mjs) is yours to edit: add characters,
// captions, moods. Re-run build.mjs after editing.
import fs from "node:fs/promises";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { loadMesh } from "../brick-check/tools/mesh-load.mjs";
import { brickify } from "../brick-check/tools/brickify.mjs";
import { sections, sectionNames } from "../brick-check/tools/sections.mjs";
import { clusterToLego } from "../brick-check/lib/palette.mjs";
import { fitToCatalogue } from "../brick-check/lib/availability.mjs";
import { check } from "../brick-check/lib/check.mjs";
import { footprint } from "../brick-check/lib/parts.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const flag = (k, d) => { const i = args.indexOf(`--${k}`); return i >= 0 ? args.splice(i, 2)[1] : d; };
const height = +flag("height", 48), up = flag("up"), maxColours = +flag("colours", 8), credit = flag("credit", "");
let name = flag("name");
const [file, title = "A Brick Model"] = args;
if (!file) { console.log('usage: node showcase.mjs <file> "Title" [--height 48] [--up y|z] [--colours 8] [--credit "…"] [--name slug]'); process.exit(1); }
name ||= title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

// 1. load, and choose a small set of LEGO colours so the model reads cleanly
const mesh = await loadMesh(file, up ? { up } : {});
// Group the model's colours into a few clusters first (shading divided out),
// then give each its LEGO colour: AI-made and scanned models bake lighting in,
// and matching shade by shade turns a yellow duck brown.
const codes = clusterToLego(mesh.rgb, maxColours);
const kept = [...new Set(codes)];
console.log(`${path.basename(file)} · ${mesh.format} · ${mesh.stats.triangles} triangles${mesh.stats.textured ? " · textured" : ""} → ${kept.length} LEGO colours`);

// 2. bricks, real parts, checked
const bricked = brickify(mesh.triangles, codes, { heightPlates: height, hollow: 2 });
const fitted = await fitToCatalogue(bricked.parts);
const parts = fitted.parts;
const res = check({ steps: [{ note: name, parts }] });
console.log(`  ${parts.length} plates · ${res.ok ? "passes every check" : "FAILS: " + [...new Set(res.errors.map((e) => e.rule))].join(", ")}` +
  `${bricked.stats.dropped?.unplaceable ? ` · ${bricked.stats.dropped.unplaceable} plates dropped` : ""}${fitted.changes.length ? ` · recoloured ${fitted.changes.join(", ")}` : ""}`);

// 3. sections at the narrow points
const secs = sections(parts);
const names = sectionNames(secs.length);
console.log(`  sections: ${secs.map((s, k) => `${names[k]} (plates ${s.base}–${s.top}${s.subassembly ? ", built on its own" : ""})`).join(" · ")}`);

// 4. write the model and an editable story
await fs.mkdir(path.join(here, "models"), { recursive: true });
await fs.writeFile(path.join(here, "models", `${name}.json`), JSON.stringify({ source: path.basename(file), credit, parts, stats: bricked.stats, sections: secs }));
let w = 0, d = 0; for (const p of parts) { const f = footprint(p); w = Math.max(w, p.x + f.w); d = Math.max(d, p.z + f.d); }
const cx = Math.round(w / 2), cz = Math.round(d / 2), dist = Math.round(Math.max(height * 0.4, w, d) * 2.4);
const subTop = secs.length > 1 && secs.at(-1).subassembly;
const lines = secs.map((s, k) => {
  const id = `s${k}`, isSub = subTop && k === secs.length - 1;
  return [
    `  s.section(${JSON.stringify(names[k])});`,
    `  s.shot({ at: [${cx}, ${Math.round((s.base + s.top) / 2)}, ${cz}], az: ${20 - k * 12}, el: 18, dist: ${dist} }, 2000);`,
    k === 0 ? `  s.build(part(${k}, "base"), { at: [0, 0, 0], from: "path", stagger: STAGGER });`
      : isSub ? [
        `  // built on its own beside the model, then set on top — like a booklet's sub-assembly`,
        `  s.build(part(${k}, "${id}", ${s.base}), { at: [${w + 6}, 0, 0], from: "path", stagger: STAGGER });`,
        `  s.attach("${id}", { onto: "base", at: [0, ${s.base}, 0] });`,
      ].join("\n")
      : `  s.build(part(${k}, "${id}"), { onto: "base", from: "path", stagger: STAGGER });`,
  ].join("\n");
}).join("\n\n");
const story = `// ${title} — made by showcase.mjs from ${path.basename(file)}${credit ? ` (${credit})` : ""}.
// Edit freely: add captions, characters, moods. Then: node build.mjs ${name}
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { story, model } from "../lib/director.mjs";

const data = JSON.parse(fs.readFileSync(fileURLToPath(new URL("../models/${name}.json", import.meta.url)), "utf8"));
const STAGGER = ${Math.max(8, Math.min(60, Math.round(12000 / parts.length)))};          // ms between parts: the whole build takes ~12 s
// section k of the model, as its own model (shifted down if it's built on its own)
const part = (k, id, base = 0) => { const s = data.sections[k]; return model(id, data.parts.slice(s.from, s.to).map((p) => ({ ...p, y: p.y - base }))); };

export default story({
  title: ${JSON.stringify(title)}, drift: 0.4,
  sources: ${JSON.stringify(credit ? [`Shape: ${credit}`] : [])},
}, (s) => {
  s.shot({ at: [${cx}, ${Math.round(height / 2)}, ${cz}], az: 30, el: 18, dist: ${dist} }, 0);
  s.card("A BRICK MODEL OF", ${JSON.stringify(title)}, { sub: ${JSON.stringify(`${parts.length} LEGO plates${credit ? ` · ${credit}` : ""}`)} });

${lines}

  s.caption(${JSON.stringify(`${parts.length} plates. Checked on a computer, not yet with real bricks.`)});
  s.wait(2400);
  s.clearCaption();
  s.turnaround("base", { dur: 7000, el: 12, dist: ${Math.round(dist * 1.1)}, offset: [0, ${Math.round(height / 2)}, 0] });
  s.wait(7000);
});
`;
const storyFile = path.join(here, "stories", `${name}.mjs`);
await fs.writeFile(storyFile, story);
console.log(`  wrote stories/${name}.mjs and models/${name}.json`);

// 5. animation, booklet, poster
for (const [script, extra] of [["build.mjs", []], ["booklet.mjs", []], ["poster.mjs", []]]) {
  try { execFileSync(process.execPath, [path.join(here, script), name, ...extra], { stdio: "inherit" }); }
  catch { console.log(`  ${script} failed — see above`); }
}
console.log(`\nopen out/${name}/index.html   ·   edit stories/${name}.mjs   ·   live preview: node dev.mjs ${name}`);

