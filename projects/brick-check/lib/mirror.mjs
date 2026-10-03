// Mirror images, for left/right pairs like the Microduck's legs. Mirroring
// across a vertical plane flips positions and turns slopes to face the other
// way: across x, a part facing +x (rot 90) faces -x (rot 270); across z,
// rot 0 and rot 180 swap.
import { footprint } from "./parts.mjs";

export function mirror(parts, { axis = "x", about } = {}) {
  if (axis !== "x" && axis !== "z") throw new Error('mirror axis must be "x" or "z"');
  const lo = Math.min(...parts.map((p) => p[axis]));
  const hi = Math.max(...parts.map((p) => p[axis] + footprint(p)[axis === "x" ? "w" : "d"]));
  const plane = about ?? (lo + hi) / 2;               // default: mirror in place
  const swap = axis === "x" ? { 90: 270, 270: 90 } : { 0: 180, 180: 0 };
  return parts.map((p) => {
    const size = footprint(p)[axis === "x" ? "w" : "d"];
    return { ...p, [axis]: 2 * plane - (p[axis] + size), rot: swap[p.rot] ?? p.rot };
  });
}
