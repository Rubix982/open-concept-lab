// The blueprint player: draws an explainer timeline (from script.mjs) as a
// pure function of time on a 1920×1080 canvas — navy paper, thin bright line
// art, mono labels — and exposes the same contract as the brick player, so
// render.mjs can turn it into an MP4 with sound and captions:
//   __renderAt(ms), __duration, __renderAudio(from, to), __narration
// A classic script: reads window.TIMELINE, draws into <canvas id="stage">.
(function () {
"use strict";
const TL = window.TIMELINE, W = TL.meta.w, H = TL.meta.h, DUR = TL.meta.duration;

// ---- theme
const C = {
  bg0: "#0b1636", bg1: "#060c22", grid: "rgba(120,150,255,0.055)", grid2: "rgba(120,150,255,0.10)",
  ink: "#dbe6ff", dim: "rgba(219,230,255,0.55)", faint: "rgba(219,230,255,0.22)", ghost: "rgba(219,230,255,0.10)",
  accent: "#ff7a59", cyan: "#7cc8ff", green: "#7ee0a8", violet: "#9d7dff", gold: "#ffd27a",
};
const color = (name) => C[name] || name;
const MONO = '"IBM Plex Mono", ui-monospace, Menlo, monospace', SANS = '"IBM Plex Sans", -apple-system, sans-serif';
const ADV = 0.6; // mono advance as a fraction of font size (IBM Plex Mono)

// ---- easing and timeline evaluation
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const EASE = {
  out: (k) => 1 - Math.pow(1 - k, 3),
  inout: (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
  linear: (k) => k,
  step: () => 1,
};
const tweens = {};
for (const tw of TL.tweens) (tweens[tw.id] ||= []).push(tw);
for (const k in tweens) tweens[k].sort((a, b) => a.t0 - b.t0);

function propsAt(obj, t) {
  const p = Object.assign({}, obj.props);
  for (const tw of tweens[obj.id] || []) {
    if (t < tw.t0) break;
    const k = tw.ease === "step" ? 1 : (EASE[tw.ease] || EASE.inout)(clamp((t - tw.t0) / Math.max(1, tw.t1 - tw.t0)));
    const from = p[tw.prop];
    p[tw.prop] = typeof tw.to === "number" && typeof from === "number" ? from + (tw.to - from) * k : tw.to;
  }
  return p;
}

// deterministic noise for glitches
const hash = (n) => { n = (n ^ 61) ^ (n >>> 16); n = n + (n << 3); n = n ^ (n >>> 4); n = Math.imul(n, 0x27d4eb2d); return ((n ^ (n >>> 15)) >>> 0) / 4294967296; };
const GLYPHS = "▚▞░▒▓#%&@$*+=?/\\<>~";

// ---- drawing helpers
function glow(ctx, c, blur = 10) { ctx.shadowColor = c; ctx.shadowBlur = blur; }
function noGlow(ctx) { ctx.shadowBlur = 0; }
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}
// a polyline drawn up to fraction k of its length
function partial(ctx, pts, k) {
  let L = 0; const seg = [];
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); L += d; }
  let left = L * k;
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  let tip = pts[0], dir = [1, 0];
  for (let i = 1; i < pts.length && left > 0; i++) {
    const d = seg[i - 1], f = Math.min(1, left / (d || 1));
    tip = [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f];
    dir = [pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]];
    ctx.lineTo(tip[0], tip[1]);
    left -= d;
  }
  ctx.stroke();
  return { tip, dir, L };
}
function at(pts, k) { // point at fraction k along a polyline
  let L = 0; const seg = [];
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); L += d; }
  let left = L * clamp(k);
  for (let i = 1; i < pts.length; i++) {
    if (left <= seg[i - 1]) { const f = left / (seg[i - 1] || 1); return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f]; }
    left -= seg[i - 1];
  }
  return pts[pts.length - 1];
}
// smooth a few control points into a dense polyline (Catmull–Rom)
function smooth(pts, steps = 18) {
  if (pts.length < 3) {
    const out = []; for (let i = 0; i <= steps; i++) { const k = i / steps; out.push([pts[0][0] + (pts[1][0] - pts[0][0]) * k, pts[0][1] + (pts[1][1] - pts[0][1]) * k]); } return out;
  }
  const out = [], P = [pts[0], ...pts, pts[pts.length - 1]];
  for (let i = 1; i < P.length - 2; i++) {
    for (let s = 0; s < steps; s++) {
      const t = s / steps, t2 = t * t, t3 = t2 * t;
      const f = (a, b, c, d) => 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
      out.push([f(P[i - 1][0], P[i][0], P[i + 1][0], P[i + 2][0]), f(P[i - 1][1], P[i][1], P[i + 1][1], P[i + 2][1])]);
    }
  }
  out.push(pts[pts.length - 1]);
  return out;
}
function arrowHead(ctx, tip, dir, size = 12) {
  const a = Math.atan2(dir[1], dir[0]);
  ctx.beginPath();
  ctx.moveTo(tip[0], tip[1]);
  ctx.lineTo(tip[0] - size * Math.cos(a - 0.45), tip[1] - size * Math.sin(a - 0.45));
  ctx.moveTo(tip[0], tip[1]);
  ctx.lineTo(tip[0] - size * Math.cos(a + 0.45), tip[1] - size * Math.sin(a + 0.45));
  ctx.stroke();
}
const visText = (s) => String(s).replace(/^ /, "").replace(/\n/g, "↵");

// token chip layout, shared with script.mjs (mono advance, so it can be computed anywhere)
function chipLayout(list, size, gap, x, y) {
  const pad = size * 0.45, ws = list.map((s) => visText(s).length * size * ADV + pad * 2);
  const total = ws.reduce((a, b) => a + b, 0) + gap * (list.length - 1);
  let cx = x - total / 2;
  return ws.map((w) => { const r = { x: cx, w, y: y - size * 0.8, h: size * 1.6 }; cx += w + gap; return r; });
}


