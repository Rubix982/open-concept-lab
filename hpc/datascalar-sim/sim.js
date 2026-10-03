// DataScalar vs. traditional request/response — a toy timing + energy model.
//
// Machine: N nodes, each owning a contiguous slice of a shared address space.
//   Traditional: node 0 runs the program; every load to another node's slice is
//                a request (L) + owner read (m) + response (L), fully serialized.
//   DataScalar:  every node runs the same program. On each load, the owner reads
//                locally (m) and one-way broadcasts the value (L); the others stall
//                until it arrives. Owners run ahead, so broadcasts pipeline.
//
// Loads all go through program order on in-order cores, so processing the trace
// sequentially while tracking a clock per node is exact for this model.

(function (root) {
  const ADDR_SPACE = 256;

  function rng(seed) {
    let s = seed >>> 0;
    return () => {
      s = (s * 1664525 + 1013904223) >>> 0;
      return s / 4294967296;
    };
  }

  // A trace is a list of {kind: 'load', addr} | {kind: 'op'}.
  function makeTrace({ pattern, loads, opsPerLoad, seed = 7 }) {
    const r = rng(seed);
    const trace = [];
    for (let i = 0; i < loads; i++) {
      let addr;
      if (pattern === 'streaming') addr = Math.floor(i * ADDR_SPACE / loads);
      else if (pattern === 'strided') addr = (i * 37) % ADDR_SPACE;
      else addr = Math.floor(r() * ADDR_SPACE);
      trace.push({ kind: 'load', addr });
      for (let k = 0; k < opsPerLoad; k++) trace.push({ kind: 'op' });
    }
    return trace;
  }

  const ownerOf = (addr, n) => Math.floor(addr / (ADDR_SPACE / n));

  // Segment kinds: 'op' compute, 'mem' local memory read, 'stall' waiting on data.
  function seg(list, node, t0, t1, kind) {
    if (t1 > t0) list.push({ node, t0, t1, kind });
  }

  function simTraditional(trace, { n, L, m, c }) {
    const segs = [], msgs = [];
    let t = 0, remote = 0, loads = 0, ops = 0;
    for (const ins of trace) {
      if (ins.kind === 'op') { seg(segs, 0, t, t + c, 'op'); t += c; ops++; continue; }
      loads++;
      const o = ownerOf(ins.addr, n);
      if (o === 0) { seg(segs, 0, t, t + m, 'mem'); t += m; continue; }
      remote++;
      msgs.push({ from: 0, to: [o], t0: t, t1: t + L, kind: 'req' });
      seg(segs, o, t + L, t + L + m, 'mem');
      msgs.push({ from: o, to: [0], t0: t + L + m, t1: t + 2 * L + m, kind: 'resp' });
      seg(segs, 0, t, t + 2 * L + m, 'stall');
      t += 2 * L + m;
    }
    return {
      segs, msgs, finish: t,
      serialized: remote,           // off-chip accesses on the critical path
      wireMessages: 2 * remote,
      instructionsExecuted: loads + ops,
    };
  }

  function simDataScalar(trace, { n, L, m, c, bus }) {
    const segs = [], msgs = [];
    const t = new Array(n).fill(0);
    let busFree = 0, loads = 0, ops = 0, broadcasts = 0;
    for (const ins of trace) {
      if (ins.kind === 'op') {
        for (let j = 0; j < n; j++) { seg(segs, j, t[j], t[j] + c, 'op'); t[j] += c; }
        ops++; continue;
      }
      loads++;
      const o = ownerOf(ins.addr, n);
      seg(segs, o, t[o], t[o] + m, 'mem');
      t[o] += m;
      let send = t[o];
      if (bus === 'shared') { send = Math.max(send, busFree); busFree = send + 1; }
      const arrive = send + L;
      const to = [];
      for (let j = 0; j < n; j++) if (j !== o) to.push(j);
      msgs.push({ from: o, to, t0: send, t1: arrive, kind: 'bcast' });
      broadcasts++;
      for (const j of to) {
        if (arrive > t[j]) { seg(segs, j, t[j], arrive, 'stall'); t[j] = arrive; }
      }
    }
    // Critical path: the program is done when every node has retired it.
    let finish = 0;
    for (let j = 0; j < n; j++) finish = Math.max(finish, t[j]);
    return {
      segs, msgs, finish,
      serialized: countOwnerSwitches(trace, n),
      wireMessages: bus === 'shared' ? broadcasts : broadcasts * (n - 1),
      instructionsExecuted: (loads + ops) * n,
    };
  }

  // In DataScalar a one-way latency lands on the critical path only when
  // ownership changes hands; runs of same-owner loads pipeline behind it.
  function countOwnerSwitches(trace, n) {
    let prev = -1, k = 0;
    for (const ins of trace) {
      if (ins.kind !== 'load') continue;
      const o = ownerOf(ins.addr, n);
      if (o !== prev && prev !== -1) k++;
      prev = o;
    }
    return k;
  }

  // Energy in units of one instruction. `ratio` = energy to move one word
  // across the interconnect / energy of one instruction.
  function energy(res, ratio) {
    return res.instructionsExecuted + res.wireMessages * ratio;
  }

  function run(params) {
    const trace = makeTrace(params);
    return {
      trace,
      trad: simTraditional(trace, params),
      ds: simDataScalar(trace, params),
    };
  }

  const api = { ADDR_SPACE, makeTrace, ownerOf, simTraditional, simDataScalar, energy, run };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.DSim = api;
})(typeof window !== 'undefined' ? window : globalThis);
