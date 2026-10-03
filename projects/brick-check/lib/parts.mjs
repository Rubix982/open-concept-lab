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
  "3622":  { name: "Brick 1 x 3",       kind: "brick", w: 3,  d: 1, h: 3 },
  "3008":  { name: "Brick 1 x 8",       kind: "brick", w: 8,  d: 1, h: 3 },
  "3002":  { name: "Brick 2 x 3",       kind: "brick", w: 3,  d: 2, h: 3 },
  "2456":  { name: "Brick 2 x 6",       kind: "brick", w: 6,  d: 2, h: 3 },
  "3623":  { name: "Plate 1 x 3",       kind: "plate", w: 3,  d: 1, h: 1 },
  "3666":  { name: "Plate 1 x 6",       kind: "plate", w: 6,  d: 1, h: 1 },
  "3460":  { name: "Plate 1 x 8",       kind: "plate", w: 8,  d: 1, h: 1 },
  "3021":  { name: "Plate 2 x 3",       kind: "plate", w: 3,  d: 2, h: 1 },
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
  // Not boxes: drawn from their real LDraw geometry (`mesh`). A slope's studs
  // are only on its high back row, and its origin sits 10 LDU off-centre.
  "3039":  { name: "Slope 45 2 x 2",    kind: "brick", w: 2,  d: 2, h: 3, mesh: true, studs: [[0, 1], [1, 1]], center: [0, -10] },
  "3040b": { name: "Slope 45 2 x 1",    kind: "brick", w: 1,  d: 2, h: 3, mesh: true, studs: [[0, 1]], center: [0, -10], bl: "3040" },
  "3062b": { name: "Round Brick 1 x 1", kind: "brick", w: 1,  d: 1, h: 3, mesh: true },
  "6141":  { name: "Round Plate 1 x 1", kind: "plate", w: 1,  d: 1, h: 1, mesh: true, bl: "4073" },
  "98138": { name: "Round Tile 1 x 1",  kind: "tile",  w: 1,  d: 1, h: 1, mesh: true },
};

// `bl` is the BrickLink item id where it differs from the LDraw file name.
// `studs` lists the top cells that carry a stud (default: all, none for a
// tile); `center` is the footprint centre in the part's own LDU frame
// (default: the origin).

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
  5:  ["Dark Pink", 47, "#c870a0"],
  29: ["Bright Pink", 104, "#e4adc8"],
  // LEGO's common current solid colours, for shapes sampled from scans and
  // models. Code = LDraw code = Rebrickable id (checked against both in
  // test/catalog.test.mjs); RGB from Rebrickable; BrickLink ids from
  // BrickLink's colour guide.
  3:   ["Dark Turquoise", 39, "#008f9b"],
  26:  ["Magenta", 71, "#923978"],
  28:  ["Dark Tan", 69, "#958a73"],
  30:  ["Medium Lavender", 157, "#ac78ba"],
  73:  ["Medium Blue", 42, "#5a93db"],
  78:  ["Light Nougat", 90, "#f6d7b3"],
  84:  ["Medium Nougat", 150, "#aa7d55"],
  85:  ["Dark Purple", 89, "#3f3691"],
  191: ["Bright Light Orange", 110, "#f8bb3d"],
  212: ["Bright Light Blue", 105, "#9fc3e9"],
  226: ["Bright Light Yellow", 103, "#fff03a"],
  272: ["Dark Blue", 63, "#0a3463"],
  288: ["Dark Green", 80, "#184632"],
  308: ["Dark Brown", 120, "#352100"],
  320: ["Dark Red", 59, "#720e0f"],
  321: ["Dark Azure", 153, "#078bc9"],
  322: ["Medium Azure", 156, "#36aebf"],
  323: ["Light Aqua", 152, "#adc3c0"],
  378: ["Sand Green", 48, "#a0bcac"],
  379: ["Sand Blue", 55, "#6074a1"],
  484: ["Dark Orange", 68, "#a95500"],
};

export const ROTATIONS = [0, 90, 180, 270];

// Footprint after rotation about the vertical axis.
export function footprint(p) {
  const s = PARTS[p.part];
  return p.rot === 90 || p.rot === 270 ? { w: s.d, d: s.w, h: s.h } : { w: s.w, d: s.d, h: s.h };
}

// A local cell (i along the part's own x, k along its z) in the rotated
// footprint, matching the LDraw rotation matrices in ldraw.mjs.
export function rotateCell([i, k], s, rot) {
  if (rot === 90) return [k, s.w - 1 - i];
  if (rot === 180) return [s.w - 1 - i, s.d - 1 - k];
  if (rot === 270) return [s.d - 1 - k, i];
  return [i, k];
}

// Grid cells (x, z) on top of a placed part that carry a stud.
export function topStuds(p) {
  const s = PARTS[p.part];
  let cells = s.studs;
  if (!cells) {
    if (s.kind === "tile") return [];
    cells = [];
    for (let i = 0; i < s.w; i++) for (let k = 0; k < s.d; k++) cells.push([i, k]);
  }
  return cells.map((c) => rotateCell(c, s, p.rot)).map(([i, k]) => [p.x + i, p.z + k]);
}
