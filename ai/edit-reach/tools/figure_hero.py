"""The finding in one frame, for the top of the paper.

Every other figure here answers a question the reader already has. This one is
read before the reader has any question at all, so it carries the result and
nothing else: an edit lands on whatever names the subject, and does not reach
the facts that actually depend on it.

The four numbers are the same ones [E-046] and [E-004] put in the near/far
figure, read from the same two files rather than typed in, so the hero and the
figure it introduces cannot drift apart. Llama-3.1-8B at layer 5, the model and
depth the rest of the paper quotes by default.

What the picture has to get right is that the light follows the *name*, not the
dependency. So every question out in the dark keeps its dependency line: all of
them genuinely rest on the fact that was edited, every line is drawn, and not
one of them lights up.

A first version split the dark field into questions that depend on the edit and
questions that do not. That misreads the measurement. Both far-field numbers are
read on the *same* questions — {own} is what one receives from its own edit and
{floor} from a stranger's. The pair that cannot be told apart is two sources,
not two sets of questions.

    python3 ai/edit-reach/tools/figure_hero.py

Writes web/static/img/edit-reach/where-the-edit-lands.svg.
"""
from __future__ import annotations

import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
RES = ROOT / "ai" / "edit-reach" / "results"
NEAR = RES / "E-046-near-field-floor.json"
FAR = RES / "E-004-far-field-floor.json"
OUT = ROOT / "web" / "static" / "img" / "edit-reach" / "where-the-edit-lands.svg"

MODEL = "meta-llama/Llama-3.1-8B"

W, H = 1000, 620
CX, CY = 265, 300          # centre of the lit field
RX, RY = 162, 118          # where the near-field questions sit around it
BOUND = 520                # where the question stops naming the subject

# Six questions that all name the subject and ask six different things. The
# labels are the argument: the coefficient does not read what is being asked.
NEAR_Q = [(90, "born where?"), (30, "wrote what?"), (330, "which language?"),
          (270, "died when?"), (210, "nationality?"), (150, "his publisher?")]

# Out in the dark. Every one of these is a question that genuinely rests on the
# edited fact and never names its subject, so every one keeps a dependency line.
FAR_Q = [(600, 186), (740, 162), (872, 194), (938, 280),
         (604, 322), (762, 292), (892, 350), (698, 410)]


def pill(x: float, y: float, text: str, lit: bool) -> str:
    w = 11.0 + 6.35 * len(text)
    h = 27.0
    cls = "qlit" if lit else "qdark"
    tcl = "qlit-t" if lit else "qdark-t"
    return (f'  <g><rect x="{x - w / 2:.1f}" y="{y - h / 2:.1f}" width="{w:.1f}" '
            f'height="{h:.1f}" rx="13.5" class="{cls}"/>'
            f'<text x="{x:.1f}" y="{y + 4.2:.1f}" class="{tcl}">{text}</text></g>')


