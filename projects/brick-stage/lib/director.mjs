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
export function model(name, parts) { return { name, parts }; }

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
  shot(shot, dur = 1600) { this.camera.push({ t: this.t, dur, shot }); return this; }
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
        ...p, ...f, kind: PARTS[p.part].kind,
        t0: this.t + i * stagger, dur,
        from: dirOf(r), spin: [(r() - 0.5) * 6, (r() - 0.5) * 8, (r() - 0.5) * 6],
      };
    });
    if (host) { host.parts.push(...parts); host.modelParts = allParts; host.checkedAs = checkedAs; }
    else this.actors[as] = { model: m.name, checkedAs, modelParts: allParts, parts, moves: [{ t: -1, dur: 0, to: at, hop: 0 }], turns: [] };
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
      reports[name] = { ok: r.ok, errors: r.errors, warnings: r.warnings, stats: r.stats, parts: m.parts };
    }
    return {
      meta: this.meta, duration: this.t + 600,
      actors: Object.fromEntries(Object.entries(this.actors).map(([k, a]) => [k, a.kind === "figure"
        ? { kind: "figure", t0: a.t0, appear: a.appear, face: a.face, moves: a.moves, turns: a.turns }
        : { kind: "bricks", parts: a.parts, moves: a.moves, turns: a.turns }])),
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