// ---- 3D: a stage object rendered by three.js off screen, painted into the
// frame in draw order, with a soft additive pass so the edges glow. 2D notes
// and chips can be pinned to its points (anchor: { obj, col, row }).
let THREE = null;
const STAGES = {};
const SP = { dx: 1, dy: 0.55, depth: 2.2 }; // plate spacing in world units
function Stack(o) {
  const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(o.fov || 32, o.w / o.h, 0.1, 400);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1); renderer.setSize(o.w, o.h, false); renderer.setClearColor(0x000000, 0);
  const rows = o.rows, cols = o.cols, cx = (cols - 1) / 2;
  const P = (c, r) => new THREE.Vector3((c - cx) * SP.dx, r * SP.dy, 0);
  const ink = new THREE.Color(C.ink), plates = [], nodes = [], colLines = [];
  const plateW = cols * SP.dx + 0.6;
  for (let r = 0; r < rows; r++) {
    const g = new THREE.Group();
    const box = new THREE.BoxGeometry(plateW, 0.06, SP.depth);
    const edge = new THREE.LineSegments(new THREE.EdgesGeometry(box), new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.5 }));
    const fill = new THREE.Mesh(box, new THREE.MeshBasicMaterial({ color: 0x5b7cff, transparent: true, opacity: 0.05, depthWrite: false }));
    g.add(fill, edge); g.position.y = r * SP.dy; scene.add(g);
    plates.push({ g, edge, fill });
    const row = [];
    for (let c = 0; c < cols; c++) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.16, 0.16), new THREE.MeshBasicMaterial({ color: ink, transparent: true, opacity: 0.6 }));
      m.position.copy(P(c, r)); m.position.y += 0.08; g.parent.add(m); row.push(m);
    }
    nodes.push(row);
  }
  for (let c = 0; c < cols; c++) {
    const geo = new THREE.BufferGeometry().setFromPoints([P(c, 0), P(c, rows - 1)]);
    const line = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: ink, transparent: true, opacity: 0.12 }));
    scene.add(line); colLines.push(line);
  }
  // the route: a dense curve through (col, row) waypoints, drawn on, with a glowing head
  let routeLine = null, routePts = [], head = null, pulses = [];
  const routeMat = new THREE.LineBasicMaterial({ color: new THREE.Color(C.accent), transparent: true, opacity: 1 });
  function setRoute(way) {
    if (routeLine || !way) return;
    const curve = new THREE.CatmullRomCurve3(way.map(([c, r]) => { const v = P(c, r); v.y += 0.12; return v; }), false, "centripetal");
    routePts = curve.getPoints(400);
    // a tube, not a line: WebGL lines are always one pixel wide
    routeLine = new THREE.Mesh(new THREE.TubeGeometry(curve, 400, 0.07, 8, false), new THREE.MeshBasicMaterial({ color: new THREE.Color(C.accent) }));
    scene.add(routeLine);
    const sph = () => new THREE.Mesh(new THREE.SphereGeometry(0.16, 16, 12), new THREE.MeshBasicMaterial({ color: new THREE.Color(C.accent) }));
    head = sph(); scene.add(head);
    for (let i = 0; i < 4; i++) { const p = sph(); p.scale.setScalar(0.7); scene.add(p); pulses.push(p); }
  }
  const tmp = new THREE.Vector3();
  const api = {
    update(p, t, born) {
      // camera on a sphere around the middle of the stack
      const az = (p.az * Math.PI) / 180, el = (p.el * Math.PI) / 180, ty = p.ty ?? ((rows - 1) * SP.dy) / 2;
      cam.position.set(p.dist * Math.cos(el) * Math.sin(az), ty + p.dist * Math.sin(el), p.dist * Math.cos(el) * Math.cos(az));
      cam.lookAt(0, ty, 0); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
      const up = p.reveal * rows;
      const glow = p.glow || [];
      plates.forEach((pl, r) => {
        const k = clamp(up - r), e = EASE.out(k);
        pl.g.visible = k > 0; pl.g.position.y = r * SP.dy - (1 - e) * 1.2;
        pl.edge.material.opacity = 0.5 * e * (r === Math.round(p.scan) && p.scan >= 0 ? 2 : 1);
        pl.fill.material.opacity = 0.05 * e;
        nodes[r].forEach((m, c) => {
          m.visible = k > 0; m.position.y = r * SP.dy - (1 - e) * 1.2 + 0.08;
          let col = ink, s = 1, op = 0.55 * e;
          if (c === p.hiCol) { col = new THREE.Color(C.cyan); op = 0.95 * e; s = 1.25; }
          for (const g of glow) if (c === g.col && r >= g.r0 && r <= g.r1) { col = new THREE.Color(color(g.color)); s = 1 + 1.2 * (g.k ?? 1); op = e; }
          m.material.color.copy(col); m.material.opacity = op; m.scale.setScalar(s);
        });
      });
      colLines.forEach((l, c) => { l.material.opacity = (c === p.hiCol ? 0.6 : 0.12) * clamp(p.reveal * 3); l.material.color.set(c === p.hiCol ? C.cyan : C.ink); });
      if (p.route) setRoute(p.route);
      if (routeLine) {
        const k = clamp(p.routeK || 0), n = Math.max(2, Math.floor(k * routePts.length));
        routeLine.geometry.setDrawRange(0, Math.floor(k * 400) * 8 * 6); routeLine.visible = k > 0;
        head.visible = k > 0 && k < 1; head.position.copy(routePts[Math.min(routePts.length - 1, n - 1)]);
        pulses.forEach((q, i) => {
          const on = k >= 1, ph = ((t - born) / 2600 + i / pulses.length) % 1;
          q.visible = on; if (on) q.position.copy(routePts[Math.floor(ph * (routePts.length - 1))]);
        });
      }
      renderer.render(scene, cam);
    },
    // a stage point in frame pixels
    project(c, r, x0, y0) {
      tmp.copy(P(c, r)); tmp.y += 0.08; tmp.project(cam);
      return [x0 + (tmp.x * 0.5 + 0.5) * o.w, y0 + (-tmp.y * 0.5 + 0.5) * o.h];
    },
    canvas: renderer.domElement,
  };
  return api;
}


// A stage of real LEGO parts (from brickcharts.mjs, checked at build time),
// shaded as plastic under a soft key light, assembling in build order.
let KIT = null, ADDONS = null;
const PLATE = 0.4;
// the shared LEGO kit and plastic materials, for any stage that draws bricks
function kit() { return (KIT ||= brickKit({ THREE, RoundedBoxGeometry: ADDONS.RoundedBoxGeometry, toCreasedNormals: ADDONS.toCreasedNormals, meshes: TL.meshes || {}, PLATE })); }
const MATS = new Map();
function plastic(c) { if (!MATS.has(c)) MATS.set(c, new THREE.MeshStandardMaterial({ color: (TL.colors[c] || TL.colors[71])[2], roughness: 0.28, metalness: 0 })); return MATS.get(c); }
function Bricks(o) {
  const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(o.fov || 30, o.w / o.h, 0.1, 500);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1); renderer.setSize(o.w, o.h, false); renderer.setClearColor(0x000000, 0);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  KIT ||= kit();
  scene.add(new THREE.HemisphereLight(0xe8eeff, 0x1a2550, 1.6));
  const key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(-18, 34, 22); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048); const sc = key.shadow.camera; sc.left = sc.bottom = -40; sc.right = sc.top = 40; sc.near = 1; sc.far = 120;
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x9fb8ff, 0.9); rim.position.set(20, 12, -24); scene.add(rim);
  const [W, Hp, D] = o.size;
  const center = new THREE.Vector3(W / 2, 0, -D / 2);
  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.ShadowMaterial({ opacity: 0.35 }));
  shadow.rotation.x = -Math.PI / 2; shadow.position.y = -0.001; shadow.receiveShadow = true; scene.add(shadow);
  const mat = plastic;
  // hide studs covered by a part sitting on them
  const occ = new Set();
  for (const p of o.parts) for (let x = p.x; x < p.x + p.w; x++) for (let z = p.z; z < p.z + p.d; z++) occ.add(`${x},${p.y},${z}`);
  const covered = (x, y, z) => occ.has(`${x},${y},${z}`);
  const pieces = o.parts.map((p) => {
    const g = KIT.brick(p, mat(p.color), covered);
    g.userData.home = g.userData.home.clone().sub(center);
    g.position.copy(g.userData.home); g.visible = false; scene.add(g);
    return g;
  });
  const tmp = new THREE.Vector3(), N = pieces.length;
  return {
    canvas: renderer.domElement,
    update(p) {
      const az = (p.az * Math.PI) / 180, el = (p.el * Math.PI) / 180, ty = p.ty ?? (Hp * PLATE) / 2;
      cam.position.set(p.dist * Math.cos(el) * Math.sin(az), ty + p.dist * Math.sin(el), p.dist * Math.cos(el) * Math.cos(az));
      cam.lookAt(0, ty, 0); cam.updateMatrixWorld(); cam.updateProjectionMatrix();
      // each part drops into place in order; a drop lasts a few percent of the build
      const at = p.reveal * (N + N * 0.05), span = Math.max(1, N * 0.05);
      pieces.forEach((g, i) => {
        const k = clamp((at - i) / span);
        g.visible = k > 0;
        if (k > 0) { const e = EASE.out(k); g.position.copy(g.userData.home); g.position.y += (1 - e) * 5; }
      });
      renderer.render(scene, cam);
    },
    // an anchor ([x, y, z] in studs, plates, studs) in frame pixels
    anchor(a, x0, y0) {
      tmp.set(a[0], a[1] * PLATE, -a[2]).sub(center).project(cam);
      return [x0 + (tmp.x * 0.5 + 0.5) * o.w, y0 + (-tmp.y * 0.5 + 0.5) * o.h];
    },
  };
}

