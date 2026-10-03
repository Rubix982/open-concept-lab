// Export to LDraw (.ldr), which BrickLink Studio, LDView and LPub3D all open.
// Grid -> LDU: 1 stud = 20 LDU, 1 plate = 8 LDU, -Y is up, part origin is the
// centre of its top face.
import { PARTS, COLORS, footprint } from "./parts.mjs";

// Rotations about the vertical axis, as LDraw 3x3 matrices (row-major).
export const MATRIX = {
  0: [1, 0, 0, 0, 1, 0, 0, 0, 1],
  90: [0, 0, 1, 0, 1, 0, -1, 0, 0],
  180: [-1, 0, 0, 0, 1, 0, 0, 0, -1],
  270: [0, 0, -1, 0, 1, 0, 1, 0, 0],
};

export function toLDR(design) {
  const lines = [`0 ${design.title}`, `0 Name: ${design.name}.ldr`, `0 Author: brick-check`, ``];
  design.steps.forEach((s) => {
    // Older LDraw tools expect ASCII.
    lines.push(`0 // ${s.note.replace(/×/g, "x").replace(/[—–]/g, "-").replace(/[‘’]/g, "'").replace(/[^\x20-\x7e]/g, "")}`);
    for (const p of s.parts) {
      const f = footprint(p), M = MATRIX[p.rot], [cx, cz] = PARTS[p.part].center || [0, 0];
      // The footprint centre lands on the grid; the part's own origin may sit off it.
      const X = (p.x + f.w / 2) * 20 - (M[0] * cx + M[2] * cz), Z = (p.z + f.d / 2) * 20 - (M[6] * cx + M[8] * cz), Y = -(p.y + f.h) * 8;
      const R = M.join(" ");
      lines.push(`1 ${p.color} ${X} ${Y} ${Z} ${R} ${p.part}.dat`);
    }
    lines.push(`0 STEP`);
  });
  return lines.join("\n") + "\n";
}

export function partsList(design) {
  const counts = new Map();
  for (const s of design.steps) for (const p of s.parts) {
    const k = p.part + "|" + p.color;
    counts.set(k, (counts.get(k) || 0) + 1);
  }
  return [...counts].map(([k, qty]) => {
    const [part, color] = k.split("|");
    return { part, name: PARTS[part].name, color: +color, colorName: COLORS[color][0], blColor: COLORS[color][1], qty };
  }).sort((a, b) => b.qty - a.qty || a.part.localeCompare(b.part));
}

// BrickLink "wanted list" XML — upload it, nothing is ordered.
export function toBrickLinkXML(design) {
  const items = partsList(design).map((r) =>
    `  <ITEM><ITEMTYPE>P</ITEMTYPE><ITEMID>${PARTS[r.part].bl || r.part}</ITEMID><COLOR>${r.blColor}</COLOR><MINQTY>${r.qty}</MINQTY><CONDITION>X</CONDITION></ITEM>`);
  return `<INVENTORY>\n${items.join("\n")}\n</INVENTORY>\n`;
}
