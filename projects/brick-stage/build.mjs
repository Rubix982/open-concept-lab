#!/usr/bin/env node
// node build.mjs [story]  — checks every model in a story, then writes a
// self-contained player to out/<story>/ along with each model as LDraw.
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { COLORS } from "../brick-check/lib/parts.mjs";
import { toLDR } from "../brick-check/lib/ldraw.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const name = process.argv[2] || "little-builder";
const story = (await import(`./stories/${name}.mjs`)).default;
const out = path.join(here, "out", name);
await fs.mkdir(path.join(out, "models"), { recursive: true });

let ok = true;
console.log(`${story.meta.title} · ${(story.duration / 1000).toFixed(1)} s`);
for (const [model, r] of Object.entries(story.reports)) {
  ok &&= r.ok;
  console.log(`  ${r.ok ? "✓" : "✗"} ${model} · ${r.stats?.parts ?? "?"} parts${r.ok ? ` · ${r.stats.studConnections} stud connections` : ""}`);
  for (const e of r.errors) console.log(`      ✗ ${e.rule}: ${e.msg}`);
  const file = model.replace(/[^a-z0-9-]+/gi, "_");
  await fs.writeFile(path.join(out, "models", `${file}.ldr`), toLDR({ title: model, name: file, steps: [{ note: model, parts: r.parts }] }));
}
const { reports, ...rest } = story;
const slim = { ...rest, colors: COLORS, reports: Object.fromEntries(Object.entries(reports).map(([k, r]) => [k, { ok: r.ok, stats: r.stats, errors: r.errors }])) };
const html = (await fs.readFile(path.join(here, "lib", "player.html"), "utf8"))
  .replace("__TITLE__", story.meta.title)
  .replace("__STORY__", JSON.stringify(slim));
await fs.writeFile(path.join(out, "index.html"), html);
console.log(`  wrote out/${name}/`);
if (!ok) { console.log("  some models can't be built as written — fix them before sharing"); process.exit(1); }
