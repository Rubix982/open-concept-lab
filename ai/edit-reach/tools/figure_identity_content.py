"""Draw §5.3: whose fact was edited against what the fact was changed to.

[E-002] scored the same 495 probes under three arms — the real edit, a
different fact about the SAME person, and another person's edit matched on
magnitude. Two differences come out of that, and both are read PAIRED, probe
by probe, because the arms share their probes:

    content  = real edit            -  same-subject control
    identity = same-subject control -  different-subject control

The paper's headline is the ratio between them. This figure draws it.

**Why the three arm medians are not drawn.** The obvious picture is three
points on one axis with the gaps between them, and it is wrong here: the arm
medians are 0.0977, 0.0625 and 0.0016, whose unpaired gap for content is
0.0352 — about thirty-eight times the paired estimate of 0.0009. §5.3 records
that trap in prose; a figure that drew it would reinstate it. So every bar on
this figure is a median of per-item differences, computed from `items`.

**Why there is a magnified inset.** On one linear axis content is a hairline,
which IS the finding, but a hairline cannot carry a confidence interval. The
inset re-draws the same bar on its own axis, with the magnification printed on
it, so the reader can both see that content is invisible beside identity and
read what it actually is.

**Why the bottom panel exists.** The ratio is pooled over 495 probes and is
not uniform underneath. In five of six families identity dominates; on
`exposure` it inverts and content is the larger of the two. That is not a
defect in the pooled number — exposure probes ask whether the injected object
shows up, so they are the family that asks about content — but a pooled ratio
with no spread behind it is a claim a reader cannot check. Log axis, because
the family values span three orders of magnitude.

    python3 ai/edit-reach/tools/figure_identity_content.py

Writes web/static/img/edit-reach/identity-against-content.svg.
"""
from __future__ import annotations

import json
import math
import pathlib
import random
import statistics

ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = ROOT / "ai" / "edit-reach" / "results" / "E-002-different-subject-arm.json"
OUT = ROOT / "web" / "static" / "img" / "edit-reach" / "identity-against-content.svg"

SEED = 1538          # the paper's pinned seed, so the bars match its CIs
RESAMPLES = 10_000

W = 1000
AX_X0, AX_W = 232, 536
HEAD, AXY = 42, 86
ROW_H, BAR_H = 56, 26
INSET_X, INSET_Y, INSET_W, INSET_H = 232, 236, 318, 104
LOW_HEAD = 400
LOW_AXY = 448
LOW_ROW = 34


def median_ci(values: list[float]) -> tuple[float, float, float]:
    """Median and a 95% percentile bootstrap interval at the pinned seed."""
    rnd = random.Random(SEED)
    n = len(values)
    draws = sorted(statistics.median([values[rnd.randrange(n)] for _ in range(n)])
                   for _ in range(RESAMPLES))
    lo = draws[int(0.025 * RESAMPLES)]
    hi = draws[int(0.975 * RESAMPLES)]
    return statistics.median(values), lo, hi


