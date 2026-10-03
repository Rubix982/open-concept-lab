#!/usr/bin/env node
// Fetches LDraw part files (official library) and computes each part's true
// bounding box by walking subfiles. Used to verify the footprint, height and
// orientation that brick-check assumes for every part it emits.
//   node tools/ldraw-bbox.mjs 3001 3020 ...
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const cacheDir = path.join(here, "..", ".cache", "ldraw");
const BASE = "https://library.ldraw.org/library/official/";
const DIRS = ["parts/", "p/", "parts/s/", "p/48/"];

async function fetchDat(name) {
  const key = name.toLowerCase().replace(/\\/g, "/");
  const cached = path.join(cacheDir, key.replace(/\//g, "__"));
  try { return await fs.readFile(cached, "utf8"); } catch {}
  for (const d of DIRS) {
    const res = await fetch(BASE + d + key);
    if (res.ok) {
      const text = await res.text();
      await fs.mkdir(cacheDir, { recursive: true });
      await fs.writeFile(cached, text);
      return text;
    }
  }
  throw new Error("not found in LDraw library: " + name);
}

const mul = (A, B) => { // 3x4 affine [a b c x; d e f y; g h i z]
  const r = [];
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) r[i * 4 + j] = A[i*4]*B[j] + A[i*4+1]*B[4+j] + A[i*4+2]*B[8+j];
    r[i * 4 + 3] = A[i*4]*B[3] + A[i*4+1]*B[7] + A[i*4+2]*B[11] + A[i*4+3];
  }
  return r;
};
const apply = (M, [x, y, z]) => [
  M[0]*x + M[1]*y + M[2]*z + M[3], M[4]*x + M[5]*y + M[6]*z + M[7], M[8]*x + M[9]*y + M[10]*z + M[11]];

async function bbox(name, M, box) {
  const text = await fetchDat(name);
  for (const raw of text.split(/\r?\n/)) {
    const t = raw.trim().split(/\s+/);
    if (t[0] === "1") {
      const [x, y, z, a, b, c, d, e, f, g, h, i] = t.slice(2, 14).map(Number);
      await bbox(t.slice(14).join(" "), mul(M, [a, b, c, x, d, e, f, y, g, h, i, z]), box);
    } else if (t[0] === "3" || t[0] === "4") {
      const n = t[0] === "3" ? 3 : 4;
      for (let k = 0; k < n; k++) {
        const p = apply(M, t.slice(2 + k * 3, 5 + k * 3).map(Number));
        for (let q = 0; q < 3; q++) { box.min[q] = Math.min(box.min[q], p[q]); box.max[q] = Math.max(box.max[q], p[q]); }
      }
    }
  }
}

export async function partBox(id) {
  const box = { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] };
  await bbox(id + ".dat", [1,0,0,0, 0,1,0,0, 0,0,1,0], box);
  const title = (await fetchDat(id + ".dat")).split(/\r?\n/)[0].replace(/^0\s*/, "");
  return { id, title, box };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  for (const id of process.argv.slice(2)) {
    const { title, box } = await partBox(id);
    const r = v => Math.round(v * 10) / 10;
    console.log(`${id.padEnd(6)} ${title.padEnd(32)} x[${r(box.min[0])},${r(box.max[0])}] y[${r(box.min[1])},${r(box.max[1])}] z[${r(box.min[2])},${r(box.max[2])}]`);
  }
}
