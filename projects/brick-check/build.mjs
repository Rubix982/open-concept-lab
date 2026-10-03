#!/usr/bin/env node
// node build.mjs [design]  — checks a design and writes everything to out/<name>/
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { check } from "./lib/check.mjs";
import { toLDR, toBrickLinkXML, partsList } from "./lib/ldraw.mjs";
import { PARTS, COLORS, footprint } from "./lib/parts.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const name = process.argv[2] || "datascalar-machine";
const design = (await import(`./designs/${name}.mjs`)).default;
const report = check(design);
const out = path.join(here, "out", name);
await fs.mkdir(out, { recursive: true });

const { parts, edges, ...summary } = report;
const viewerData = {
  title: design.title, name: design.name,
  steps: design.steps.map((s) => ({ note: s.note })),
  parts: parts.map((p) => ({ ...p, ...footprint(p), kind: PARTS[p.part].kind, partName: PARTS[p.part].name })),
  colors: COLORS, list: partsList(design), report: summary,
};
await fs.writeFile(path.join(out, `${name}.ldr`), toLDR(design));
await fs.writeFile(path.join(out, "bricklink-wanted.xml"), toBrickLinkXML(design));
await fs.writeFile(path.join(out, "report.json"), JSON.stringify(summary, null, 2));
await fs.writeFile(path.join(out, "design.js"), `window.DESIGN = ${JSON.stringify(viewerData)};\n`);
await fs.copyFile(path.join(here, "viewer", "index.html"), path.join(out, "index.html"));

const s = report.stats || {};
console.log(`${design.title}: ${report.ok ? "PASS" : "FAIL"}`);
if (report.ok) console.log(`  ${s.parts} parts · ${s.steps} steps · ${s.studConnections} stud connections · ${s.pieces} piece · centre of mass ${s.comMarginStuds} studs inside the footprint`);
for (const e of report.errors) console.log(`  ✗ ${e.rule}: ${e.msg}`);
for (const w of report.warnings) console.log(`  ! ${w.rule}: ${w.msg}`);
console.log(`  wrote out/${name}/`);
process.exit(report.ok ? 0 : 1);
