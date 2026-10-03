const test = require("node:test");
const assert = require("node:assert/strict");
const DE = require("../engine.js");

const polys = {
  "n^2 + n + 41": (n) => BigInt(n) ** 2n + BigInt(n) + 41n,
  "n^3": (n) => BigInt(n) ** 3n,
  "n(n+1)/2": (n) => (BigInt(n) * BigInt(n + 1)) / 2n,
  "n^7": (n) => BigInt(n) ** 7n,
  "5000 - 3n^2": (n) => 5000n - 3n * BigInt(n) ** 2n,
};

test("wheel addition equals integer addition mod 10^8", () => {
  let s = 12345;
  const rnd = () => (s = (s * 1103515245 + 12345) % 2 ** 31) / 2 ** 31;
  for (let k = 0; k < 5000; k++) {
    const a = Math.floor(rnd() * DE.MOD), b = Math.floor(rnd() * DE.MOD);
    assert.equal(DE.addColumns(a, b).value, (a + b) % DE.MOD);
  }
  assert.deepEqual(DE.addColumns(99999999, 1).carries, [1, 2, 3, 4, 5, 6, 7]);
  assert.equal(DE.addColumns(99999999, 1).value, 0);
});

for (const [name, f] of Object.entries(polys)) {
  test(`prints ${name} correctly while it fits on the wheels`, () => {
    const rows = DE.verify(f, 0, 60);
    for (const r of rows) if (r.fits) assert.equal(BigInt(r.printed), r.exact, `n=${r.n}`);
  });
}

test("random polynomials up to degree 7, any starting n", () => {
  let s = 7;
  const rnd = (k) => (s = (s * 48271) % 2147483647) % k;
  for (let trial = 0; trial < 200; trial++) {
    const deg = rnd(8), coef = Array.from({ length: deg + 1 }, () => BigInt(rnd(19) - 9));
    const f = (n) => coef.reduce((acc, c, i) => acc + c * BigInt(n) ** BigInt(i), 0n);
    const n0 = rnd(20);
    const rows = DE.verify(f, n0, 40);
    for (const r of rows) assert.equal(BigInt(r.printed), ((r.exact % 100000000n) + 100000000n) % 100000000n, `trial ${trial} n=${r.n}`);
  }
});

test("textbook differences give the wrong table on a two-phase engine", () => {
  // Δ for n^3 at n=0: 0, 1, 6, 6 — correct for one-column-at-a-time adding.
  const s = { n: 0, cols: [0, 1, 6, 6, 0, 0, 0, 0] };
  const printed = [];
  for (let t = 0; t < 5; t++) printed.push(DE.turn(s).printed);
  assert.notDeepEqual(printed, [1, 8, 27, 64, 125]);
});

test("n^7 runs out of digits at n = 14 and verify() says so", () => {
  const rows = DE.verify(polys["n^7"], 0, 15);
  assert.ok(rows[13].ok);
  assert.equal(rows[14].fits, false);
  assert.equal(rows[14].ok, false);
});
