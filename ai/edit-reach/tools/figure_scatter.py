"""Draw the 495 probes behind [E-001] as a two-panel scatter.

The paper reports the headline as two correlations — raw 0.522, excess 0.085
once a same-subject control is removed — and shows medians by family. It never
shows the points. A reader cannot see the spread, cannot see that the excess
cloud sits on zero, and cannot see the thing that qualifies the statistic most:
the coefficient is **bimodal**, so a correlation over it is closer to a
two-group comparison than to a trend.

Generated rather than drawn, for the reason the other figures here are not: at
495 points hand-writing is not possible, and the alt text must carry numbers
that cannot drift from the file they came from. Everything printed below is read
out of the run.

    python3 ai/edit-reach/tools/figure_scatter.py

Writes web/static/img/edit-reach/coefficient-vs-movement.svg.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = ROOT / "ai" / "edit-reach" / "results" / "E-001-predicted-vs-measured.json"
OUT = ROOT / "web" / "static" / "img" / "edit-reach" / "coefficient-vs-movement.svg"

W, H = 1000, 430
PAD_L, PAD_R, PAD_T, PAD_B = 74, 26, 54, 64
PANEL_GAP = 58
PANEL_W = (W - PAD_L - PAD_R - PANEL_GAP) / 2
PLOT_H = H - PAD_T - PAD_B

X_MAX = 1.08
Y_MIN, Y_MAX = -0.62, 1.0


def x_of(panel: int, v: float) -> float:
    left = PAD_L + panel * (PANEL_W + PANEL_GAP)
    return left + (v / X_MAX) * PANEL_W


def y_of(v: float) -> float:
    return PAD_T + PLOT_H * (Y_MAX - v) / (Y_MAX - Y_MIN)


def panel(index: int, values: list[tuple[float, float]], title: str,
          rho: float, lo: float, hi: float) -> str:
    left = PAD_L + index * (PANEL_W + PANEL_GAP)
    out = [f'  <g class="panel">']
    out.append(f'    <text x="{left:.0f}" y="{PAD_T - 26:.0f}" class="title">{title}</text>')
    out.append(
        f'    <text x="{left:.0f}" y="{PAD_T - 8:.0f}" class="stat">'
        f'Spearman {rho:.3f} &#160;(95% CI {lo:.3f} to {hi:.3f})</text>')
    # zero line, drawn under the points because the excess cloud sits on it
    out.append(f'    <path d="M{left:.1f} {y_of(0):.1f} H{left + PANEL_W:.1f}" class="zero"/>')
    out.append(f'    <path d="M{left:.1f} {PAD_T:.1f} V{PAD_T + PLOT_H:.1f}" class="axis"/>')
    # Both panels share one vertical scale. Without a mark on the second axis a
    # reader can take it for a scale of its own, which is the misreading the
    # one-axis rule exists to prevent; the ticks make the correspondence visible
    # without repeating the labels.
    for v in (-0.5, 0.0, 0.5, 1.0):
        out.append(f'    <path d="M{left - 4:.1f} {y_of(v):.1f} H{left:.1f}" class="axis"/>')
    out.append(f'    <path d="M{left:.1f} {PAD_T + PLOT_H:.1f} H{left + PANEL_W:.1f}" class="axis"/>')
    for cx, cy in values:
        out.append(f'    <circle cx="{x_of(index, cx):.1f}" cy="{y_of(cy):.1f}" r="2.4" class="pt"/>')
    for tick in (0.0, 0.5, 1.0):
        out.append(
            f'    <text x="{x_of(index, tick):.1f}" y="{PAD_T + PLOT_H + 18:.0f}" '
            f'class="tick mid">{tick:.1f}</text>')
    out.append(
        f'    <text x="{left + PANEL_W / 2:.0f}" y="{PAD_T + PLOT_H + 40:.0f}" '
        f'class="axlab mid">coefficient, computed before the edit</text>')
    out.append("  </g>")
    return "\n".join(out)


def main() -> None:
    run = json.loads(SRC.read_text())
    items = run["items"]
    raw = [(r["coefficient"], r["movement"]) for r in items]
    exc = [(r["coefficient"], r["excess"]) for r in items]
    o = run["overall"]
    r_rho, (r_lo, r_hi) = o["raw"]["rho"], o["raw"]["ci95"]
    e_rho, (e_lo, e_hi) = o["excess"]["rho"], o["excess"]["ci95"]

    near = sum(1 for c, _ in raw if c >= 0.8)
    far = sum(1 for c, _ in raw if c <= 0.2)
    middle = len(raw) - near - far

    alt = (
        f"Two scatter plots sharing one vertical scale, {len(raw)} probes each. "
        f"On the left, the coefficient against how far the edit actually moved the "
        f"model: the points trend upward and Spearman is {r_rho:.3f}. On the right, "
        f"the same coefficient against what is left once a same-subject control is "
        f"removed: the cloud collapses onto the zero line and Spearman is {e_rho:.3f}, "
        f"with an interval from {e_lo:.3f} to {e_hi:.3f} that crosses zero. In both "
        f"panels the coefficient is bimodal — {near} probes sit at 0.8 or above and "
        f"{far} at 0.2 or below, with only {middle} in between — so the statistic is "
        f"closer to a comparison of two groups than to a trend."
    )

    ticks = [(-0.5, "-0.5"), (0.0, "0"), (0.5, "0.5"), (1.0, "1.0")]
    grid = "\n".join(
        f'  <text x="{PAD_L - 12:.0f}" y="{y_of(v) + 4:.1f}" class="tick end">{lab}</text>'
        for v, lab in ticks)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{alt}">
  <style type="text/css"><![CDATA[
    /* The page has a light and a dark theme. An image element cannot inherit
       the page's custom properties, because it is a separate document; its own
       stylesheet is honoured though, media queries included. Every var() keeps
       a light fallback so the PDF converter, which does not read :root, still
       renders what a reader sees. */
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
    .title {{ font-size: 15px; font-weight: 600; fill: var(--ink, #2b2a28); }}
    .stat  {{ font-size: 12.5px; fill: var(--faint, #6b6863); font-family: "IBM Plex Mono", ui-monospace, monospace; }}
    .tick  {{ font-size: 11.5px; fill: var(--faint, #6b6863); }}
    .axlab {{ font-size: 12px; fill: var(--faint, #6b6863); }}
    .mid   {{ text-anchor: middle; }}
    .end   {{ text-anchor: end; }}
    .axis  {{ stroke: var(--rule, #d9d3c7); stroke-width: 1; fill: none; }}
    .zero  {{ stroke: var(--rule, #d9d3c7); stroke-width: 1; stroke-dasharray: 3 4; fill: none; }}
    /* One series, so no legend and no hue: density is the encoding, and a
       translucent dot lets 495 of them show where they pile up. */
    .pt    {{ fill: var(--link, #4338a8); fill-opacity: 0.32; }}
  ]]></style>

  <rect width="{W}" height="{H}" fill="var(--paper, #f4f1ea)"/>
{grid}
  <text x="{PAD_L - 12:.0f}" y="{PAD_T - 26:.0f}" class="tick end">movement</text>

{panel(0, raw, "What the edit actually moved", r_rho, r_lo, r_hi)}

{panel(1, exc, "What is left after the control", e_rho, e_lo, e_hi)}
</svg>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg)
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {len(raw)} probes · raw rho {r_rho:.4f} · excess rho {e_rho:.4f}")
    print(f"  bimodal: {near} at >=0.8, {far} at <=0.2, {middle} between")


if __name__ == "__main__":
    main()
