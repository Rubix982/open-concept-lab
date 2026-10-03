#!/usr/bin/env node
// Loads Pollen Robotics' open Microduck (github.com/pollen-robotics/microduck_rl,
// Apache-2.0) as one triangle soup at its zero joint pose, so brickify.mjs has
// a real CAD shape to sample. Reads the MJCF body tree, places every visual
// mesh, and gives each triangle the LEGO colour nearest its material.
//   node tools/mjcf-mesh.mjs      -> summary of what was loaded
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { COLORS } from "../lib/parts.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const REPO = "https://raw.githubusercontent.com/pollen-robotics/microduck_rl/develop/src/mjlab_microduck/robot/microduck";
// robot_walk.xml: the walking robot with every visual mesh (no extra collision shapes)
const ROBOT = "robot_walk.xml";
export const SOURCE = "Microduck by Pollen Robotics, CAD from github.com/pollen-robotics/microduck_rl (Apache-2.0)";

async function cached(cacheDir, rel) {
  const file = path.join(cacheDir, rel.replace(/\//g, "__"));
  try { return await fs.readFile(file); } catch {}
  const res = await fetch(`${REPO}/${rel}`);
  if (!res.ok) throw new Error(`download failed (${res.status}): ${rel}`);
  const buf = Buffer.from(await res.arrayBuffer());
  await fs.mkdir(cacheDir, { recursive: true });
  await fs.writeFile(file, buf);
  return buf;
}

// ---- a small XML reader: enough for MJCF (elements, attributes, nesting)
function parseXml(text) {
  text = text.replace(/<!--[\s\S]*?-->/g, "").replace(/<\?[\s\S]*?\?>/g, "");
  const root = { tag: "#root", attrs: {}, children: [] }, stack = [root];
  for (const m of text.matchAll(/<(\/?)([\w:-]+)((?:\s+[\w:-]+\s*=\s*"[^"]*")*)\s*(\/?)>/g)) {
    const [, close, tag, attrText, selfClose] = m;
    if (close) { stack.pop(); continue; }
    const attrs = {};
    for (const a of attrText.matchAll(/([\w:-]+)\s*=\s*"([^"]*)"/g)) attrs[a[1]] = a[2];
    const el = { tag, attrs, children: [] };
    stack.at(-1).children.push(el);
    if (!selfClose) stack.push(el);
  }
  return root;
}
const nums = (s, d) => (s ? s.trim().split(/\s+/).map(Number) : d);

// ---- quaternions (w, x, y, z) and rigid transforms
const qmul = ([aw, ax, ay, az], [bw, bx, by, bz]) => [
  aw * bw - ax * bx - ay * by - az * bz, aw * bx + ax * bw + ay * bz - az * by,
  aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw];
function qrot([w, x, y, z], [vx, vy, vz]) {
  const n = Math.hypot(w, x, y, z) || 1; w /= n; x /= n; y /= n; z /= n;
  const tx = 2 * (y * vz - z * vy), ty = 2 * (z * vx - x * vz), tz = 2 * (x * vy - y * vx);
  return [vx + w * tx + (y * tz - z * ty), vy + w * ty + (z * tx - x * tz), vz + w * tz + (x * ty - y * tx)];
}
const compose = (parent, pos, quat) => {
  const p = qrot(parent.q, pos);
  return { p: [parent.p[0] + p[0], parent.p[1] + p[1], parent.p[2] + p[2]], q: qmul(parent.q, quat) };
};

// ---- STL, binary or ASCII
function parseStl(buf) {
  const n = buf.length >= 84 ? buf.readUInt32LE(80) : 0;
  if (buf.length === 84 + n * 50) {
    const out = new Float32Array(n * 9);
    for (let i = 0; i < n; i++) for (let k = 0; k < 9; k++) out[i * 9 + k] = buf.readFloatLE(84 + i * 50 + 12 + k * 4);
    return out;
  }
  const v = [...buf.toString("latin1").matchAll(/vertex\s+(\S+)\s+(\S+)\s+(\S+)/g)].flatMap((m) => [+m[1], +m[2], +m[3]]);
  return Float32Array.from(v);
}

// nearest LEGO colour by perceptual (CIE Lab) distance: plain RGB distance
// calls a light grey shell "Bright Pink"
function lab(r, g, b) {
  const lin = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  const [R, G, B] = [lin(r), lin(g), lin(b)];
  const f = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
  const x = f((R * 0.4124 + G * 0.3576 + B * 0.1805) / 0.95047), y = f(R * 0.2126 + G * 0.7152 + B * 0.0722), z = f((R * 0.0193 + G * 0.1192 + B * 0.9505) / 1.08883);
  return [116 * y - 16, 500 * (x - y), 200 * (y - z)];
}
const PALETTE = Object.entries(COLORS).map(([code, [, , hex]]) => [+code, lab(parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16))]);
export function nearestColor(r, g, b) {
  const L = lab(r, g, b);
  let best = 15, bd = Infinity;
  for (const [code, P] of PALETTE) { const d = (P[0] - L[0]) ** 2 + (P[1] - L[1]) ** 2 + (P[2] - L[2]) ** 2; if (d < bd) { bd = d; best = code; } }
  return best;
}

// A keyframe's hinge angles, in the order the joints appear in the robot file.
// STAND is the robot's own standing pose (scene.xml); the zero pose leans.
async function keyframe(cacheDir, name) {
  const scene = parseXml((await cached(cacheDir, "scene.xml")).toString("utf8"));
  const all = (el, out = []) => { for (const c of el.children) { if (c.tag === "key") out.push(c); all(c, out); } return out; };
  const key = all(scene).find((k) => k.attrs.name === name);
  if (!key) throw new Error(`no keyframe "${name}" in scene.xml`);
  return nums(key.attrs.qpos).slice(7);                       // skip the free joint's 7 values
}

export async function loadMjcfRobot({ cacheDir = path.join(here, "..", ".cache", "microduck"), pose = "STAND" } = {}) {
  const doc = parseXml((await cached(cacheDir, ROBOT)).toString("utf8"));
  const angles = pose ? await keyframe(cacheDir, pose) : [];
  let hinge = 0;
  const mujoco = doc.children.find((e) => e.tag === "mujoco");
  const meshdir = mujoco.children.find((e) => e.tag === "compiler")?.attrs.meshdir || "assets";
  const all = (el, tag, out = []) => { for (const c of el.children) { if (c.tag === tag) out.push(c); all(c, tag, out); } return out; };

  const meshFiles = {}, materials = {};
  for (const m of all(mujoco, "mesh")) {
    const name = m.attrs.name || path.basename(m.attrs.file, path.extname(m.attrs.file));
    meshFiles[name] = { file: m.attrs.file, scale: nums(m.attrs.scale, [1, 1, 1]) };
  }
  for (const m of all(mujoco, "material")) materials[m.attrs.name] = nums(m.attrs.rgba, [0.8, 0.8, 0.8, 1]);

  // walk the body tree: each body's frame is its parent's times its pos/quat,
  // then turned about its hinge (if any) by the keyframe angle
  const placed = [];
  (function walk(el, T) {
    for (const c of el.children) {
      if (c.tag === "body") {
        let B = compose(T, nums(c.attrs.pos, [0, 0, 0]), nums(c.attrs.quat, [1, 0, 0, 0]));
        const j = c.children.find((x) => x.tag === "joint" && (x.attrs.type || "hinge") === "hinge" && x.attrs.axis);
        if (j) {
          const a = angles[hinge++] || 0, ax = nums(j.attrs.axis), n = Math.hypot(...ax), jp = nums(j.attrs.pos, [0, 0, 0]);
          const q = [Math.cos(a / 2), ...ax.map((v) => (v / n) * Math.sin(a / 2))];
          B = compose(compose(compose(B, jp, [1, 0, 0, 0]), [0, 0, 0], q), jp.map((v) => -v), [1, 0, 0, 0]);
        }
        walk(c, B);
      }
      else if (c.tag === "geom" && c.attrs.mesh && (c.attrs.class === "visual" || c.attrs.group === "2")) {
        placed.push({ mesh: c.attrs.mesh, material: c.attrs.material, T: compose(T, nums(c.attrs.pos, [0, 0, 0]), nums(c.attrs.quat, [1, 0, 0, 0])) });
      }
    }
  })(mujoco.children.find((e) => e.tag === "worldbody"), { p: [0, 0, 0], q: [1, 0, 0, 0] });

  const stls = {};
  for (const name of new Set(placed.map((g) => g.mesh))) {
    const mf = meshFiles[name];
    if (!mf) throw new Error(`mesh "${name}" isn't declared in the MJCF assets`);
    stls[name] = parseStl(await cached(cacheDir, `${meshdir}/${mf.file}`));
  }

  const total = placed.reduce((s, g) => s + stls[g.mesh].length / 9, 0);
  const triangles = new Float32Array(total * 9), colors = new Uint8Array(total);
  let t = 0;
  for (const g of placed) {
    const src = stls[g.mesh], sc = meshFiles[g.mesh].scale, rgba = materials[g.material] || [0.8, 0.8, 0.8, 1];
    const col = nearestColor(rgba[0] * 255, rgba[1] * 255, rgba[2] * 255);
    for (let i = 0; i < src.length; i += 9, t++) {
      for (let k = 0; k < 3; k++) {
        const v = qrot(g.T.q, [src[i + k * 3] * sc[0], src[i + k * 3 + 1] * sc[1], src[i + k * 3 + 2] * sc[2]]);
        triangles[t * 9 + k * 3] = v[0] + g.T.p[0]; triangles[t * 9 + k * 3 + 1] = v[1] + g.T.p[1]; triangles[t * 9 + k * 3 + 2] = v[2] + g.T.p[2];
      }
      colors[t] = col;
    }
  }
  return { triangles, colors, meshes: [...new Set(placed.map((g) => g.mesh))] };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const { triangles, colors, meshes } = await loadMjcfRobot();
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < triangles.length; i++) { const k = i % 3; min[k] = Math.min(min[k], triangles[i]); max[k] = Math.max(max[k], triangles[i]); }
  const counts = {};
  for (const c of colors) counts[c] = (counts[c] || 0) + 1;
  console.log(`${triangles.length / 9} triangles from ${meshes.length} meshes`);
  console.log(`bounding box (m): x ${min[0].toFixed(3)}..${max[0].toFixed(3)}  y ${min[1].toFixed(3)}..${max[1].toFixed(3)}  z ${min[2].toFixed(3)}..${max[2].toFixed(3)}`);
  console.log("colours:", Object.entries(counts).map(([c, n]) => `${COLORS[c][0]} ${n}`).join(", "));
}
