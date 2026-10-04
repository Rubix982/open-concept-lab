// s.morph(id, chartA, chartB, o): a brick model that rebuilds itself into
// another. It starts as chartA, built part by part; then
//   s.set(id, { morph: 1 }, { dur: 3500 })
// turns it into chartB. With o.models = [A, B, C, …], morph runs 0 → n − 1.
// Anchors: "a:bar0" / "b:cell:2:3" (or "m2:top4") pin to one model; a plain
// name ("bar0") follows whichever model the morph is nearer.
export function install(s, { add }) {
  s.morph = (id, A, B, o = {}) => {
    const models = (o.models || [A, B]).filter(Boolean).map((m) => ({ parts: m.parts, anchors: m.anchors, size: m.size }));
    const anchors = {};
    const names = new Set();
    models.forEach((m, i) => {
      for (const [k, p] of Object.entries(m.anchors || {})) {
        anchors[`m${i}:${k}`] = { m: i, p };
        if (i < 2) anchors[`${"ab"[i]}:${k}`] = { m: i, p };
        names.add(k);
      }
    });
    for (const k of names) anchors[k] = { by: models.map((m) => (m.anchors || {})[k] || null) };
    const { models: _m, ...rest } = o;
    const n0 = models[0].parts.length;
    return add(id, "stage3d", {
      kind: "morph", x: 0, y: 0, w: 1920, h: 1080, az: 25, el: 28, dist: 40,
      models, anchors, morph: 0, ...rest,
    }, o.dur ?? Math.min(6000, 400 + n0 * 12));
  };
}
