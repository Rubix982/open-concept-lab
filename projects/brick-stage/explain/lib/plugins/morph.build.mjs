// Build hook for morph stages: every model in the chain goes through
// brick-check, like any brick-stage model; parts get their footprint, kind and
// mesh flag, and round parts get their real geometry.
export async function build(tl, ctx) {
  const stages = tl.objects.filter((o) => o.type === "stage3d" && o.props.kind === "morph");
  if (!stages.length) return "";
  const { check } = await import("../../../../brick-check/lib/check.mjs");
  const { PARTS, COLORS, footprint } = await import("../../../../brick-check/lib/parts.mjs");
  const { partMesh } = await import("../../../../brick-check/tools/ldraw-mesh.mjs");
  const meshIds = new Set();
  for (const o of stages) {
    o.props.models.forEach((m, i) => {
      const r = check({ steps: [{ note: `${o.id}[${i}]`, parts: m.parts }] });
      ctx.log(`${r.ok ? "✓" : "✗"} ${o.id} · model ${i} · ${m.parts.length} parts${r.ok ? " · buildable" : ": " + [...new Set(r.errors.map((e) => e.rule))].join(", ")}`);
      if (!r.ok) process.exitCode = 1;
      m.parts = m.parts.map((p) => {
        const f = footprint(p), def = PARTS[p.part];
        if (def.mesh) meshIds.add(p.part);
        return { ...p, w: f.w, d: f.d, h: f.h, kind: def.kind, mesh: Boolean(def.mesh) };
      });
    });
  }
  tl.colors = COLORS;
  tl.meshes ||= {};
  for (const id of meshIds) if (!tl.meshes[id]) tl.meshes[id] = { tri: (await partMesh(id)).tri, center: PARTS[id].center || [0, 0] };
  return "";
}
