// The loader, tested on a small coloured box written in every format (so the
// expected triangles, outline and colours are known exactly), then on two
// real CC0 models if the network is there.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";
import { PNG } from "pngjs";
import { loadMesh } from "../tools/mesh-load.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const dir = await fs.mkdtemp(path.join(os.tmpdir(), "mesh-load-"));

// A 1 x 2 x 3 box in the file's own axes, one colour per face, so the "up"
// conversion and the colours can both be checked.
const FACES = [
  [[1, 0, 0], [1, 2, 0], [1, 2, 3], [1, 0, 3]], [[0, 0, 0], [0, 0, 3], [0, 2, 3], [0, 2, 0]],
  [[0, 2, 0], [0, 2, 3], [1, 2, 3], [1, 2, 0]], [[0, 0, 0], [1, 0, 0], [1, 0, 3], [0, 0, 3]],
  [[0, 0, 3], [1, 0, 3], [1, 2, 3], [0, 2, 3]], [[0, 0, 0], [0, 2, 0], [1, 2, 0], [1, 0, 0]],
];
const FC = [[200, 30, 30], [30, 200, 30], [30, 30, 200], [200, 200, 30], [200, 30, 200], [30, 200, 200]];
const TRIS = FACES.flatMap((q, k) => [[q[0], q[1], q[2], k], [q[0], q[2], q[3], k]]);
// texture: 2 columns x 3 rows, face k in pixel (k % 2, row floor(k / 2) from the top)
const png = (() => {
  const p = new PNG({ width: 2, height: 3 });
  FC.forEach(([r, g, b], k) => { const i = (Math.floor(k / 2) * 2 + (k % 2)) * 4; p.data.set([r, g, b, 255], i); });
  return PNG.sync.write(p);
})();
const faceUV = (k, corner, topLeft) => {
  const u = ((k % 2) + 0.3 + 0.4 * (corner === 1 || corner === 2)) / 2;
  const vTop = (Math.floor(k / 2) + 0.3 + 0.4 * (corner >= 2)) / 3;
  return [u, topLeft ? vTop : 1 - vTop];
};

const Y_UP = { min: [0, -3, 0], max: [1, 0, 2] }, Z_UP = { min: [0, 0, 0], max: [1, 2, 3] };
function near(a, b, tol, msg) { a.forEach((v, i) => assert.ok(Math.abs(v - b[i]) <= tol, `${msg}: ${a} vs ${b}`)); }
function faceColours(m) { return FC.map((_, k) => [...m.rgb.subarray(k * 6, k * 6 + 3)]); }
function checkBox(m, bbox, msg) {
  assert.equal(m.stats.triangles, 12, msg);
  near(m.stats.bbox.min, bbox.min, 1e-5, `${msg} bbox min`);
  near(m.stats.bbox.max, bbox.max, 1e-5, `${msg} bbox max`);
}

test("binary STL, with VisCAM colours, and ASCII STL", async () => {
  const b = Buffer.alloc(84 + 12 * 50); b.writeUInt32LE(12, 80);
  TRIS.forEach(([p, q, r, k], i) => {
    const o = 84 + i * 50;
    [p, q, r].forEach((v, j) => v.forEach((c, n) => b.writeFloatLE(c, o + 12 + j * 12 + n * 4)));
    const [R, G, B] = FC[k].map((c) => Math.round((c * 31) / 255));
    b.writeUInt16LE(0x8000 | R | (G << 5) | (B << 10), o + 48);
  });
  await fs.writeFile(path.join(dir, "box.stl"), b);
  const m = await loadMesh(path.join(dir, "box.stl"));
  checkBox(m, Z_UP, "binary STL");
  faceColours(m).forEach((c, k) => near(c, FC[k], 5, `STL face ${k}`));

  const ascii = "solid box\n" + TRIS.map(([p, q, r]) => `facet normal 0 0 0\n outer loop\n${[p, q, r].map((v) => `  vertex ${v.join(" ")}`).join("\n")}\n endloop\nendfacet`).join("\n") + "\nendsolid box\n";
  await fs.writeFile(path.join(dir, "ascii.stl"), ascii);
  const a = await loadMesh(path.join(dir, "ascii.stl"));
  checkBox(a, Z_UP, "ASCII STL");
  assert.deepEqual([...a.rgb.subarray(0, 3)], [160, 165, 169], "no colour: grey");
});

