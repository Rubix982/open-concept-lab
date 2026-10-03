#!/usr/bin/env node
// Flattens an LDraw part into triangles and edge lines in the part's own LDU
// frame, so a player can draw its real shape (slopes, round parts).
//   node tools/ldraw-mesh.mjs 3039     -> prints triangle and edge counts
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { partBox } from "./ldraw-bbox.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const cacheDir = path.join(here, "..", ".cache", "ldraw");
const read = (name) => fs.readFile(path.join(cacheDir, name.toLowerCase().replace(/\\/g, "/").replace(/\//g, "__")), "utf8");
const mul = (A, B) => {
  const r = [];
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) r[i * 4 + j] = A[i*4]*B[j] + A[i*4+1]*B[4+j] + A[i*4+2]*B[8+j];
    r[i * 4 + 3] = A[i*4]*B[3] + A[i*4+1]*B[7] + A[i*4+2]*B[11] + A[i*4+3];
  }
  return r;
};
const apply = (M, x, y, z) => [M[0]*x + M[1]*y + M[2]*z + M[3], M[4]*x + M[5]*y + M[6]*z + M[7], M[8]*x + M[9]*y + M[10]*z + M[11]];

async function walk(name, M, out) {
  const text = await read(name);
  for (const raw of text.split(/\r?\n/)) {
    const t = raw.trim().split(/\s+/), v = t.slice(2).map(Number);
    if (t[0] === "1") {
      const [x, y, z, a, b, c, d, e, f, g, h, i] = v;
      await walk(t.slice(14).join(" "), mul(M, [a, b, c, x, d, e, f, y, g, h, i, z]), out);
    } else if (t[0] === "2") {
      out.edge.push(...apply(M, v[0], v[1], v[2]), ...apply(M, v[3], v[4], v[5]));
    } else if (t[0] === "3") {
      out.tri.push(...apply(M, v[0], v[1], v[2]), ...apply(M, v[3], v[4], v[5]), ...apply(M, v[6], v[7], v[8]));
    } else if (t[0] === "4") {
      const p = [0, 1, 2, 3].map((k) => apply(M, v[k * 3], v[k * 3 + 1], v[k * 3 + 2]));
      out.tri.push(...p[0], ...p[1], ...p[2], ...p[0], ...p[2], ...p[3]);
    }
  }
}

// Coordinates rounded to 0.1 LDU (0.005 of a stud) to keep pages small.
export async function partMesh(id) {
  await partBox(id);                           // fetches and caches every file it needs
  const out = { tri: [], edge: [] };
  await walk(id + ".dat", [1,0,0,0, 0,1,0,0, 0,0,1,0], out);
  const q = (a) => a.map((x) => Math.round(x * 10) / 10);
  return { tri: q(out.tri), edge: q(out.edge) };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  for (const id of process.argv.slice(2)) {
    const m = await partMesh(id);
    console.log(`${id.padEnd(6)} ${m.tri.length / 9} triangles · ${m.edge.length / 6} edges · ${(JSON.stringify(m).length / 1024).toFixed(0)} KB`);
  }
}
