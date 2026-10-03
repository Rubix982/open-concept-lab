// Split a model into building sections the way a booklet does: at its narrow
// points (ankles, waist, neck), where the cross-section is much smaller than
// the layers around it. Works on any parts list in build order, e.g. from
// brickify. Each cut is where everything later in the order sits at or above
// the cut, so each section rests on the ones before it. If the top section
// can be built on its own, it's offered as a sub-assembly to set on last,
// like the Microduck booklet's head.
import { footprint } from "../lib/parts.mjs";
import { check } from "../lib/check.mjs";

export function sections(parts, { maxSections = 4, minHeight = 6, narrow = 0.6 } = {}) {
  const area = new Map();
  let top = 0;
  for (const p of parts) {
    const f = footprint(p);
    area.set(p.y, (area.get(p.y) || 0) + f.w * f.d);
    top = Math.max(top, p.y + f.h);
  }
  const A = (y) => area.get(y) || 0;
  const widest = (y0, y1) => { let m = 0; for (let y = y0; y < y1; y++) m = Math.max(m, A(y)); return m; };

  // A layer is narrow if it's much smaller than the widest layer within reach
  // on BOTH sides (comparing with near neighbours misses the middle of a long
  // neck). Runs of narrow layers are necks; cut where a run ends, so a neck
  // stays with what's below it and the wider part above starts a section.
  const reach = minHeight * 2, runs = [];
  let run = null;
  for (let y = 1; y < top; y++) {
    const r = A(y) / Math.min(widest(y - reach, y) || Infinity, widest(y + 1, y + 1 + reach) || Infinity);
    if (A(y) && r <= narrow) { if (!run) run = { start: y, ratio: r }; run.end = y; run.ratio = Math.min(run.ratio, r); }
    else if (run) { runs.push(run); run = null; }
  }
  if (run) runs.push(run);
  const cuts = [];
  for (const r of runs.sort((a, b) => a.ratio - b.ratio)) {
    const y = r.end + 1;
    if (y < minHeight || y > top - minHeight) continue;
    if (cuts.length < maxSections - 1 && cuts.every((c) => Math.abs(c - y) >= minHeight)) cuts.push(y);
  }
  cuts.sort((a, b) => a - b);

  // a cut's place in the build order: the first index after which nothing is below it
  const suffixMin = []; for (let i = parts.length - 1, m = Infinity; i >= 0; i--) suffixMin[i] = m = Math.min(m, parts[i].y);
  const bounds = [0];
  for (const y of cuts) {
    const i = suffixMin.findIndex((v) => v >= y);
    if (i > bounds[bounds.length - 1] && i < parts.length) bounds.push(i);
  }
  bounds.push(parts.length);
  const out = [];
  for (let k = 0; k + 1 < bounds.length; k++) {
    const slice = parts.slice(bounds[k], bounds[k + 1]);
    out.push({ from: bounds[k], to: bounds[k + 1], base: Math.min(...slice.map((p) => p.y)), top: Math.max(...slice.map((p) => p.y + footprint(p).h)) });
  }
  // can the top section be built on its own, sitting on the table?
  const last = out[out.length - 1];
  if (out.length > 1) {
    const alone = parts.slice(last.from, last.to).map((p) => ({ ...p, y: p.y - last.base }));
    last.subassembly = check({ steps: [{ note: "top", parts: alone }] }).ok;
  }
  return out;
}

// Plain names for sections, bottom to top.
export function sectionNames(n) {
  return [[], ["The whole model"], ["Base", "Top"], ["Base", "Middle", "Top"], ["Base", "Lower body", "Upper body", "Top"]][n] || Array.from({ length: n }, (_, i) => `Section ${i + 1}`);
}