test("OBJ with MTL colours, and OBJ with a texture (V flipped from glTF)", async () => {
  const v = TRIS.flatMap(([p, q, r]) => [p, q, r]).map((x) => `v ${x.join(" ")}`).join("\n");
  await fs.writeFile(path.join(dir, "kd.mtl"), FC.map((c, k) => `newmtl m${k}\nKd ${c.map((x) => x / 255).join(" ")}`).join("\n"));
  const faces = TRIS.map((_, i) => `usemtl m${TRIS[i][3]}\nf ${i * 3 + 1} ${i * 3 + 2} ${-(34 - i * 3)}`).join("\n");   // a negative index too
  await fs.writeFile(path.join(dir, "kd.obj"), `mtllib kd.mtl\n${v}\n${faces}\n`);
  const m = await loadMesh(path.join(dir, "kd.obj"));
  checkBox(m, Y_UP, "OBJ+MTL");
  faceColours(m).forEach((c, k) => near(c, FC[k], 1, `OBJ face ${k}`));

  await fs.writeFile(path.join(dir, "tex.png"), png);
  await fs.writeFile(path.join(dir, "tex.mtl"), "newmtl t\nKd 1 1 1\nmap_Kd -s 1 1 1 tex.png\n");
  // one quad per face, as an n-gon, with texture coordinates
  const verts = FACES.flat().map((x) => `v ${x.join(" ")}`).join("\n");
  const uvs = FACES.flatMap((_, k) => [0, 1, 2, 3].map((c) => `vt ${faceUV(k, c, false).join(" ")}`)).join("\n");
  const quads = FACES.map((_, k) => `f ${[1, 2, 3, 4].map((c) => `${k * 4 + c}/${k * 4 + c}`).join(" ")}`).join("\n");
  await fs.writeFile(path.join(dir, "tex.obj"), `mtllib tex.mtl\n${verts}\n${uvs}\nusemtl t\n${quads}\n`);
  const t = await loadMesh(path.join(dir, "tex.obj"));
  checkBox(t, Y_UP, "textured OBJ");
  assert.equal(t.stats.textured, true);
  faceColours(t).forEach((c, k) => near(c, FC[k], 1, `textured OBJ face ${k}`));
});

test("PLY, ASCII and binary, with vertex colours", async () => {
  const verts = FACES.flatMap((q, k) => q.map((p) => [...p, ...FC[k]]));
  const faces = FACES.map((_, k) => [k * 4, k * 4 + 1, k * 4 + 2, k * 4 + 3]);
  const head = (fmt) => `ply\nformat ${fmt} 1.0\nelement vertex ${verts.length}\nproperty float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nelement face ${faces.length}\nproperty list uchar int vertex_indices\nend_header\n`;
  await fs.writeFile(path.join(dir, "box.ply"), head("ascii") + verts.map((v) => v.join(" ")).join("\n") + "\n" + faces.map((f) => `4 ${f.join(" ")}`).join("\n") + "\n");
  const a = await loadMesh(path.join(dir, "box.ply"));
  checkBox(a, Y_UP, "ASCII PLY");
  faceColours(a).forEach((c, k) => near(c, FC[k], 0, `PLY face ${k}`));

  const body = Buffer.alloc(verts.length * 15 + faces.length * 17);
  let o = 0;
  for (const v of verts) { for (let i = 0; i < 3; i++) { body.writeFloatLE(v[i], o); o += 4; } for (let i = 3; i < 6; i++) body[o++] = v[i]; }
  for (const f of faces) { body[o++] = 4; for (const i of f) { body.writeInt32LE(i, o); o += 4; } }
  await fs.writeFile(path.join(dir, "bin.ply"), Buffer.concat([Buffer.from(head("binary_little_endian")), body]));
  const b = await loadMesh(path.join(dir, "bin.ply"));
  checkBox(b, Y_UP, "binary PLY");
  faceColours(b).forEach((c, k) => near(c, FC[k], 0, `binary PLY face ${k}`));
});

