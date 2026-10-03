// The director: a story file calls these methods in order, and the director
// lays every action onto one timeline. The player then evaluates that
// timeline as a pure function of time, so scrubbing is exact and playback is
// smooth however fast the machine is.
//
// Units: studs across, plates up (a brick is 3 plates). Times in ms.
import { check } from "../../brick-check/lib/check.mjs";
import { footprint, PARTS } from "../../brick-check/lib/parts.mjs";

export const P = (part, color, x, y, z, rot = 0) => ({ part, color, x, y, z, rot });

// A model is a list of parts in build order. That order is what the camera
// sees, and brick-check verifies it can really be built that way.
//
// Joints let a character move part of itself: name a group of part indices,
// a pivot [x, y, z] (studs, plates, studs) and an axis ("x" swings forward
// and back, "z" sideways, "y" twists). The model is checked in its rest pose;
// a joint is only physically real if the build uses a hinge there.
export function model(name, parts, { joints = {} } = {}) {
  for (const [j, spec] of Object.entries(joints)) {
    if (!spec.parts?.length || !spec.pivot) throw new Error(`joint "${j}" of "${name}" needs parts and a pivot`);
    for (const i of spec.parts) if (!parts[i]) throw new Error(`joint "${j}" of "${name}" names part ${i}, which doesn't exist`);
  }
  return { name, parts, joints };
}

function rng(seed) { let s = seed >>> 0 || 1; return () => (s = (s * 16807) % 2147483647) / 2147483647; }

const DIRECTIONS = {
  above: (r) => [(r() - 0.5) * 2, 14 + r() * 6, (r() - 0.5) * 2],
  below: (r) => [(r() - 0.5) * 2, -10, (r() - 0.5) * 2],
  left: (r) => [-18 - r() * 4, 3 + r() * 3, (r() - 0.5) * 3],
  right: (r) => [18 + r() * 4, 3 + r() * 3, (r() - 0.5) * 3],
  front: (r) => [(r() - 0.5) * 3, 3 + r() * 3, 16 + r() * 4],
  everywhere: (r) => {
    const a = r() * Math.PI * 2, up = 0.25 + r() * 0.75, d = 14 + r() * 6;
    return [Math.cos(a) * d * (1 - up * 0.5), up * d, Math.sin(a) * d * (1 - up * 0.5)];
  },
};

export class Director {
  constructor(meta) {
    this.meta = meta;
    this.t = 0;
    this.actors = {};      // id -> { model, parts: [...], moves: [...] }
    this.camera = [];      // { t, dur, shot }
    this.captions = [];    // { t, kicker, text }
    this.cards = [];       // { t, dur, kicker, title, sub }
    this.callouts = [];    // { t, dur, text, on, at, offset }
    this.bubbles = [];     // { t, dur, actor, text }
    this.emitters = [];    // { t, dur, kind, on, at, offset, count, seed }
    this.moods = [];       // { t, dur, name }
    this.letterboxes = []; // { t, on, dur }
    this.fades = [];       // { t, on, dur, color }
    this.musicCues = [];   // { t, name }
    this.models = {};
    this.props = {};       // buttons, doors, signal lines
    this.roomSpec = null;
    this._group = null;
    this._seed = 1;
  }
  _advance(end) {
    if (this._group) this._group.end = Math.max(this._group.end, end);
    else this.t = end;
  }

