#!/usr/bin/env node
// Load a 3D model from the formats people actually have (glTF/GLB, OBJ+MTL,
// STL, PLY, MagicaVoxel .vox) into one shape brickify can use: a triangle
// soup, Z up, with one colour per triangle. Textures are sampled, so a scan or
// an AI-made model keeps its colours.
//   node tools/mesh-load.mjs <file> [--up y|z]
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { PNG } from "pngjs";
import jpeg from "jpeg-js";

const GREY = [160, 165, 169];          // light bluish grey, for formats with no colour

// Each format has a usual "up". glTF says Y up in its spec; OBJ and PLY don't
// say, but Y up is what most exporters and scanners write; STL (from CAD) and
// MagicaVoxel are Z up. `up` overrides when a file breaks the habit.
const DEFAULT_UP = { glb: "y", gltf: "y", obj: "y", ply: "y", stl: "z", vox: "z" };

export async function loadMesh(file, { up } = {}) {
  const ext = path.extname(file).slice(1).toLowerCase();
  const read = READERS[ext];
  if (!read) throw new Error(`can't load .${ext} — supported: ${Object.keys(READERS).join(", ")}`);
  const out = new Soup();
  const textured = await read(file, out);
  if ((up ?? DEFAULT_UP[ext]) === "y") out.yUpToZUp();
  return out.result(ext, textured);
}

// ---- the shared output ---------------------------------------------------
class Soup {
  constructor() { this.pos = []; this.rgb = []; }
  tri(a, b, c, rgb) { this.pos.push(...a, ...b, ...c); this.rgb.push(...rgb.map((v) => Math.max(0, Math.min(255, Math.round(v))))); }
  // rotate +90° about x: (x, y, z) → (x, -z, y) keeps the shape right-handed
  yUpToZUp() { const p = this.pos; for (let i = 0; i < p.length; i += 3) { const y = p[i + 1]; p[i + 1] = -p[i + 2]; p[i + 2] = y; } }
  result(format, textured) {
    const triangles = Float32Array.from(this.pos), rgb = Uint8Array.from(this.rgb);
    const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
    for (let i = 0; i < triangles.length; i++) { const k = i % 3; min[k] = Math.min(min[k], triangles[i]); max[k] = Math.max(max[k], triangles[i]); }
    const colours = new Set();
    for (let i = 0; i < rgb.length; i += 3) colours.add((rgb[i] << 16) | (rgb[i + 1] << 8) | rgb[i + 2]);
    return { triangles, rgb, format, stats: { triangles: triangles.length / 9, bbox: { min, max }, textured: !!textured, colours: colours.size } };
  }
}

// ---- colour helpers ------------------------------------------------------
// glTF colour factors and vertex colours are linear; textures and our output
// are sRGB, so mixing happens in linear light.
const toLinear = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
const toSrgb = (l) => 255 * (l <= 0.0031308 ? l * 12.92 : 1.055 * l ** (1 / 2.4) - 0.055);

function decodeImage(buf) {
  if (buf[0] === 0x89 && buf[1] === 0x50) { const p = PNG.sync.read(buf); return { w: p.width, h: p.height, data: p.data }; }
  if (buf[0] === 0xff && buf[1] === 0xd8) { const j = jpeg.decode(buf, { useTArray: true, formatAsRGBA: true }); return { w: j.width, h: j.height, data: j.data }; }
  throw new Error("texture is neither PNG nor JPEG");
}
// Sample with repeat wrapping. `topLeft`: glTF puts v = 0 at the top row,
// OBJ at the bottom.
function sample(img, u, v, topLeft) {
  u -= Math.floor(u); v -= Math.floor(v);
  const x = Math.min(img.w - 1, Math.floor(u * img.w));
  const y = Math.min(img.h - 1, Math.floor((topLeft ? v : 1 - v) * img.h));
  const i = (y * img.w + x) * 4;
  return [img.data[i], img.data[i + 1], img.data[i + 2]];
}
// A triangle's texture colour: the three corners and the centre, averaged.
function sampleTri(img, uvs, topLeft) {
  const c = [(uvs[0][0] + uvs[1][0] + uvs[2][0]) / 3, (uvs[0][1] + uvs[1][1] + uvs[2][1]) / 3];
  const s = [...uvs, c].map(([u, v]) => sample(img, u, v, topLeft));
  return [0, 1, 2].map((k) => s.reduce((a, x) => a + x[k], 0) / 4);
}