test("MagicaVoxel .vox: two voxels, with and without a palette", async () => {
  const chunk = (id, content, children = Buffer.alloc(0)) => {
    const h = Buffer.alloc(12); h.write(id, 0, "latin1"); h.writeUInt32LE(content.length, 4); h.writeUInt32LE(children.length, 8);
    return Buffer.concat([h, content, children]);
  };
  const ints = (...xs) => { const b = Buffer.alloc(xs.length * 4); xs.forEach((x, i) => b.writeUInt32LE(x, i * 4)); return b; };
  const vox = (voxels, rgba) => {
    const kids = [chunk("SIZE", ints(2, 1, 1)), chunk("XYZI", Buffer.concat([ints(voxels.length), Buffer.from(voxels.flat())]))];
    if (rgba) kids.push(chunk("RGBA", rgba));
    const head = Buffer.alloc(8); head.write("VOX ", 0, "latin1"); head.writeUInt32LE(150, 4);
    return Buffer.concat([head, chunk("MAIN", Buffer.alloc(0), Buffer.concat(kids))]);
  };
  const pal = Buffer.alloc(1024); pal.set([255, 0, 0, 255], 0); pal.set([0, 0, 255, 255], 4);   // colour indices 1 and 2
  await fs.writeFile(path.join(dir, "two.vox"), vox([[0, 0, 0, 1], [1, 0, 0, 2]], pal));
  const m = await loadMesh(path.join(dir, "two.vox"));
  assert.equal(m.stats.triangles, 20, "12 + 12 faces' triangles minus the shared face on each");
  near(m.stats.bbox.min, [0, 0, 0], 0, "vox min"); near(m.stats.bbox.max, [2, 1, 1], 0, "vox max");
  const cols = new Set(); for (let i = 0; i < m.rgb.length; i += 3) cols.add(`${m.rgb[i]},${m.rgb[i + 1]},${m.rgb[i + 2]}`);
  assert.deepEqual([...cols].sort(), ["0,0,255", "255,0,0"]);

  await fs.writeFile(path.join(dir, "default.vox"), vox([[0, 0, 0, 1], [1, 0, 0, 216]]));
  const d = await loadMesh(path.join(dir, "default.vox"));
  const dc = new Set(); for (let i = 0; i < d.rgb.length; i += 3) dc.add(`${d.rgb[i]},${d.rgb[i + 1]},${d.rgb[i + 2]}`);
  assert.deepEqual([...dc].sort(), ["238,0,0", "255,255,255"], "default palette: 1 is white, 216 starts the red ramp");
});

function glb({ factor, texture, translation }) {
  const pos = new Float32Array(TRIS.flatMap(([p, q, r]) => [...p, ...q, ...r]));
  const uv = new Float32Array(FACES.flatMap((_, k) => [[0, 1, 2], [0, 2, 3]].flatMap((t) => t.flatMap((c) => faceUV(k, c, true)))));
  const parts = [Buffer.from(pos.buffer)];
  if (texture) parts.push(Buffer.from(uv.buffer), png);
  const pad = (b) => Buffer.concat([b, Buffer.alloc((4 - (b.length % 4)) % 4)]);
  const views = [], padded = [];
  let off = 0;
  for (const p of parts) { const q = pad(p); views.push({ buffer: 0, byteOffset: off, byteLength: p.length }); padded.push(q); off += q.length; }
  const bin = Buffer.concat(padded);
  const json = {
    asset: { version: "2.0" }, scene: 0, scenes: [{ nodes: [0] }],
    nodes: [{ mesh: 0, ...(translation ? { translation } : {}) }],
    meshes: [{ primitives: [{ attributes: { POSITION: 0, ...(texture ? { TEXCOORD_0: 1 } : {}) }, material: 0 }] }],
    materials: [{ pbrMetallicRoughness: { baseColorFactor: [...(factor || [1, 1, 1]), 1], ...(texture ? { baseColorTexture: { index: 0 } } : {}) } }],
    accessors: [{ bufferView: 0, componentType: 5126, count: 36, type: "VEC3", min: [0, 0, 0], max: [1, 2, 3] }, ...(texture ? [{ bufferView: 1, componentType: 5126, count: 36, type: "VEC2" }] : [])],
    bufferViews: views, buffers: [{ byteLength: bin.length }],
    ...(texture ? { textures: [{ source: 0 }], images: [{ bufferView: 2, mimeType: "image/png" }] } : {}),
  };
  let js = Buffer.from(JSON.stringify(json)); js = Buffer.concat([js, Buffer.alloc((4 - (js.length % 4)) % 4, 0x20)]);
  const chunk = (type, data) => { const h = Buffer.alloc(8); h.writeUInt32LE(data.length, 0); h.writeUInt32LE(type, 4); return Buffer.concat([h, data]); };
  const body = Buffer.concat([chunk(0x4e4f534a, js), chunk(0x004e4942, bin)]);
  const head = Buffer.alloc(12); head.writeUInt32LE(0x46546c67, 0); head.writeUInt32LE(2, 4); head.writeUInt32LE(12 + body.length, 8);
  return Buffer.concat([head, body]);
}

test("GLB: a colour factor (linear light) on a moved node, and an embedded texture", async () => {
  await fs.writeFile(path.join(dir, "factor.glb"), glb({ factor: [0.5, 0.25, 1], translation: [10, 0, 0] }));
  const f = await loadMesh(path.join(dir, "factor.glb"));
  checkBox(f, { min: [10, -3, 0], max: [11, 0, 2] }, "GLB with a translated node");
  near([...f.rgb.subarray(0, 3)], [188, 137, 255], 1, "linear 0.5/0.25/1 shown in sRGB");

  await fs.writeFile(path.join(dir, "tex.glb"), glb({ texture: true }));
  const t = await loadMesh(path.join(dir, "tex.glb"));
  checkBox(t, Y_UP, "textured GLB");
  assert.equal(t.stats.textured, true);
  faceColours(t).forEach((c, k) => near(c, FC[k], 1, `GLB texture face ${k}`));
});

