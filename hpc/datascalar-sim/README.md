# DataScalar Race

An interactive toy simulator of **DataScalar** (Burger, Kaxiras & Goodman,
[DataScalar Architectures](https://www.cs.utexas.edu/ftp/dburger/papers/JSA99.pdf), ISCA '97 / JSA '99).
Memory is split across chips. A traditional machine runs the program once and
fetches remote data with request/response. DataScalar runs the same program on
every chip; whichever chip owns the data broadcasts it one way.

## Run

Open `index.html` in a browser. No build, no dependencies.

## What you can change

- number of chips, access pattern, arithmetic per load, chip-to-chip latency
- shared bus vs point-to-point interconnect
- the energy cost of moving a word relative to one instruction, which moves you
  along the "when does wasted compute pay off?" curve

## Rough edges

- Toy model: in-order chips, no caches, one word per load, contiguous memory slices.
- Time always favours DataScalar here. Energy is where the tradeoff shows up.
- `sim.js` holds the model and can be `require`d from Node for quick checks.
