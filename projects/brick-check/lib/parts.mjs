// Parts brick-check knows about. Dimensions are in studs (w along LDraw X,
// d along LDraw Z) and plate heights (a brick is 3 plates). Each entry was
// checked against the part's real geometry from the official LDraw library —
// see tools/ldraw-bbox.mjs and test/catalog.test.mjs.
export const PARTS = {
  "3001":  { name: "Brick 2 x 4",       kind: "brick", w: 4,  d: 2, h: 3 },
  "3003":  { name: "Brick 2 x 2",       kind: "brick", w: 2,  d: 2, h: 3 },
  "3004":  { name: "Brick 1 x 2",       kind: "brick", w: 2,  d: 1, h: 3 },
  "3010":  { name: "Brick 1 x 4",       kind: "brick", w: 4,  d: 1, h: 3 },
  "3005":  { name: "Brick 1 x 1",       kind: "brick", w: 1,  d: 1, h: 3 },
  "3009":  { name: "Brick 1 x 6",       kind: "brick", w: 6,  d: 1, h: 3 },
  "3024":  { name: "Plate 1 x 1",       kind: "plate", w: 1,  d: 1, h: 1 },
  "3023b": { name: "Plate 1 x 2",       kind: "plate", w: 2,  d: 1, h: 1, bl: "3023" },
  "3022":  { name: "Plate 2 x 2",       kind: "plate", w: 2,  d: 2, h: 1 },
  "3034":  { name: "Plate 2 x 8",       kind: "plate", w: 8,  d: 2, h: 1 },
  "3070b": { name: "Tile 1 x 1",        kind: "tile",  w: 1,  d: 1, h: 1 },
  "3020":  { name: "Plate 2 x 4",       kind: "plate", w: 4,  d: 2, h: 1 },
  "3710":  { name: "Plate 1 x 4",       kind: "plate", w: 4,  d: 1, h: 1 },
  "3795":  { name: "Plate 2 x 6",       kind: "plate", w: 6,  d: 2, h: 1 },
  "2445":  { name: "Plate 2 x 12",      kind: "plate", w: 12, d: 2, h: 1 },
  "3031":  { name: "Plate 4 x 4",       kind: "plate", w: 4,  d: 4, h: 1 },
  "3032":  { name: "Plate 4 x 6",       kind: "plate", w: 6,  d: 4, h: 1 },
  "3030":  { name: "Plate 4 x 10",      kind: "plate", w: 10, d: 4, h: 1 },
  "3029":  { name: "Plate 4 x 12",      kind: "plate", w: 12, d: 4, h: 1 },
  "3069b": { name: "Tile 1 x 2",        kind: "tile",  w: 2,  d: 1, h: 1 },
  "2431":  { name: "Tile 1 x 4",        kind: "tile",  w: 4,  d: 1, h: 1 },
  "3068b": { name: "Tile 2 x 2",        kind: "tile",  w: 2,  d: 2, h: 1 },
};

// `bl` is the BrickLink item id where it differs from the LDraw file name.

// LDraw colour code -> [name, BrickLink colour id, hex for the viewer]
export const COLORS = {
  0:  ["Black", 11, "#1b2a34"],
  1:  ["Blue", 7, "#1e5aa8"],
  2:  ["Green", 6, "#00852b"],
  4:  ["Red", 5, "#b40000"],
  14: ["Yellow", 3, "#fac80a"],
  15: ["White", 1, "#f4f4f4"],
  25: ["Orange", 4, "#d67923"],
  71: ["Light Bluish Gray", 86, "#a0a5a9"],
  72: ["Dark Bluish Gray", 85, "#6c6e68"],
  10: ["Bright Green", 36, "#58ab41"],
  19: ["Tan", 2, "#e4cd9e"],
  27: ["Lime", 34, "#bbe90b"],
  70: ["Reddish Brown", 88, "#5f3109"],
};

// Footprint after rotation about the vertical axis (0 or 90 degrees).
export function footprint(p) {
  const s = PARTS[p.part];
  return p.rot === 90 ? { w: s.d, d: s.w, h: s.h } : { w: s.w, d: s.d, h: s.h };
}
