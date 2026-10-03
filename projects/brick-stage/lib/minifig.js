// Minifigure-style characters, drawn from simple shapes and rigged for
// animation: legs swing from the hips, arms from the shoulders, C-shaped
// hands twist at the wrist, the head turns on its neck, and the body can lean.
// Faces are drawn on a texture, so expressions can change. These are
// characters, not checked LEGO models. Inlined into the player by the build.
function minifigKit(THREE, colors) {
  const SKIN = "#f2cd37";
  const col = (c, fallback) => (c == null ? fallback : typeof c === "string" ? c : colors[c]?.[2] || fallback);
  const mat = (c, opts = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.32, ...opts });

  // ---- faces: eyes, brows and a mouth per expression
  function faceTexture(expr, extra) {
    const c = document.createElement("canvas"); c.width = 512; c.height = 256;
    const g = c.getContext("2d");
    g.fillStyle = SKIN; g.fillRect(0, 0, 512, 256);
    const cx = 256, ey = 108, dx = 34;
    g.fillStyle = "#1b1b1b"; g.strokeStyle = "#1b1b1b"; g.lineCap = "round"; g.lineWidth = 9;
    const eye = (x, h = 22) => { g.beginPath(); g.ellipse(x, ey, 11, h / 2, 0, 0, Math.PI * 2); g.fill(); g.fillStyle = "#fff"; g.beginPath(); g.arc(x + 3, ey - 4, 3.5, 0, Math.PI * 2); g.fill(); g.fillStyle = "#1b1b1b"; };
    const brow = (x, tilt, lift = 0) => { g.beginPath(); g.moveTo(x - 16, ey - 32 - lift + tilt); g.lineTo(x + 16, ey - 32 - lift - tilt); g.stroke(); };
    const mouth = (kind) => {
      g.beginPath();
      if (kind === "smile") g.arc(cx, 150, 34, 0.15 * Math.PI, 0.85 * Math.PI);
      else if (kind === "grin") { g.arc(cx, 146, 40, 0.05 * Math.PI, 0.95 * Math.PI); g.closePath(); g.fillStyle = "#fff"; g.fill(); g.fillStyle = "#1b1b1b"; }
      else if (kind === "sad") g.arc(cx, 196, 30, 1.2 * Math.PI, 1.8 * Math.PI);
      else if (kind === "o") { g.ellipse(cx, 168, 13, 17, 0, 0, Math.PI * 2); g.fill(); return; }
      else if (kind === "smirk") { g.moveTo(cx - 26, 172); g.quadraticCurveTo(cx + 10, 180, cx + 30, 160); }
      else if (kind === "wavy") { g.moveTo(cx - 30, 172); g.quadraticCurveTo(cx - 15, 160, cx, 172); g.quadraticCurveTo(cx + 15, 184, cx + 30, 170); }
      else { g.moveTo(cx - 26, 172); g.lineTo(cx + 26, 172); }
      g.stroke();
    };
    const E = {
      smile: () => { eye(cx - dx); eye(cx + dx); mouth("smile"); },
      grin: () => { eye(cx - dx); eye(cx + dx); brow(cx - dx, -2, 4); brow(cx + dx, 2, 4); mouth("grin"); },
      neutral: () => { eye(cx - dx); eye(cx + dx); mouth("line"); },
      sad: () => { eye(cx - dx, 16); eye(cx + dx, 16); brow(cx - dx, -7); brow(cx + dx, 7); mouth("sad"); },
      worried: () => { eye(cx - dx); eye(cx + dx); brow(cx - dx, -6, 6); brow(cx + dx, 6, 6); mouth("wavy"); },
      surprised: () => { eye(cx - dx, 28); eye(cx + dx, 28); brow(cx - dx, 0, 12); brow(cx + dx, 0, 12); mouth("o"); },
      determined: () => { eye(cx - dx); eye(cx + dx); brow(cx - dx, 7, -2); brow(cx + dx, -7, -2); mouth("smirk"); },
      deadpan: () => { g.fillRect(cx - dx - 12, ey - 3, 24, 7); g.fillRect(cx + dx - 12, ey - 3, 24, 7); mouth("line"); },
    };
    (E[expr] || E.smile)();
    if (extra?.includes("flour")) { g.fillStyle = "rgba(255,255,255,.85)"; g.beginPath(); g.ellipse(cx + 70, 150, 22, 10, -0.3, 0, Math.PI * 2); g.fill(); }
    if (extra?.includes("whiskers")) { g.strokeStyle = "#7a5a2a"; g.lineWidth = 4; for (const s of [-1, 1]) { g.beginPath(); g.moveTo(cx + s * 50, 150); g.lineTo(cx + s * 90, 140); g.stroke(); } }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
  }

  // ---- torso prints on the front
  function torsoTexture(base, print) {
    const c = document.createElement("canvas"); c.width = 256; c.height = 256;
    const g = c.getContext("2d");
    g.fillStyle = base; g.fillRect(0, 0, 256, 256);
    if (print === "vest") {
      g.fillStyle = "#fe8a18"; g.fillRect(28, 0, 70, 256); g.fillRect(158, 0, 70, 256);
      g.fillStyle = "#d9dde0"; g.fillRect(28, 150, 70, 22); g.fillRect(158, 150, 70, 22); g.fillRect(28, 196, 70, 22); g.fillRect(158, 196, 70, 22);
    } else if (print === "apron") {
      g.fillStyle = "#ffffff"; g.beginPath(); g.moveTo(70, 40); g.lineTo(186, 40); g.lineTo(206, 256); g.lineTo(50, 256); g.closePath(); g.fill();
      g.strokeStyle = "#ffffff"; g.lineWidth = 8; g.beginPath(); g.moveTo(72, 42); g.lineTo(40, 0); g.moveTo(184, 42); g.lineTo(216, 0); g.stroke();
      g.fillStyle = "rgba(200,170,120,.5)"; g.beginPath(); g.ellipse(150, 170, 16, 9, 0.4, 0, Math.PI * 2); g.fill();
    } else if (print === "sweater") {
      g.strokeStyle = "rgba(255,255,255,.35)"; g.lineWidth = 6; for (let y = 20; y < 256; y += 28) { g.beginPath(); g.moveTo(0, y); g.lineTo(256, y); g.stroke(); }
    } else if (print === "chef") {
      g.fillStyle = "#1b1b1b"; for (const y of [70, 120, 170]) for (const x of [100, 156]) { g.beginPath(); g.arc(x, y, 7, 0, Math.PI * 2); g.fill(); }
    } else if (print === "firefighter") {
      g.fillStyle = "#fac80a"; g.fillRect(0, 150, 256, 20); g.fillRect(0, 196, 256, 20); g.fillStyle = "#1b1b1b"; g.fillRect(120, 0, 16, 256);
    } else if (print === "astronaut") {
      g.fillStyle = "#1e5aa8"; g.beginPath(); g.arc(128, 110, 40, 0, Math.PI * 2); g.fill(); g.fillStyle = "#fac80a"; g.beginPath(); g.moveTo(98, 130); g.lineTo(128, 72); g.lineTo(158, 130); g.closePath(); g.fill();
    } else if (print === "knight") {
      g.strokeStyle = "rgba(0,0,0,.35)"; g.lineWidth = 6; g.strokeRect(30, 20, 196, 216); g.beginPath(); g.moveTo(128, 20); g.lineTo(128, 236); g.moveTo(30, 128); g.lineTo(226, 128); g.stroke();
      g.fillStyle = "#b40000"; g.beginPath(); g.moveTo(128, 60); g.lineTo(170, 90); g.lineTo(128, 200); g.lineTo(86, 90); g.closePath(); g.fill();
    }
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
  }

  // ---- hats and hair, sitting on the head's top (y = 0 there)
  function hat(kind, color, tilt = 0) {
    const g = new THREE.Group();
    const M = mat(color);
    if (kind === "hardhat") {
      const dome = new THREE.Mesh(new THREE.SphereGeometry(0.66, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), M); dome.position.y = -0.12;
      const brim = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.82, 0.07, 28), M); brim.position.y = -0.1;
      const ridge = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.12, 1.1), M); ridge.position.y = 0.48;
      g.add(dome, brim, ridge);
    } else if (kind === "cap") {
      const dome = new THREE.Mesh(new THREE.SphereGeometry(0.63, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), M); dome.position.y = -0.1;
      const visor = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.05, 20, 1, false, -Math.PI / 2, Math.PI), M); visor.position.set(0, -0.08, 0.5); visor.scale.set(1, 1, 0.9);
      g.add(dome, visor);
    } else if (kind === "chef") {
      const band = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.6, 0.35, 24), M); band.position.y = 0.05;
      const puff = new THREE.Mesh(new THREE.SphereGeometry(0.72, 24, 16), M); puff.position.y = 0.55; puff.scale.set(1, 0.7, 1);
      g.add(band, puff);
    } else if (kind === "knight") {
      const helm = new THREE.Mesh(new THREE.CylinderGeometry(0.66, 0.68, 1.2, 28), M); helm.position.y = -0.48;
      const top = new THREE.Mesh(new THREE.SphereGeometry(0.66, 24, 10, 0, Math.PI * 2, 0, Math.PI / 2), M); top.position.y = 0.1;
      const slit = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.09, 0.2), mat("#1b1b1b")); slit.position.set(0, -0.42, 0.6);
      g.add(helm, top, slit);
    } else if (kind === "astronaut") {
      const bubble = new THREE.Mesh(new THREE.SphereGeometry(0.88, 28, 20), mat(color, { roughness: 0.2 })); bubble.position.y = -0.48;
      const visor = new THREE.Mesh(new THREE.SphereGeometry(0.9, 28, 20, -0.75, 1.5, 0.95, 0.85), mat("#9aa6ad", { roughness: 0.05, metalness: 0.9 })); visor.position.y = -0.48;
      g.add(bubble, visor);
    } else if (kind === "firefighter") {
      const dome = new THREE.Mesh(new THREE.SphereGeometry(0.68, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), M); dome.position.y = -0.1;
      const brim = new THREE.Mesh(new THREE.CylinderGeometry(0.85, 0.9, 0.06, 28, 1, false, Math.PI / 2, Math.PI), M); brim.position.set(0, -0.12, -0.08);
      g.add(dome, brim);
    } else if (kind === "hair") {
      const h = new THREE.Mesh(new THREE.SphereGeometry(0.64, 24, 12, 0, Math.PI * 2, 0, Math.PI / 1.8), M); h.position.y = -0.18;
      g.add(h);
    }
    g.rotation.z = tilt;
    g.traverse((o) => { if (o.isMesh) o.castShadow = true; });
    return g;
  }

  // ---- the figure: origin at the feet, facing +z
  function build(look = {}) {
    const torsoC = col(look.torso, "#e4cd9e"), legsC = col(look.legs, "#1e5aa8");
    const root = new THREE.Group(), body = new THREE.Group(); root.add(body);
    const skin = mat(SKIN), legM = mat(legsC);
    const rb = (w, h, d, m) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); b.castShadow = b.receiveShadow = true; return b; };
    // legs swing from the hip line
    const legs = [-0.48, 0.48].map((x) => {
      const hip = new THREE.Group(); hip.position.set(x, 1.3, 0);
      const leg = rb(0.9, 1.25, 1.0, legM); leg.position.y = -0.66; hip.add(leg);
      body.add(hip); return hip;
    });
    const hips = rb(1.9, 0.36, 0.95, legM); hips.position.y = 1.47; body.add(hips);
    // the upper body leans from the hips
    const upper = new THREE.Group(); upper.position.y = 1.62; body.add(upper);
    const tg = new THREE.BoxGeometry(1.95, 1.55, 0.95);
    const pos = tg.attributes.position;
    for (let i = 0; i < pos.count; i++) if (pos.getY(i) > 0) pos.setX(i, pos.getX(i) * 0.76);   // narrower at the shoulders
    tg.computeVertexNormals();
    const torsoMat = mat(torsoC), front = mat("#fff", { map: torsoTexture(torsoC, look.print) });
    const torso = new THREE.Mesh(tg, [torsoMat, torsoMat, torsoMat, torsoMat, front, torsoMat]); torso.position.y = 0.78; torso.castShadow = true; upper.add(torso);
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.26, 0.16, 16), skin); neck.position.y = 1.63; upper.add(neck);
    // head: turns on the neck; the face is drawn on the front of the cylinder
    const head = new THREE.Group(); head.position.y = 1.7; upper.add(head);
    const faceMat = mat("#fff", { map: faceTexture(look.face || "smile", look.extra) });
    const headMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.58, 0.58, 1.0, 32, 1, false, Math.PI, Math.PI * 2), [faceMat, skin, skin]);
    headMesh.position.y = 0.5; headMesh.castShadow = true; head.add(headMesh);
    const stud = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.2, 18), skin); stud.position.y = 1.1; head.add(stud);
    const hatSocket = new THREE.Group(); hatSocket.position.y = 1.05; head.add(hatSocket);
    if (look.hat) hatSocket.add(hat(look.hat, col(look.hatColor, "#fac80a"), look.hatTilt || 0));
    if (look.beard) { const b = new THREE.Mesh(new THREE.SphereGeometry(0.5, 20, 12), mat("#f4f4f4")); b.position.set(0, 0.12, 0.42); b.scale.set(1, 0.9, 0.55); head.add(b); }
    // arms swing from the shoulders; hands are C-shaped clips that twist
    const sockets = {};
    const arms = [[-1, "r"], [1, "l"]].map(([s, side]) => {
      const sh = new THREE.Group(); sh.position.set(s * 0.86, 1.36, 0); upper.add(sh);
      const tilt = new THREE.Group(); tilt.rotation.z = s * 0.14; sh.add(tilt);
      const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.22, 1.2, 16), torsoMat); arm.position.y = -0.55; arm.castShadow = true; tilt.add(arm);
      const wrist = new THREE.Group(); wrist.position.set(0, -1.2, 0.12); tilt.add(wrist);
      const hand = new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.085, 10, 20, Math.PI * 1.55), skin);
      hand.rotation.set(0, 0, Math.PI * 1.22); hand.castShadow = true; wrist.add(hand);
      const socket = new THREE.Group(); wrist.add(socket); sockets[side] = socket;
      return { sh, wrist, side };
    });
    root.traverse((o) => { if (o.isMesh) o.receiveShadow = true; });
    return {
      root, body, upper, head, legs, arms, sockets, hatSocket, faceMat, look,
      setFace(expr) { if (this._expr === expr) return; this._expr = expr; faceMat.map = faceTexture(expr, look.extra); faceMat.needsUpdate = true; },
    };
  }
  return { build, hat };
}
