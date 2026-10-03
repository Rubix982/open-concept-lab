// The Little Builder — the first brick-stage story.
// Every model below is checked by brick-check: the order its parts appear in
// is an order you could build it in with real bricks.
import { story, model, P } from "../lib/director.mjs";
import { robot } from "./cast/robot.mjs";

const WHITE = 15, LGRAY = 71, DGRAY = 72, ORANGE = 25, BLUE = 1;

// The robot lives in cast/robot.mjs, so other stories can use it too.

// One room: three courses of white wall with a door, a stepped grey roof.
const room = (x0) => [
  P("3004", WHITE, x0 + 0, 1, 0), P("3004", WHITE, x0 + 4, 1, 0),
  P("3009", WHITE, x0 + 0, 1, 5),
  P("3010", WHITE, x0 + 0, 1, 1, 90), P("3010", WHITE, x0 + 5, 1, 1, 90),
  P("3009", WHITE, x0 + 0, 4, 0, 90), P("3009", WHITE, x0 + 5, 4, 0, 90),
  P("3005", ORANGE, x0 + 1, 4, 0), P("3005", ORANGE, x0 + 4, 4, 0),
  P("3010", WHITE, x0 + 1, 4, 5),
  P("3009", WHITE, x0 + 0, 7, 0),
  P("3010", WHITE, x0 + 0, 7, 1, 90), P("3010", WHITE, x0 + 5, 7, 1, 90),
  P("3009", WHITE, x0 + 0, 7, 5),
  P("3032", DGRAY, x0 + 0, 10, 0), P("3795", DGRAY, x0 + 0, 10, 4),
  P("3031", DGRAY, x0 + 1, 11, 1),
  P("3005", ORANGE, x0 + 5, 11, 0),                              // chimney
  P("3022", DGRAY, x0 + 2, 12, 2),
  P("3068b", ORANGE, x0 + 2, 13, 2),
];
const base = [P("3029", LGRAY, 0, 0, 0), P("2445", LGRAY, 0, 0, 4)];
const shelter = model("shelter", [...base, ...room(0)]);
const extension = model("extension", room(6));

export default story({ title: "The Little Builder", poster: 28600, drift: 1.2 }, (s) => {
  s.shot({ at: [-9, 8, -4], az: 28, el: 16, dist: 34 }, 0);
  s.card("PROCEDURE 01", "Assemble the unit.");

  s.shot({ at: [-9, 7, -4], az: 18, el: 12, dist: 22 }, 4000);
  s.build(robot("unit", ORANGE), { as: "unit", at: [-11, 0, -4], from: "everywhere" });
  s.caption("Unit is operational.");
  s.highlight("unit", { dur: 1800 });
  s.callout("Visor", { on: "unit", offset: [0, -4, -1], dur: 2200 });
  s.move("unit", [-11, 0, -4], { dur: 900, hop: 2.5, steps: 2 });
  s.wait(900);

  s.caption("The unit assembles a shelter.", "PROCEDURE 02");
  s.together((g) => {
    g.shot({ at: [-1, 6, -2], az: 24, el: 20, dist: 38 }, 2200);
    g.move("unit", [-13, 0, -7], { dur: 1600 });
  });
  s.turn("unit", 35, { dur: 600 });
  s.build(shelter, { as: "shelter", at: [0, 0, 0], from: "above", stagger: 110 });
  s.shot({ at: [3, 6, 1], az: 12, el: 10, dist: 24 }, 1800);
  s.caption("Shelter rated for one.");
  s.wait(2600);

  s.caption("The unit assembles a second unit.", "PROCEDURE 03");
  s.shot({ at: [-8, 7, -6], az: -14, el: 12, dist: 26 }, 1800);
  s.build(robot("unit-2", BLUE), { as: "unit-2", at: [-6, 0, -8], from: "everywhere", stagger: 110 });
  s.move("unit-2", [-6, 0, -8], { dur: 900, hop: 2.5, steps: 2 });
  // they look at each other …
  s.together((g) => { g.turn("unit", 10, { dur: 500 }); g.turn("unit-2", -45, { dur: 700 }); });
  s.wait(700);
  // … then both look over at the shelter
  s.together((g) => { g.turn("unit", -10, { dur: 700 }); g.turn("unit-2", 80, { dur: 900 }); });
  s.caption("Shelter rated for one.");
  s.shot({ at: [0, 6, -3], az: 10, el: 14, dist: 36 }, 1800);
  s.wait(2400);

  s.caption("Revise the shelter.", "PROCEDURE 04");
  s.together((g) => {
    g.shot({ at: [2, 6, -2], az: -20, el: 18, dist: 40 }, 3500);
    g.build(extension, { onto: "shelter", from: "right", stagger: 100 });
  });
  s.caption("Shelter rated for two.");
  s.together((g) => {
    g.move("unit", [-13, 0, -7], { dur: 900, hop: 2.5, steps: 2 });
    g.move("unit-2", [-6, 0, -8], { dur: 900, hop: 2.5, steps: 2 });
  });
  s.orbit(-35, { dur: 2600 });
  s.wait(2600);
  s.clearCaption();
  s.card("END OF PROCEDURE", "Every model in this story", { sub: "can be built with real bricks.", dur: 3600 });
});
