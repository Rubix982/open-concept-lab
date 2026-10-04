// Morph: one checked brick model rebuilds itself into another, on camera.
// A stage of kind "morph" holds a chain of models (props.models); props.morph
// runs 0 → models.length − 1. Parts are matched model to model (same part,
// nearest first, colour may change); matched parts lift, fly an arc and
// settle in their new home, staggered left to right; parts the next model
// doesn't need lift off and shrink away; new parts drop in.
// Uses the core's LEGO kit (BP.kit), plastic (BP.plastic) and the same light
// as the built-in bricks stage.
(function () {
  "use strict";
  const { clamp, EASE, PLATE } = BP;

  // match model a's parts to model b's: same part and colour, then same part
  // (colour changes in flight); nearest home first. Returns b index → a index.
  function match(a, b, ha, hb) {
    const used = new Set(), out = new Map();
    for (const pass of [(p, q) => p.part === q.part && p.color === q.color, (p, q) => p.part === q.part]) {
      // cheap candidate lists per part id
      const byPart = new Map();
      a.forEach((p, i) => { if (!used.has(i)) (byPart.get(p.part) || byPart.set(p.part, []).get(p.part)).push(i); });
      b.forEach((q, j) => {
        if (out.has(j)) return;
        let best = -1, bd = Infinity;
        for (const i of byPart.get(q.part) || []) {
          if (used.has(i) || !pass(a[i], q)) continue;
          const d = ha[i].distanceToSquared(hb[j]);
          if (d < bd) { bd = d; best = i; }
        }
        if (best >= 0) { used.add(best); out.set(j, best); }
      });
    }
    return out;
  }

  function make(o) {
    const THREE = BP.THREE, KIT = BP.kit();
    const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(o.fov || 30, o.w / o.h, 0.1, 500);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(1); renderer.setSize(o.w, o.h, false); renderer.setClearColor(0x000000, 0);
    renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    scene.add(new THREE.HemisphereLight(0xe8eeff, 0x1a2550, 1.6));
    const key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(-18, 34, 22); key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048); const sc = key.shadow.camera; sc.left = sc.bottom = -45; sc.right = sc.top = 45; sc.near = 1; sc.far = 140;
    scene.add(key);
    const rim = new THREE.DirectionalLight(0x9fb8ff, 0.9); rim.position.set(20, 12, -24); scene.add(rim);
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.ShadowMaterial({ opacity: 0.35 }));
    shadow.rotation.x = -Math.PI / 2; shadow.position.y = -0.001; shadow.receiveShadow = true; scene.add(shadow);

    const models = o.models, M = models.length;
    // each model is centred on the origin, on the table
    const centers = models.map((m) => new THREE.Vector3(m.size[0] / 2, 0, -m.size[2] / 2));
    const homeOf = (p, m) => new THREE.Vector3(p.x + p.w / 2, (p.y + p.h / 2) * PLATE, -(p.z + p.d / 2)).sub(centers[m]);
    const homes = models.map((m, mi) => m.parts.map((p) => homeOf(p, mi)));

    // pieces: one 3D brick per part of model 0, reused by matched parts later
    // pieces[k] = { g, at: [{ home, color, rot } | null per model], order: [per model] }
    const pieces = [];
    const owner = models.map(() => []);
    const newPiece = (p, mi, j) => {
      const g = KIT.brick(p, BP.plastic(p.color));
      g.visible = false; scene.add(g);
      const piece = { g, base: p, at: models.map(() => null), mat: new Map() };
      pieces.push(piece);
      return piece;
    };
    models[0].parts.forEach((p, j) => { const k = newPiece(p, 0, j); k.at[0] = { home: homes[0][j], color: p.color, rot: p.rot, j }; owner[0][j] = pieces.length - 1; });
    for (let mi = 1; mi < M; mi++) {
      const m = match(models[mi - 1].parts, models[mi].parts, homes[mi - 1], homes[mi]);
      models[mi].parts.forEach((q, j) => {
        let idx;
        if (m.has(j)) idx = owner[mi - 1][m.get(j)];
        else { newPiece(q, mi, j); idx = pieces.length - 1; }
        pieces[idx].at[mi] = { home: homes[mi][j], color: q.color, rot: q.rot, j };
        owner[mi][j] = idx;
      });
    }
    // stagger: each piece's start within a step, left to right across its destination
    // left to right across the destination, and bottom to top within a column,
    // so a growing bar fills like a cascade rather than arriving in one block
    const span = (mi) => { const xs = homes[mi].map((h) => h.x), ys = homes[mi].map((h) => h.y); return [Math.min(...xs), Math.max(...xs) - Math.min(...xs) || 1, Math.max(...ys) || 1]; };
    const spans = models.map((_, mi) => span(mi));
    const delay = (h, mi) => 0.3 * clamp((h.x - spans[mi][0]) / spans[mi][1]) + 0.14 * clamp(h.y / spans[mi][2]) + 0.02 * ((Math.abs(h.z * 7.3) % 1));

    const N0 = models[0].parts.length;
    const tmp = new THREE.Vector3();
    const place = (pc, pos, color, rotY, scale) => {
      const g = pc.g;
      g.visible = scale > 0.01;
      g.position.copy(pos); g.rotation.y = rotY; g.scale.setScalar(Math.max(0.001, scale));
      if (pc.color !== color) {
        pc.color = color;
        g.traverse((m) => { if (m.isMesh) m.material = BP.plastic(color); });
      }
    };
    const rad = (deg) => (deg * Math.PI) / 180;
    let cur = { v: 0 };

    return {
      canvas: renderer.domElement,
      update(p) {
        const v = clamp(p.morph || 0, 0, M - 1), step = Math.min(M - 2, Math.floor(v)), k = M > 1 ? v - Math.max(0, step) : 0;
        cur.v = v;
        // camera, aimed at the middle height of whichever models are in play
        const hA = models[Math.max(0, step)].size[1] * PLATE, hB = models[Math.min(M - 1, Math.max(0, step) + 1)].size[1] * PLATE;
        const az = rad(p.az), el = rad(p.el), ty = p.ty ?? (hA + (hB - hA) * EASE.inout(k)) / 2;
        cam.position.set(p.dist * Math.cos(el) * Math.sin(az), ty + p.dist * Math.sin(el), p.dist * Math.cos(el) * Math.cos(az));
        cam.lookAt(0, ty, 0); cam.updateMatrixWorld(); cam.updateProjectionMatrix();

        if (v <= 0 || M === 1) {
          // building model 0, part by part, like the bricks stage
          const at = p.reveal * (N0 + N0 * 0.05), sp = Math.max(1, N0 * 0.05);
          for (const pc of pieces) {
            const a = pc.at[0];
            if (!a) { pc.g.visible = false; continue; }
            const kk = clamp((at - a.j) / sp), e = EASE.out(kk);
            tmp.copy(a.home); tmp.y += (1 - e) * 5;
            place(pc, tmp, a.color, 0, kk > 0 ? 1 : 0);
          }
        } else {
          const A = step, B = step + 1;
          for (const pc of pieces) {
            const a = pc.at[A], b = pc.at[B];
            const r0 = rad(-((pc.base.rot || 0))), rotOf = (s) => rad(-(s.rot || 0)) - r0;
            if (a && b) {
              // fly an arc: lift, travel, settle
              // pieces that stay put (most of the base) don't hop
              const dist = a.home.distanceTo(b.home), moving = clamp(dist / 0.6);
              const d = delay(b.home, B), u = clamp((k - d) / 0.5), e = EASE.inout(u);
              const lift = Math.sin(Math.PI * u) * (2.5 + 0.12 * dist) * moving;
              tmp.lerpVectors(a.home, b.home, e); tmp.y += lift;
              place(pc, tmp, u < 0.5 ? a.color : b.color, rotOf(a) + (rotOf(b) - rotOf(a)) * e, 1);
            } else if (a) {
              // not needed: lift off and shrink away, early in the step
              const d = delay(a.home, A) * 0.6, u = clamp((k - d) / 0.35), e = EASE.inout(u);
              tmp.copy(a.home); tmp.y += e * 7;
              place(pc, tmp, a.color, rotOf(a) + e * 0.8, 1 - e);
            } else if (b) {
              // new: drops in, late in the step
              const d = 0.45 + delay(b.home, B) * 0.6, u = clamp((k - d) / 0.3), e = EASE.out(u);
              tmp.copy(b.home); tmp.y += (1 - e) * 6;
              place(pc, tmp, b.color, rotOf(b), u > 0 ? 0.25 + 0.75 * e : 0);
            } else pc.g.visible = false;
          }
        }
        renderer.render(scene, cam);
      },
      // anchors: "m<i>:name" (or "a:"/"b:") pin to one model; a plain name
      // follows whichever model is nearer in the morph
      anchor(a, x0, y0) {
        if (!a) return [-999, -999];
        let pt, m;
        if (Array.isArray(a)) { pt = a; m = 0; }
        else if (a.p) { pt = a.p; m = a.m; }
        else {
          const want = Math.round(cur.v);
          m = a.by[want] ? want : a.by.findIndex(Boolean);
          pt = a.by[m];
        }
        tmp.set(pt[0], pt[1] * PLATE, -pt[2]).sub(centers[m]).project(cam);
        return [x0 + (tmp.x * 0.5 + 0.5) * o.w, y0 + (-tmp.y * 0.5 + 0.5) * o.h];
      },
    };
  }
  BP.stage("morph", make, { glow: false, overlays: false });

  // the sound of a morph: a burst of plastic clicks under a soft whoosh
  BP.voice("morph", (s, e, at) => {
    const d = (e.dur || 2500) / 1000;
    s.noise(at, d * 0.8, 0.03, 300, 2600, "lowpass", 0.7);
    const n = Math.min(90, Math.floor(d / 0.045));
    for (let i = 0; i < n; i++) {
      const a = at + d * (0.15 + 0.8 * (i / n)) + s.rnd() * 0.03;
      s.noise(a, 0.025, 0.045, 3600 + s.rnd() * 1800, 2400, "bandpass", 3);
      s.tone(a, 1800 + s.rnd() * 600, 0.02, "triangle", 0.01);
    }
  });
})();