// ---- object types
const STAGE_KINDS = { stack: Stack, bricks: Bricks };
Stack.glow = true; Stack.overlays = true;
const DRAW = {

  stage3d(ctx, p, t, obj) {
    const make = STAGE_KINDS[p.kind || "stack"];
    if (!make) throw new Error(`no 3D stage kind "${p.kind}" (is its plugin built in?)`);
    const st = STAGES[obj.id] || (STAGES[obj.id] = make({ ...p }));
    st.update(p, t, obj.born);
    st.x = p.x; st.y = p.y; st.anchors = p.anchors;
    ctx.save();
    if (make.glow) { // line art glows: a blurred additive copy under the sharp one
      ctx.globalCompositeOperation = "lighter"; ctx.filter = "blur(7px)"; ctx.globalAlpha = 0.9 * ctx._alpha;
      ctx.drawImage(st.canvas, p.x, p.y, p.w, p.h);
      ctx.filter = "none"; ctx.globalCompositeOperation = "source-over";
    }
    ctx.globalAlpha = ctx._alpha;
    ctx.drawImage(st.canvas, p.x, p.y, p.w, p.h);
    ctx.restore();
    if (!make.overlays) return;
    // what the highlighted column would say at each plate, pinned beside it
    if (p.labels && p.hiCol >= 0) {
      ctx.font = `500 15px ${MONO}`; ctx.textBaseline = "middle"; ctx.textAlign = "left";
      for (let r = 0; r < p.labels.length && r <= p.labelUpTo; r++) {
        const lab = p.labels[r]; if (!lab) continue;
        const k = clamp(p.labelUpTo - r + 1), [nx, ny] = st.project(p.hiCol, r, p.x, p.y);
        const lx = nx + 46 + (r % 2) * 0;
        ctx.globalAlpha = k * ctx._alpha * (lab.hot || lab.warm ? 1 : 0.75);
        const c = lab.hot ? C.accent : lab.warm ? C.gold : C.dim;
        ctx.strokeStyle = c; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(nx + 8, ny); ctx.lineTo(lx - 6, ny); ctx.stroke();
        ctx.fillStyle = c; if (lab.hot) glow(ctx, C.accent, 10);
        ctx.fillText(`${r === 0 ? "embed" : "L" + r}  ${lab.text}`, lx, ny + 1); noGlow(ctx);
      }
      ctx.globalAlpha = ctx._alpha;
    }
    // the words under their columns, at the bottom plate
    if (p.colLabels) {
      ctx.font = `500 16px ${MONO}`; ctx.textAlign = "center"; ctx.textBaseline = "top";
      p.colLabels.forEach((l, c) => {
        const [x, y] = st.project(c, 0, p.x, p.y), on = c === p.hiCol || (p.colHl || []).includes(c);
        ctx.globalAlpha = clamp(p.reveal * 4) * ctx._alpha;
        ctx.fillStyle = c === p.hiCol ? C.cyan : on ? C.accent : C.dim;
        ctx.fillText(visText(l), x, y + 22);
      });
      ctx.globalAlpha = ctx._alpha;
    }
  },
  heading(ctx, p) {
    const text = p.text, n = Math.ceil(text.length * clamp(p.reveal * 1.25));
    ctx.font = `600 38px ${SANS}`; ctx.fillStyle = C.ink; ctx.textBaseline = "alphabetic"; ctx.textAlign = "left";
    glow(ctx, "rgba(160,190,255,0.35)", 8);
    ctx.fillText(text.slice(0, n), p.x, p.y);
    const w = ctx.measureText(text).width;
    ctx.strokeStyle = C.ink; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(p.x, p.y + 16); ctx.lineTo(p.x + w * 0.42 * EASE.out(clamp(p.reveal)), p.y + 16); ctx.stroke();
    noGlow(ctx);
  },
  text(ctx, p, t) {
    const text = String(p.text), n = Math.floor(text.length * clamp(p.reveal));
    ctx.font = `${p.weight} ${p.size}px ${p.font === "mono" ? MONO : SANS}`;
    ctx.textBaseline = "middle";
    const full = ctx.measureText(text).width;
    const x0 = p.align === "center" ? p.x - full / 2 : p.align === "right" ? p.x - full : p.x;
    ctx.textAlign = "left"; ctx.fillStyle = color(p.color);
    if (p.color === "accent") glow(ctx, C.accent, 12); else glow(ctx, "rgba(160,190,255,0.25)", 6);
    ctx.fillText(text.slice(0, n), x0, p.y);
    if (p.reveal < 1 && Math.floor(t / 260) % 2 === 0) {
      const w = ctx.measureText(text.slice(0, n)).width;
      ctx.fillRect(x0 + w + 3, p.y - p.size * 0.42, p.size * 0.5, p.size * 0.84);
    }
    noGlow(ctx);
  },
  tokens(ctx, p, t) {
    const L = chipLayout(p.list, p.size, p.gap, p.x, p.y), hl = new Set(p.hl || []);
    const shown = p.reveal * p.list.length;
    ctx.font = `500 ${p.size}px ${MONO}`; ctx.textBaseline = "middle"; ctx.textAlign = "center";
    L.forEach((r, i) => {
      const k = clamp(shown - i);
      if (k <= 0) return;
      const isHl = hl.has(i), noisy = isHl && p.noise > 0;
      const jx = noisy ? (hash(i * 977 + Math.floor(t / 50)) - 0.5) * 8 * p.noise : 0;
      ctx.globalAlpha = k * (isHl || !p.dim ? 1 : 1 - 0.6 * p.dim) * ctx._alpha;
      const c = isHl ? C.accent : C.ink;
      ctx.strokeStyle = isHl ? C.accent : C.faint; ctx.lineWidth = isHl ? 2 : 1.5;
      if (isHl) glow(ctx, C.accent, 14);
      roundRect(ctx, r.x + jx, r.y, r.w, r.h, 6); ctx.stroke();
      noGlow(ctx);
      let s = visText(p.list[i]);
      if (noisy) s = s.split("").map((ch, j) => (hash(i * 131 + j * 17 + Math.floor(t / 70)) < p.noise ? GLYPHS[Math.floor(hash(j * 7 + i + Math.floor(t / 70) * 3) * GLYPHS.length)] : ch)).join("");
      ctx.fillStyle = c; if (isHl) glow(ctx, C.accent, 10);
      ctx.fillText(s, r.x + r.w / 2 + jx, p.y + 1);
      noGlow(ctx);
    });
    ctx.globalAlpha = ctx._alpha;
  },
  chip(ctx, p) {
    ctx.font = `600 ${p.size}px ${MONO}`; ctx.textBaseline = "middle"; ctx.textAlign = "left";
    const val = p.value == null ? "" : `  ${p.value >= 0.995 ? "≈100" : p.value >= 0.1 ? Math.round(p.value * 100) : (p.value * 100).toFixed(1)}%`;
    const label = visText(p.label), tw = ctx.measureText(label + val).width, padX = p.size * 0.6, dot = p.size * 0.9;
    const w = tw + padX * 2 + dot, h = p.size * 1.7, x = p.x - w / 2, y = p.y - h / 2;
    const k = EASE.out(clamp(p.reveal));
    ctx.globalAlpha = k * ctx._alpha;
    const c = p.accent ? C.accent : C.ink;
    glow(ctx, c, 16); ctx.strokeStyle = c; ctx.lineWidth = 2.5; roundRect(ctx, x, y, w, h, h / 2); ctx.stroke();
    ctx.fillStyle = c; ctx.beginPath(); ctx.arc(x + padX + dot * 0.25, p.y, p.size * 0.18, 0, Math.PI * 2); ctx.fill();
    noGlow(ctx);
    ctx.fillStyle = C.ink; ctx.fillText(label, x + padX + dot, p.y + 1);
    ctx.fillStyle = c; ctx.fillText(val, x + padX + dot + ctx.measureText(label).width, p.y + 1);
    ctx.globalAlpha = ctx._alpha;
  },
  lattice(ctx, p, t) {
    const { cols, rows } = p, dx = p.w / cols, dy = p.h / (rows - 1);
    const X = (c) => p.x + dx * (c + 0.5), Y = (r) => p.y + p.h - dy * r;
    const upto = p.reveal * rows;
    // columns: the word's stream, drawn upwards
    ctx.lineWidth = 1;
    for (let c = 0; c < cols; c++) {
      const hi = c === p.hiCol, mark = (p.colHl || []).includes(c);
      ctx.strokeStyle = hi ? C.cyan : mark ? "rgba(255,122,89,0.55)" : C.ghost; ctx.lineWidth = hi || mark ? 2 : 1;
      if (hi) glow(ctx, C.cyan, 10);
      ctx.beginPath(); ctx.moveTo(X(c), Y(0)); ctx.lineTo(X(c), Y(Math.min(rows - 1, upto))); ctx.stroke();
      noGlow(ctx);
    }
    // layer rails
    for (let r = 0; r < rows; r++) {
      if (r > upto) break;
      const k = clamp(upto - r);
      ctx.globalAlpha = k * ctx._alpha;
      ctx.strokeStyle = r % 4 === 0 ? C.faint : C.ghost; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(p.x, Y(r)); ctx.lineTo(p.x + p.w, Y(r)); ctx.stroke();
      if (r % 4 === 0) {
        ctx.fillStyle = C.dim; ctx.font = `400 15px ${MONO}`; ctx.textAlign = "right"; ctx.textBaseline = "middle";
        ctx.fillText(r === 0 ? "embed" : r === rows - 1 ? "out" : `L${r}`, p.x - 12, Y(r));
      }
      for (let c = 0; c < cols; c++) {
        const hi = c === p.hiCol;
        ctx.fillStyle = hi ? C.cyan : C.dim;
        const s = hi ? 5 : 3.5;
        ctx.fillRect(X(c) - s / 2, Y(r) - s / 2, s, s);
      }
    }
    ctx.globalAlpha = ctx._alpha;
    // the words under their columns
    if (p.colLabels) {
      ctx.font = `500 16px ${MONO}`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      const hl = new Set(p.colHl || []);
      p.colLabels.forEach((l, c) => {
        const on = c === p.hiCol || hl.has(c);
        ctx.fillStyle = on ? (c === p.hiCol ? C.cyan : C.accent) : C.dim;
        if (on) glow(ctx, ctx.fillStyle, 8);
        ctx.fillText(visText(l), X(c), Y(0) + 30); noGlow(ctx);
      });
    }
    // pulses flowing up every column
    if (p.flow > 0) {
      for (let c = 0; c < cols; c++) {
        for (let j = 0; j < 2; j++) {
          const ph = ((t / 2200) + j * 0.5 + hash(c * 31) ) % 1, r = ph * (rows - 1);
          if (r > upto) continue;
          ctx.globalAlpha = p.flow * Math.sin(Math.PI * ph) * ctx._alpha;
          const col = c === p.hiCol ? C.cyan : C.ink;
          glow(ctx, col, 12); ctx.fillStyle = col;
          ctx.beginPath(); ctx.arc(X(c), Y(r), 3.2, 0, Math.PI * 2); ctx.fill(); noGlow(ctx);
        }
      }
      ctx.globalAlpha = ctx._alpha;
    }
    // what each layer would say, up the highlighted column
    if (p.labels && p.hiCol >= 0) {
      ctx.font = `500 15px ${MONO}`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      for (let r = 0; r < rows && r <= p.labelUpTo; r++) {
        const lab = p.labels[r]; if (!lab) continue;
        const k = clamp(p.labelUpTo - r + 1);
        ctx.globalAlpha = k * ctx._alpha;
        const hot = lab.hot, cx = X(p.hiCol), bw = dx * 1.9;
        ctx.fillStyle = "rgba(8,16,44,0.92)"; ctx.fillRect(cx - bw / 2, Y(r) - dy * 0.42, bw, dy * 0.84);
        ctx.strokeStyle = hot ? C.accent : lab.warm ? C.gold : C.faint; ctx.lineWidth = hot ? 1.8 : 1;
        if (hot) glow(ctx, C.accent, 10);
        ctx.strokeRect(cx - bw / 2, Y(r) - dy * 0.42, bw, dy * 0.84); noGlow(ctx);
        ctx.fillStyle = hot ? C.accent : lab.warm ? C.gold : C.ink;
        ctx.fillText(lab.text, cx, Y(r) + 1);
      }
      ctx.globalAlpha = ctx._alpha;
    }
  },
  heat(ctx, p) {
    const rows = p.values.length, cols = p.values[0].length, cs = p.cell, gap = 2;
    const hue = color(p.hue), upto = p.reveal * cols;
    if (p.title) { ctx.font = `600 18px ${SANS}`; ctx.fillStyle = C.ink; ctx.textAlign = "left"; ctx.textBaseline = "alphabetic"; ctx.fillText(p.title, p.x, p.y - 34); }
    ctx.font = `400 14px ${MONO}`; ctx.fillStyle = C.dim; ctx.textBaseline = "middle";
    ctx.textAlign = "center";
    for (let c = 0; c < cols; c += 4) ctx.fillText(String(c + 1), p.x + c * (cs + gap) + cs / 2, p.y - 12);
    ctx.textAlign = "right";
    p.rowLabels.forEach((l, r) => { ctx.fillStyle = (p.rowHl || []).includes(r) ? C.accent : C.dim; ctx.fillText(visText(l), p.x - 10, p.y + r * (cs + gap) + cs / 2); });
    for (let c = 0; c < cols; c++) {
      const k = clamp(upto - c);
      if (k <= 0) break;
      for (let r = 0; r < rows; r++) {
        const v = clamp(p.values[r][c]), x = p.x + c * (cs + gap), y = p.y + r * (cs + gap);
        ctx.strokeStyle = C.ghost; ctx.lineWidth = 1; ctx.strokeRect(x + 0.5, y + 0.5, cs - 1, cs - 1);
        if (v > 0.02) {
          ctx.globalAlpha = k * Math.pow(v, 0.8) * ctx._alpha;
          if (v > 0.5) glow(ctx, hue, 10);
          ctx.fillStyle = hue; ctx.fillRect(x, y, cs, cs); noGlow(ctx);
          ctx.globalAlpha = ctx._alpha;
        }
      }
    }
    // the sweep line
    if (p.reveal > 0 && p.reveal < 1) {
      const x = p.x + upto * (cs + gap);
      ctx.strokeStyle = C.ink; ctx.lineWidth = 2; glow(ctx, C.ink, 10);
      ctx.beginPath(); ctx.moveTo(x, p.y - 4); ctx.lineTo(x, p.y + rows * (cs + gap)); ctx.stroke(); noGlow(ctx);
    }
    if (p.focus && p.focusReveal > 0) {
      const f = p.focus, x0 = p.x + f.c0 * (cs + gap) - 5, y0 = p.y + f.r0 * (cs + gap) - 5;
      const x1 = p.x + (f.c1 + 1) * (cs + gap) + 3, y1 = p.y + (f.r1 + 1) * (cs + gap) + 3;
      ctx.strokeStyle = C.accent; ctx.lineWidth = 2; glow(ctx, C.accent, 14);
      partial(ctx, [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]], clamp(p.focusReveal)); noGlow(ctx);
    }
  },
  chart(ctx, p) {
    const X = (v) => p.x + (v / p.xMax) * p.w;
    const ly = (v) => p.logY ? Math.log10(Math.max(v, p.yMin)) : v;
    const Y = (v) => p.y + p.h - ((ly(v) - ly(p.yMin)) / (ly(p.yMax) - ly(p.yMin))) * p.h;
    const k = clamp(p.reveal);
    if (p.title) { ctx.font = `600 18px ${SANS}`; ctx.fillStyle = C.ink; ctx.textAlign = "left"; ctx.textBaseline = "alphabetic"; ctx.fillText(p.title, p.x, p.y - 22); }
    ctx.lineWidth = 1; ctx.font = `400 14px ${MONO}`; ctx.textBaseline = "middle";
    for (const [v, l] of p.yTicks) { ctx.strokeStyle = C.ghost; ctx.beginPath(); ctx.moveTo(p.x, Y(v)); ctx.lineTo(p.x + p.w, Y(v)); ctx.stroke(); ctx.fillStyle = C.dim; ctx.textAlign = "right"; ctx.fillText(l, p.x - 8, Y(v)); }
    ctx.textAlign = "center";
    for (const [v, l] of p.xTicks) { ctx.fillStyle = C.dim; ctx.fillText(l, X(v), p.y + p.h + 18); }
    ctx.strokeStyle = C.faint; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x, p.y + p.h); ctx.lineTo(p.x + p.w, p.y + p.h); ctx.stroke();
    for (const m of p.marks) {
      if (m.x / p.xMax > k + 0.001) continue;
      ctx.strokeStyle = color(m.color || "gold"); ctx.setLineDash([4, 5]); ctx.beginPath(); ctx.moveTo(X(m.x), p.y); ctx.lineTo(X(m.x), p.y + p.h); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = color(m.color || "gold"); ctx.textAlign = "left"; ctx.font = `500 14px ${MONO}`; ctx.fillText(m.label, X(m.x) + 6, p.y + 10 + (m.dy || 0));
    }
    const pts = p.points.map(([x, y]) => [X(x), Y(y)]);
    ctx.strokeStyle = C.cyan; ctx.lineWidth = 2.5; glow(ctx, C.cyan, 12);
    const { tip } = partial(ctx, pts, k); noGlow(ctx);
    ctx.fillStyle = C.cyan; glow(ctx, C.cyan, 16); ctx.beginPath(); ctx.arc(tip[0], tip[1], 5, 0, Math.PI * 2); ctx.fill(); noGlow(ctx);
  },
  list(ctx, p) {
    const n = p.items.length, shown = p.reveal * n;
    if (p.title) { ctx.font = `500 17px ${SANS}`; ctx.fillStyle = C.dim; ctx.textAlign = "left"; ctx.textBaseline = "alphabetic"; ctx.fillText(p.title, p.x, p.y - 26); }
    ctx.font = `500 16px ${MONO}`; ctx.textBaseline = "middle";
    p.items.forEach((it, i) => {
      const k = clamp(shown - i); if (k <= 0) return;
      const y = p.y + i * p.gap, d = Math.abs(p.active - i), on = d < 0.5;
      const text = typeof it === "string" ? it : it.text;
      const w = Math.max(150, text.length * 16 * ADV + 40);
      ctx.globalAlpha = k * (p.active < 0 ? 0.9 : on ? 1 : 0.42) * ctx._alpha;
      ctx.strokeStyle = on ? C.ink : C.faint; ctx.lineWidth = on ? 1.8 : 1.2;
      if (on) glow(ctx, "rgba(180,205,255,0.6)", 10);
      roundRect(ctx, p.x, y - 15, w, 30, 15); ctx.stroke(); noGlow(ctx);
      ctx.fillStyle = on ? C.ink : C.dim; ctx.fillRect(p.x + 12, y - 7, 3, 14);
      ctx.textAlign = "left"; ctx.fillText(text, p.x + 24, y + 1);
      ctx.fillStyle = on ? C.ink : C.faint; ctx.beginPath(); ctx.arc(p.x + w + 26, y, 2.5, 0, Math.PI * 2); ctx.fill();
    });
    ctx.globalAlpha = ctx._alpha;
    if (p.active >= 0 && shown > 0) {
      const y = p.y + p.active * p.gap, text = p.items[Math.round(clamp(p.active, 0, n - 1))];
      const w = Math.max(150, (typeof text === "string" ? text : text.text).length * 16 * ADV + 40);
      const x = p.x + w + 44;
      ctx.strokeStyle = C.ink; ctx.fillStyle = C.ink; ctx.lineWidth = 2; glow(ctx, C.ink, 10);
      ctx.beginPath(); ctx.moveTo(x + 14, y); ctx.lineTo(x, y); ctx.stroke(); arrowHead(ctx, [x, y], [-1, 0], 8);
      ctx.beginPath(); ctx.arc(x + 20, y, 4, 0, Math.PI * 2); ctx.fill(); noGlow(ctx);
    }
  },
  dial(ctx, p, t) {
    const r = 30, k = clamp(p.reveal), frac = clamp(p.n / p.of);
    ctx.globalAlpha = k * ctx._alpha;
    ctx.strokeStyle = C.faint; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = C.ink; ctx.lineWidth = 3; glow(ctx, C.ink, 10);
    ctx.beginPath(); ctx.arc(p.x, p.y, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * frac); ctx.stroke(); noGlow(ctx);
    const pulse = 0.75 + 0.25 * Math.sin(t / 300);
    ctx.fillStyle = C.accent; glow(ctx, C.accent, 14 * pulse); ctx.fillRect(p.x - 6, p.y - 6, 12, 12); noGlow(ctx);
    ctx.font = `500 16px ${MONO}`; ctx.fillStyle = C.dim; ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
    ctx.fillText(`${Math.round(p.n)} · ${p.label}`, p.x, p.y + r + 28);
    ctx.globalAlpha = ctx._alpha;
  },
  path(ctx, p, t, obj) {
    const pts = (!Array.isArray(p.anchors) && obj._dense) || (obj._dense = p.curve ? smooth(p.pts) : p.pts);
    const c = color(p.color);
    ctx.strokeStyle = c; ctx.lineWidth = p.width; glow(ctx, c, 10);
    const { tip, dir } = partial(ctx, pts, clamp(p.reveal));
    if (p.arrow && p.reveal > 0.02) arrowHead(ctx, tip, dir, 12);
    noGlow(ctx);
    if (p.pulses > 0 && p.reveal >= 1) {
      for (let i = 0; i < p.pulses; i++) {
        const ph = ((t - obj.born) / p.period + i / p.pulses) % 1, q = at(pts, ph);
        ctx.globalAlpha = Math.sin(Math.PI * ph) * ctx._alpha;
        ctx.fillStyle = c; glow(ctx, c, 16); ctx.beginPath(); ctx.arc(q[0], q[1], 4.5, 0, Math.PI * 2); ctx.fill(); noGlow(ctx);
      }
      ctx.globalAlpha = ctx._alpha;
    }
  },
  box(ctx, p) {
    const c = color(p.color);
    ctx.strokeStyle = c; ctx.lineWidth = 1.5; if (p.dash) ctx.setLineDash([6, 6]);
    partial(ctx, [[p.x, p.y], [p.x + p.w, p.y], [p.x + p.w, p.y + p.h], [p.x, p.y + p.h], [p.x, p.y]], clamp(p.reveal));
    ctx.setLineDash([]);
    if (p.label && p.reveal > 0.3) {
      ctx.font = `500 15px ${MONO}`; ctx.textAlign = "left"; ctx.textBaseline = "middle";
      const w = ctx.measureText(p.label).width;
      ctx.fillStyle = C.bg0; ctx.fillRect(p.x + 14, p.y - 10, w + 12, 20);
      ctx.fillStyle = c; ctx.fillText(p.label, p.x + 20, p.y);
    }
  },
  note(ctx, p) {
    const c = color(p.color), k = clamp(p.reveal);
    if (p.to) {
      ctx.strokeStyle = c; ctx.lineWidth = 1.5; glow(ctx, c, 8);
      const { tip } = partial(ctx, [[p.x, p.y], p.to], clamp(k * 1.6)); noGlow(ctx);
      if (k * 1.6 >= 1) { ctx.fillStyle = c; ctx.beginPath(); ctx.arc(tip[0], tip[1], 4, 0, Math.PI * 2); ctx.fill(); }
    }
    const lines = String(p.text).split("\n");
    ctx.font = `500 ${p.size}px ${SANS}`; ctx.textBaseline = "middle"; ctx.textAlign = p.align;
    ctx.globalAlpha = clamp(k * 2 - 0.6) * ctx._alpha;
    ctx.fillStyle = c; glow(ctx, c, 6);
    const dy = p.to && p.to[1] < p.y ? 1 : -1;
    lines.forEach((l, i) => ctx.fillText(l, p.x + (p.align === "left" ? 8 : p.align === "right" ? -8 : 0), p.y + (dy > 0 ? 18 + i * p.size * 1.3 : -18 - (lines.length - 1 - i) * p.size * 1.3)));
    noGlow(ctx); ctx.globalAlpha = ctx._alpha;
  },
};

