#!/usr/bin/env node
// Where a part's top studs are, in grid cells, read from its LDraw file
// (every reference to a stud primitive, transformed into the part's frame).
//   node tools/ldraw-studs.mjs 3039 3062b
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { partBox } from "./ldraw-bbox.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const cacheDir = path.join(here, "..", ".cache", "ldraw");
const read = async (name) => fs.readFile(path.join(cacheDir, name.toLowerCase().replace(/\\/g, "/").replace(/\//g, "__")), "utf8");

const mul = (A, B) => {
  const r = [];
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) r[i * 4 + j] = A[i*4]*B[j] + A[i*4+1]*B[4+j] + A[i*4+2]*B[8+j];
    r[i * 4 + 3] = A[i*4]*B[3] + A[i*4+1]*B[7] + A[i*4+2]*B[11] + A[i*4+3];
  }
  return r;
};
// Top studs only: stud.dat, stud2.dat (hollow), and their logo-less variants.
const isStud = (n) => /^stud2?a?\.dat$/i.test(n) || /^stud\.dat$/i.test(n);

async function walk(name, M, out) {
  let text; try { text = await read(name); } catch { return; }
  for (const raw of text.split(/\r?\n/)) {
    const t = raw.trim().split(/\s+/);
    if (t[0] !== "1") continue;
    const file = t.slice(14).join(" ");
    const [x, y, z, a, b, c, d, e, f, g, h, i] = t.slice(2, 14).map(Number);
    const N = mul(M, [a, b, c, x, d, e, f, y, g, h, i, z]);
    if (isStud(path.basename(file.replace(/\\/g, "/")))) { if (N[5] > 0) out.push([N[3], N[7], N[11]]); }   // upright studs only
    else await walk(file, N, out);
  }
}

export async function studCells(id) {
  const { box } = await partBox(id);          // also makes sure the files are cached
  const pts = [];
  await walk(id + ".dat", [1,0,0,0, 0,1,0,0, 0,0,1,0], pts);
  return pts.map(([x, , z]) => [Math.round((x - box.min[0] - 10) / 20), Math.round((z - box.min[2] - 10) / 20)])
    .sort((p, q) => p[0] - q[0] || p[1] - q[1]);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  for (const id of process.argv.slice(2)) {
    const { title, box } = await partBox(id);
    console.log(`${id.padEnd(6)} ${title.padEnd(34)} x[${box.min[0]},${box.max[0]}] y[${box.min[1]},${box.max[1]}] z[${box.min[2]},${box.max[2]}]  studs ${JSON.stringify(await studCells(id))}`);
  }
}
