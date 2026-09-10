"""
build_deck.py — render the trajectory walkthrough into a designed PPTX.

Structure (2026-08-24): a LEAN ~6-min CORE spine for a first-call conversation,
then a LIVE handoff to results/, then BACKUP slides (detail tables, engineering,
hard-Qs) shown on demand / during the live walkthrough. Content is structured in
this file so layout / tables / diagram / notes stay controlled.

Switch the look with THEME below ("midnight" | "slate" | "paper").

Run in the project venv:
    source .venv/bin/activate
    python presentation/build_deck.py     # or .venv/bin/python if the shell aliases python
Output: presentation/DECK_trajectory.pptx
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

# ── themes ────────────────────────────────────────────────────────────────────
THEME = "midnight"   # "midnight" | "slate" | "paper"

THEMES = {
    "midnight": dict(
        BG=0x0F1320, PANEL=0x161C2E, PANEL2=0x1E2540, FG=0xEAECF4, MUTE=0x8A93A8,
        ACCENT=0x7C9CFF, ACCENT2=0xF6A96B, GOOD=0x6FD39A, BAD=0xF58AA0,
        SEP=0x2A3247, HEADTX=0x0F1320,
    ),
    "slate": dict(
        BG=0x14161B, PANEL=0x1A1E26, PANEL2=0x222834, FG=0xE6E8EC, MUTE=0x9AA0AA,
        ACCENT=0x4FC3F7, ACCENT2=0xFFB74D, GOOD=0x6FCF97, BAD=0xE57373,
        SEP=0x2A3038, HEADTX=0x14161B,
    ),
    "paper": dict(
        BG=0xF7F7F4, PANEL=0xFFFFFF, PANEL2=0xEEF1F6, FG=0x1A1D24, MUTE=0x6B7280,
        ACCENT=0x2D5BFF, ACCENT2=0xC2410C, GOOD=0x15803D, BAD=0xB91C1C,
        SEP=0xD9DEE7, HEADTX=0xFFFFFF,
    ),
}
_t = THEMES[THEME]
def _c(k): return RGBColor((_t[k] >> 16) & 0xFF, (_t[k] >> 8) & 0xFF, _t[k] & 0xFF)
BG, PANEL, PANEL2, FG, MUTE = _c("BG"), _c("PANEL"), _c("PANEL2"), _c("FG"), _c("MUTE")
ACCENT, ACCENT2, GOOD, BAD = _c("ACCENT"), _c("ACCENT2"), _c("GOOD"), _c("BAD")
SEP, HEADTX = _c("SEP"), _c("HEADTX")

SLIDE_W, SLIDE_H = Emu(12192000), Emu(6858000)
MARGIN = Emu(760000)
USABLE = Emu(int(SLIDE_W) - 2 * int(MARGIN))
FONT, MONO = "Helvetica Neue", "Menlo"
REPO = Path(__file__).resolve().parent.parent   # image paths resolve from repo root


@dataclass
class Slide:
    tag: str
    title: str
    time: str = ""
    bullets: list = field(default_factory=list)
    table: list | None = None
    table_colors: dict | None = None
    diagram: str | None = None
    notes: str = ""
    big: str | None = None
    divider: bool = False        # section divider (big centred label)
    image: str | None = None     # repo-relative PNG path; centred, with optional caption


# ── primitives ────────────────────────────────────────────────────────────────
def _set_bg(slide):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG


def _tb(slide, left, top, w, h):
    b = slide.shapes.add_textbox(left, top, w, h)
    b.text_frame.word_wrap = True
    return b.text_frame


def _run(p, text, size, color=FG, bold=False, italic=False, font=FONT):
    r = p.add_run()
    r.text, r.font.size = text, Pt(size)
    r.font.color.rgb, r.font.bold, r.font.italic, r.font.name = color, bold, italic, font
    return r


def _rect(slide, left, top, w, h, fill, line=None, line_w=1.0, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, left, top, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(line_w)
    s.shadow.inherit = False
    return s


def _emit_inline(p, text, size, base):
    """**bold**, *italic*, `mono`, [[green]], {{red}}, <<amber>>."""
    pat = r"(\*\*.*?\*\*|`.*?`|\[\[.*?\]\]|\{\{.*?\}\}|<<.*?>>|\*[^*\n]+?\*)"
    for tok in re.split(pat, text):
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            _run(p, tok[2:-2], size, FG, bold=True)
        elif tok.startswith("`") and tok.endswith("`"):
            _run(p, tok[1:-1], size, ACCENT, font=MONO)
        elif tok.startswith("[[") and tok.endswith("]]"):
            _run(p, tok[2:-2], size, GOOD, bold=True)
        elif tok.startswith("{{") and tok.endswith("}}"):
            _run(p, tok[2:-2], size, BAD, bold=True)
        elif tok.startswith("<<") and tok.endswith(">>"):
            _run(p, tok[2:-2], size, ACCENT2, bold=True)
        elif tok.startswith("*") and tok.endswith("*"):
            _run(p, tok[1:-1], size, base, italic=True)
        else:
            _run(p, tok, size, base)


def _pill(slide, left, top, text, fg, bg, size=12, bold=True):
    w = Emu(int(230000 + len(text) * 92000))
    s = _rect(slide, left, top, w, Emu(340000), bg, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    tf = s.text_frame
    tf.margin_top = tf.margin_bottom = Emu(8000)
    tf.margin_left = tf.margin_right = Emu(120000)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    _run(p, text, size, fg, bold=bold)
    return w


# ── table (borderless, banded, accent header band) ────────────────────────────
def _clean_table_style(tbl):
    tblPr = tbl._tbl.find(qn("a:tblPr"))
    if tblPr is None:
        tblPr = etree.SubElement(tbl._tbl, qn("a:tblPr"))
    tblPr.set("firstRow", "0"); tblPr.set("bandRow", "0")
    for old in tblPr.findall(qn("a:tableStyleId")):
        tblPr.remove(old)
    sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
    sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # No Style, No Grid


def _cell_border_bottom(cell, color, w=9525):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        for el in tcPr.findall(qn(tag)):
            tcPr.remove(el)
    made = []
    for tag, col in (("a:lnL", None), ("a:lnR", None), ("a:lnT", None), ("a:lnB", color)):
        ln = etree.SubElement(tcPr, qn(tag))
        ln.set("w", str(w if col else 12700)); ln.set("cap", "flat")
        if col is None:
            etree.SubElement(ln, qn("a:noFill"))
        else:
            sf = etree.SubElement(ln, qn("a:solidFill"))
            etree.SubElement(sf, qn("a:srgbClr")).set("val", str(col))
        made.append(ln)
    for el in made:
        tcPr.remove(el)
    for el in reversed(made):
        tcPr.insert(0, el)


def _add_table(slide, rows, top, colors=None):
    colors = colors or {}
    n_rows, n_cols = len(rows), len(rows[0])
    gf = slide.shapes.add_table(n_rows, n_cols, MARGIN, top, USABLE,
                                Emu(560000 * n_rows))
    tbl = gf.table
    _clean_table_style(tbl)
    if n_cols == 2:
        tbl.columns[0].width = Emu(int(int(USABLE) * 0.56))
        tbl.columns[1].width = Emu(int(int(USABLE) * 0.44))
    elif n_cols == 3:
        tbl.columns[0].width = Emu(int(int(USABLE) * 0.46))
        tbl.columns[1].width = Emu(int(int(USABLE) * 0.29))
        tbl.columns[2].width = Emu(int(int(USABLE) * 0.25))
    for r in range(n_rows):
        tbl.rows[r].height = Emu(620000 if r else 560000)
        for c in range(n_cols):
            cell = tbl.cell(r, c)
            head = r == 0
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            _run(p, rows[r][c], 15,
                 HEADTX if head else colors.get((r, c), FG if c == 0 else MUTE),
                 bold=head or c == 0)
            cell.fill.solid()
            cell.fill.fore_color.rgb = (
                ACCENT if head else (PANEL if r % 2 else PANEL2))
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = cell.margin_right = Emu(160000)
            cell.margin_top = cell.margin_bottom = Emu(40000)
            _cell_border_bottom(cell, None if head else SEP, w=9525)


# ── pipeline diagram ──────────────────────────────────────────────────────────
def _add_pipeline(slide, top):
    boxes = [("ROUTE", "m", None), ("APPLY", "m", None), ("PROBE", "n", None),
             ("DETECT", "x", "novel"), ("RECONCILE", "m", "v2"), ("CERTIFY", "x", "novel")]
    n = len(boxes)
    bw, bh = Emu(1560000), Emu(840000)
    gap = Emu(int((int(USABLE) - int(bw) * n) / (n - 1)))
    fill = {"m": PANEL, "n": PANEL2, "x": PANEL2}
    line = {"m": SEP, "n": SEP, "x": ACCENT}
    txt = {"m": MUTE, "n": FG, "x": ACCENT}
    x = MARGIN
    mid = Emu(int(top) + int(bh) // 2)
    for i, (label, kind, sub) in enumerate(boxes):
        b = _rect(slide, x, top, bw, bh, fill[kind], line[kind],
                  1.5 if kind == "x" else 1.0, MSO_SHAPE.ROUNDED_RECTANGLE)
        tf = b.text_frame; tf.margin_top = tf.margin_bottom = Emu(18000)
        pp = tf.paragraphs[0]; pp.alignment = PP_ALIGN.CENTER
        _run(pp, label, 13, txt[kind], bold=True)
        if sub:
            sp = tf.add_paragraph(); sp.alignment = PP_ALIGN.CENTER
            _run(sp, sub, 9, MUTE, italic=True)
        if i < n - 1:
            gx = Emu(int(x) + int(bw))
            gp = _tb(slide, gx, Emu(int(mid) - 150000), gap, Emu(300000)).paragraphs[0]
            gp.alignment = PP_ALIGN.CENTER
            _run(gp, "→", 20, MUTE, bold=True)
        x = Emu(int(x) + int(bw) + int(gap))
    lp = _tb(slide, MARGIN, Emu(int(top) + int(bh) + 210000), USABLE, Emu(400000)).paragraphs[0]
    _run(lp, "■ ", 14, MUTE); _run(lp, "adopted (DMM Gov)      ", 13, MUTE)
    _run(lp, "■ ", 14, ACCENT); _run(lp, "novel — build + measure      ", 13, ACCENT)
    _run(lp, "RECONCILE = v2", 13, MUTE, italic=True)


# ── frame ─────────────────────────────────────────────────────────────────────
def _frame(slide, sl, idx, total):
    _rect(slide, Emu(0), Emu(0), SLIDE_W, Emu(56000), ACCENT)
    _pill(slide, MARGIN, Emu(430000), sl.tag, ACCENT, PANEL2)
    if sl.time:
        w = Emu(int(230000 + len(f"⏱ {sl.time}") * 92000))
        _pill(slide, Emu(int(SLIDE_W) - int(MARGIN) - int(w)), Emu(430000),
              f"⏱ {sl.time}", MUTE, PANEL)
    _tb(slide, MARGIN, Emu(870000), USABLE, Emu(900000))
    _run(slide.shapes[-1].text_frame.paragraphs[0], sl.title, 28, FG, bold=True)
    _rect(slide, MARGIN, Emu(1660000), USABLE, Emu(15000), SEP)
    _rect(slide, MARGIN, Emu(1636000), Emu(720000), Emu(60000), ACCENT)
    fp = _tb(slide, MARGIN, Emu(int(SLIDE_H) - 470000), USABLE, Emu(300000)).paragraphs[0]
    _run(fp, "Consistency seam · a trajectory", 10, MUTE)
    rp = _tb(slide, MARGIN, Emu(int(SLIDE_H) - 470000), USABLE, Emu(300000)).paragraphs[0]
    rp.alignment = PP_ALIGN.RIGHT
    _run(rp, f"{idx:02d} / {total:02d}", 10, MUTE)
    _rect(slide, Emu(0), Emu(int(SLIDE_H) - 46000), SLIDE_W, Emu(46000), PANEL2)
    _rect(slide, Emu(0), Emu(int(SLIDE_H) - 46000),
          Emu(int(int(SLIDE_W) * idx / total)), Emu(46000), ACCENT)


def _add_bullets(slide, bullets, top):
    tf = _tb(slide, MARGIN, top, USABLE, Emu(int(SLIDE_H) - int(top) - 560000))
    first = True
    for item in bullets:
        text, level = (item if isinstance(item, tuple) else (item, 0))
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        p.space_after = Pt(8 if level == 0 else 5)
        p.line_spacing = 1.08
        size = 18 - (2 if level else 0)
        _run(p, f"{'    ' * level}{'●  ' if level == 0 else '–  '}",
             size, ACCENT if level == 0 else MUTE)
        _emit_inline(p, text, size, FG if level == 0 else MUTE)


# ── builder ───────────────────────────────────────────────────────────────────
def build(deck, out: Path, subtitle: str):
    prs = Presentation()
    prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H
    blank = prs.slide_layouts[6]

    # title
    s = prs.slides.add_slide(blank); _set_bg(s)
    _rect(s, Emu(0), Emu(0), SLIDE_W, Emu(56000), ACCENT)
    _rect(s, MARGIN, Emu(2560000), Emu(760000), Emu(66000), ACCENT2)
    tf = _tb(s, MARGIN, Emu(2720000), USABLE, Emu(1600000))
    _run(tf.paragraphs[0], "Knowledge editing → the consistency seam", 40, FG, bold=True)
    _run(tf.add_paragraph(), "a trajectory", 40, ACCENT, bold=True)
    _run(_tb(s, MARGIN, Emu(4480000), USABLE, Emu(700000)).paragraphs[0],
         subtitle, 16, MUTE)
    _rect(s, Emu(0), Emu(int(SLIDE_H) - 46000), SLIDE_W, Emu(46000), PANEL2)
    s.notes_slide.notes_text_frame.text = (
        "~6 min spoken (the CORE), then a LIVE walkthrough of results/. Slow, honest, "
        "invite steering. Deck is a backstop, not a script.")

    total = len(deck) + 1
    for i, sl in enumerate(deck, start=2):
        s = prs.slides.add_slide(blank); _set_bg(s)
        if sl.divider:
            _rect(s, Emu(0), Emu(0), SLIDE_W, Emu(56000), ACCENT2)
            tf = _tb(s, MARGIN, Emu(2950000), USABLE, Emu(1000000))
            p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
            _run(p, sl.title, 30, MUTE, bold=True)
            _rect(s, Emu(0), Emu(int(SLIDE_H) - 46000), SLIDE_W, Emu(46000), PANEL2)
            if sl.notes:
                s.notes_slide.notes_text_frame.text = sl.notes
            continue
        _frame(s, sl, i, total)
        body_top = Emu(1900000)
        if sl.image:
            top = Emu(1900000)
            h = Emu(3500000) if sl.bullets else Emu(3950000)
            pic = s.shapes.add_picture(str(REPO / sl.image), Emu(0), top, height=h)
            pic.left = Emu(int((int(SLIDE_W) - int(pic.width)) // 2))
            if sl.bullets:
                cap = _tb(s, MARGIN, Emu(int(top) + int(h) + 130000), USABLE, Emu(520000))
                cp = cap.paragraphs[0]; cp.alignment = PP_ALIGN.CENTER
                first = sl.bullets[0]
                _emit_inline(cp, first[0] if isinstance(first, tuple) else first, 14, MUTE)
        else:
            if sl.big:
                tf = _tb(s, MARGIN, Emu(2650000), USABLE, Emu(2000000))
                p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; p.line_spacing = 1.2
                _emit_inline(p, sl.big, 24, FG)
            if sl.bullets:
                _add_bullets(s, sl.bullets, body_top)
            if sl.table:
                _add_table(s, sl.table, body_top if not sl.bullets else Emu(3520000),
                           sl.table_colors)
            if sl.diagram == "pipeline":
                _add_pipeline(s, Emu(3820000))
        if sl.notes:
            s.notes_slide.notes_text_frame.text = sl.notes

    prs.save(str(out))
    return out


# ══ deck content ══════════════════════════════════════════════════════════════
# CORE = the ~6-min spoken spine. Everything after the LIVE handoff is on-demand.
DECK = [
    # ── CORE ──────────────────────────────────────────────────────────────────
    Slide(
        tag="§1 · THE DIRECTION (agreed Aug 2)", time="1m",
        title="Does representational geometry predict edit propagation?",
        bullets=[
            "The thread we agreed on: does the **representational geometry** between an edited "
            "fact and its logically-entailed neighbours predict whether an edit actually "
            "**propagates** to them?",
            ("Resolved across **entailment hops** (paraphrase / 1-hop / 2-hop), measured "
             "**causally** (IIA) — not just behaviourally — comparing "
             "**raw-distance vs. structured-geometry vs. alignment** predictors.", 1),
            "Stakes: editing **fails** ripple today — ROME-edited GPT-J answers only {{7.6%}} of "
            "MQuAKE multi-hop.",
            "Homework first (Asta + literature incl. NDIF corpus): the hop-resolved *causal* "
            "comparison looked **unclaimed** (dense: SLAQ, Kim/Jeong, Nishi shattering, RAVEL).",
        ],
        notes="1m. Ground everyone in the AGREED direction (the email, Aug 2). This is the "
              "shared starting point before I show where running it led.",
    ),
    Slide(
        tag="§ · WHAT I'D LOVE FROM TODAY", time="30s",
        title="Pressure-test where it stands",
        bullets=[
            "**Is the direction still sound?** — I have results that reframed it; check my logic.",
            "**What am I missing?** — pointers, prior work, blind spots.",
            "**Attack the hard questions** — I've written them down (last slide); try to break them.",
            "**How do we scale it** — compute + collaboration toward sharper outcomes.",
        ],
        notes="30s. Then ~5 min of trajectory, then results live. Frame Arnab's role as the "
              "adversarial reviewer (Natalie's framing) — the hard-questions slide is for him.",
    ),
    Slide(
        tag="§2 · THE PHENOMENON", time="1m",
        title="Editing propagation collapses — and over-propagates — with hop",
        bullets=[
            "**Reproduced the ripple failure** (random RippleEdits, n=397): correct propagation "
            "collapses beyond paraphrase — 1-hop mostly {{stale (61%)}}, 2-hop mostly "
            "{{broken (81%)}} `[E-014]`.",
            "**Over-propagation is the mechanism** — of broken cases, target-bleed rises with "
            "hop: 0% → 25% → <<58%>> (the edit's value spills into farther neighbours).",
            "Non-cherry-picked + reproducible; FT baseline shows the same hop-decay `[E-012]`. "
            "(Locality not yet measurable — needs a capable model.)",
        ],
        notes="1m. The phenomenon (E-014). Figure next. Keep to the research finding — the "
              "deployment angle is the coda, later.",
    ),
    Slide(
        tag="§2 · THE DISTRIBUTION", time="30s",
        title="ROME edit → neighbour outcomes (no cherry-picking)",
        image="results/final/figures/scale_distribution.png",
        bullets=["90 random edits · 397 neighbours · gpt2-small · seed 1538 — "
                 "reproducible from results/final/"],
        notes="Let the figure carry it: paraphrase 57% updated; 1-hop 61% stale; 2-hop 81% "
              "broken. Locality excluded (n=3, not measurable). Anti-cherry-pick payoff — "
              "the clean landmark story (5/5) becomes 57% at scale.",
    ),
    Slide(
        tag="§3 · DOES GEOMETRY PREDICT IT?", time="1m",
        title="Yes — but which geometry depends on the hop",
        image="results/final/figures/predict_scale_auc.png",
        bullets=["raw distance predicts NEAR (paraphrase AUC 0.80 [0.74,0.86]) but fails FAR "
                 "(2-hop 0.46, spans chance); structured/alignment capture the FAR signal "
                 "(~0.75, CI >0.5) `[E-015]`. **Bootstrap CIs confirm the crossover** "
                 "(1-hop uninterpretable, 2 pos). ALL-column is type-confounded → per-hop is honest."],
        notes="1m. The predictor-by-hop crossover. This is the agreed direction's core "
              "comparison (raw vs structured vs alignment), against the real 397-row labels.",
    ),
    Slide(
        tag="§4 · IS IT CAUSAL? (E-016)", time="1m",
        title="Subject site carries weight — but propagation isn't cleanly localized",
        image="results/final/figures/iia_by_hop.png",
        bullets=["Interchange (n=228 affected): subject-site patch reproduces the edit 90–100%, "
                 "**~20pts above** a random-position control `[E-016]` — real causal weight "
                 "(clear at 2-hop, n=178). BUT control is high (66–76%) → the edit's rep is "
                 "**broadly readable, not localized**; and **no near/far hop-differential**. "
                 "Suggestive, not clean — next: a tighter intervention (path-patching)."],
        notes="1m. HONEST result: partial causal signal (subject beats random ~20pts, clear at "
              "2-hop) but high control = not clean localization, and no hop-crossover. Do NOT "
              "overclaim. This is exactly what to hand Arnab — a diagnosed inconclusive with a "
              "concrete fix (clean-vector control / path patching / attention knockout).",
    ),
    Slide(
        tag="§5 · WHAT THE DATA SAYS", time="1m",
        title="Entailment neighbours drift from representational neighbours with hop",
        bullets=[
            "Logical neighbours are **not uniformly representational neighbours** — closeness "
            "(and, we test, causal readability) **decays with hop**.",
            "That one fact explains both failures: at distance the edit can't *reach* the "
            "neighbour ({{stale}}) or reaches the wrong slot (<<over-propagation>>).",
            "The **two graphs** — logical entailment vs. the model's causal-read graph — "
            "look like they **align near the edit, diverge with hop** `[T-006]` — "
            "*behaviourally + predictively*.",
            ("Causal leg (E-016) is **not clean yet**: the subject site carries weight "
             "(beats random ~20pts) but the edit's rep is broadly readable (control ~75%), "
             "no hop-differential → a targeted intervention is the next step, not a claim yet.", 1),
        ],
        notes="1m. Honest, data-led. The behavioural (E-014) + predictive (E-015) arcs support "
              "the two-graphs picture; the first causal probe is suggestive but inconclusive. "
              "Present the causal leg as an open, well-diagnosed next step — that's rigor.",
    ),
    Slide(
        tag="§5 · THE TWO GRAPHS (schematic)", time="30s",
        title="Logical neighbours become representational strangers with hop",
        image="results/final/figures/two_graphs.png",
        bullets=["Left: logical entailment (all hops connected). Right: the model's read graph "
                 "— strong near, weak/mis-routed far. Ripple fails where they diverge. "
                 "(Behavioural + predictive picture; the causal leg is still open — E-016.)"],
        notes="30s. The thesis, visualized. HONEST label: this is the behavioural (E-014) + "
              "predictive (E-015) picture; the causal-read edges are the hypothesis E-016 "
              "probed but did NOT cleanly confirm. Draft schematic — refine styling rested.",
    ),
    # ── CODA — the deployment pitch, built on the evidence ──────────────────────
    Slide(tag="", title="CODA · where this goes — infrastructure for reliable editing",
          divider=True,
          notes="Transition: the research says editing is unreliable in a characterizable way. "
                "As an infra engineer, here's the deployable consequence. Clearly forward-"
                "looking / less mature than the spine — say so."),
    Slide(
        tag="CODA · THE REFRAME", time="1m",
        title="I was grading editing on RAG's exam",
        bullets=[
            "Two things collided: **MEMIT** holds ~90 editing-score at 10K edits (editing isn't "
            "broadly breaking models); the **ripple failure is specifically multi-hop**.",
            "**Resolution `[T-017]`:** editing = what the model **believes** (reasons *from*); "
            "RAG = what it **reasons over** at inference.",
            ("Different functions, different metrics. Multi-hop is RAG's job.", 1),
            "MEMIT succeeding at belief AND failing multi-hop are [[not a contradiction]] — two jobs.",
        ],
        notes="1m — the pivot. Complementary, not competitors (Liu 2025, Zhang 2025). "
              "Deliver as 'where the evidence pushed me', ~70% conviction, not decided.",
    ),
    Slide(
        tag="CODA · THE GAP IT OPENS", time="1m",
        title="Hybrid systems use both stores — nobody checks they agree",
        bullets=[
            "The research says editing is unreliable in a *characterizable* way. In deployment, "
            "you pair it with RAG: **edit for belief, retrieve for reasoning.** Do the two agree?",
            "They can silently contradict — model asserts its **stale parametric belief** while "
            "the RAG index holds the fix, or **retrieves the fix and ignores it** (edit skipping).",
            "{{No current metric catches this}} — editing benchmarks probe weights only; "
            "RAG benchmarks probe retrieval only. Nobody checks the **seam**.",
        ],
        notes="1m. The deployment consequence of the research. Arnab's wheelhouse.",
    ),
    Slide(
        tag="CODA · THE INFRASTRUCTURE", time="1.5m",
        title="A consistency-certifier for reliable editing",
        bullets=[
            "**My angle:** I build infrastructure. If editing is unreliable this way, the "
            "deployable fix is a **reliability layer** — so ordinary researchers can keep a model "
            "current without silently corrupting it.",
            "Probe both stores → **detect** contradictions → optionally **reconcile** → emit a "
            "**scoped certificate**.",
            "**Honest `[T-018]`:** DMM Gov *specifies* this loop; nobody builds/measures it — "
            "'first to **build + certify**', never 'conceive'. Less mature than the spine above.",
        ],
        diagram="pipeline",
        notes="1.5m. The pitch — motivated by the data, framed through the infra identity, "
              "honestly labeled forward-looking. Invite Arnab to attack it. First experiment = "
              "the significance gate (backup).",
    ),
    Slide(
        tag="· WHAT I'M ASKING YOU", time="45s",
        title="Four questions — research first, then the coda",
        bullets=[
            "**Is the interpretation sound?** the two-graphs read — align near, diverge with hop "
            "— do you buy it?",
            "**Is the causal design right?** the E-016 interchange — anything you'd change before "
            "I scale it to GPT-J?",
            "**The coda** — is the reliability-layer direction worth pursuing, and unclaimed "
            "beyond DMM Gov? (adversarial review welcome)",
            "**Compute** — GPU for GPT-J to scale the causal test + a capable-model specificity check?",
        ],
        notes="45s. Research first (is the science sound), then the coda pitch (is the infra "
              "worth it). End the spoken part here; hand off to the live demo.",
    ),
    # ── LIVE handoff ───────────────────────────────────────────────────────────
    Slide(
        tag="→ LIVE · results/",
        title="Now — let me show you, empirically",
        bullets=[
            "Everything under `results/final/` — data, figures, tables + a README that "
            "regenerates it all (seed 1538).",
            "**Distribution + predictor + causal:** `figures/{scale_distribution, "
            "predict_scale_auc, iia_by_hop}.png`.",
            "**Raw rows:** `data/{scale_study(397), iia_scale, rome_study, tb_rows}.json`; "
            "numbers + CIs in `tables/`.",
            "**Every run logged + reproducible** (`results/logs/`).",
            ("Because it's all reproducible, the effort **scales**: swap model/editor, add edits, "
             "or move to GPT-J for the causal + specificity tests. →", 1),
        ],
        notes="Transition to the live demo. Open results/, walk the blast-radius PNG, the 3-way "
              "json, the predictor arc. Emphasise reproducibility → scaling (GPU, bigger models, "
              "the certifier run). Backup slides below hold the exact tables if you'd rather show those.",
    ),
    Slide(tag="", title="Backup · detail on demand", divider=True,
          notes="Everything past here is on-demand — pull a slide if asked, or show the "
                "live results/ artifacts instead."),
    # ── BACKUP ────────────────────────────────────────────────────────────────
    Slide(
        tag="BACKUP · OUTCOME 1 (FT baseline)", time="",
        title="FT-L baseline: propagation decays with hop `[E-012]`",
        image="results/final/figures/ft_propagation_by_hop.png",
        bullets=["FT-L · gpt2-small · 20 edits — 20% → 14% → 0% by hop. "
                 "Locality omitted: no competence filter → not a clean specificity measure."],
        notes="The FT wrecking-ball baseline, visualized (results/final/tables/propagation_table.txt). "
              "Corroborates the hop-decay shape. Do NOT claim locality — that run had no competence "
              "filter, so 'preserved' conflates specificity with unchanged garbage.",
    ),
    Slide(
        tag="BACKUP · OUTCOME 2 (landmark — SUPERSEDED)", time="",
        title="The 5 hand-picked landmarks — before the scale run corrected it",
        bullets=[
            "The original n=5 (Eiffel/Louvre/…), **SUPERSEDED by the n=397 random run** "
            "(paraphrase 5/5 → 57%). Kept only to show the non-obvious patterns it first surfaced:",
            ("**non-monotone** (1-hop breaks more than 2-hop); **over-propagation** "
             "(city → country slot); **target-bleed** into unrelated facts.", 1),
        ],
        table=[
            ["type", "outcome (n=5 landmarks)"],
            ["paraphrase", "updated 5/5"],
            ["1-hop", "broken 4, stale 1"],
            ["2-hop", "updated 3, broken 2"],
            ["locality", "fine 4, broken 6  (~60% leak)"],
        ],
        table_colors={(1, 1): GOOD, (2, 1): BAD, (4, 1): BAD},
        notes="[T-015] — the LANDMARK set, superseded by E-014's random n=397. Do not cite 5/5 "
              "as a result; it's the cherry-pick baseline. Figure: rome_blast_radius.png.",
    ),
    Slide(
        tag="BACKUP · ROBUSTNESS (2nd sample)", time="",
        title="The hop-decay replicates on a second RippleEdits split",
        image="results/final/figures/replication.png",
        bullets=["popular (90 edits/397) vs random (97/371): same shape — paraphrase updates "
                 "(57/69%), 1-hop stalls (61/71% stale), 2-hop breaks (81/74%) `[T-022]`. "
                 "Two independent samples → not a cherry-picked distribution."],
        notes="Robustness: the distribution holds across two independent RippleEdits samples. "
              "Strengthens the anti-cherry-pick point directly.",
    ),
    Slide(
        tag="BACKUP · THE STRUCTURAL RUN", time="",
        title="Structure did NOT beat distance (yet)",
        bullets=[
            "`sep = mean(cos, propagate-types) − cos(locality)`; **sep > 0** ⇒ separates.",
            "Real-label test: raw cosine AUC **0.68** `[E-013]`; capacity helps — GPT-J "
            "last-token sep ≈ **+0.06** `[E-007]`.",
        ],
        table=[
            ["setting", "raw distance", "structured"],
            ["gpt2-small · mean-pool", "+0.006", "−0.001"],
            ["gpt2-medium · mean-pool", "~0", "~0"],
            ["gpt2-medium · last-token", "+0.007 → +0.019", "~0"],
        ],
        table_colors={(3, 1): GOOD, (1, 2): BAD, (2, 2): MUTE, (3, 2): MUTE},
        notes="[E-011/E-011b], 171 pairs. mean-pool washes out; last-token faint raw signal; "
              "structured sep~0 everywhere. Proxy (unedited-model type-separation), small n. "
              "Figures: results/predictor_arc.png, gpt2med_last_arc.png.",
    ),
    Slide(
        tag="BACKUP · THE ENGINEERING", time="",
        title="What those results cost",
        bullets=[
            "**NDIF** regressed mid-work (whitelist bug) — isolated, reported, fixed. `[E-006]`",
            "**NDIF can't do iterative weight edits** → real editing must be local. `[E-012]`",
            "**EasyEdit** locally: `device=cpu`, `num_workers=0`; it **silently rolls back** the "
            "edit before you can query it — patched off → [[all 5 ROME edits flipped]]. `[T-015]`",
            "gpt2-medium **NaNs at the logits** on this Mac → gpt2-small (weak but real). `[E-012]`",
        ],
        notes="Execution / sitting-with-it signal. Logs in results/.",
    ),
    Slide(
        tag="BACKUP · THE FIRST EXPERIMENT", time="",
        title="Significance gate — run this first",
        bullets=[
            "**Do realistic hybrid updates create silent contradictions that editing-only and "
            "RAG-only metrics MISS?**",
            "**One figure:** silent-contradiction rate split — (i) editing-metrics miss, "
            "(ii) RAG-metrics miss, (iii) certifier catches.",
            "If real → (i)+(ii) tall, (iii) recovers them. If ~0 → [[publish the negative and stop]].",
            "Setup: gpt2-xl/GPT-J + small FAISS store, ROME edits, constructed contradiction "
            "ground-truth (edit P→X, retrieval Y≠X; agree-pairs as negatives).",
        ],
        notes="Design backward from one figure; pre-registered null branch.",
    ),
    Slide(
        tag="SUMMARY", title="", big="The data says entailment neighbours drift from "
        "representational neighbours as hops grow — editing reaches near facts, stalls or "
        "over-propagates on far ones. **That's the science.** And because it makes editing "
        "unreliable in a *measurable* way, it points to the infrastructure I want to build: a "
        "reliability layer that makes editing safe to ship.",
        notes="One breath. Science first, then the infra it motivates. Then hard questions, floor.",
    ),
    Slide(
        tag="THE HARDER QUESTIONS", time="",
        title="What I'd want an adversarial reviewer to attack",
        bullets=[
            "**Why edit, not just RAG?** Category error — systems use *both*; the question is 'do they agree?'.",
            "**Zhang et al. (DMM Gov) specified this — what's new?** They specify; I build + measure.",
            "**Am I inventing a problem?** That's the FIRST experiment, with a pre-registered null branch.",
            "**Does reconcile converge, or is it whack-a-mole?** Empirical (v2); if it fails → detect+certify+flag.",
            "**Do you know what the model will answer?** which_wins (edit-skipping); if not → narrow the claim.",
            "**gpt2-small is a toy / can you measure specificity?** Agreed — needs a capable model (GPU/GPT-J).",
            "**Scale to 10K edits?** No — v1 is small-batch high-assurance, not mass editing.",
        ],
        notes="Closing slide — invite the attack (Arnab's adversarial-reviewer role). These are "
              "MY answers; I want them stress-tested. Silence is also feedback.",
    ),
]


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    out = here / "DECK_trajectory.pptx"
    build(DECK, out, subtitle="Walkthrough for Arnab · 2026-08-25 · Saif Ul Islam")
    core = sum(1 for s in DECK if not s.divider and not s.tag.startswith("BACKUP")
               and s.tag != "SUMMARY")
    print(f"wrote {out}  ({len(DECK) + 1} slides · theme={THEME} · ~{core} core slides)")
