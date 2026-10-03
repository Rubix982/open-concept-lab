#!/usr/bin/env node
// Brickifies Pollen Robotics' Microduck from its open CAD and checks the
// result with brick-check. Writes out/microduck/microduck-bricks.json and .ldr.
//   node tools/microduck-model.mjs [heightPlates=64] [hollow=0] [maxGap=16]
// At this size the body is too slim to hollow, and struts of up to 16 plates
// let the head and thighs rest on what's under them (see brickify.mjs).
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadMjcfRobot, SOURCE } from "./mjcf-mesh.mjs";
import { brickify } from "./brickify.mjs";
import { fitToCatalogue } from "../lib/availability.mjs";
import { check } from "../lib/check.mjs";
import { toLDR } from "../lib/ldraw.mjs";
import { COLORS } from "../lib/parts.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const heightPlates = +process.argv[2] || 64, hollow = process.argv[3] !== undefined ? +process.argv[3] : 0, maxGap = process.argv[4] !== undefined ? +process.argv[4] : 16;

const { triangles, colors } = await loadMjcfRobot();
const bricked = brickify(triangles, colors, { heightPlates, hollow, maxGap });
// only parts LEGO actually makes in each colour (Rebrickable)
const fitted = await fitToCatalogue(bricked.parts);
const parts = fitted.parts, stats = { ...bricked.stats, recolouredForCatalogue: fitted.changes };
const design = { title: "Microduck (brickified)", name: "microduck-bricks", steps: [{ note: "built bottom-up", parts }] };
const r = check(design);

const out = path.join(here, "..", "out", "microduck");
await fs.mkdir(out, { recursive: true });
await fs.writeFile(path.join(out, "microduck-bricks.json"), JSON.stringify({ parts, stats, check: { ok: r.ok, stats: r.stats, errors: r.errors.slice(0, 20) }, source: SOURCE }, null, 1));
await fs.writeFile(path.join(out, "microduck-bricks.ldr"), toLDR(design));

console.log(`Microduck, ${heightPlates} plates tall, hollow ${hollow}, struts up to ${maxGap} plates`);
console.log(`  ${stats.plates} plates from ${stats.cells} cells · ${stats.layers} layers · ${stats.sizeStuds[0]} x ${stats.sizeStuds[1]} studs · ${stats.sizeCm.join(" x ")} cm`);
console.log(`  colours: ${Object.entries(stats.colours).map(([c, n]) => `${COLORS[c][0]} ${n}`).join(", ")}`);
console.log(`  dropped: ${stats.dropped.islands} plates in floating islands, ${stats.dropped.unplaceable} that couldn't be placed in order (seam pattern ${stats.seed}); ${stats.recolouredCells} cells recoloured, ${stats.strutCells} strut cells added so hanging parts rest on what's below`);
console.log(`  brick-check: ${r.ok ? "PASS" : "FAIL"}${r.ok ? ` · ${r.stats.studConnections} stud connections · centre of mass ${r.stats.comMarginStuds} studs inside` : ""}`);
for (const e of r.errors.slice(0, 8)) console.log(`    ✗ ${e.rule}: ${e.msg}`);
