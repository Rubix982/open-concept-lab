"""Draw the twelve readings behind the premise and its control, against depth.

§3.2 says two things that look alike and are not. The anchor is **analytic** —
a prompt opening with the edited subject has the key the edit had, so the
coefficient is 1 by arithmetic, for any covariance at any layer. The
different-subject floor it is read against is **empirical**, and nothing fixes
it at all.

Printed as prose those two sit in neighbouring sentences and read as a pair of
measurements. Drawn, they are not a pair: one is a straight rule across the
whole chart, the other wanders between 0.031 and 0.388 and crosses itself. That
is the whole figure, and it is why this one is worth drawing at twelve points
when a table would hold them.

Depth is the x axis rather than the layer number, because layer 5 is 16% of the
way through a 32-layer model and 6% through an 80-layer one. The paper's
original claim — that the floor falls with model size — came from comparing
three models at layer 5, where size and depth move together. On this axis the
ordering breaks twice.

    python3 ai/edit-reach/tools/figure_depth.py

Writes web/static/img/edit-reach/premise-and-floor-by-depth.svg.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = ROOT / "ai" / "edit-reach" / "results" / "E-040-depth-sweep.json"
OUT = ROOT / "web" / "static" / "img" / "edit-reach" / "premise-and-floor-by-depth.svg"

W, H = 1000, 460
PAD_L, PAD_R, PAD_T, PAD_B = 76, 188, 58, 64
PLOT_W = W - PAD_L - PAD_R
PLOT_H = H - PAD_T - PAD_B

X_MAX = 0.55
Y_MAX = 1.06

#: Model id -> (short label, css class). Fixed order, never cycled: the third
#: slot exists because there are three models, not because a loop ran out.
SERIES: list[tuple[str, str, str]] = [
    ("EleutherAI/gpt-j-6b", "GPT-J-6B", "s1"),
    ("meta-llama/Llama-3.1-8B", "Llama-3.1-8B", "s2"),
    ("meta-llama/Llama-3.1-70B", "Llama-3.1-70B", "s3"),
]


def x_of(v: float) -> float:
    return PAD_L + (v / X_MAX) * PLOT_W


def y_of(v: float) -> float:
    return PAD_T + PLOT_H * (Y_MAX - v) / Y_MAX


def main() -> None:
    doc = json.loads(SRC.read_text())
    by_model: dict[str, list[dict]] = {}
    for r in doc["rows"]:
        by_model.setdefault(r["model"], []).append(r)
    for rs in by_model.values():
        rs.sort(key=lambda r: r["depth_fraction_actual"])

    anchors = [r["anchor_median"] for r in doc["rows"]]
    floors = [r["floor_median"] for r in doc["rows"]]
    worst = max(r["anchor_worst_deviation"] for r in doc["rows"])
    body: list[str] = []

    # --- grid, drawn first so every mark sits on top of it ------------------
    for v in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        body.append(f'  <path d="M{PAD_L} {y_of(v):.1f} H{PAD_L + PLOT_W}" class="grid"/>')
        body.append(f'  <text x="{PAD_L - 12}" y="{y_of(v) + 4:.1f}" class="tick end">{v:.1f}</text>')
    for v in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
        body.append(f'  <text x="{x_of(v):.1f}" y="{PAD_T + PLOT_H + 24:.0f}" class="tick mid">'
                    f'{v * 100:.0f}%</text>')
    body.append(f'  <path d="M{PAD_L} {PAD_T + PLOT_H} H{PAD_L + PLOT_W}" class="axis"/>')
    body.append(f'  <text x="{PAD_L + PLOT_W / 2:.0f}" y="{PAD_T + PLOT_H + 50:.0f}" '
                f'class="axlab mid">how far through the model the layer sits</text>')
    body.append(f'  <text transform="translate(22,{PAD_T + PLOT_H / 2:.0f}) rotate(-90)" '
                f'class="axlab mid">coefficient</text>')

    # --- the anchor: one rule, twelve dots on it ---------------------------
    # Drawn as a rule rather than a polyline per model, because the three
    # polylines would lie exactly on top of each other and the figure would
    # claim three lines where the data has one value.
    body.append(f'  <path d="M{PAD_L} {y_of(1.0):.1f} H{PAD_L + PLOT_W}" class="pinned"/>')
    for r in doc["rows"]:
        body.append(f'  <circle cx="{x_of(r["depth_fraction_actual"]):.1f}" '
                    f'cy="{y_of(r["anchor_median"]):.1f}" r="4.5" class="pindot"/>')
    body.append(f'  <text x="{PAD_L + PLOT_W + 14}" y="{y_of(1.0) + 4:.1f}" class="pinlab">'
                f'anchor &#183; 1.000</text>')
    body.append(f'  <text x="{PAD_L + PLOT_W + 14}" y="{y_of(1.0) + 21:.1f}" class="pinsub">'
                f'all 12 readings</text>')

    # --- the floor: one line per model -------------------------------------
    # Only four readings get a printed number: the two extremes, and the two
    # that break the size ordering. A number on all twelve was the first draft
    # and it collided with itself at three of the four depths — and a value on
    # every point is what the chart is for, not what a label is for.
    lo = min(doc["rows"], key=lambda r: r["floor_median"])
    hi = max(doc["rows"], key=lambda r: r["floor_median"])
    breaks = []
    for frac in (0.16, 0.30):
        col = [r for r in doc["rows"] if abs(r["depth_fraction_requested"] - frac) < 1e-6]
        breaks.append(max(col, key=lambda r: r["floor_median"]))
    labelled = {id(r) for r in (lo, hi, *breaks)}

    ends: list[tuple[float, str, str]] = []
    for model, label, cls in SERIES:
        rs = by_model[model]
        pts = [(x_of(r["depth_fraction_actual"]), y_of(r["floor_median"])) for r in rs]
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        body.append(f'  <path d="{d}" class="line {cls}"/>')
        for (x, y), r in zip(pts, rs):
            # A ring in the surface colour, so a crossing reads as two marks
            # rather than one blob. 70B crosses the other two twice.
            body.append(f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" class="ring"/>')
            body.append(f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="4" class="dot {cls}"/>')
            if id(r) in labelled:
                body.append(f'  <text x="{x:.1f}" y="{y - 12:.1f}" class="val mid">'
                            f'{r["floor_median"]:.3f}</text>')
        ends.append((pts[-1][1], label, cls))

    # The three series end within 20px of each other at 50% depth, so the
    # labels are spaced apart rather than drawn where their lines happen to
    # stop. Spacing them is not decoration: two overlapping labels name neither.
    ends.sort()
    placed: list[float] = []
    for y, label, cls in ends:
        while placed and y - placed[-1] < 19:
            y = placed[-1] + 19
        placed.append(y)
        body.append(f'  <path d="M{PAD_L + PLOT_W + 4} {y - 4:.1f} '
                    f'H{PAD_L + PLOT_W + 10}" class="leader {cls}"/>')
        body.append(f'  <text x="{PAD_L + PLOT_W + 14:.1f}" y="{y:.1f}" '
                    f'class="dlab {cls}">{label}</text>')

    # --- where the ordering breaks -----------------------------------------
    # Named on the chart because it is the finding, and a reader asked to spot
    # a crossing in three lines will not reliably find the right one.
    for frac, who in ((0.16, "70B highest"), (0.30, "8B highest")):
        col = [r for r in doc["rows"]
               if abs(r["depth_fraction_requested"] - frac) < 1e-6]
        top = max(col, key=lambda r: r["floor_median"])
        x = x_of(top["depth_fraction_actual"])
        body.append(f'  <path d="M{x:.1f} {y_of(top["floor_median"]) - 24:.1f} '
                    f'V{PAD_T + 14}" class="callout"/>')
        body.append(f'  <text x="{x:.1f}" y="{PAD_T + 4}" class="note mid">{who}</text>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"
     width="{W}" height="{H}" role="img"
     aria-label="Two quantities read at twelve points: three models, each at four
     fractions of its own depth. The anchor coefficient is 1.000 at every one of
     the twelve, drawn as a straight rule across the top with the worst deviation
     from 1 being {worst:.0e}. The different-subject floor beneath it is not
     fixed: it runs from {min(floors):.3f} to {max(floors):.3f} and is ordered by
     neither model size nor depth. At 16 percent of depth the largest model,
     Llama-3.1-70B, returns the highest floor of the three at 0.140, and at 30
     percent the middle model, Llama-3.1-8B, does at 0.256. Llama-3.1-70B alone
     reads 0.031, 0.140, 0.046 and 0.161 as the layer descends.">
  <style><![CDATA[
    /* Both triples pass all six dataviz checks on their own surface. The dark
       steps are chosen against the dark surface, not lightened from the light
       ones: a flipped palette leaves the band. */
    :root {{
        --paper: #f4f1ea; --ink: #2b2a28; --faint: #6b6863; --rule: #d9d3c7;
        --s1: #5b4fc4; --s2: #a4442f; --s3: #00876b;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
          --paper: #1b1a18; --ink: #eeece6; --faint: #9a968e; --rule: #3a3833;
          --s1: #8078e0; --s2: #c9664a; --s3: #0d9b7d;
      }}
    }}
    text {{ font-family: Lato, "Helvetica Neue", sans-serif; }}
    .mid {{ text-anchor: middle; }}
    .end {{ text-anchor: end; }}
    .grid   {{ stroke: var(--rule, #d9d3c7); stroke-width: 1; }}
    .axis   {{ stroke: var(--faint, #6b6863); stroke-width: 1; }}
    .tick   {{ font-size: 11px; fill: var(--faint, #6b6863); }}
    .axlab  {{ font-size: 12px; fill: var(--faint, #6b6863); }}
    .pinned {{ stroke: var(--ink, #2b2a28); stroke-width: 2; }}
    .pindot {{ fill: var(--ink, #2b2a28); }}
    .pinlab {{ font-size: 13px; font-weight: 600; fill: var(--ink, #2b2a28); }}
    .pinsub {{ font-size: 11.5px; fill: var(--faint, #6b6863); }}
    .line   {{ fill: none; stroke-width: 2; stroke-linejoin: round; }}
    .ring   {{ fill: var(--paper, #f4f1ea); }}
    /* Every var() carries its light-mode fallback. Without one a renderer that
       does not resolve :root on an SVG root drops the declaration, and the
       lines vanish rather than falling back to a colour — which is how this
       figure first came out as twelve black dots and no lines. */
    .dot.s1 {{ fill: var(--s1, #5b4fc4); }}
    .dot.s2 {{ fill: var(--s2, #a4442f); }}
    .dot.s3 {{ fill: var(--s3, #00876b); }}
    .line.s1 {{ stroke: var(--s1, #5b4fc4); }}
    .line.s2 {{ stroke: var(--s2, #a4442f); }}
    .line.s3 {{ stroke: var(--s3, #00876b); }}
    .dlab   {{ font-size: 12.5px; font-weight: 600; }}
    .dlab.s1 {{ fill: var(--s1, #5b4fc4); }}
    .dlab.s2 {{ fill: var(--s2, #a4442f); }}
    .dlab.s3 {{ fill: var(--s3, #00876b); }}
    /* The value is printed beside every mark, so identity never rests on
       colour alone and the figure survives being read in grayscale. */
    .val    {{ font-size: 10.5px; font-family: "IBM Plex Mono", ui-monospace, monospace;
               fill: var(--faint, #6b6863); }}
    .callout {{ stroke: var(--faint, #6b6863); stroke-width: 1; stroke-dasharray: 2 3; }}
    .leader {{ stroke-width: 2; }}
    .leader.s1 {{ stroke: var(--s1, #5b4fc4); }}
    .leader.s2 {{ stroke: var(--s2, #a4442f); }}
    .leader.s3 {{ stroke: var(--s3, #00876b); }}
    .note   {{ font-size: 11.5px; fill: var(--faint, #6b6863); }}
  ]]></style>

  <rect width="{W}" height="{H}" fill="var(--paper, #f4f1ea)"/>
{chr(10).join(body)}
</svg>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg)
    print(f"{OUT.relative_to(ROOT)}")
    print(f"  {len(doc['rows'])} readings, {len(by_model)} models")
    print(f"  anchor   {min(anchors):.6f} .. {max(anchors):.6f}  worst dev {worst:.1e}")
    print(f"  floor    {min(floors):.4f} .. {max(floors):.4f}")


if __name__ == "__main__":
    main()
