# Model Microscope

GPT-2 medium, opened up three ways on prepared prompts:

1. **What it thinks, layer by layer** — the logit lens: each layer's state read
   out as if the model stopped there.
2. **Where it's looking** — attention from any word to the words before it,
   per layer (average of heads, or the strongest head for the last word).
3. **Where the fact lives** — causal tracing as in ROME (Meng et al., 2022):
   scramble the subject, restore one piece of the clean run at a time, and see
   which piece brings the answer back.

Everything is computed ahead of time; the page is plain HTML reading JSON.

## Look at it

```bash
cd site && python3 -m http.server 8765   # then open http://localhost:8765
```

(Opening `site/index.html` straight from disk won't load the data — browsers
block `fetch` from `file://`.)

## Add or change a case

Cases live in `cases.py`: a prompt, the next word to follow (`target`, with its
leading space), and the part of the prompt to scramble (`corrupt`). Then:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
.venv/bin/python trace.py            # every case, about 80 s each on a laptop CPU
.venv/bin/python trace.py eiffel     # just one
```

The "What to look for" notes are in `site/index.html` (`NOTES`), written by
reading the results — re-check them if you re-run a case.

## Known rough edges

- On this machine the weights load memory-mapped and Apple's accelerated
  matmul returns NaN on that memory, so `trace.py` copies them first.
- The target is a single token: for "A later year" the model spreads its bet
  over many years, so following one of them shows a weak signal.
- Causal tracing uses one fixed noise seed and ten draws; small differences
  between neighbouring cells are noise.