// ---- glTF / GLB -----------------------------------------------------------
async function readGltf(file, out) {
  const raw = await fs.readFile(file), dir = path.dirname(file);
  let json, bin = null;
  if (raw.readUInt32LE(0) === 0x46546c67) {                 // "glTF" binary container
    let off = 12;
    while (off < raw.length) {
      const len = raw.readUInt32LE(off), type = raw.readUInt32LE(off + 4), data = raw.subarray(off + 8, off + 8 + len);
      if (type === 0x4e4f534a) json = JSON.parse(data.toString("utf8"));
      else if (type === 0x004e4942) bin = data;
      off += 8 + len;
    }
  } else json = JSON.parse(raw.toString("utf8"));
  const fromUri = async (uri) => uri.startsWith("data:") ? Buffer.from(uri.slice(uri.indexOf(",") + 1), "base64") : fs.readFile(path.join(dir, decodeURIComponent(uri)));
  const buffers = await Promise.all((json.buffers || []).map((b, i) => (b.uri === undefined ? (i === 0 ? bin : null) : fromUri(b.uri))));
  const view = (i) => { const v = json.bufferViews[i]; return buffers[v.buffer].subarray(v.byteOffset || 0, (v.byteOffset || 0) + v.byteLength); };

  const SIZE = { 5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4 }, COUNT = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 };
  const MAXV = { 5120: 127, 5121: 255, 5122: 32767, 5123: 65535, 5125: 4294967295 };
  function accessor(i) {
    const a = json.accessors[i], n = COUNT[a.type], size = SIZE[a.componentType];
    const out = new Array(a.count);
    if (a.bufferView === undefined) { for (let k = 0; k < a.count; k++) out[k] = new Array(n).fill(0); return out; }
    const b = view(a.bufferView), bv = json.bufferViews[a.bufferView], stride = bv.byteStride || n * size, base = a.byteOffset || 0;
    const dv = new DataView(b.buffer, b.byteOffset, b.byteLength);
    const get = { 5120: (o) => dv.getInt8(o), 5121: (o) => dv.getUint8(o), 5122: (o) => dv.getInt16(o, true), 5123: (o) => dv.getUint16(o, true), 5125: (o) => dv.getUint32(o, true), 5126: (o) => dv.getFloat32(o, true) }[a.componentType];
    for (let k = 0; k < a.count; k++) {
      const e = new Array(n);
      for (let c = 0; c < n; c++) {
        const v = get(base + k * stride + c * size);
        e[c] = a.normalized ? Math.max(v / MAXV[a.componentType], -1) : v;
      }
      out[k] = e;
    }
    return out;
  }
  const images = await Promise.all((json.images || []).map(async (im) => decodeImage(im.bufferView !== undefined ? view(im.bufferView) : await fromUri(im.uri))));
  const texImage = (texIndex) => (texIndex === undefined ? null : images[json.textures[texIndex].source]);

  // node transforms, as column-major 4x4 matrices
  const mul = (A, B) => { const r = new Array(16).fill(0); for (let c = 0; c < 4; c++) for (let rr = 0; rr < 4; rr++) for (let k = 0; k < 4; k++) r[c * 4 + rr] += A[k * 4 + rr] * B[c * 4 + k]; return r; };
  function local(node) {
    if (node.matrix) return node.matrix;
    const [tx, ty, tz] = node.translation || [0, 0, 0], [x, y, z, w] = node.rotation || [0, 0, 0, 1], [sx, sy, sz] = node.scale || [1, 1, 1];
    return [
      (1 - 2 * (y * y + z * z)) * sx, 2 * (x * y + z * w) * sx, 2 * (x * z - y * w) * sx, 0,
      2 * (x * y - z * w) * sy, (1 - 2 * (x * x + z * z)) * sy, 2 * (y * z + x * w) * sy, 0,
      2 * (x * z + y * w) * sz, 2 * (y * z - x * w) * sz, (1 - 2 * (x * x + y * y)) * sz, 0,
      tx, ty, tz, 1,
    ];
  }
  const apply = (M, [x, y, z]) => [M[0] * x + M[4] * y + M[8] * z + M[12], M[1] * x + M[5] * y + M[9] * z + M[13], M[2] * x + M[6] * y + M[10] * z + M[14]];

  let textured = false;
  function drawMesh(mesh, M) {
    for (const prim of mesh.primitives) {
      const mode = prim.mode ?? 4;
      if (![4, 5, 6].includes(mode)) continue;                  // points and lines have no surface
      const pos = accessor(prim.attributes.POSITION).map((p) => apply(M, p));
      const mat = prim.material !== undefined ? json.materials[prim.material] : {};
      const pbr = mat.pbrMetallicRoughness || {};
      const factor = (pbr.baseColorFactor || [1, 1, 1, 1]).slice(0, 3);
      const tex = pbr.baseColorTexture, img = tex ? texImage(tex.index) : null;
      const uv = img && prim.attributes[`TEXCOORD_${tex.texCoord || 0}`] !== undefined ? accessor(prim.attributes[`TEXCOORD_${tex.texCoord || 0}`]) : null;
      const col = prim.attributes.COLOR_0 !== undefined ? accessor(prim.attributes.COLOR_0) : null;
      if (img && uv) textured = true;
      let idx = prim.indices !== undefined ? accessor(prim.indices).map((e) => e[0]) : pos.map((_, i) => i);
      const tris = [];
      if (mode === 4) for (let i = 0; i + 2 < idx.length; i += 3) tris.push([idx[i], idx[i + 1], idx[i + 2]]);
      else if (mode === 5) for (let i = 0; i + 2 < idx.length; i++) tris.push(i % 2 ? [idx[i + 1], idx[i], idx[i + 2]] : [idx[i], idx[i + 1], idx[i + 2]]);
      else for (let i = 1; i + 1 < idx.length; i++) tris.push([idx[0], idx[i], idx[i + 1]]);
      for (const t of tris) {
        let lin = factor.slice();
        if (img && uv) { const s = sampleTri(img, t.map((i) => uv[i]), true); lin = lin.map((f, k) => f * toLinear(s[k])); }
        if (col) lin = lin.map((f, k) => f * (col[t[0]][k] + col[t[1]][k] + col[t[2]][k]) / 3);
        out.tri(pos[t[0]], pos[t[1]], pos[t[2]], lin.map(toSrgb));
      }
    }
  }
  function walk(i, parent) {
    const node = json.nodes[i], M = mul(parent, local(node));
    if (node.mesh !== undefined) drawMesh(json.meshes[node.mesh], M);
    for (const c of node.children || []) walk(c, M);
  }
  const I = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  const scene = json.scenes?.[json.scene ?? 0];
  if (scene) for (const n of scene.nodes) walk(n, I);
  else for (const m of json.meshes || []) drawMesh(m, I);   // no scene: draw meshes as they are
  return textured;
}