// ---- the frame
function background(ctx, t) {
  const g = ctx.createRadialGradient(W * 0.5, H * 0.45, 100, W * 0.5, H * 0.5, W * 0.75);
  g.addColorStop(0, C.bg0); g.addColorStop(1, C.bg1);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.lineWidth = 1;
  for (let x = 0; x <= W; x += 40) { ctx.strokeStyle = x % 200 === 0 ? C.grid2 : C.grid; ctx.beginPath(); ctx.moveTo(x + 0.5, 0); ctx.lineTo(x + 0.5, H); ctx.stroke(); }
  for (let y = 0; y <= H; y += 40) { ctx.strokeStyle = y % 200 === 0 ? C.grid2 : C.grid; ctx.beginPath(); ctx.moveTo(0, y + 0.5); ctx.lineTo(W, y + 0.5); ctx.stroke(); }
  // crop marks and ruler ticks
  ctx.strokeStyle = C.faint; ctx.lineWidth = 1.5;
  const m = 36, L = 22;
  for (const [x, y, sx, sy] of [[m, m, 1, 1], [W - m, m, -1, 1], [m, H - m, 1, -1], [W - m, H - m, -1, -1]]) {
    ctx.beginPath(); ctx.moveTo(x, y + sy * L); ctx.lineTo(x, y); ctx.lineTo(x + sx * L, y); ctx.stroke();
  }
  ctx.strokeStyle = C.ghost; ctx.lineWidth = 1;
  for (let x = 120; x < W - 100; x += 20) { const h = x % 100 === 0 ? 8 : 4; ctx.beginPath(); ctx.moveTo(x, H - m); ctx.lineTo(x, H - m - h); ctx.stroke(); }
  for (let y = 120; y < H - 100; y += 20) { const w = y % 100 === 0 ? 8 : 4; ctx.beginPath(); ctx.moveTo(W - m, y); ctx.lineTo(W - m - w, y); ctx.stroke(); }
}

