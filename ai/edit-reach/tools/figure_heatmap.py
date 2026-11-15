"""Draw the conformance sweep as a heat map grid: three models, five layers each.

§4.1 says the arithmetic-site disagreement spans two to three orders of
magnitude across depth with no predictable direction. The paper states that and
shows none of it. This is the grid behind the sentence: six checks down, the
sampled layers across, one panel per model.

Two decisions worth naming.

**Sequential, not diverging.** Every value is a magnitude of disagreement, so
there is no polarity and no midpoint — a diverging scale would invent one. One
hue, light to dark, on log10 because the values span 1e-8 to 1e-1.

**Zero gets its own mark, not the lightest step.** "Matches exactly" is a
different kind of statement from "small but nonzero", and a scale that renders
them as neighbouring shades hides the only check that is analytic. Exact zeros
are drawn empty with a dot.

    python3 ai/edit-reach/tools/figure_heatmap.py

Writes web/static/img/edit-reach/conformance-by-layer.svg.
"""
from __future__ import annotations

import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
RES = ROOT / "ai" / "edit-reach" / "results"
OUT = ROOT / "web" / "static" / "img" / "edit-reach" / "conformance-by-layer.svg"

FILES = [
    ("Llama-3.1-8B", "E-010-layers-8b.json"),
    ("GPT-J-6B", "E-010-layers-gptj.json"),
    ("Llama-3.1-70B", "E-011-layers-70b.json"),
]

CELL_W, CELL_H = 46, 30
PAD_L, PAD_T, PAD_B = 118, 74, 72
PANEL_GAP = 46

LO, HI = -8.0, -0.5          # log10 bounds, from the data below


def shade(value: float) -> tuple[str, float]:
    """A single hue, light to dark, on log10. Returns (class, opacity)."""
    if value == 0:
        return "zero", 1.0
    lg = max(LO, min(HI, math.log10(value)))
    t = (lg - LO) / (HI - LO)
    return "cell", 0.10 + 0.85 * t