  // A full-screen card. Advances time.
  card(kicker, title, { sub = "", dur = 2800 } = {}) {
    this.cards.push({ t: this.t, dur, kicker, title, sub });
    this._advance(this.t + dur);
    return this;
  }
  // A caption that stays until the next one. Doesn't advance time.
  caption(text, kicker = "") { this.captions.push({ t: this.t, kicker, text }); return this; }
  clearCaption() { return this.caption("", ""); }
  // Ease the camera to a shot. Doesn't advance time.
  // shot: { at: [x, y, z] in studs, az, el (degrees), dist (studs) }
  shot(shot, dur = 1600) { this.camera.push({ t: this.t, dur, shot }); this._lastShot = shot; return this; }
  // Keep the camera on an actor as it moves. Doesn't advance time.
  follow(actor, { az, el, dist, offset, dur = 1400 } = {}) {
    const last = this._lastShot || { az: 20, el: 18, dist: 30 };
    return this.shot({ follow: actor, offset, az: az ?? last.az, el: el ?? last.el, dist: dist ?? last.dist }, dur);
  }
  // Swing the camera around the current target by `deg`. Doesn't advance time.
  orbit(deg, { dur = 3000, el, dist } = {}) {
    const last = this._lastShot;
    if (!last) throw new Error("orbit() needs a shot() or follow() before it");
    return this.shot({ ...last, az: last.az + deg, el: el ?? last.el, dist: dist ?? last.dist }, dur);
  }
  // Make an actor glow, to draw the eye. Doesn't advance time.
  highlight(actor, { dur = 1600, color = "#ff8a2a" } = {}) {
    const a = this.actors[actor];
    if (!a) throw new Error(`no actor "${actor}"`);
    (a.highlights ||= []).push({ t: this.t, dur, color });
    return this;
  }
  // A label with a leader line, pinned to an actor (on) or a point (at).
  // Doesn't advance time.
  callout(text, { on, at, offset = [0, 0, 0], dur = 2600 } = {}) {
    if (on && !this.actors[on]) throw new Error(`no actor "${on}"`);
    if (!on && !at) throw new Error("callout() needs `on` or `at`");
    this.callouts.push({ t: this.t, dur, text, on, at, offset });
    return this;
  }
  wait(ms) { this._advance(this.t + ms); return this; }

  // Assemble a model at a position, piece by piece. Advances time.
  // With `onto`, the parts are added to an actor that is already built (same
  // coordinates, moves with it), and the combined model is what gets checked.
  build(m, { as = m.name, at = [0, 0, 0], from = "everywhere", stagger = 130, dur = 750, seed, onto } = {}) {
    const host = onto && this.actors[onto];
    if (onto && !host) throw new Error(`no actor "${onto}" to build onto`);
    if (!onto && this.actors[as]) throw new Error(`an actor called "${as}" already exists`);
    const checkedAs = host ? `${host.checkedAs} + ${m.name}` : m.name;
    const allParts = host ? [...host.modelParts, ...m.parts] : m.parts;
    if (host) delete this.models[host.checkedAs];
    this.models[checkedAs] = { name: checkedAs, parts: allParts };
    const r = rng(seed ?? this._seed++ * 7919);
    const dirOf = DIRECTIONS[from];
    if (!dirOf) throw new Error(`unknown direction "${from}"`);
    const parts = m.parts.map((p, i) => {
      const f = footprint(p);
      return {
        ...p, ...f, kind: PARTS[p.part].kind, mesh: !!PARTS[p.part].mesh,
        t0: this.t + i * stagger, dur,
        from: dirOf(r), spin: [(r() - 0.5) * 6, (r() - 0.5) * 8, (r() - 0.5) * 6],
      };
    });
    const shift = host ? host.parts.length : 0;
    const joints = Object.fromEntries(Object.entries(m.joints || {}).map(([j, spec]) => [j, { ...spec, parts: spec.parts.map((i) => i + shift) }]));
    if (host) { host.parts.push(...parts); host.modelParts = allParts; host.checkedAs = checkedAs; Object.assign(host.joints, joints); }
    else this.actors[as] = { model: m.name, checkedAs, modelParts: allParts, parts, moves: [{ t: -1, dur: 0, to: at, hop: 0 }], turns: [], joints, poses: [] };
    this._advance(this.t + (m.parts.length - 1) * stagger + dur);
    return this;
  }

