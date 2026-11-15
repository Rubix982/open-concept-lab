"""Near and far field, three models, under the same matched floor.

Replaces a hand-drawn figure that showed one model and printed a floor of 0.0506
that no run produces ([E-046]). Generated from the run files instead, so the
marks and the numbers beside them cannot drift apart again.

Both regimes use the **same-relation** floor, which is the one §5's table
reports and the tighter of the two: a donor sharing the relation is topically as
close to the question as the real subject is, so it is the control that can
actually be wrong.

What the figure has to show is a contrast between two contrasts. In the near
field the real edit and the stranger's are far apart on every model. In the far
field they are the same mark on every model. The three models disagree about
*how* far apart the near-field pair is — GPT-J reads 0.7985 where the Llamas
read 0.93 — and agree completely about the far field being nothing.

    python3 ai/edit-reach/tools/figure_near_far.py

Writes web/static/img/edit-reach/near-and-far-field.svg.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
RES = ROOT / "ai" / "edit-reach" / "results"
NEAR = RES / "E-046-near-field-floor.json"
OUT = ROOT / "web" / "static" / "img" / "edit-reach" / "near-and-far-field.svg"

FAR = {
    "meta-llama/Llama-3.1-8B": "E-004-far-field-floor.json",
    "meta-llama/Llama-3.1-70B": "E-004-far-field-floor-meta-llama_Llama-3.1-70B.json",
    "EleutherAI/gpt-j-6b": "E-004-far-field-floor-EleutherAI_gpt-j-6b.json",
}
LABEL = {"meta-llama/Llama-3.1-8B": "Llama-3.1-8B",
         "meta-llama/Llama-3.1-70B": "Llama-3.1-70B",
         "EleutherAI/gpt-j-6b": "GPT-J-6B"}
ORDER = list(FAR)

W, H = 1000, 500
PAD_L, PAD_R, PAD_T, PAD_B = 150, 150, 74, 58
PLOT_W = W - PAD_L - PAD_R
ROW_H = 58
PANEL_GAP = 46


def x_of(v: float) -> float:
    return PAD_L + v * PLOT_W


def main() -> None:
    near = json.loads(NEAR.read_text())["by_model"]
    far = {m: json.loads((RES / f).read_text())["hop2"] for m, f in FAR.items()}
    body: list[str] = []
    y = PAD_T

    for panel, (title, note) in enumerate(
            [("Near field", "the question names the edited subject"),
             ("Far field", "the question never names it")]):
        body.append(f'  <text x="{PAD_L}" y="{y - 26:.0f}" class="panel">{title}</text>')
        body.append(f'  <text x="{PAD_L}" y="{y - 9:.0f}" class="sub">{note}</text>')
        for model in ORDER:
            d = near[model] if panel == 0 else far[model]
            own = d["own_median"]
            floor = d["floor_same_relation"]
            exc = d["excess_over_same_relation"] if panel == 0 \
                else d["excess_over_same_relation"]
            body.append(f'  <text x="{PAD_L - 14:.0f}" y="{y + 5:.0f}" '
                        f'class="rowlab end">{LABEL[model]}</text>')
            body.append(f'  <path d="M{PAD_L} {y:.0f} H{PAD_L + PLOT_W}" class="rail"/>')
            # The connector is the claim: its length is what the control buys.
            lo, hi = sorted((x_of(floor), x_of(own)))
            body.append(f'  <path d="M{lo:.1f} {y:.0f} H{hi:.1f}" class="span"/>')
            body.append(f'  <circle cx="{x_of(floor):.1f}" cy="{y:.0f}" r="6" class="ring"/>')
            body.append(f'  <circle cx="{x_of(floor):.1f}" cy="{y:.0f}" r="4.5" class="floor"/>')
            body.append(f'  <circle cx="{x_of(own):.1f}" cy="{y:.0f}" r="6" class="ring"/>')
            body.append(f'  <circle cx="{x_of(own):.1f}" cy="{y:.0f}" r="4.5" class="own"/>')
            body.append(f'  <text x="{PAD_L + PLOT_W + 14:.0f}" y="{y + 5:.0f}" '
                        f'class="exc">{exc:+.4f}</text>')
            y += ROW_H
        y += PANEL_GAP

    # one shared axis, drawn once, because the two panels share a scale
    axis_y = y - PANEL_GAP - ROW_H + 34
    for v in (0.0, 0.25, 0.5, 0.75, 1.0):
        body.append(f'  <path d="M{x_of(v):.1f} {PAD_T - 42:.0f} V{axis_y:.0f}" class="grid"/>')
        body.append(f'  <text x="{x_of(v):.1f}" y="{axis_y + 20:.0f}" class="tick mid">{v:.2f}</text>')
    body.append(f'  <text x="{PAD_L + PLOT_W / 2:.0f}" y="{axis_y + 42:.0f}" '
                f'class="sub mid">coefficient — the fraction of the update the token receives</text>')
    body.append(f'  <text x="{PAD_L + PLOT_W + 14:.0f}" y="{PAD_T - 26:.0f}" class="sub">excess</text>')

    # legend: two marks, named, so identity never rests on colour
    lx = PAD_L
    body.append(f'  <circle cx="{lx:.0f}" cy="{PAD_T - 52:.0f}" r="4.5" class="own"/>')
    body.append(f'  <text x="{lx + 11:.0f}" y="{PAD_T - 48:.0f}" class="sub">the subject\'s own edit</text>')
    body.append(f'  <circle cx="{lx + 180:.0f}" cy="{PAD_T - 52:.0f}" r="4.5" class="floor"/>')
    body.append(f'  <text x="{lx + 191:.0f}" y="{PAD_T - 48:.0f}" class="sub">a stranger\'s, same relation</text>')

    n8 = near["meta-llama/Llama-3.1-8B"]
    f8 = far["meta-llama/Llama-3.1-8B"]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"
     width="{W}" height="{H}" role="img"
     aria-label="Two panels on one shared scale from 0 to 1, three models in each.
     In the near field, where the question names the edited subject, the subject's
     own edit and a stranger's edit on the same relation sit far apart on every
     model: {n8['own_median']:.4f} against {n8['floor_same_relation']:.4f} on
     Llama-3.1-8B, an excess of {n8['excess_over_same_relation']:+.4f}, and
     0.7985 against 0.1563 on GPT-J-6B. In the far field, where the question never
     names the subject, the two marks are one mark on every model:
     {f8['own_median']:.4f} against {f8['floor_same_relation']:.4f} on
     Llama-3.1-8B, an excess of {f8['excess_over_same_relation']:+.4f}.">
  <style><![CDATA[
    :root {{
        --paper: #f4f1ea; --ink: #2b2a28; --faint: #6b6863; --rule: #d9d3c7;
        --own: #5b4fc4; --floor: #a4442f;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
          --paper: #1b1a18; --ink: #eeece6; --faint: #9a968e; --rule: #3a3833;
          --own: #8078e0; --floor: #c9664a;
      }}
    }}
    text {{ font-family: Lato, "Helvetica Neue", sans-serif; }}
    .mid {{ text-anchor: middle; }} .end {{ text-anchor: end; }}
    .panel {{ font-size: 15px; font-weight: 600; fill: var(--ink, #2b2a28); }}
    .sub   {{ font-size: 12px; fill: var(--faint, #6b6863); }}
    .rowlab{{ font-size: 12.5px; fill: var(--ink, #2b2a28); }}
    .tick  {{ font-size: 11px; fill: var(--faint, #6b6863); }}
    .grid  {{ stroke: var(--rule, #d9d3c7); stroke-width: 1; }}
    .rail  {{ stroke: var(--rule, #d9d3c7); stroke-width: 1; }}
    .span  {{ stroke: var(--ink, #2b2a28); stroke-width: 2; opacity: 0.55; }}
    .ring  {{ fill: var(--paper, #f4f1ea); }}
    .own   {{ fill: var(--own, #5b4fc4); }}
    .floor {{ fill: var(--floor, #a4442f); }}
    /* The excess is printed on every row, so the figure survives grayscale. */
    .exc   {{ font-size: 12px; font-family: "IBM Plex Mono", ui-monospace, monospace;
              fill: var(--ink, #2b2a28); }}
  ]]></style>

  <rect width="{W}" height="{H}" fill="var(--paper, #f4f1ea)"/>
{chr(10).join(body)}
</svg>
"""
    OUT.write_text(svg)
    print(f"{OUT.relative_to(ROOT)}")
    for m in ORDER:
        print(f"  {LABEL[m]:<16} near {near[m]['own_median']:.4f} vs "
              f"{near[m]['floor_same_relation']:.4f}   far "
              f"{far[m]['own_median']:.4f} vs {far[m]['floor_same_relation']:.4f}")


if __name__ == "__main__":
    main()
