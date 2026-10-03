# Difference Engine

A 3D difference engine after Babbage's No. 2 design. It assembles itself from
about 200 parts flying in from every direction, then tabulates polynomials by
addition alone when you turn the crank.

## Run

Open `index.html` in a browser. Three.js loads from a CDN; nothing else is needed.

```sh
node --test test/*.test.cjs   # the arithmetic, tested on its own
```

## How it computes

- **Columns:** eight columns of eight figure wheels. Column 0 is the table and
  columns 1–7 hold differences, so it handles polynomials up to degree 7.
- **Two half-cycles per crank turn:**
  - First half: odd columns add into the column below them
    (Δ1→Table, Δ3→Δ2, Δ5→Δ4, Δ7→Δ6).
  - Second half: even columns add into the column below them
    (Δ2→Δ1, Δ4→Δ3, Δ6→Δ5).
- **Staggered starting values:** the second half reads columns the first half
  just changed, so textbook differences give the wrong table. `engine.js` solves
  exactly for the starting values that work.
- **Wheel arithmetic:** every digit adds at once, then carries ripple up from
  the units. Values are modulo 10^8, so negative differences are stored as
  ten's complements.

## What's checked

- **Every printed value** is compared live with the polynomial computed
  directly (shown with ✓ in the table).
- **The tests** cover:
  - wheel addition against integer addition (5,000 random pairs)
  - five named tables
  - 200 random polynomials of degree up to 7
  - textbook differences failing on a two-phase engine
  - n⁷ running out of digits at n = 14

## Tables to try

- **Euler's n² + n + 41:** prime for n = 0…39, then 1681 = 41².
- **n³**
- **n⁷:** uses all eight columns and overflows at n = 14.
- **5000 − 3n²:** negative differences, stored as complements.

## Rough edges

- Eight digits per column, where the real No. 2 has 31.
- The carry and locking mechanisms are drawn as plain levers and sectors. The
  arithmetic and the two-phase timing are faithful; the mechanical detail is not.
- Keys: space turns the crank, R runs, 1–4 switch views, O orbits, H hides the panel, F goes fullscreen.
