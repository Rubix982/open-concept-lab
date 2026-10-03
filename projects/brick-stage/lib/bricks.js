// Brick drawing, shared by the player and the printable booklet (the build
// inlines this file into both). Plain parts are rounded boxes with studs;
// slopes and round parts use their real LDraw geometry, turned into the scene
// frame: LDU / 20, y and z flipped, rotated the way the LDraw export rotates it.
function brickKit({ THREE, RoundedBoxGeometry, toCreasedNormals, meshes, PLATE }) {
  const toScene = (x, yPlates, z) => new THREE.Vector3(x, yPlates * PLATE, -z);
  const geoCache = new Map(), meshGeoCache = new Map();
  const studGeo = new THREE.CylinderGeometry(0.3, 0.3, 0.18, 24);
  function bodyGeo(w, h, d) {
    const k = `${w}x${h}x${d}`;
    if (!geoCache.has(k)) geoCache.set(k, new RoundedBoxGeometry(w - 0.03, h * PLATE - 0.02, d - 0.03, 3, 0.05));
    return geoCache.get(k);
  }
  function meshGeo(p) {
    const key = `${p.part}@${p.rot}`;
    if (meshGeoCache.has(key)) return meshGeoCache.get(key);
    const m = meshes[p.part], [cx, cz] = m.center, phi = THREE.MathUtils.degToRad(-p.rot), cs = Math.cos(phi), sn = Math.sin(phi);
    const pos = new Float32Array(m.tri.length);
    for (let i = 0; i < m.tri.length; i += 3) {
      const lx = (m.tri[i] - cx) / 20, ly = -m.tri[i + 1] / 20 + (p.h * PLATE) / 2, lz = -(m.tri[i + 2] - cz) / 20;
      pos[i] = lx * cs + lz * sn; pos[i + 1] = ly; pos[i + 2] = -lx * sn + lz * cs;
    }
    let geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo = toCreasedNormals(geo, Math.PI / 6);
    meshGeoCache.set(key, geo);
    return geo;
  }
  // `covered` (optional): skip studs hidden under another part, for big models
  function brick(p, mat, covered) {
    const g = new THREE.Group();
    g.userData.home = toScene(p.x + p.w / 2, p.y + p.h / 2, p.z + p.d / 2);
    if (p.mesh && meshes?.[p.part]) {
      const m = new THREE.Mesh(meshGeo(p), mat); m.castShadow = m.receiveShadow = true; g.add(m);
      return g;
    }
    const body = new THREE.Mesh(bodyGeo(p.w, p.h, p.d), mat);
    body.castShadow = body.receiveShadow = true; g.add(body);
    if (p.kind !== "tile") for (let i = 0; i < p.w; i++) for (let k = 0; k < p.d; k++) {
      if (covered && covered(p.x + i, p.y + p.h, p.z + k)) continue;
      const s = new THREE.Mesh(studGeo, mat); s.castShadow = true;
      s.position.set(-p.w / 2 + 0.5 + i, p.h * PLATE / 2 + 0.09, p.d / 2 - 0.5 - k);
      g.add(s);
    }
    return g;
  }
  return { brick, toScene, bodyGeo, meshGeo };
}
