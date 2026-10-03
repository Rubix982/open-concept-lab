// __TITLE__ — a brick-stage story. Run `node dev.mjs __NAME__` and edit away:
// every save rebuilds and the page reopens where you were watching.
import { story, model, P } from "../lib/director.mjs";
import { robot } from "./cast/robot.mjs";

// Colours are LDraw codes: 15 white, 0 black, 4 red, 1 blue, 14 yellow,
// 2 green, 25 orange, 71 light grey, 72 dark grey (see brick-check/lib/parts.mjs).
const RED = 4, WHITE = 15, ORANGE = 25;

// A model is its parts in build order: P(part, colour, x, y, z, rotation).
// x and z count studs, y counts plates (a brick is 3 plates tall).
const tower = model("tower", [
  P("3003", WHITE, 0, 0, 0),     // a 2x2 brick on the ground
  P("3003", RED, 0, 3, 0),       // another on top of it
  P("3039", WHITE, 0, 6, 0),     // a slope to finish
]);

export default story({ title: "__TITLE__", drift: 0.5 }, (s) => {
  s.shot({ at: [0, 8, 0], az: 20, el: 14, dist: 34 }, 0);
  s.card("CHAPTER ONE", "__TITLE__");

  s.build(robot("hero", ORANGE), { at: [-8, 0, 0], from: "above" });
  s.say("hero", "Let's build something.");

  s.caption("Build a tower.", "STEP 01");
  s.build(tower, { at: [2, 0, 0], from: "everywhere" });
  s.emit("sparkles", { on: "tower" });
  s.pose("hero", "right-arm", 120);
  s.wait(1500);
});
