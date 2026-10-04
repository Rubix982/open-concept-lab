// The presenter: a LEGO minifigure host for explainers.
//
//   s.presenter("host", { x: 60, y: 380, w: 540, h: 680, look: { torso: 1, hat: "cap" } });
//   s.walkIn("host");
//   s.present("host", "wave", { dur: 1800 });
//   s.present("host", "point", { at: { obj: "bars", at: "bar0" }, dur: 2400 });
//   s.face("host", "grin");
//   s.walkOut("host");
//
// Every gesture is a 0..1 strength tweened on the stage object's props; the
// player turns strengths into joint angles as a pure function of time, so a
// render lands on the same pose as the live page. Gestures can overlap (point
// while talking, nod while waving).

const GESTURES = ["wave", "point", "talk", "shrug", "nod", "think"];

export function install(s, { add, span, need, tl }) {
  const tween = (id, prop, to, t0, dur, ease = "inout") =>
    tl.tweens.push({ id, prop, to, t0, t1: t0 + Math.max(1, dur), ease: typeof to === "number" ? ease : "step" });

  /** A minifig host on a little plate, in its own 3D stage at (x, y, w, h).
   *  look: minifig look (torso, legs, print, hat, hatColor, face, beard...).
   *  side: the side it walks in from and out to ("left" | "right").
   *  standing: true to start on the plate; otherwise it waits offstage for walkIn().
   *  talkOnNarration: bob and gesture while a caption is on screen (default true). */
  const sides = {};
  s.presenter = (id, o = {}) => {
    sides[id] = o.side || "left";
    const look = { torso: 1, legs: 72, print: "sweater", hat: "cap", hatColor: 4, face: "smile", ...(o.look || {}) };
    return add(id, "stage3d", {
      kind: "presenter", x: 60, y: 380, w: 540, h: 680, plate: 72, facing: 0, talkOnNarration: true, pointAt: null,
      ...Object.fromEntries(GESTURES.map((g) => [g, 0])),
      ...o,
      look, face: o.face || look.face, side: sides[id],
      walk: o.standing ? 1 : 0, // offstage until walkIn(), unless it starts standing
    }, o.dur ?? 300);
  };

  /** A gesture for dur ms: "wave" | "point" | "talk" | "shrug" | "nod" | "think".
   *  point takes at: { obj, at } (an anchor on another stage) or { x, y } (a frame point). */
  s.present = (id, gesture, o = {}) => {
    need(id);
    if (!GESTURES.includes(gesture)) throw new Error(`present: no gesture "${gesture}" (have ${GESTURES.join(", ")})`);
    const dur = o.dur ?? 1800, ease = Math.min(400, dur / 3), t0 = s.t;
    if (gesture === "point") {
      if (!o.at) throw new Error("present(…, \"point\") needs at: { obj, at } or { x, y }");
      tween(id, "pointAt", o.at, t0, 1);
    }
    tween(id, gesture, o.strength ?? 1, t0, ease);
    tween(id, gesture, 0, t0 + dur - ease, ease);
    if (o.face) tween(id, "face", o.face, t0, 1);
    span(dur);
    return s;
  };

  /** Change the face: smile, grin, neutral, sad, worried, surprised, determined, deadpan. */
  s.face = (id, expr) => { need(id); tween(id, "face", expr, s.t, 1); return s; };

  /** Walk onto the plate from the side, then turn to the camera. */
  s.walkIn = (id, o = {}) => {
    need(id);
    const dur = o.dur ?? 2200, t0 = s.t, side = (sides[id] = o.side || sides[id]);
    tween(id, "side", side, t0, 1);
    tween(id, "walk", 0, t0, 1);
    tween(id, "facing", side === "right" ? -90 : 90, t0, 1);
    tween(id, "walk", 1, t0, dur - 350, "linear");
    tween(id, "facing", 0, t0 + dur - 380, 380);
    span(dur);
    return s;
  };

  /** Turn and walk off the way it came. */
  s.walkOut = (id, o = {}) => {
    need(id);
    const dur = o.dur ?? 2000, t0 = s.t, side = (sides[id] = o.side || sides[id]);
    tween(id, "side", side, t0, 1);
    tween(id, "facing", side === "right" ? 90 : -90, t0, 320);
    tween(id, "walk", 0, t0 + 320, dur - 320, "linear");
    span(dur);
    return s;
  };
}
