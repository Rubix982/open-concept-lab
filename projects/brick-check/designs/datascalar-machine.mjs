// A tiny DataScalar machine: four chips on a green board, each with its own
// memory slice behind it, all tapped onto one yellow shared bus in front.
// Grid: x, z in studs (min corner), y in plates above the table.
const GREEN = 2, BLACK = 0, LBG = 71, YELLOW = 14;
const SLICE = [4, 1, 25, 15]; // memory colours: red, blue, orange, white
const P = (part, color, x, y, z, rot = 0) => ({ part, color, x, y, z, rot });
const CHIP_X = [1, 7, 13, 19];

const bottom = [];
for (const z of [0, 4, 8]) for (const x of [0, 12]) bottom.push(P("3029", GREEN, x, 0, z));

// Seams on the top layer (x 6, 18; z 2, 6, 10) never line up with the
// bottom layer's (x 12; z 4, 8), so every bottom plate is bridged.
const top = [];
for (const [z, deep] of [[0, false], [2, true], [6, true], [10, false]]) {
  top.push(P(deep ? "3032" : "3795", GREEN, 0, 1, z));
  top.push(P(deep ? "3029" : "2445", GREEN, 6, 1, z));
  top.push(P(deep ? "3032" : "3795", GREEN, 18, 1, z));
}

const bus = [0, 4, 8, 12, 16, 20].map((x) => P("2431", YELLOW, x, 2, 1));
const traces = CHIP_X.map((x) => P("3069b", YELLOW, x + 1, 2, 2));

const chip = (x) => [
  P("3001", BLACK, x, 2, 3), P("3001", BLACK, x, 2, 5),          // body
  P("3020", BLACK, x, 5, 3, 90), P("3020", BLACK, x + 2, 5, 3, 90), // lid ties the body together
  P("3068b", LBG, x + 1, 6, 4),                                   // the die
  P("3069b", BLACK, x, 6, 3), P("3069b", BLACK, x + 2, 6, 3),
  P("3069b", BLACK, x, 6, 6), P("3069b", BLACK, x + 2, 6, 6),
  P("3069b", BLACK, x, 6, 4, 90), P("3069b", BLACK, x + 3, 6, 4, 90),
];

const memory = (x, color) => [8, 10].flatMap((z) => [
  P("3010", color, x, 2, z), P("3710", color, x, 5, z), P("2431", color, x, 6, z),
]);

export default {
  name: "datascalar-machine",
  title: "Tiny DataScalar Machine",
  steps: [
    { note: "Lay out the base: six 4×12 plates. They don't hold together yet.", parts: bottom },
    { note: "Lock the base: the top layer's seams cross the bottom layer's, so it's now one board.", parts: top },
    { note: "The shared bus, and a trace from each chip's spot down to it.", parts: [...bus, ...traces] },
    ...CHIP_X.map((x, k) => ({ note: `Chip ${k}: two bricks, a lid that ties them, and a smooth top with its die.`, parts: chip(x) })),
    ...CHIP_X.map((x, k) => ({ note: `Chip ${k}'s memory slice — the only data this chip owns.`, parts: memory(x, SLICE[k]) })),
  ],
};
