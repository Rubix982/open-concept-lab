// Capability 5: a three-plate bridge sags, then folds; the cake falls in.
import { story, model, P } from "../../lib/director.mjs";
const GREEN = 2, BROWN = 70, BLUE_T = 33, PINK = 29, WHITE = 15;
// a bank on each side, and a river of trans-blue tiles between them
// banks stand a brick above the water, so the bridge spans clear of it
const bank = (name) => model(name, [P("3031", GREEN, 0, 0, 0), P("3031", GREEN, 0, 0, 4), P("3020", GREEN, 0, 1, 2, 90), P("3020", GREEN, 2, 1, 2, 90),
  P("3001", GREEN, 0, 2, 0, 90), P("3001", GREEN, 2, 2, 0, 90), P("3001", GREEN, 0, 2, 4, 90), P("3001", GREEN, 2, 2, 4, 90), P("3031", GREEN, 0, 5, 2)]);
const river = model("river", [
  P("3029", 72, 0, 0, 0), P("3029", 72, 0, 0, 4),
  ...[0, 1, 6, 7].flatMap((z) => [0, 4, 8].map((x) => P("2431", BLUE_T, x, 1, z))),     // tiles along the edges
  ...Array.from({ length: 12 }, (_, x) => P("2431", BLUE_T, x, 1, 2, 90)),             // tiles across the seam hold the two plates together
]);
// the bridge: two planks resting on the banks, joined by a plate across the
// middle; each plank hinges where it meets its bank, and the joining plate
// goes with the left one when it breaks
const bridge = model("bridge", [P("3460", BROWN, 0, 0, 0), P("3460", BROWN, 8, 0, 0), P("3666", BROWN, 5, 1, 0)],
  { joints: { left: { parts: [0, 2], pivot: [2, 0.5, 0.5], axis: "z" }, right: { parts: [1], pivot: [14, 0.5, 0.5], axis: "z" } } });
const cake = model("cake", [P("3941", PINK, 0, 0, 0), P("4032b", WHITE, 0, 3, 0)]);

export default story({ title: "Capability: joints and folding", poster: 7500 }, (s) => {
  s.shot({ at: [10, 5, 4], az: 0, el: 14, dist: 32 }, 0);
  s.mood("midday", { dur: 10 });
  s.build(bank("left bank"), { as: "left", at: [0, 0, 0], from: "below", stagger: 20, dur: 300 });
  s.build(bank("right bank"), { as: "right", at: [16, 0, 0], from: "below", stagger: 20, dur: 300 });
  s.build(river, { as: "river", at: [4, 0, 0], from: "below", stagger: 8, dur: 300 });
  s.build(bridge, { as: "bridge", at: [2, 6, 3.5], from: "above", stagger: 200, dur: 400 });
  s.build(cake, { as: "cake", at: [9, 8, 3], from: "above", dur: 400 });
  // when it folds, the planks grind on the banks they're hinged to and drop into the water
  s.contact("bridge", "left"); s.contact("bridge", "right"); s.contact("bridge", "river");
  s.caption("the middle sags with a creak");
  s.sfx("creak");
  s.together((g) => { g.pose("bridge", "left", -5, { dur: 900 }); g.pose("bridge", "right", 5, { dur: 900 }); });
  s.caption("then folds, quietly, almost politely");
  s.together((g) => {
    g.pose("bridge", "left", -50, { dur: 1100 }); g.pose("bridge", "right", 50, { dur: 1100 });
    g.move("cake", [9, 2, 3], { dur: 1400, arc: 3, spin: [450, 0, 0] });     // lands on its side
  });
  s.sfx("tik");
  s.wait(1200);
});