const AFTER = [];
function frame(ctx, t) {
  ctx.save();
  background(ctx, t);
  for (const obj of TL.objects) {
    if (t < obj.born) continue;
    const p = propsAt(obj, t);
    if (p.opacity <= 0.002) continue;
    const where = (a) => { const st = STAGES[a.obj]; return a.at != null ? st.anchor(st.anchors[a.at], st.x, st.y) : st.project(a.col, a.row, st.x, st.y); };
    if (Array.isArray(p.anchors) && p.anchors.every((a) => STAGES[a.obj])) { p.pts = p.anchors.map(where); obj._dense = null; }
    if (p.anchor && STAGES[p.anchor.obj]) {
      const st = STAGES[p.anchor.obj], pt = where(p.anchor);
      if (obj.type === "note") p.to = pt;
      else { p.x = pt[0] + (p.anchor.dx || 0); p.y = pt[1] + (p.anchor.dy || 0); }
      if (obj.type === "note" && p.anchor.ox != null) { p.x = pt[0] + p.anchor.ox; p.y = pt[1] + p.anchor.oy; }
    }
    ctx.save();
    ctx._alpha = clamp(p.opacity);
    ctx.globalAlpha = ctx._alpha;
    DRAW[obj.type](ctx, p, t, obj);
    ctx.restore();
  }
  for (const f of AFTER) f(ctx, t);
  // fade in from black, out at the end
  const f = Math.max(clamp(1 - t / 600), clamp((t - (DUR - 700)) / 700));
  if (f > 0) { ctx.fillStyle = `rgba(3,6,18,${f})`; ctx.fillRect(0, 0, W, H); }
  ctx.restore();
}