// ---- OBJ + MTL --------------------------------------------------------------
async function readMtl(file) {
  const mats = {}, dir = path.dirname(file);
  let cur = null;
  for (const line of (await fs.readFile(file, "utf8")).split(/\r?\n/)) {
    const t = line.trim().split(/\s+/);
    if (t[0] === "newmtl") mats[(cur = t.slice(1).join(" "))] = { kd: [1, 1, 1] };
    else if (cur && t[0] === "Kd") mats[cur].kd = t.slice(1, 4).map(Number);
    else if (cur && t[0] === "map_Kd") {              // options like -s 1 1 1 come first; the file name is last
      try { mats[cur].img = decodeImage(await fs.readFile(path.join(dir, t[t.length - 1].replace(/\\/g, "/")))); } catch { /* a missing texture leaves Kd */ }
    }
  }
  return mats;
}
async function readObj(file, out) {
  const v = [], vc = [], vt = [], dir = path.dirname(file);
  let mats = {}, mat = null, textured = false;
  for (const line of (await fs.readFile(file, "utf8")).split(/\r?\n/)) {
    const t = line.trim().split(/\s+/);
    if (t[0] === "v") { v.push(t.slice(1, 4).map(Number)); vc.push(t.length >= 7 ? t.slice(4, 7).map(Number) : null); }
    else if (t[0] === "vt") vt.push(t.slice(1, 3).map(Number));
    else if (t[0] === "mtllib") for (const f of line.trim().slice(7).trim().split(/\s+(?=\S+\.mtl)/i)) { try { Object.assign(mats, await readMtl(path.join(dir, f))); } catch { /* no mtl: plain grey */ } }
    else if (t[0] === "usemtl") mat = mats[t.slice(1).join(" ")] || null;
    else if (t[0] === "f") {
      // v, v/vt, v//vn, v/vt/vn; negative indices count back from the end
      const corners = t.slice(1).map((c) => {
        const [a, b] = c.split("/");
        const vi = +a < 0 ? v.length + +a : +a - 1, ti = b ? (+b < 0 ? vt.length + +b : +b - 1) : -1;
        return { vi, ti };
      });
      for (let i = 1; i + 1 < corners.length; i++) {        // n-gons as a fan
        const c = [corners[0], corners[i], corners[i + 1]];
        let rgb = GREY;
        if (mat) {
          rgb = mat.kd.map((k) => 255 * k);
          if (mat.img && c.every((x) => x.ti >= 0)) { const s = sampleTri(mat.img, c.map((x) => vt[x.ti]), false); rgb = s.map((x, k) => x * mat.kd[k]); textured = true; }
        } else if (c.every((x) => vc[x.vi])) rgb = [0, 1, 2].map((k) => (255 * c.reduce((a, x) => a + vc[x.vi][k], 0)) / 3);
        out.tri(v[c[0].vi], v[c[1].vi], v[c[2].vi], rgb);
      }
    }
  }
  return textured;
}