def main() -> None:
    near = json.loads(NEAR.read_text())["by_model"][MODEL]
    far = json.loads(FAR.read_text())["hop2"]
    n_own, n_floor = near["own_median"], near["floor_same_relation"]
    f_own, f_floor = far["own_median"], far["floor_same_relation"]

    b: list[str] = []

    # spokes first, so the pills sit on top of them
    pts = []
    for deg, label in NEAR_Q:
        r = math.radians(deg)
        pts.append((CX + RX * math.cos(r), CY - RY * math.sin(r), label))
    for x, y, _ in pts:
        b.append(f'  <path d="M{CX} {CY} L{x:.1f} {y:.1f}" class="spoke"/>')

    b.append(pill(CX, CY, "the edited name", True))
    for x, y, label in pts:
        b.append(pill(x, y, label, True))

    # Every dependency line leaves the lit field and keeps going.
    #
    # The start points are spread evenly along the halo's right edge, ordered by
    # how high the target sits, rather than taken in each target's own direction.
    # Direction-based starts put four of the eight within two degrees of each
    # other, and the lines left the figure as a knot — visible only on a render.
    ordered = sorted(FAR_Q, key=lambda q: q[1])
    n_q = len(ordered)
    for i, (x, y) in enumerate(ordered):
        a = math.radians(-42 + 84 * i / (n_q - 1))
        sx, sy = CX + 198 * math.cos(a), CY + 152 * math.sin(a)
        mx, my = (sx + x) / 2, (sy + y) / 2 - 16
        b.append(f'  <path d="M{sx:.0f} {sy:.0f} Q{mx:.0f} {my:.0f} '
                 f'{x - 14:.0f} {y:.0f}" class="dep"/>')
    for x, y in FAR_Q:
        b.append(f'  <circle cx="{x}" cy="{y}" r="13" class="dark"/>')

    body = "\n".join(b)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"
     width="{W}" height="{H}" role="img"
     aria-label="One picture of where a rank-one edit arrives. On the left, a lit
     field: the edited name at the centre, ringed by six questions that all name
     it and each ask something different — where he was born, what he wrote,
     which language he spoke, when he died, his nationality, his publisher. Every
     one of them is filled in, and the reading beneath them is
     {n_own:.4f}, against {n_floor:.4f} for an unrelated edit on the same
     relation. On the right, past a dashed boundary marked the question never
     names the subject, eight hollow circles sit on bare paper. Every one of them
     keeps a dependency line back to the edited name, because every one of them
     genuinely rests on the fact that was changed — and not one is filled in. The
     reading there is {f_own:.4f} from the question's own edit and {f_floor:.4f}
     from a stranger's, which is the same number twice.">
  <style type="text/css"><![CDATA[
    /* An <img> is its own document and cannot see the page's custom properties,
       but its own stylesheet is honoured, media queries included. Every var()
       keeps a light fallback so the PDF converter, which never reads :root,
       renders what a reader sees. */
    :root {{
      --paper: #f4f1ea;
      --ink: #2b2a28;
      --muted: #55534e;
      --faint: #6b6863;
      --oxide: #a4442f;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --paper: #1b1a18;
        --ink: #eeece6;
        --muted: #c2beb5;
        --faint: #9a968e;
        --oxide: #e3977f;
      }}
      rect[filter*="grain"] {{ display: none; }}
    }}
    .h    {{ font-family: Lato, sans-serif; font-size: 15px; font-weight: 900;
             letter-spacing: 0.9px; fill: var(--ink, #2b2a28); }}
    .sub  {{ font-family: Georgia, serif; font-size: 13.5px; font-style: italic;
             fill: var(--faint, #6b6863); }}
    .zone {{ font-family: "IBM Plex Mono", monospace; font-size: 10.5px;
             letter-spacing: 1.4px; fill: var(--faint, #6b6863); }}
    .spoke {{ stroke: var(--oxide, #a4442f); stroke-width: 1.6; opacity: 0.45;
              fill: none; }}
    .dep  {{ stroke: var(--faint, #6b6863); stroke-width: 1.3; fill: none;
             stroke-dasharray: 5 5; opacity: 0.62; }}
    .qlit {{ fill: var(--oxide, #a4442f); }}
    .qlit-t {{ font-family: Georgia, serif; font-size: 12px; text-anchor: middle;
               fill: var(--paper, #f4f1ea); }}
    .dark {{ fill: none; stroke: var(--faint, #6b6863); stroke-width: 1.5;
             opacity: 0.72; }}
    .big  {{ font-family: "IBM Plex Mono", monospace; font-size: 31px;
             fill: var(--oxide, #a4442f); }}
    .bigd {{ font-family: "IBM Plex Mono", monospace; font-size: 31px;
             fill: var(--muted, #55534e); }}
    .num  {{ font-family: "IBM Plex Mono", monospace; font-size: 13px;
             fill: var(--muted, #55534e); }}
    .lab  {{ font-family: Georgia, serif; font-size: 12.5px;
             fill: var(--faint, #6b6863); }}
    .verdict {{ font-family: Georgia, serif; font-size: 13.5px;
                fill: var(--ink, #2b2a28); }}
  ]]></style>

  <defs>
    <radialGradient id="halo" cx="50%" cy="50%" r="50%">
      <stop offset="0%"   stop-color="var(--oxide, #a4442f)" stop-opacity="0.19"/>
      <stop offset="62%"  stop-color="var(--oxide, #a4442f)" stop-opacity="0.07"/>
      <stop offset="100%" stop-color="var(--oxide, #a4442f)" stop-opacity="0"/>
    </radialGradient>
    <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9"
      numOctaves="1" seed="4"/><feColorMatrix
      values="0 0 0 0 0.35  0 0 0 0 0.3  0 0 0 0 0.2  0 0 0 0.05 0"/></filter>
  </defs>

  <rect width="{W}" height="{H}" fill="var(--paper, #f4f1ea)"/>
  <rect width="{W}" height="{H}" filter="url(#grain)"/>

  <text x="40" y="44" class="h">WHERE A RANK-ONE EDIT ACTUALLY LANDS</text>
  <text x="40" y="68" class="sub">Fraction of the update arriving at a question's last token, computable before the edit is made. Llama-3.1-8B, layer 5.</text>

  <ellipse cx="{CX}" cy="{CY}" rx="268" ry="212" fill="url(#halo)"/>

  <path d="M{BOUND} 104 V{H - 134}" stroke="var(--faint, #6b6863)" stroke-width="1"
        stroke-dasharray="3 7" opacity="0.5" fill="none"/>

  <text x="40" y="118" class="zone">THE QUESTION NAMES THE EDITED SUBJECT</text>
  <text x="{BOUND + 20}" y="118" class="zone">IT NEVER DOES</text>

{body}

  <path d="M{BOUND + 20} 136 h26" class="dep"/>
  <text x="{BOUND + 54}" y="140" class="lab">each of these genuinely rests on the fact that was edited</text>

  <path d="M40 {H - 118} H{W - 40}" stroke="var(--faint, #6b6863)" stroke-width="1" opacity="0.3" fill="none"/>

  <text x="40" y="{H - 90}" class="lab">from the question's own edit</text>
  <text x="40" y="{H - 54}" class="big">{n_own:.4f}</text>
  <text x="180" y="{H - 56}" class="num">· {n_floor:.4f} from a stranger's</text>
  <text x="40" y="{H - 24}" class="verdict">It arrives whatever the question goes on to ask.</text>

  <text x="{BOUND + 20}" y="{H - 90}" class="lab">from the question's own edit</text>
  <text x="{BOUND + 20}" y="{H - 54}" class="bigd">{f_own:.4f}</text>
  <text x="{BOUND + 160}" y="{H - 56}" class="num">· {f_floor:.4f} from a stranger's</text>
  <text x="{BOUND + 20}" y="{H - 24}" class="verdict">Nothing here to tell apart.</text>
</svg>
"""
    OUT.write_text(svg)
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  near {n_own:.4f} vs {n_floor:.4f}   far {f_own:.4f} vs {f_floor:.4f}")


if __name__ == "__main__":
    main()
