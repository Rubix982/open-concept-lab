// The arithmetic of a Babbage-style difference engine, kept apart from the
// animation so it can be tested on its own.
//
// Eight columns of eight decimal figure wheels: column 0 is the table, columns
// 1..7 hold differences. A crank turn has two half-cycles, as in Babbage's
// No. 2 design: first every odd column is added into the even column below it
// (Δ1→Table, Δ3→Δ2, Δ5→Δ4, Δ7→Δ6), then every even column into the odd column
// below it (Δ2→Δ1, Δ4→Δ3, Δ6→Δ5). Because the second half reads columns the
// first half just changed, the starting values are not the textbook
// differences; setup() solves for the staggered values that make the table
// come out right, and verify() checks every printed number against the
// polynomial computed directly.
//
// Each addition is done the way the wheels do it: every digit adds at once,
// then carries ripple up from the units. Arithmetic is modulo 10^8, so a
// negative difference sits on the wheels as its ten's complement.

(function (root) {
  const COLS = 8, DIGITS = 8, MOD = 10 ** DIGITS;
  const PHASES = {
    A: [[0, 1], [2, 3], [4, 5], [6, 7]],   // [target, source]
    B: [[1, 2], [3, 4], [5, 6]],
  };

  const digitsOf = (v) => Array.from({ length: DIGITS }, (_, j) => Math.floor(v / 10 ** j) % 10);
  const valueOf = (ds) => ds.reduce((s, d, j) => s + d * 10 ** j, 0);
  const mod = (x) => ((x % MOD) + MOD) % MOD;

  // ---- exact solve for the staggered starting values -------------------
  const big = (x) => BigInt(x);
  const gcd = (a, b) => { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) [a, b] = [b, a % b]; return a; };
  const frac = (n, d = 1n) => { if (d < 0n) { n = -n; d = -d; } const g = gcd(n, d) || 1n; return { n: n / g, d: d / g }; };
  const sub = (a, b) => frac(a.n * b.d - b.n * a.d, a.d * b.d);
  const mul = (a, b) => frac(a.n * b.n, a.d * b.d);
  const div = (a, b) => frac(a.n * b.d, a.d * b.n);

  // Table outputs (column 0 before any turn, then after each turn), exact.
  function outputs(v, turns) {
    const c = v.slice(), out = [c[0]];
    for (let t = 0; t < turns; t++) {
      for (const [a, b] of PHASES.A) c[a] += c[b];
      for (const [a, b] of PHASES.B) c[a] += c[b];
      out.push(c[0]);
    }
    return out;
  }

  // f: n -> BigInt (any polynomial of degree <= 7 with integer values)
  function setup(f, n0) {
    const M = [];
    for (let i = 0; i < COLS; i++) {
      const e = Array(COLS).fill(0n); e[i] = 1n;
      outputs(e, COLS - 1).forEach((y, t) => { (M[t] ||= [])[i] = frac(y); });
    }
    const rhs = Array.from({ length: COLS }, (_, t) => frac(f(n0 + t)));
    for (let k = 0; k < COLS; k++) {
      let p = k; while (M[p][k].n === 0n) p++;
      [M[k], M[p]] = [M[p], M[k]]; [rhs[k], rhs[p]] = [rhs[p], rhs[k]];
      for (let r = 0; r < COLS; r++) if (r !== k && M[r][k].n !== 0n) {
        const m = div(M[r][k], M[k][k]);
        for (let c = k; c < COLS; c++) M[r][c] = sub(M[r][c], mul(m, M[k][c]));
        rhs[r] = sub(rhs[r], mul(m, rhs[k]));
      }
    }
    const x = rhs.map((r, k) => div(r, M[k][k]));
    if (x.some((q) => q.d !== 1n)) throw new Error("starting values are not whole numbers");
    const M8 = big(MOD);
    return { n: n0, cols: x.map((q) => Number(((q.n % M8) + M8) % M8)) };
  }

  // Add column `source` into column `target` the way the wheels do.
  function addColumns(a, b) {
    const da = digitsOf(a), db = digitsOf(b);
    const afterAdd = da.map((d, j) => (d + db[j]) % 10);
    const pending = da.map((d, j) => d + db[j] >= 10);
    const carries = [], ds = afterAdd.slice();
    for (let j = 0; j < DIGITS - 1; j++) {
      if (!pending[j]) continue;
      carries.push(j + 1);                       // wheel j+1 steps forward by one
      ds[j + 1] = (ds[j + 1] + 1) % 10;
      if (ds[j + 1] === 0) pending[j + 1] = true; // a 9 rolled over: carry again
    }
    return { before: da, step: db, afterAdd, carries, after: ds, value: valueOf(ds) };
  }

  function halfCycle(state, phase) {
    const ops = PHASES[phase].map(([t, s]) => {
      const r = addColumns(state.cols[t], state.cols[s]);
      return { target: t, source: s, ...r };
    });
    for (const op of ops) state.cols[op.target] = op.value;
    return ops;
  }

  function turn(state) {
    const A = halfCycle(state, "A");
    const B = halfCycle(state, "B");
    state.n += 1;
    return { A, B, printed: state.cols[0] };
  }

  // Run the engine and compare every printed value with f(n) itself.
  function verify(f, n0, turns) {
    const s = setup(f, n0), rows = [];
    const row = (n, printed) => {
      const exact = f(n), fits = exact >= 0n && exact < big(MOD);
      rows.push({ n, printed, exact, fits, ok: fits && big(printed) === exact });
    };
    row(n0, s.cols[0]);
    for (let t = 0; t < turns; t++) { turn(s); row(s.n, s.cols[0]); }
    return rows;
  }

  const api = { COLS, DIGITS, MOD, PHASES, digitsOf, valueOf, mod, setup, addColumns, halfCycle, turn, verify, outputs };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.DE = api;
})(typeof window !== "undefined" ? window : globalThis);