// ---- STL ------------------------------------------------------------------
async function readStl(file, out) {
  const buf = await fs.readFile(file);
  const n = buf.length >= 84 ? buf.readUInt32LE(80) : 0;
  if (buf.length === 84 + n * 50) {
    for (let i = 0; i < n; i++) {
      const o = 84 + i * 50, f = (k) => buf.readFloatLE(o + 12 + k * 4);
      const attr = buf.readUInt16LE(o + 48);
      // VisCAM/SolidView: bit 15 set means the low 15 bits are a 5:5:5 colour
      const rgb = attr & 0x8000 ? [attr & 31, (attr >> 5) & 31, (attr >> 10) & 31].map((c) => (c * 255) / 31) : GREY;
      out.tri([f(0), f(1), f(2)], [f(3), f(4), f(5)], [f(6), f(7), f(8)], rgb);
    }
  } else {
    const vs = [...buf.toString("utf8").matchAll(/vertex\s+(\S+)\s+(\S+)\s+(\S+)/g)].map((m) => [+m[1], +m[2], +m[3]]);
    for (let i = 0; i + 2 < vs.length; i += 3) out.tri(vs[i], vs[i + 1], vs[i + 2], GREY);
  }
  return false;
}

// ---- PLY ------------------------------------------------------------------
async function readPly(file, out) {
  const buf = await fs.readFile(file);
  const end = buf.indexOf("end_header");
  const header = buf.subarray(0, end).toString("latin1").split(/\r?\n/);
  let body = end + "end_header".length;
  while (buf[body] === 0x0d || buf[body] === 0x0a) { body++; if (buf[body - 1] === 0x0a) break; }
  let format = "ascii";
  const elements = [];
  for (const line of header) {
    const t = line.trim().split(/\s+/);
    if (t[0] === "format") format = t[1];
    else if (t[0] === "element") elements.push({ name: t[1], count: +t[2], props: [] });
    else if (t[0] === "property") elements[elements.length - 1].props.push(t[1] === "list" ? { list: true, countType: t[2], type: t[3], name: t[4] } : { type: t[1], name: t[2] });
  }
  const TYPES = { char: ["Int8", 1], int8: ["Int8", 1], uchar: ["Uint8", 1], uint8: ["Uint8", 1], short: ["Int16", 2], int16: ["Int16", 2], ushort: ["Uint16", 2], uint16: ["Uint16", 2],
    int: ["Int32", 4], int32: ["Int32", 4], uint: ["Uint32", 4], uint32: ["Uint32", 4], float: ["Float32", 4], float32: ["Float32", 4], double: ["Float64", 8], float64: ["Float64", 8] };
  const little = format !== "binary_big_endian";
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  let off = body, tokens = null, ti = 0;
  if (format === "ascii") tokens = buf.subarray(body).toString("latin1").trim().split(/\s+/);
  const next = (type) => {
    if (tokens) return +tokens[ti++];
    const [kind, size] = TYPES[type]; const v = dv[`get${kind}`](off, little); off += size; return v;
  };
  const data = {};
  for (const el of elements) {
    data[el.name] = [];
    for (let i = 0; i < el.count; i++) {
      const rec = {};
      for (const p of el.props) {
        if (p.list) { const n = next(p.countType); rec[p.name] = Array.from({ length: n }, () => next(p.type)); }
        else rec[p.name] = next(p.type);
      }
      data[el.name].push(rec);
    }
  }
  const verts = data.vertex || [];
  const isFloat = (name) => /float|double/.test(elements.find((e) => e.name === "vertex")?.props.find((p) => p.name === name)?.type || "");
  const colourOf = (r) => {
    const key = r.red !== undefined ? ["red", "green", "blue"] : r.diffuse_red !== undefined ? ["diffuse_red", "diffuse_green", "diffuse_blue"] : null;
    return key ? key.map((k) => (isFloat(k) ? r[k] * 255 : r[k])) : null;
  };
  for (const f of data.face || []) {
    const ix = f.vertex_indices || f.vertex_index || [];
    const fc = colourOf(f);
    for (let i = 1; i + 1 < ix.length; i++) {
      const c = [ix[0], ix[i], ix[i + 1]].map((k) => verts[k]);
      const cols = c.map(colourOf);
      const rgb = fc || (cols.every(Boolean) ? [0, 1, 2].map((k) => cols.reduce((a, x) => a + x[k], 0) / 3) : GREY);
      out.tri(...c.map((r) => [r.x, r.y, r.z]), rgb);
    }
  }
  return false;
}