// ---- sound: the same voices live and in the render
function synth(ctx, out) {
  let seed = 7;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const tone = (at, f, dur, type = "sine", gain = 0.1, slide = 0, attack = 0.004) => {
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type; o.frequency.setValueAtTime(f, at);
    if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(30, f * slide), at + dur);
    g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(gain, at + attack); g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    o.connect(g).connect(out); o.start(at); o.stop(at + dur + 0.05);
  };
  const noise = (at, dur, gain = 0.05, from = 2000, to = 600, type = "bandpass", q = 1.2) => {
    const buf = ctx.createBuffer(1, Math.ceil(ctx.sampleRate * dur), ctx.sampleRate), d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = rnd() * 2 - 1;
    const src = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain();
    src.buffer = buf; f.type = type; f.Q.value = q; f.frequency.setValueAtTime(from, at); f.frequency.exponentialRampToValueAtTime(to, at + dur);
    g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(gain, at + 0.015); g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    src.connect(f).connect(g).connect(out); src.start(at);
  };
  const pad = (at, f, dur, gain = 0.012) => {
    for (const [type, det] of [["sine", 0], ["triangle", 6], ["sine", -5]]) {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.type = type; o.frequency.setValueAtTime(f, at); o.detune.setValueAtTime(det, at);
      g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(gain, at + 1.6); g.gain.setValueAtTime(gain, at + dur - 1.6); g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
      o.connect(g).connect(out); o.start(at); o.stop(at + dur + 0.05);
    }
  };
  return { tone, noise, pad, rnd };
}
const VOICE = {
  tick: (s, e, at) => s.tone(at, 2200, 0.05, "sine", 0.05),
  draw: (s, e, at) => s.noise(at, 0.45, 0.018, 4200, 1400),
  type: (s, e, at) => { for (let i = 0; i < (e.n || 6); i++) s.tone(at + i * 0.045, 1500 + s.rnd() * 500, 0.025, "square", 0.012); },
  chime: (s, e, at) => { s.tone(at, 880, 1.4, "sine", 0.05); s.tone(at + 0.07, 1318.5, 1.6, "sine", 0.035); s.tone(at + 0.14, 1760, 1.2, "sine", 0.02); },
  glitch: (s, e, at) => { for (let i = 0; i < 9; i++) s.noise(at + i * 0.06 + s.rnd() * 0.03, 0.05, 0.05, 900 + s.rnd() * 3000, 400, "bandpass", 6); s.tone(at, 140, 0.5, "square", 0.025, 0.5); },
  whoosh: (s, e, at) => s.noise(at, 0.7, 0.03, 300, 2400, "lowpass", 0.7),
  thud: (s, e, at) => s.tone(at, 85, 0.5, "sine", 0.14, 0.55, 0.002),
  rise: (s, e, at) => { s.tone(at, 220, 1.4, "triangle", 0.03, 2); s.noise(at, 1.4, 0.015, 400, 3000, "lowpass", 0.7); },
  clicks: (s, e, at) => { const d = (e.dur || 2000) / 1000, n = Math.min(80, Math.floor(d / 0.07)); for (let i = 0; i < n; i++) { const a = at + (i / n) * d + s.rnd() * 0.03; s.noise(a, 0.03, 0.05, 3800 + s.rnd() * 1500, 2600, "bandpass", 3); s.tone(a, 1900 + s.rnd() * 400, 0.02, "triangle", 0.012); } },
  sweep: (s, e, at) => { const d = (e.dur || 2000) / 1000; for (let i = 0; i < Math.floor(d / 0.11); i++) s.tone(at + i * 0.11, 900 + i * 18, 0.03, "sine", 0.016); },
};
// a slow four-chord bed under the whole thing
const CHORDS = [[110, 164.81, 220, 261.63], [87.31, 130.81, 174.61, 220], [130.81, 196, 261.63, 329.63], [98, 146.83, 196, 246.94]];
function music(s, from, to) {
  const bar = 8;
  for (let b = Math.floor(from / 1000 / bar); b * bar < to / 1000; b++) {
    const at = b * bar - from / 1000, ch = CHORDS[b % CHORDS.length];
    if (at + bar < 0) continue;
    for (const f of ch) s.pad(Math.max(0, at), f, bar + 1.5 - Math.max(0, -at), 0.009);
    s.tone(Math.max(0, at), ch[0] / 2, bar, "sine", 0.03, 0, 1.2);
  }
}
async function renderAudio(fromMs, toMs, rate = 48000) {
  const len = Math.ceil(((toMs - fromMs) / 1000 + 1) * rate);
  const ctx = new OfflineAudioContext(1, len, rate), master = ctx.createGain();
  master.gain.value = 0.9; master.connect(ctx.destination);
  const s = synth(ctx, master);
  if (TL.meta.music !== false) music(s, fromMs, toMs);
  for (const e of TL.sounds) if (e.t >= fromMs && e.t < toMs) VOICE[e.kind]?.(s, e, (e.t - fromMs) / 1000, ctx, master);
  // voices that start before the range but are still sounding (long clips)
  for (const e of TL.sounds) if (e.t < fromMs && e.long && e.t + e.long > fromMs) VOICE[e.kind]?.(s, e, (e.t - fromMs) / 1000, ctx, master);
  return ctx.startRendering();
}
function wavBase64(buf, n) {
  const data = buf.getChannelData(0), rate = buf.sampleRate;
  const wav = new DataView(new ArrayBuffer(44 + n * 2));
  const str = (o, x) => { for (let i = 0; i < x.length; i++) wav.setUint8(o + i, x.charCodeAt(i)); };
  str(0, "RIFF"); wav.setUint32(4, 36 + n * 2, true); str(8, "WAVEfmt "); wav.setUint32(16, 16, true); wav.setUint16(20, 1, true); wav.setUint16(22, 1, true);
  wav.setUint32(24, rate, true); wav.setUint32(28, rate * 2, true); wav.setUint16(32, 2, true); wav.setUint16(34, 16, true); str(36, "data"); wav.setUint32(40, n * 2, true);
  for (let i = 0; i < n; i++) wav.setInt16(44 + i * 2, Math.max(-1, Math.min(1, data[i])) * 32767, true);
  let bin = ""; const bytes = new Uint8Array(wav.buffer);
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}

