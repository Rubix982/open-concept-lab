// Real-world size and an estimated weight, the way the Microduck booklet
// quotes them ("about 27 cm tall … about 1.1 kg, estimated").
// Size is exact: a stud is 8 mm, a plate 3.2 mm, a stud stands 1.7 mm tall.
// Weight is an estimate from volume: LEGO parts are hollow, so we use an
// effective density per kind, calibrated on common parts (a 2x4 brick is
// about 2.3 g, a 2x4 plate about 1.3 g). Expect it to be within ~25%.
import { PARTS, footprint } from "./parts.mjs";

const DENSITY = { brick: 0.48, plate: 0.8, tile: 0.85 };   // g per cm³ of bounding box

export function physical(parts) {
  let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity, y1 = 0, grams = 0;
  for (const p of parts) {
    const f = footprint(p), s = PARTS[p.part];
    x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x + f.w); z0 = Math.min(z0, p.z); z1 = Math.max(z1, p.z + f.d);
    y1 = Math.max(y1, p.y + f.h);
    const cm3 = (f.w * 0.8) * (f.d * 0.8) * (f.h * 0.32);
    grams += cm3 * DENSITY[s.kind] * (s.mesh && s.kind === "brick" ? 0.8 : 1);   // slopes and rounds are less than a full box
  }
  const studOnTop = parts.some((p) => p.y + footprint(p).h === y1 && PARTS[p.part].kind !== "tile");
  return {
    widthMm: Math.round((x1 - x0) * 8), depthMm: Math.round((z1 - z0) * 8),
    heightMm: Math.round(y1 * 3.2 + (studOnTop ? 1.7 : 0)),
    grams: Math.round(grams), estimated: true,
  };
}
