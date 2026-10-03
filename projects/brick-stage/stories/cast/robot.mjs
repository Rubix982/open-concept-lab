// The robot from The Little Builder, with joints: both arms swing from the
// shoulder and the head turns on its neck. Facing the camera is z = 0.
import { model, P } from "../../lib/director.mjs";

const WHITE = 15, LGRAY = 71, DGRAY = 72, BLACK = 0, YELLOW = 14;

export const robot = (name, accent) => model(name, [
  P("3004", DGRAY, 0, 0, 0, 90), P("3004", DGRAY, 3, 0, 0, 90),   //  0  1  legs
  P("3020", DGRAY, 0, 3, 0),                                      //  2     hips
  P("3001", WHITE, 0, 4, 0), P("3001", WHITE, 0, 7, 0),           //  3  4  body
  P("3795", accent, -1, 10, 0),                                   //  5     shoulders
  P("3005", LGRAY, -1, 7, 0), P("3005", LGRAY, -1, 4, 0),         //  6  7  left arm, pushed up from below
  P("3005", LGRAY, 4, 7, 0), P("3005", LGRAY, 4, 4, 0),           //  8  9  right arm
  P("3024", DGRAY, -1, 3, 0), P("3024", DGRAY, 4, 3, 0),          // 10 11  hands
  P("3022", DGRAY, 1, 11, 0),                                     // 12     neck
  P("3020", WHITE, 0, 12, 0),                                     // 13     head plate
  P("3005", WHITE, 0, 13, 0), P("3004", BLACK, 1, 13, 0),         // 14 15  face: a black visor
  P("3005", WHITE, 3, 13, 0), P("3010", WHITE, 0, 13, 1),         // 16 17    between white cheeks
  P("3020", WHITE, 0, 16, 0),                                     // 18     cap ties the head together
  P("3024", accent, 2, 17, 1), P("3070b", YELLOW, 2, 18, 1),      // 19 20  antenna and its light
], {
  joints: {
    "left-arm": { parts: [6, 7, 10], pivot: [-0.5, 10, 0.5], axis: "x" },
    "right-arm": { parts: [8, 9, 11], pivot: [4.5, 10, 0.5], axis: "x" },
    head: { parts: [13, 14, 15, 16, 17, 18, 19, 20], pivot: [2, 12, 1], axis: "y" },
  },
});