// ---- the page: canvas, captions, controls
const canvas = document.getElementById("stage"), ctx = canvas.getContext("2d");
canvas.width = W; canvas.height = H;
const capEl = document.getElementById("caption");
const $ = (id) => document.getElementById(id);
let t = 0, playing = false, last = 0, captions = true, sound = false, audioCtx = null, track = null, src = null;

function caption(t) {
  const n = TL.narration.find((x) => t >= x.t && t < x.t + x.dur);
  capEl.textContent = n && captions ? n.text : "";
  capEl.style.opacity = n && captions ? 1 : 0;
}
function draw(ms) { t = clamp(ms, 0, DUR); frame(ctx, t); caption(t); if ($("scrub")) { $("scrub").value = Math.round((t / DUR) * 1000); $("time").textContent = `${(t / 1000).toFixed(1)} / ${(DUR / 1000).toFixed(0)} s`; } }

async function startSound() {
  if (!sound || !playing) return;
  audioCtx ||= new (window.AudioContext || window.webkitAudioContext)();
  if (!track) track = await renderAudio(0, DUR, audioCtx.sampleRate);
  if (!playing) return;
  src = audioCtx.createBufferSource(); src.buffer = track; src.connect(audioCtx.destination);
  src.start(0, t / 1000);
}
function stopSound() { try { src?.stop(); } catch {} src = null; }

