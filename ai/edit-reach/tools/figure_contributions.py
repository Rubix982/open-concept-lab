"""Draw §5.4 as a heat map: what each half of an edit is carried by.

One rank-one update does two things — it breaks the old answer and it supplies
the new one — and [E-003] scored both on the same 495 probes under three arms.
The paper reports that the two halves put their effect in opposite columns.
This is the grid: six probe families down, the two contributions across, one
panel per half.

The two contributions are differences between arms, so they are read as:

    content  = real edit  -  a different fact about the SAME person
    identity = that same-subject control  -  another person's edit

Content is what changes when you keep the person and change the fact; identity
is what changes when you keep the fact's shape and change the person.

**Diverging, not sequential.** These are signed differences and the sign is the
finding, so the scale needs two hues and a neutral midpoint at zero. The poles
are validated against both surfaces with the dataviz validator rather than
chosen by eye: light #5b4fc4 / #a4442f and dark #8078e0 / #c9664a both pass all
six checks, which the paper's own ink tokens do not on the dark surface — the
oxide text colour reads as gray there.

    python3 ai/edit-reach/tools/figure_contributions.py

Writes web/static/img/edit-reach/what-carries-each-half.svg.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC = ROOT / "ai" / "edit-reach" / "results" / "E-003-destination.json"
OUT = ROOT / "web" / "static" / "img" / "edit-reach" / "what-carries-each-half.svg"

PANELS = [
    ("Destruction — breaking the old answer",
     "destruction_real", "destruction_ctl", "destruction_other"),
    ("Destination — supplying the new one",
     "hit_real", "hit_ctl", "hit_other"),
]

CELL_W, CELL_H = 132, 38
PAD_L, PAD_T, PAD_B = 132, 86, 74
PANEL_GAP = 52


def main() -> None:
    doc = json.loads(SRC.read_text())
    fams = sorted(doc["by_family"])

    panels = []
    for title, real, ctl, other in PANELS:
        grid = {}
        for f in fams:
            g = doc["by_family"][f]
            grid[f] = (g[real] - g[ctl], g[ctl] - g[other])
        panels.append((title, grid))

    peak = max(abs(v) for _, g in panels for pair in g.values() for v in pair)

    panel_w = 2 * CELL_W
    width = PAD_L + len(panels) * panel_w + (len(panels) - 1) * PANEL_GAP + 28
    height = PAD_T + len(fams) * CELL_H + PAD_B

    body: list[str] = []
    for pi, (title, grid) in enumerate(panels):
        left = PAD_L + pi * (panel_w + PANEL_GAP)
        body.append(f'  <text x="{left}" y="{PAD_T - 46}" class="panel">{title}</text>')
        for ci, col in enumerate(("content", "identity")):
            body.append(f'  <text x="{left + ci * CELL_W + CELL_W / 2:.0f}" '
                        f'y="{PAD_T - 18}" class="collab mid">{col}</text>')
        for ri, fam in enumerate(fams):
            for ci, value in enumerate(grid[fam]):
                x, y = left + ci * CELL_W, PAD_T + ri * CELL_H
                cls = "warm" if value >= 0 else "cool"
                op = min(1.0, abs(value) / peak) * 0.92 + 0.04
                body.append(f'  <rect x="{x}" y="{y}" width="{CELL_W - 3}" '
                            f'height="{CELL_H - 3}" class="{cls}" fill-opacity="{op:.3f}"/>')
                body.append(f'  <text x="{x + (CELL_W - 3) / 2:.0f}" '
                            f'y="{y + CELL_H / 2 + 4:.0f}" class="val mid">{value:+.4f}</text>')

    rows = "\n".join(
        f'  <text x="{PAD_L - 14}" y="{PAD_T + i * CELL_H + CELL_H / 2 + 4:.0f}" '
        f'class="rowlab end">{f}</text>' for i, f in enumerate(fams))

    ly = height - 40
    legend = [f'  <text x="{PAD_L - 14}" y="{ly + 13}" class="rowlab end">scale</text>']
    for i, (cls, lab) in enumerate((("cool", f"−{peak:.2f}"), ("cool", "−0"),
                                    ("warm", "+0"), ("warm", f"+{peak:.2f}"))):
        op = (0.96 if i in (0, 3) else 0.08)
        x = PAD_L + i * 30
        legend.append(f'  <rect x="{x}" y="{ly}" width="26" height="18" '
                      f'class="{cls}" fill-opacity="{op:.2f}"/>')
    legend.append(f'  <text x="{PAD_L}" y="{ly + 32}" class="tick">−{peak:.2f}</text>')
    legend.append(f'  <text x="{PAD_L + 120}" y="{ly + 32}" class="tick end">+{peak:.2f}</text>')
    legend.append(f'  <text x="{PAD_L + 140}" y="{ly + 13}" class="tick">'
                  f'difference between two arms, on the same probes</text>')

    d = {f: panels[0][1][f] for f in fams}
    e = {f: panels[1][1][f] for f in fams}
    alt = (
        f"Two heat map panels, six probe families down and two columns across — "
        f"content and identity. Content is the real edit minus a different fact about "
        f"the same person; identity is that control minus another person's edit. In the "
        f"destruction panel the identity column is filled and the content column is "
        f"nearly empty; in the destination panel it is the reverse. For example on "
        f"repetition, destruction splits {d['repetition'][0]:+.4f} content against "
        f"{d['repetition'][1]:+.4f} identity, while destination splits "
        f"{e['repetition'][0]:+.4f} content against {e['repetition'][1]:+.4f} identity. "
        f"Every cell carries its number."
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{alt}">
  <style type="text/css"><![CDATA[
    /* Diverging: two hues and a neutral midpoint, because these are signed
       differences. Both pairs pass all six dataviz checks on their own
       surface; the page's own ink tokens do not on the dark one. */
    :root {{
        --paper: #f4f1ea;
        --ink: #2b2a28;
        --faint: #6b6863;
        --rule: #d9d3c7;
        --cool: #5b4fc4;
        --warm: #a4442f;
        --oncell: #2b2a28;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
          --paper: #1b1a18;
          --ink: #eeece6;
          --faint: #9a968e;
          --rule: #3a3833;
          --cool: #8078e0;
          --warm: #c9664a;
          --oncell: #eeece6;
      }}
    }}
    text {{ font-family: Lato, "Helvetica Neue", sans-serif; }}
    .panel  {{ font-size: 14px; font-weight: 600; fill: var(--ink, #2b2a28); }}
    .collab {{ font-size: 12px; fill: var(--faint, #6b6863); letter-spacing: 0.04em; text-transform: uppercase; }}
    .rowlab {{ font-size: 12px; fill: var(--faint, #6b6863); }}
    .tick   {{ font-size: 11px; fill: var(--faint, #6b6863); }}
    .mid    {{ text-anchor: middle; }}
    .end    {{ text-anchor: end; }}
    /* The number is in every cell, so identity never rests on colour alone. */
    .val    {{ font-size: 11.5px; font-family: "IBM Plex Mono", ui-monospace, monospace; fill: var(--oncell, #2b2a28); }}
    .cool   {{ fill: var(--cool, #5b4fc4); }}
    .warm   {{ fill: var(--warm, #a4442f); }}
  ]]></style>

  <rect width="{width}" height="{height}" fill="var(--paper, #f4f1ea)"/>
{rows}
{chr(10).join(body)}
{chr(10).join(legend)}
</svg>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg)
    print(f"wrote {OUT.relative_to(ROOT)}")
    for title, grid in panels:
        print(f"  {title}")
        for f in fams:
            print(f"    {f:16} content {grid[f][0]:+.4f}   identity {grid[f][1]:+.4f}")


if __name__ == "__main__":
    main()