def main() -> None:
    doc = json.loads(SRC.read_text())
    items = doc["items"]

    content_v = [i["movement"] - i["control_movement"] for i in items]
    identity_v = [i["control_movement"] - i["other_movement"] for i in items]
    content = median_ci(content_v)
    identity = median_ci(identity_v)
    ratio = identity[0] / content[0]

    fams: dict[str, list[dict]] = {}
    for i in items:
        fams.setdefault(i["family"], []).append(i)
    by_fam = {
        f: (statistics.median([i["movement"] - i["control_movement"] for i in v]),
            statistics.median([i["control_movement"] - i["other_movement"] for i in v]),
            len(v))
        for f, v in sorted(fams.items())
    }

    # --- top panel: one linear axis, both pooled differences ------------------
    top = max(identity[2], content[2]) * 1.06
    def x(v: float) -> float:
        return AX_X0 + AX_W * v / top

    b: list[str] = []
    b.append(f'  <text x="{AX_X0 - 22}" y="{HEAD}" class="panel end">'
             f'Pooled over all {len(items)} probes</text>')
    b.append(f'  <text x="{AX_X0}" y="{HEAD}" class="note">'
             f'median of per-probe differences, 95% bootstrap interval</text>')

    ticks = [0, 0.02, 0.04, 0.06]
    for t in ticks:
        b.append(f'  <line x1="{x(t):.1f}" y1="{AXY}" x2="{x(t):.1f}" '
                 f'y2="{AXY + 2 * ROW_H + 8}" class="grid"/>')
        b.append(f'  <text x="{x(t):.1f}" y="{AXY - 10}" class="tick mid">{t:.2f}</text>')
    b.append(f'  <line x1="{AX_X0}" y1="{AXY}" x2="{AX_X0 + AX_W}" y2="{AXY}" class="axis"/>')

    rows = [
        ("identity", "Identity", "whose fact was edited", identity, "warm"),
        ("content", "Content", "what it was changed to", content, "cool"),
    ]
    for ri, (_key, name, gloss, (med, lo, hi), cls) in enumerate(rows):
        y = AXY + 22 + ri * ROW_H
        cy = y + BAR_H / 2
        b.append(f'  <text x="{AX_X0 - 22}" y="{y + 11}" class="rowlab end">{name}</text>')
        b.append(f'  <text x="{AX_X0 - 22}" y="{y + 26}" class="rowsub end">{gloss}</text>')
        b.append(f'  <rect x="{AX_X0}" y="{y}" width="{max(x(med) - AX_X0, 1.4):.2f}" '
                 f'height="{BAR_H}" rx="3" class="{cls}"/>')
        b.append(f'  <line x1="{x(lo):.1f}" y1="{cy}" x2="{x(hi):.1f}" y2="{cy}" class="ci"/>')
        for e in (lo, hi):
            b.append(f'  <line x1="{x(e):.1f}" y1="{cy - 5}" x2="{x(e):.1f}" '
                     f'y2="{cy + 5}" class="ci"/>')
        b.append(f'  <text x="{max(x(hi), x(med)) + 12:.1f}" y="{cy + 4:.0f}" '
                 f'class="val">{med:+.4f}</text>')

    # --- the zoom: content's own axis, with the magnification printed ---------
    zoom_top = content[2] * 1.12
    mag = (AX_W / zoom_top) / (AX_W / top)
    sliver = x(zoom_top)
    b.append(f'  <path d="M{AX_X0} {AXY + 2 * ROW_H + 8} L{INSET_X} {INSET_Y}" class="lead"/>')
    b.append(f'  <path d="M{sliver:.1f} {AXY + 2 * ROW_H + 8} '
             f'L{INSET_X + INSET_W} {INSET_Y}" class="lead"/>')
    b.append(f'  <rect x="{AX_X0}" y="{AXY + ROW_H + 22}" width="{max(sliver - AX_X0, 1.4):.2f}" '
             f'height="{BAR_H}" class="zoombox"/>')
    b.append(f'  <rect x="{INSET_X}" y="{INSET_Y}" width="{INSET_W}" '
             f'height="{INSET_H}" rx="4" class="inset"/>')

    iy = INSET_Y + 62
    def zx(v: float) -> float:
        return INSET_X + 16 + (INSET_W - 76) * v / zoom_top
    b.append(f'  <text x="{INSET_X + 16}" y="{INSET_Y + 24}" class="insetlab">'
             f'Content alone, magnified {mag:.0f}×</text>')
    b.append(f'  <line x1="{zx(0):.1f}" y1="{iy - 10}" x2="{zx(zoom_top):.1f}" '
             f'y2="{iy - 10}" class="axis"/>')
    for t in (0.0, 0.001, 0.002):
        b.append(f'  <text x="{zx(t):.1f}" y="{iy - 18}" class="tick mid">{t:.3f}</text>')
    b.append(f'  <rect x="{zx(0):.1f}" y="{iy}" width="{zx(content[0]) - zx(0):.2f}" '
             f'height="18" rx="2" class="cool"/>')
    b.append(f'  <line x1="{zx(content[1]):.1f}" y1="{iy + 9}" x2="{zx(content[2]):.1f}" '
             f'y2="{iy + 9}" class="ci"/>')
    for e in (content[1], content[2]):
        b.append(f'  <line x1="{zx(e):.1f}" y1="{iy + 4}" x2="{zx(e):.1f}" '
                 f'y2="{iy + 14}" class="ci"/>')
    b.append(f'  <text x="{INSET_X + 16}" y="{INSET_Y + INSET_H - 10}" class="insetnote">'
             f'interval excludes zero — content is detectable</text>')

    # the ratio, stated beside the two bars it is the ratio of
    rx = AX_X0 + AX_W + 24
    b.append(f'  <text x="{rx}" y="{AXY + 70}" class="ratio">×{ratio:.0f}</text>')
    b.append(f'  <text x="{rx}" y="{AXY + 90}" class="rowsub">identity</text>')
    b.append(f'  <text x="{rx}" y="{AXY + 104}" class="rowsub">over content</text>')

    # --- bottom panel: every family, log axis --------------------------------
    lo_v = min(min(c, i) for c, i, _ in by_fam.values()) * 0.6
    hi_v = max(max(c, i) for c, i, _ in by_fam.values()) * 1.6
    def lx(v: float) -> float:
        return AX_X0 + AX_W * (math.log10(v) - math.log10(lo_v)) / (
            math.log10(hi_v) - math.log10(lo_v))

    b.append(f'  <text x="{AX_X0 - 22}" y="{LOW_HEAD}" class="panel end">'
             f'By probe family</text>')
    b.append(f'  <text x="{AX_X0}" y="{LOW_HEAD}" class="note">'
             f'the same two numbers, each line running from content to identity '
             f'— log scale</text>')
    for t in (0.001, 0.01, 0.1):
        b.append(f'  <line x1="{lx(t):.1f}" y1="{LOW_AXY}" x2="{lx(t):.1f}" '
                 f'y2="{LOW_AXY + len(by_fam) * LOW_ROW + 6}" class="grid"/>')
        b.append(f'  <text x="{lx(t):.1f}" y="{LOW_AXY - 10}" class="tick mid">{t:g}</text>')
    b.append(f'  <line x1="{AX_X0}" y1="{LOW_AXY}" x2="{AX_X0 + AX_W}" '
             f'y2="{LOW_AXY}" class="axis"/>')

    order = sorted(by_fam, key=lambda f: by_fam[f][1] / by_fam[f][0])
    for ri, fam in enumerate(order):
        c, i, n = by_fam[fam]
        y = LOW_AXY + 24 + ri * LOW_ROW
        b.append(f'  <text x="{AX_X0 - 22}" y="{y + 4}" class="rowlab end">{fam}</text>')
        b.append(f'  <text x="{AX_X0 - 22}" y="{y + 18}" class="rowsub end">n = {n}</text>')
        x0, x1 = lx(c), lx(i)
        step = 7 if x1 >= x0 else -7
        b.append(f'  <line x1="{x0:.1f}" y1="{y}" x2="{x1 - step:.1f}" y2="{y}" class="span"/>')
        b.append(f'  <circle cx="{x0:.1f}" cy="{y}" r="4.5" class="cool"/>')
        b.append(f'  <path d="M{x1:.1f} {y} L{x1 - step:.1f} {y - 5} '
                 f'L{x1 - step:.1f} {y + 5} Z" class="warm"/>')
        tx = max(x0, x1) + 14
        b.append(f'  <text x="{tx:.1f}" y="{y + 4}" class="famval">'
                 f'×{i / c:.0f}</text>' if i >= c else
                 f'  <text x="{tx:.1f}" y="{y + 4}" class="famval">'
                 f'content larger, ×{c / i:.1f}</text>')

    ly = LOW_AXY + 24 + len(by_fam) * LOW_ROW + 16
    b.append(f'  <circle cx="{AX_X0 + 6}" cy="{ly - 4}" r="4.5" class="cool"/>')
    b.append(f'  <text x="{AX_X0 + 18}" y="{ly}" class="tick">content</text>')
    b.append(f'  <path d="M{AX_X0 + 108} {ly - 4} L{AX_X0 + 101} {ly - 9} '
             f'L{AX_X0 + 101} {ly + 1} Z" class="warm"/>')
    b.append(f'  <text x="{AX_X0 + 116}" y="{ly}" class="tick">identity</text>')

    height = ly + 28

    alt = (
        f"Two panels. The top panel pools all {len(items)} probes on one linear axis and "
        f"draws two medians of per-probe differences: identity, meaning the same-subject "
        f"control minus another person's edit, at {identity[0]:+.4f} with a 95% interval "
        f"of {identity[1]:.4f} to {identity[2]:.4f}; and content, meaning the real edit "
        f"minus the same-subject control, at {content[0]:+.4f} with an interval of "
        f"{content[1]:.4f} to {content[2]:.4f}. On that shared axis content is a hairline, "
        f"so an inset re-draws it magnified {mag:.0f} times, where its interval is visible "
        f"and clears zero. The ratio of the two is {ratio:.0f} to one. The bottom panel "
        f"splits both numbers by probe family on a log axis, each family drawn as a line "
        f"running from its content value to its identity value. Five of six families run "
        f"rightwards — repetition by {by_fam['repetition'][1] / by_fam['repetition'][0]:.0f} "
        f"times, semantics by {by_fam['semantics'][1] / by_fam['semantics'][0]:.0f}, "
        f"position by {by_fam['position'][1] / by_fam['position'][0]:.0f} — while exposure "
        f"runs the other way, its content value "
        f"{by_fam['exposure'][0] / by_fam['exposure'][1]:.1f} times its identity value."
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" role="img" aria-label="{alt}">
  <style type="text/css"><![CDATA[
    /* An SVG loaded as an image is its own document and cannot see the page's
       custom properties, so it carries its own. Every var() keeps a light
       fallback, because the PDF converter does not resolve var() at all. */
    :root {{
        --paper: #f4f1ea;
        --ink: #2b2a28;
        --muted: #55534e;
        --faint: #6b6863;
        --rule: #d9d3c7;
        --cool: #5b4fc4;
        --warm: #a4442f;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
          --paper: #1b1a18;
          --ink: #eeece6;
          --muted: #c2beb5;
          --faint: #9a968e;
          --rule: #3a3833;
          --cool: #8078e0;
          --warm: #c9664a;
      }}
    }}
    text {{ font-family: Lato, "Helvetica Neue", sans-serif; }}
    .panel    {{ font-size: 14px; font-weight: 600; fill: var(--ink, #2b2a28); }}
    .note     {{ font-size: 11.5px; fill: var(--faint, #6b6863); }}
    .rowlab   {{ font-size: 13px; fill: var(--ink, #2b2a28); }}
    .rowsub   {{ font-size: 11px; fill: var(--faint, #6b6863); }}
    .tick     {{ font-size: 11px; fill: var(--faint, #6b6863); }}
    .mid      {{ text-anchor: middle; }}
    .end      {{ text-anchor: end; }}
    /* Numbers on every mark, so identity never rests on colour alone. */
    .val      {{ font-size: 12.5px; font-family: "IBM Plex Mono", ui-monospace, monospace; fill: var(--ink, #2b2a28); }}
    .famval   {{ font-size: 11.5px; font-family: "IBM Plex Mono", ui-monospace, monospace; fill: var(--muted, #55534e); }}
    .ratio    {{ font-size: 26px; font-weight: 600; fill: var(--warm, #a4442f); }}
    .cool     {{ fill: var(--cool, #5b4fc4); }}
    .warm     {{ fill: var(--warm, #a4442f); }}
    .axis     {{ stroke: var(--ink, #2b2a28); stroke-width: 1.2; }}
    .grid     {{ stroke: var(--rule, #d9d3c7); stroke-width: 1; }}
    .ci       {{ stroke: var(--ink, #2b2a28); stroke-width: 1.6; }}
    .span     {{ stroke: var(--rule, #d9d3c7); stroke-width: 2.4; }}
    .lead     {{ stroke: var(--rule, #d9d3c7); stroke-width: 1; fill: none; }}
    .inset    {{ fill: none; stroke: var(--rule, #d9d3c7); stroke-width: 1.2; }}
    .zoombox  {{ fill: none; stroke: var(--rule, #d9d3c7); stroke-width: 1.2; }}
    .insetlab {{ font-size: 12px; font-weight: 600; fill: var(--ink, #2b2a28); }}
    .insetnote{{ font-size: 11px; fill: var(--faint, #6b6863); }}
  ]]></style>

  <rect width="{W}" height="{height}" fill="var(--paper, #f4f1ea)"/>
{chr(10).join(b)}
</svg>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg)
    print(f"wrote {OUT.relative_to(ROOT)}  ({W}×{height})")
    print(f"  identity {identity[0]:+.4f}  ({identity[1]:.4f}, {identity[2]:.4f})")
    print(f"  content  {content[0]:+.4f}  ({content[1]:.4f}, {content[2]:.4f})")
    print(f"  ratio    {ratio:.2f}   inset magnification {mag:.1f}x")
    for f in order:
        c, i, n = by_fam[f]
        print(f"  {f:16} n={n:3d}  content {c:+.5f}  identity {i:+.5f}  ratio {i / c:8.1f}")


if __name__ == "__main__":
    main()