// ---- MagicaVoxel .vox -------------------------------------------------------
// The default palette, when a file carries none: a 6x6x6 colour cube (R, then
// G, then B, each falling from ff to 00, black left out), then ten-step ramps
// of red, green, blue and grey. Index 0 means "no voxel".
const VOX_DEFAULT = (() => {
  const p = [[0, 0, 0]], L = [255, 204, 153, 102, 51, 0], R = [0xee, 0xdd, 0xbb, 0xaa, 0x88, 0x77, 0x55, 0x44, 0x22, 0x11];
  for (const r of L) for (const g of L) for (const b of L) if (r || g || b) p.push([r, g, b]);
  for (const v of R) p.push([v, 0, 0]);
  for (const v of R) p.push([0, v, 0]);
  for (const v of R) p.push([0, 0, v]);
  for (const v of R) p.push([v, v, v]);
  return p;
})();
async function readVox(file, out) {
  const buf = await fs.readFile(file);
  if (buf.toString("latin1", 0, 4) !== "VOX ") throw new Error("not a MagicaVoxel file");
  const models = [];
  let size = null, palette = null;
  // chunks: id, content size, children size, content, children — MAIN holds the rest
  for (let off = 8; off + 12 <= buf.length;) {
    const id = buf.toString("latin1", off, off + 4), n = buf.readUInt32LE(off + 4), children = buf.readUInt32LE(off + 8), c = off + 12;
    if (id === "SIZE") size = [buf.readUInt32LE(c), buf.readUInt32LE(c + 4), buf.readUInt32LE(c + 8)];
    else if (id === "XYZI") {
      const count = buf.readUInt32LE(c), vox = [];
      for (let i = 0; i < count; i++) vox.push([buf[c + 4 + i * 4], buf[c + 5 + i * 4], buf[c + 6 + i * 4], buf[c + 7 + i * 4]]);
      models.push({ size, vox });
    } else if (id === "RGBA") {
      // entry i is colour index i + 1
      palette = [[0, 0, 0]];
      for (let i = 0; i < 255; i++) palette.push([buf[c + i * 4], buf[c + i * 4 + 1], buf[c + i * 4 + 2]]);
    }
    off = id === "MAIN" ? c + n : c + n + children;
  }
  palette ||= VOX_DEFAULT;
  // Every model sits at the origin: the scene graph (nTRN/nSHP) that would
  // place several models is not read.
  const filled = new Map();
  for (const m of models) for (const [x, y, z, ci] of m.vox) filled.set(`${x},${y},${z}`, ci);
  const FACES = [
    [[1, 0, 0], [[1, 0, 0], [1, 1, 0], [1, 1, 1], [1, 0, 1]]], [[-1, 0, 0], [[0, 0, 0], [0, 0, 1], [0, 1, 1], [0, 1, 0]]],
    [[0, 1, 0], [[0, 1, 0], [0, 1, 1], [1, 1, 1], [1, 1, 0]]], [[0, -1, 0], [[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]]],
    [[0, 0, 1], [[0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]]], [[0, 0, -1], [[0, 0, 0], [0, 1, 0], [1, 1, 0], [1, 0, 0]]],
  ];
  for (const [key, ci] of filled) {
    const [x, y, z] = key.split(",").map(Number), rgb = palette[ci] || GREY;
    for (const [[dx, dy, dz], quad] of FACES) {
      if (filled.has(`${x + dx},${y + dy},${z + dz}`)) continue;     // only faces between filled and empty
      const q = quad.map(([a, b, c]) => [x + a, y + b, z + c]);
      out.tri(q[0], q[1], q[2], rgb); out.tri(q[0], q[2], q[3], rgb);
    }
  }
  return false;
}