  // Walk (or glide) an actor to a new position. Advances time.
  move(as, to, { dur = 1800, hop, steps } = {}) {
    const a = this.actors[as];
    if (!a) throw new Error(`no actor "${as}"`);
    if (a.kind === "figure") { hop ??= 0.25; steps ??= Math.max(2, Math.round(dur / 330)); }
    hop ??= 0.6;
    a.moves.push({ t: this.t, dur, to, hop, steps: steps ?? Math.max(2, Math.round(dur / 300)) });
    this._advance(this.t + dur);
    return this;
  }

  // Swing a named joint to an angle (degrees, absolute: 0 is the rest pose).
  // Advances time.
  pose(as, joint, deg, { dur = 600 } = {}) {
    const a = this.actors[as];
    if (!a) throw new Error(`no actor "${as}"`);
    if (!a.joints?.[joint]) throw new Error(`"${as}" has no joint "${joint}"`);
    a.poses.push({ t: this.t, dur, joint, deg });
    this._advance(this.t + dur);
    return this;
  }

  // A speech bubble over an actor. Advances time while it's on screen.
  say(as, text, { dur = 2400 } = {}) {
    if (!this.actors[as]) throw new Error(`no actor "${as}"`);
    this.bubbles.push({ t: this.t, dur, actor: as, text });
    this._advance(this.t + dur);
    return this;
  }
  // Particles rising from an actor or a point: "hearts", "sparkles" or
  // "confetti". Doesn't advance time.
  emit(kind, { on, at, offset = [0, 0, 0], count = 14, dur = 2600 } = {}) {
    if (!["hearts", "sparkles", "confetti"].includes(kind)) throw new Error(`unknown particles "${kind}"`);
    if (on && !this.actors[on]) throw new Error(`no actor "${on}"`);
    this.emitters.push({ t: this.t, dur, kind, on, at, offset, count, seed: this.emitters.length * 977 + 13 });
    return this;
  }
  // Ease the light to a mood: "day", "sunset" or "night". Doesn't advance time.
  mood(name, { dur = 2500 } = {}) {
    if (!["day", "sunset", "night"].includes(name)) throw new Error(`unknown mood "${name}"`);
    this.moods.push({ t: this.t, dur, name });
    return this;
  }
  // Cinema bars top and bottom. Doesn't advance time.
  letterbox(on = true, { dur = 900 } = {}) { this.letterboxes.push({ t: this.t, on, dur }); return this; }
  // Fade the picture out to a colour, or back in. Advances time.
  fadeOut({ dur = 1200, color = "#000" } = {}) { this.fades.push({ t: this.t, on: true, dur, color }); this._advance(this.t + dur); return this; }
  fadeIn({ dur = 1200 } = {}) { this.fades.push({ t: this.t, on: false, dur }); this._advance(this.t + dur); return this; }
  // A soft generated chord pad ("romance", "wonder"), or null to stop it.
  // Doesn't advance time.
  music(name) {
    if (name && !["romance", "wonder"].includes(name)) throw new Error(`unknown music "${name}"`);
    this.musicCues.push({ t: this.t, name });
    return this;
  }

  // Turn an actor in place by `deg` degrees, relative to where it faces now.
  // Positive turns its front toward +x (stage right from the default view).
  // Advances time.
  turn(as, deg, { dur = 700 } = {}) {
    const a = this.actors[as];
    if (!a) throw new Error(`no actor "${as}"`);
    a.turns.push({ t: this.t, dur, deg });
    this._advance(this.t + dur);
    return this;
  }

  // Throw an actor's pieces away again, last piece first. Advances time.
  unbuild(as, { to = "everywhere", stagger = 60, dur = 650, seed } = {}) {
    const a = this.actors[as];
    if (!a) throw new Error(`no actor "${as}"`);
    const r = rng(seed ?? this._seed++ * 104729);
    const n = a.parts.length;
    a.parts.forEach((p, i) => { p.out = { t0: this.t + (n - 1 - i) * stagger, dur, to: DIRECTIONS[to](r) }; });
    this._advance(this.t + (n - 1) * stagger + dur);
    return this;
  }