test("--up overrides a format's habit", async () => {
  const m = await loadMesh(path.join(dir, "box.ply"), { up: "z" });
  checkBox(m, Z_UP, "PLY read as z-up");
});

// ---- real models, if the network is there ------------------------------------
const samples = path.join(here, "..", ".cache", "samples");
async function fetchCached(url, name) {
  const file = path.join(samples, name);
  try { await fs.access(file); return file; } catch {}
  const res = await fetch(url, { signal: AbortSignal.timeout(60000) });
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  await fs.mkdir(samples, { recursive: true });
  await fs.writeFile(file, Buffer.from(await res.arrayBuffer()));
  return file;
}
// just enough of a zip reader: the central directory, stored or deflated entries
async function unzip(file, into) {
  const b = await fs.readFile(file);
  let e = b.length - 22; while (e > 0 && b.readUInt32LE(e) !== 0x06054b50) e--;
  let p = b.readUInt32LE(e + 16);
  const n = b.readUInt16LE(e + 10), names = [];
  for (let i = 0; i < n; i++) {
    const method = b.readUInt16LE(p + 10), size = b.readUInt32LE(p + 20), nameLen = b.readUInt16LE(p + 28), extra = b.readUInt16LE(p + 30), comment = b.readUInt16LE(p + 32), local = b.readUInt32LE(p + 42);
    const name = b.toString("utf8", p + 46, p + 46 + nameLen);
    const start = local + 30 + b.readUInt16LE(local + 26) + b.readUInt16LE(local + 28), data = b.subarray(start, start + size);
    if (!name.endsWith("/")) {
      const out = path.join(into, name); await fs.mkdir(path.dirname(out), { recursive: true });
      await fs.writeFile(out, method === 8 ? zlib.inflateRawSync(data) : data); names.push(name);
    }
    p += 46 + nameLen + extra + comment;
  }
  return names;
}

test("real model: Khronos Avocado (GLB, textured, CC0)", async (t) => {
  let file;
  try { file = await fetchCached("https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Avocado/glTF-Binary/Avocado.glb", "Avocado.glb"); }
  catch (e) { t.skip(`offline: ${e.message}`); return; }
  const m = await loadMesh(file);
  console.log(`# Avocado: ${m.stats.triangles} triangles, bbox ${JSON.stringify(m.stats.bbox)}, ${m.stats.colours} colours, textured ${m.stats.textured}`);
  assert.ok(m.stats.triangles > 500);
  assert.equal(m.stats.textured, true);
  assert.ok(m.stats.colours > 50, "the texture's colours come through");
});

test("real model: Keenan Crane's Spot (OBJ + texture, CC0)", async (t) => {
  let zip;
  try { zip = await fetchCached("https://www.cs.cmu.edu/~kmcrane/Projects/ModelRepository/spot.zip", "spot.zip"); }
  catch (e) { t.skip(`offline: ${e.message}`); return; }
  const into = path.join(samples, "spot");
  const names = await unzip(zip, into);
  const objName = names.find((n) => /spot_triangulated\.obj$/.test(n)) || names.find((n) => n.endsWith(".obj"));
  const texName = names.find((n) => /texture\.png$/i.test(n));
  assert.ok(objName && texName, `zip holds ${names.join(", ")}`);
  // the download has no .mtl; write one that points at its texture
  const objDir = path.join(into, path.dirname(objName));
  await fs.writeFile(path.join(objDir, "spot-test.mtl"), `newmtl spot\nKd 1 1 1\nmap_Kd ${path.relative(objDir, path.join(into, texName))}\n`);
  const objText = await fs.readFile(path.join(into, objName), "utf8");
  await fs.writeFile(path.join(objDir, "spot-test.obj"), `mtllib spot-test.mtl\nusemtl spot\n${objText.replace(/^(mtllib|usemtl).*$/gm, "")}`);
  const m = await loadMesh(path.join(objDir, "spot-test.obj"));
  console.log(`# Spot: ${m.stats.triangles} triangles, bbox ${JSON.stringify(m.stats.bbox)}, ${m.stats.colours} colours, textured ${m.stats.textured}`);
  assert.ok(m.stats.triangles > 1000);
  assert.equal(m.stats.textured, true);
  assert.ok(m.stats.colours > 20, "the texture's colours come through");
});