def main() -> None:
    panels = []
    checks: list[str] = []
    for label, fname in FILES:
        doc = json.loads((RES / fname).read_text())
        layers = doc["layers"]
        by_layer = doc["by_layer"]
        grid: dict[str, dict[int, float | None]] = {}
        for layer in layers:
            for check in by_layer[str(layer)]:
                grid.setdefault(check["name"], {})[layer] = check["observed"]
        if not checks:
            checks = list(grid)
        panels.append((label, layers, grid))

    n_layers = max(len(p[1]) for p in panels)
    panel_w = n_layers * CELL_W
    width = PAD_L + len(panels) * panel_w + (len(panels) - 1) * PANEL_GAP + 30
    height = PAD_T + len(checks) * CELL_H + PAD_B

    out: list[str] = []
    for pi, (label, layers, grid) in enumerate(panels):
        left = PAD_L + pi * (panel_w + PANEL_GAP)
        out.append(f'  <text x="{left}" y="{PAD_T - 34}" class="model">{label}</text>')
        for li, layer in enumerate(layers):
            out.append(f'    <text x="{left + li * CELL_W + CELL_W / 2:.0f}" '
                       f'y="{PAD_T - 12}" class="tick mid">{layer}</text>')
        for ci, check in enumerate(checks):
            for li, layer in enumerate(layers):
                v = grid.get(check, {}).get(layer)
                x = left + li * CELL_W
                y = PAD_T + ci * CELL_H
                if v is None:
                    out.append(f'    <rect x="{x}" y="{y}" width="{CELL_W - 2}" '
                               f'height="{CELL_H - 2}" class="absent"/>')
                    continue
                kind, op = shade(v)
                out.append(f'    <rect x="{x}" y="{y}" width="{CELL_W - 2}" '
                           f'height="{CELL_H - 2}" class="{kind}" fill-opacity="{op:.3f}"/>')
                if kind == "zero":
                    out.append(f'    <circle cx="{x + (CELL_W - 2) / 2:.0f}" '
                               f'cy="{y + (CELL_H - 2) / 2:.0f}" r="2" class="zerodot"/>')
        out.append(f'    <text x="{left + panel_w / 2:.0f}" '
                   f'y="{PAD_T + len(checks) * CELL_H + 22}" class="tick mid">layer</text>')

    rows = "\n".join(
        f'  <text x="{PAD_L - 12}" y="{PAD_T + i * CELL_H + CELL_H / 2 + 4:.0f}" '
        f'class="rowlab end">{c.replace("_", " ")}</text>'
        for i, c in enumerate(checks))

    # legend: four sampled steps plus the exact-zero mark
    lg_y = height - 34
    legend = [f'  <text x="{PAD_L - 12}" y="{lg_y + 12}" class="rowlab end">disagreement</text>']
    for i, lg in enumerate((-7.0, -5.0, -3.0, -1.0)):
        _, op = shade(10 ** lg)
        x = PAD_L + i * 86
        legend.append(f'  <rect x="{x}" y="{lg_y}" width="22" height="16" class="cell" fill-opacity="{op:.3f}"/>')
        legend.append(f'  <text x="{x + 27}" y="{lg_y + 12}" class="tick">1e{int(lg)}</text>')
    zx = PAD_L + 4 * 86
    legend.append(f'  <rect x="{zx}" y="{lg_y}" width="22" height="16" class="zero"/>')
    legend.append(f'  <circle cx="{zx + 11}" cy="{lg_y + 8}" r="2" class="zerodot"/>')
    legend.append(f'  <text x="{zx + 27}" y="{lg_y + 12}" class="tick">exactly 0</text>')

    nonzero = [v for _, _, g in panels for r in g.values() for v in r.values() if v]
    alt = (
        f"A grid of {len(checks)} reproducibility checks down and the sampled layers "
        f"across, one panel per model: {', '.join(p[0] for p in panels)}. Darker means a "
        f"larger disagreement between two readings of the same quantity. The nonzero "
        f"values run from {min(nonzero):.1e} to {max(nonzero):.1e}, a span of about "
        f"{math.log10(max(nonzero) / min(nonzero)):.0f} orders of magnitude, and they do "
        f"not grow or shrink consistently with depth. Checks that match exactly are drawn "
        f"empty with a dot rather than as the palest shade."
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{alt}">
  <style type="text/css"><![CDATA[
    :root {{
        --paper: #f4f1ea;
        --ink: #2b2a28;
        --faint: #6b6863;
        --link: #4338a8;
        --rule: #d9d3c7;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
          --paper: #1b1a18;
          --ink: #eeece6;
          --faint: #9a968e;
          --link: #b1a9ff;
          --rule: #3a3833;
      }}
    }}
    text {{ font-family: Lato, "Helvetica Neue", sans-serif; }}
    .model  {{ font-size: 14px; font-weight: 600; fill: var(--ink, #2b2a28); }}
    .tick   {{ font-size: 11px; fill: var(--faint, #6b6863); }}
    .rowlab {{ font-size: 11.5px; fill: var(--faint, #6b6863); }}
    .mid    {{ text-anchor: middle; }}
    .end    {{ text-anchor: end; }}
    /* One hue, light to dark. Magnitudes have no polarity, so a diverging
       scale would invent a midpoint that the data does not have. */
    .cell   {{ fill: var(--link, #4338a8); }}
    .zero   {{ fill: none; stroke: var(--rule, #d9d3c7); stroke-width: 1; }}
    .zerodot{{ fill: var(--faint, #6b6863); }}
    .absent {{ fill: none; stroke: var(--rule, #d9d3c7); stroke-dasharray: 2 3; }}
  ]]></style>

  <rect width="{width}" height="{height}" fill="var(--paper, #f4f1ea)"/>
{rows}
{chr(10).join(out)}
{chr(10).join(legend)}
</svg>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg)
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {len(panels)} models x {len(checks)} checks; nonzero span "
          f"{min(nonzero):.1e} to {max(nonzero):.1e}")


if __name__ == "__main__":
    main()