const READERS = { glb: readGltf, gltf: readGltf, obj: readObj, stl: readStl, ply: readPly, vox: readVox };

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2), file = args.find((a) => !a.startsWith("--")), ui = args.indexOf("--up");
  if (!file) { console.log("usage: node tools/mesh-load.mjs <file> [--up y|z]"); process.exit(1); }
  const m = await loadMesh(file, { up: ui >= 0 ? args[ui + 1] : undefined });
  const r = (v) => Math.round(v * 1000) / 1000;
  console.log(`${path.basename(file)} · ${m.format} · ${m.stats.triangles} triangles · textured: ${m.stats.textured}`);
  console.log(`  bbox (z up): [${m.stats.bbox.min.map(r)}] → [${m.stats.bbox.max.map(r)}]`);
  const counts = new Map();
  for (let i = 0; i < m.rgb.length; i += 3) { const h = "#" + [m.rgb[i], m.rgb[i + 1], m.rgb[i + 2]].map((x) => x.toString(16).padStart(2, "0")).join(""); counts.set(h, (counts.get(h) || 0) + 1); }
  console.log(`  ${m.stats.colours} distinct colours; most common:`);
  for (const [h, n] of [...counts].sort((a, b) => b[1] - a[1]).slice(0, 10)) console.log(`    ${h}  ${((100 * n) / m.stats.triangles).toFixed(1)}%`);
}