  // ---- set pieces ------------------------------------------------------
  // A tiled room: floor panels flip into place in a wave, then the back and
  // right walls rise. Sizes in studs (w across, d deep) and plates (h up).
  room({ w = 48, d = 36, h = 30, cell = 4, dur = 7000, seed = 5 } = {}) {
    this.roomSpec = { w, d, h, cell, seed, t0: this.t, dur };
    this._advance(this.t + dur);
    return this;
  }
  // A pictogram figure that walks with move(), faces where it's going, and
  // turns with turn(). It drops into place when it appears.
  figure(id, at, { face = 0, dur = 700 } = {}) {
    if (this.actors[id]) throw new Error(`an actor called "${id}" already exists`);
    this.actors[id] = { kind: "figure", t0: this.t, appear: dur, face, moves: [{ t: -1, dur: 0, to: at, hop: 0 }], turns: [] };
    this._advance(this.t + dur);
    return this;
  }
  button(id, at, { dur = 700 } = {}) { return this._prop(id, { kind: "button", at }, dur); }
  // A sliding door in the back wall: x along the wall in studs, sizes in studs and plates.
  door(id, { x, width = 8, height = 20, dur = 900 } = {}) { return this._prop(id, { kind: "door", x, width, height }, dur); }
  // A dotted signal line through points [x, y, z] (studs, plates, studs); it draws itself.
  signal(id, points, { dur = 2200 } = {}) { return this._prop(id, { kind: "signal", points }, dur); }
  _prop(id, spec, dur) {
    if (this.props[id]) throw new Error(`a prop called "${id}" already exists`);
    this.props[id] = { ...spec, t0: this.t, dur, events: [] };
    this._advance(this.t + dur);
    return this;
  }
  // Switch a prop on or off: a button presses, a signal lights, a door opens.
  _set(id, on, dur) {
    const p = this.props[id];
    if (!p) throw new Error(`no prop "${id}"`);
    p.events.push({ t: this.t, on, dur });
    this._advance(this.t + dur);
    return this;
  }
  press(id, { dur = 250 } = {}) { return this._set(id, true, dur); }
  release(id, { dur = 250 } = {}) { return this._set(id, false, dur); }
  activate(id, { dur = 900 } = {}) { return this._set(id, true, dur); }
  deactivate(id, { dur = 500 } = {}) { return this._set(id, false, dur); }
  open(id, { dur = 900 } = {}) { return this._set(id, true, dur); }
  close(id, { dur = 900 } = {}) { return this._set(id, false, dur); }

  // Run several actions at the same time; time moves on to the longest.
  together(fn) {
    const outer = this._group, start = this.t;
    this._group = { end: start };
    fn(this);
    const end = this._group.end;
    this._group = outer;
    this.t = start;
    this._advance(end);
    return this;
  }

  compile() {
    const reports = {};
    for (const [name, m] of Object.entries(this.models)) {
      const r = check({ steps: [{ note: name, parts: m.parts }] });
      const actor = Object.keys(this.actors).find((k) => this.actors[k].checkedAs === name);
      reports[name] = { ok: r.ok, errors: r.errors, warnings: r.warnings, stats: r.stats, parts: m.parts, actor };
    }
    return {
      meta: this.meta, duration: this.t + 600,
      actors: Object.fromEntries(Object.entries(this.actors).map(([k, a]) => [k, a.kind === "figure"
        ? { kind: "figure", t0: a.t0, appear: a.appear, face: a.face, moves: a.moves, turns: a.turns, highlights: a.highlights || [] }
        : { kind: "bricks", parts: a.parts, moves: a.moves, turns: a.turns, highlights: a.highlights || [], joints: a.joints || {}, poses: a.poses || [] }])),
      callouts: this.callouts, bubbles: this.bubbles, emitters: this.emitters, moods: this.moods,
      letterboxes: this.letterboxes, fades: this.fades, music: this.musicCues,
      props: this.props, room: this.roomSpec, camera: this.camera, captions: this.captions, cards: this.cards,
      reports,
    };
  }
}

export function story(meta, fn) {
  const d = new Director(meta);
  fn(d);
  return d.compile();
}
