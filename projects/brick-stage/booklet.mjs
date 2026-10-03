#!/usr/bin/env node
// node booklet.mjs <story> [model]  — printable building instructions for one
// model in a story: cover, parts inventory with LEGO element IDs, every step
// at one scale, a turnaround, and what was (and wasn't) checked. Writes
// out/<story>/booklet-<model>.html, then prints it to PDF with headless Chrome
// if one can be found.
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { execFileSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { PARTS, COLORS, footprint } from "../brick-check/lib/parts.mjs";
import { availability } from "../brick-check/lib/availability.mjs";
import { physical } from "../brick-check/lib/physical.mjs";
import { check } from "../brick-check/lib/check.mjs";
import { toLDR } from "../brick-check/lib/ldraw.mjs";
import { partMesh } from "../brick-check/tools/ldraw-mesh.mjs";
import { autoSteps } from "./lib/director.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const [name, wanted] = process.argv.slice(2);
if (!name) { console.log("usage: node booklet.mjs <story> [model]"); process.exit(1); }
const story = (await import(pathToFileURL(path.join(here, "stories", `${name}.mjs`)).href)).default;
const reports = Object.entries(story.reports);
const [modelName, rep] = wanted ? reports.find(([n]) => n === wanted) || [] : reports.sort((a, b) => b[1].parts.length - a[1].parts.length)[0];
if (!rep) { console.log(`no model "${wanted}" — models: ${reports.map(([n]) => n).join(", ")}`); process.exit(1); }

const parts = rep.parts.map((p) => ({ ...p, ...footprint(p), kind: PARTS[p.part].kind, mesh: !!PARTS[p.part].mesh }));
// steps: grouped the way the director groups them
const steps = [];
for (const n of autoSteps(parts)) { const from = steps.length ? steps[steps.length - 1].to : 0; steps.push({ from, to: from + n }); }
const res = check({ steps: [{ note: modelName, parts: rep.parts }] });
const av = await availability(rep.parts);
const meshes = {};
for (const id of new Set(parts.filter((p) => p.mesh).map((p) => p.part))) meshes[id] = { tri: (await partMesh(id)).tri, center: PARTS[id].center || [0, 0] };
const dims = Object.fromEntries(Object.entries(PARTS).map(([id, s]) => [id, { w: s.w, d: s.d, h: s.h, kind: s.kind, mesh: !!s.mesh }]));
const file = modelName.replace(/[^a-z0-9-]+/gi, "_");
const vias = res.parts.reduce((m, p) => ((m[p.via] = (m[p.via] || 0) + 1), m), {});

const book = {
  // a story's main model takes the story's name; ask for another by name and it's named too
  title: wanted ? `${story.meta.title} — ${modelName}` : story.meta.title,
  subtitle: story.meta.subtitle || `from the brick-stage story “${story.meta.title}”`,
  notice: "Unofficial fan-made instructions · not physically build-tested",
  parts, steps, meshes, dims, colors: COLORS, physical: physical(rep.parts),
  inventory: av.lines.map((l) => ({ part: l.part, color: l.color, colorName: l.colorName, qty: l.qty, element: l.elementIds[0] || null, bl: PARTS[l.part].bl || l.part, exists: l.exists })),
  about: story.meta.about || `${modelName} is a model from the brick-stage story “${story.meta.title}”, designed in code and checked by brick-check.`,
  checked: `${res.ok ? "the model passes every check" : "the model FAILS some checks"}: ${res.stats?.studConnections ?? "?"} stud connections, no two parts overlap, ` +
    `each part has a real way in (${Object.entries(vias).map(([k, n]) => `${n} ${k}`).join(", ")}), it is one solid piece and its centre of mass is over its footprint. ` +
    (av.ok ? "Every part is a real LEGO part in a colour LEGO has made (Rebrickable)." : `${av.missing.length} part/colour combinations are not made by LEGO (marked in red in the inventory).`),
  files: [`Model (LDraw): models/${file}.ldr`, `Parts list: models/${file}.csv`, "This booklet: brick-stage/booklet.mjs, from the story file"],
  sources: ["Part shapes: LDraw parts library (ldraw.org, CC BY 4.0)", "Part and colour data: Rebrickable", ...(story.meta.sources || [])],
};

const out = path.join(here, "out", name);
await fs.mkdir(path.join(out, "models"), { recursive: true });
await fs.writeFile(path.join(out, "models", `${file}.ldr`), toLDR({ title: modelName, name: file, steps: [{ note: modelName, parts: rep.parts }] }));
const kit = await fs.readFile(path.join(here, "lib", "bricks.js"), "utf8");
const page = (await fs.readFile(path.join(here, "lib", "booklet.html"), "utf8"))
  .replace("__TITLE__", () => book.title)
  .replace("__BRICKS__", () => kit)
  .replace("__BOOK__", () => JSON.stringify(book));
const htmlFile = path.join(out, `booklet-${file}.html`);
await fs.writeFile(htmlFile, page);
console.log(`${book.title}: ${parts.length} parts, ${steps.length} steps → out/${name}/booklet-${file}.html`);

// print to PDF, the way the Microduck booklet was made
const chromes = [
  process.env.CHROME,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ...(await fs.readdir(path.join(os.homedir(), "Library/Caches/ms-playwright")).catch(() => []))
    .filter((d) => d.startsWith("chromium_headless_shell")).sort().reverse()
    .map((d) => path.join(os.homedir(), "Library/Caches/ms-playwright", d, "chrome-headless-shell-mac-arm64/chrome-headless-shell")),
].filter(Boolean);
let chrome = null;
for (const c of chromes) { try { await fs.access(c); chrome = c; break; } catch {} }
if (!chrome) { console.log("  no Chrome found for PDF — open the .html and print it to PDF (A4 landscape)"); process.exit(0); }
const pdf = path.join(out, `booklet-${file}.pdf`);
execFileSync(chrome, ["--headless", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-pdf-header-footer",
  "--virtual-time-budget=60000", `--print-to-pdf=${pdf}`, pathToFileURL(htmlFile).href], { stdio: "ignore", timeout: 300000 });
console.log(`  printed → out/${name}/booklet-${file}.pdf`);