function play() { if (t >= DUR - 50) draw(0); playing = true; last = performance.now(); $("play").textContent = "Pause"; startSound(); requestAnimationFrame(loop); }
function pause() { playing = false; stopSound(); $("play").textContent = t >= DUR - 50 ? "Replay" : "Play"; }
function loop(now) {
  if (!playing) return;
  draw(t + Math.min(100, now - last)); last = now;
  if (t >= DUR) { pause(); return; }
  requestAnimationFrame(loop);
}

// chapters, from the dial's steps
const chapters = [{ t: 0, label: "start" }].concat((tweens.dial || []).filter((x) => x.prop === "label").map((x) => ({ t: x.t0, label: x.to })));
const dialObj = TL.objects.find((o) => o.id === "dial");
if (dialObj) chapters.splice(1, 0, { t: dialObj.born, label: dialObj.props.label });

function controls() {
  const bar = $("controls"); if (!bar) return;
  bar.innerHTML = `<button id="play" type="button">Play</button><input id="scrub" type="range" min="0" max="1000" value="0" aria-label="Time"><span id="time"></span>
    <span class="chapters">${chapters.map((c, i) => `<button type="button" data-t="${c.t}">${i ? i + " · " : ""}${c.label}</button>`).join("")}</span>
    <label><input id="cc" type="checkbox" checked> Captions</label><label><input id="snd" type="checkbox"> Sound</label>`;
  $("play").onclick = () => (playing ? pause() : play());
  $("scrub").oninput = () => { draw(($("scrub").value / 1000) * DUR); if (playing) { stopSound(); startSound(); } };
  bar.querySelector(".chapters").onclick = (e) => { const b = e.target.closest("button"); if (b) { draw(+b.dataset.t + 1); if (playing) { stopSound(); startSound(); } } };
  $("cc").onchange = (e) => { captions = e.target.checked; draw(t); };
  $("snd").onchange = (e) => { sound = e.target.checked; stopSound(); if (sound) startSound(); };
  addEventListener("keydown", (e) => { if (e.code === "Space" && e.target === document.body) { e.preventDefault(); playing ? pause() : play(); } });
}

// ---- render.mjs contract (the page is a pure function of time)
window.__duration = DUR;
window.__narration = TL.narration;
window.__renderAudio = async (fromMs, toMs, rate = 48000) => wavBase64(await renderAudio(fromMs, toMs, rate), Math.round(((toMs - fromMs) / 1000) * rate));

const fonts = [`600 38px ${SANS}`, `500 16px ${SANS}`, `500 16px ${MONO}`, `600 16px ${MONO}`, `400 16px ${MONO}`];
// ---- the plugin API (explain/lib/plugins/*.js): new draw types, 3D stage
// kinds, sound voices, after-frame hooks, and work to finish before start
window.BP = {
  TL, W, H, DUR, C, color, MONO, SANS, ADV, clamp, EASE, hash, GLYPHS, glow, noGlow, roundRect, partial, at, smooth, arrowHead, visText, chipLayout, propsAt,
  DRAW, STAGES, STAGE_KINDS, VOICE, AFTER, PLATE,
  get THREE() { return THREE; }, get ADDONS() { return ADDONS; },
  kit, plastic, Bricks, Stack,             // the LEGO kit (brick(p, material)), plastic(colorCode), the built-in stages
  threeTypes: new Set(["stage3d"]),       // object types that need three.js
  ready: [],                              // functions returning promises, run after three.js loads
  /** register(type, draw): a 2D object type, draw(ctx, props, t, obj) */
  register(type, fn) { if (DRAW[type]) throw new Error(`draw type "${type}" exists`); DRAW[type] = fn; },
  /** stage(kind, make): a 3D stage kind; make(props) → { canvas, update(p, t, born), anchor?(a, x0, y0), project?() } */
  stage(kind, make, flags = {}) { STAGE_KINDS[kind] = Object.assign(make, flags); },
  /** voice(name, fn): a sound; fn(synth, event, atSeconds) */
  voice(name, fn) { VOICE[name] = fn; },
};
BP.start = function start() {
  const needs3d = TL.objects.some((o) => BP.threeTypes.has(o.type));
  const needsBricks = TL.objects.some((o) => o.type === "stage3d" && o.props.kind !== "stack");
  const three = needs3d ? import("three").then(async (m) => {
    THREE = m;
    if (needsBricks) {
      const [rb, bu] = await Promise.all([import("three/addons/geometries/RoundedBoxGeometry.js"), import("three/addons/utils/BufferGeometryUtils.js")]);
      ADDONS = { RoundedBoxGeometry: rb.RoundedBoxGeometry, toCreasedNormals: bu.toCreasedNormals };
    }
  }) : Promise.resolve();
  Promise.all([three, ...fonts.map((f) => document.fonts.load(f).catch(() => {}))])
    .then(() => Promise.all(BP.ready.map((f) => f())))
    .then(() => {
      window.__renderAt = (ms) => { document.body.classList.add("render"); draw(ms); };
      controls();
      draw(0);
      const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (!reduced && !/[?&]paused\b/.test(location.search)) play();
      else draw(Math.min(DUR, 9000));
    });
};
})();
