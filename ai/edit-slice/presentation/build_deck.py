"""build_deck.py — render the edit-slice findings into a plain-language PPTX.

Audience: someone who does not work on language models. The paper at
web/notebook/edit-slice/review.md is written to be judged by someone who does; this is
the other artifact, and the two are allowed to share nothing but their facts.

Rules this deck is built to keep, because a deck fails them more easily than a paper:
  * no term appears before the thing it names;
  * every claim traces to a record — the id lives in the speaker notes, never on the
    slide, so a question can be answered from the ledger live without cluttering it;
  * the withdrawn claims get their own slide, not a footnote;
  * no prescription. CLAUDE.md scopes this project to measuring what existing editors do.

RENDERER COPIED from ai/rome-neighbors/presentation/build_deck.py (2026-09-21). The two
projects have separate venvs, so importing across them would be a dependency neither
declares. A fix to the renderer in either place needs porting to the other by hand.

Run in the project venv:
    .venv/bin/python presentation/build_deck.py
Output: presentation/DECK.pptx
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
    _run(fp, FOOTER, 10, MUTE)
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
#: The title slide's headline. Parameterised because the copied renderer hard-coded
#: the other project's title, which rendered once before anyone noticed.
FOOTER = "edit-slice · what an edit really moves"
TITLE_A = "We tried to fix one fact inside an AI"
TITLE_B = "and found out what else moves"


def build(deck, out: Path, subtitle: str):
    prs = Presentation()
    prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H
    blank = prs.slide_layouts[6]

    # title
    s = prs.slides.add_slide(blank); _set_bg(s)
    _rect(s, Emu(0), Emu(0), SLIDE_W, Emu(56000), ACCENT)
    _rect(s, MARGIN, Emu(2560000), Emu(760000), Emu(66000), ACCENT2)
    tf = _tb(s, MARGIN, Emu(2720000), USABLE, Emu(1600000))
    _run(tf.paragraphs[0], TITLE_A, 38, FG, bold=True)
    _run(tf.add_paragraph(), TITLE_B, 38, ACCENT, bold=True)
    _run(_tb(s, MARGIN, Emu(4480000), USABLE, Emu(700000)).paragraphs[0],
         subtitle, 16, MUTE)
    _rect(s, Emu(0), Emu(int(SLIDE_H) - 46000), SLIDE_W, Emu(46000), PANEL2)
    s.notes_slide.notes_text_frame.text = (
        "About 10 minutes. The audience is not a specialist: no term appears before the "
        "thing it names. Every claim traces to a record and the id is in these notes, "
        "never on the slide, so a question can be answered from the ledger live. "
        "Problems 4 and 5 are our own errors — say so plainly; they are what makes the "
        "rest credible. Deck is a backstop, not a script.")

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
# Plain-language spine, ~10 minutes. Ids live in notes, never on a slide.
DECK = [
    Slide(
        tag="§1 · THE SETUP", time="1m",
        title="Fixing one fact inside an AI, without retraining it",
        bullets=[
            "An AI has learned millions of facts. Some are wrong, or go out of date.",
            "Retraining the whole thing costs a fortune — so people built tools that reach "
            "in and change **just that one fact**.",
            "These tools are widely used and they **work**, by the measure the field uses.",
            "Our question is the one underneath: when you fix one fact, "
            "<<what else moves?>>",
        ],
        notes="Keep this slow. The audience needs to believe the tools are legitimate and "
              "widely used before the problems land. Do not say ROME yet.",
    ),
    Slide(
        tag="§2 · PROBLEM 1", time="2m",
        title="It doesn't fix a fact. It smears over a name.",
        bullets=[
            "We changed which country one person was born in.",
            "Afterwards the AI also answered differently about their **job**, their "
            "**language**, their **citizenship** — things we never touched.",
            "The pattern: anything you ask that **starts with that person's name** gets hit.",
            "Think {{find-and-replace on a name}} when you meant to correct one sentence.",
            ("And not partially — at **full strength**, every time. It falls out of the "
             "arithmetic the tool uses, so it is not a glitch that better tuning fixes.", 1),
        ],
        notes="E-016 (the arithmetic), E-017, E-021 (causal: the name position is both "
              "sufficient and necessary). E-018: a DIFFERENT person's name gets 8%, so "
              "this really is keyed on the subject and not on everything.",
    ),
    Slide(
        tag="§2 · PROBLEM 2", time="2m",
        title="What looks like the AI reasoning is the AI being overwritten",
        bullets=[
            "We changed the **country** someone was born in. Then asked for the **city**.",
            "The AI named a city in the new country. [[That looks like thinking]] — as if it "
            "worked out that a new country means a new city.",
            "So we tried something that should NOT work: we changed where the person "
            "**works** instead. Where you work says nothing about where you were born.",
            "{{The AI moved their birth city anyway. Same rate. Usually the same city.}}",
            ("Nothing was being figured out. The name got painted over and everything "
             "hanging off it came along.", 1),
        ],
        notes="E-014 then E-015. 28/42 both arms, paired difference +0.0pp, exact McNemar "
              "p=1.000; same city 84% of the time. This is the slide that changes minds — "
              "let the control land before moving on.",
    ),
    Slide(
        tag="§2 · PROBLEM 3", time="2m",
        title="The tests used to check this may be graded on the glitch",
        bullets=[
            "The standard way to check whether a fix 'spread sensibly' is to ask follow-up "
            "questions.",
            "Almost all of those questions **start with the person's name**.",
            "But that is exactly the case that breaks — the one that gets the fix at full "
            "strength automatically.",
            "So a test may be measuring the glitch and <<scoring it as intelligence>>.",
            ("Nobody did this on purpose. It is just how the questions happen to be "
             "worded. We cannot yet say how much of it is affected — and that is the "
             "thing we would most like someone to check.", 1),
        ],
        notes="This is the consequence in §7 of the paper, priced at about a week: "
              "re-score one published ripple benchmark with the subject moved later in "
              "the sentence. The honest position is that we have not run it.",
    ),
    Slide(
        tag="§2 · PROBLEM 4", time="1m",
        title="The standard 'did it work?' check is too easy to pass",
        bullets=[
            "The usual check asks only: does the **new** answer now beat the **old** one?",
            "A fix can pass that while barely changing what the AI actually believes.",
            "{{We know because we fell for it ourselves.}} We built a safety check on that "
            "idea, it gave us a green light, and it was worthless.",
            ("We had to throw out a result and redo the work three times to get it "
             "honestly.", 1),
        ],
        notes="E-026's RCA. The gate matched arms on 'lift on the target', which a logit "
              "nudge also achieves. E-028a then measured it: lift spans 0.17 nats across "
              "two layers and a 4x budget while real strength spans 5.70. Say plainly "
              "that this was our error before it was anyone else's.",
    ),
    Slide(
        tag="§2 · PROBLEM 5", time="1m",
        title="Our own best idea was wrong",
        bullets=[
            "We could measure exactly **how much of a fix arrives** at any given question — "
            "cheaply, without running the damaged AI.",
            "That looked like a way to predict harm before paying for it.",
            "{{It does not predict harm.}} Same amount arriving, **three times** the damage, "
            "depending only on where in the AI you make the change.",
            ("We checked this four separate ways before believing it, because it cost us "
             "the most attractive thing we had.", 1),
        ],
        notes="T-079 answered DENY. E-028b matched the arms (16x step budget), E-028c "
              "found 63% difference at identical delivery, E-028d broke the "
              "layer/budget collinearity. 1.22 vs 0.41 nats of reach per nat displaced.",
    ),
    Slide(
        tag="§3 · THE RECORD", time="1m",
        title="Eleven claims. Eight withdrawn or narrowed.",
        bullets=[
            "Most of what we learned is what **does not** work.",
            "Every withdrawn claim is published with what killed it — including the ones "
            "we withdrew after writing them up.",
            "[[The one that survived]] is small and solid: an arithmetic reason why these "
            "fixes reach everything sharing a name.",
            ("The full record is online — every decision, every dead end, every run log. "
             "Most of it went nowhere. That is the point of publishing the list rather "
             "than the highlights.", 1),
        ],
        notes="Table 5 of the paper. This is the most credible slide in the deck and the "
              "easiest to rush — do not.",
    ),
    Slide(
        tag="§3 · THE BOUNDARY", time="1m",
        title="What the failures rule out — and what is left standing",
        bullets=[
            "Most of this is things that did not work. That counts for something only if "
            "we separate **what is ruled out** from **what we simply got wrong**.",
            "[[Ruled out, for anyone]] — you cannot tell how much damage an edit does from "
            "how much of it arrives; an edit does not blur everything about a person "
            "equally; the standard 'did it work' score is not hiding anything.",
            "{{Just our mistakes}} — a safety check on the wrong quantity, a test that "
            "could not detect its own target, a file that reported half a run as whole. "
            "In the record because they are why the rest can be trusted. Not findings.",
            ("Put the eliminations together and a boundary falls out — the clearest thing "
             "this project knows.", 1),
        ],
        notes="This slide is the argument for the negative results. Do NOT let the two "
              "lists blur: a record that mixes elimination with self-inflicted cost earns "
              "credit for neither. §5.1 of the paper.",
    ),
    Slide(
        tag="§3 · THE BOUNDARY", time="1m",
        title="We can say WHICH facts an edit touches. Not how hard.",
        big="which — yes.   how hard — no.",
        bullets=[
            "[[WHICH is settled]] — cheaply, exactly, at every size from 6B to 405B. And "
            "the probe hit hardest is the one whose answer is the same **kind of thing** "
            "as what was injected. Six cases out of six.",
            "{{HOW HARD is open}} — nothing we have predicts it. The two best candidates "
            "explain about a fifth of the variation each.",
            ("And the measurement this whole project is built on cannot help: it has "
             "**exactly the same value** for every probe whose outcome differs. Zero "
             "variance where the answer varies most.", 1),
            "That is a real boundary, it came entirely from things not working, and the "
            "question past it is the one I would most like help with.",
        ],
        notes="T-086. If there is one thing to take away, it is this slide. The last "
              "bullet is the sharpest fact in the project and the easiest to rush.",
    ),
    Slide(
        tag="§4 · WHAT I WANT", time="1m",
        title="Three things I cannot decide from inside",
        bullets=[
            "**Is the main result already known?** It is a line of arithmetic. "
            "Practitioners may simply assume it, and 'we could not find it stated' is the "
            "weakest form of a novelty claim.",
            "**Is the benchmark consequence worth a week?** Re-scoring one published test "
            "with the names moved is the only thing here that changes what others do.",
            "**Is a small, careful result publishable**, or does this need the scale work "
            "it currently refuses to do?",
            ("Nine open questions are written up with what each would settle and what it "
             "costs. Which is worth a month is the judgement I would most like "
             "contradicted.", 1),
        ],
        notes="§7 and §8 of the paper. Ask directly; do not hedge. Silence is also "
              "feedback.",
    ),
]


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    out = here / "DECK.pptx"
    build(DECK, out, subtitle="edit-slice · what we found · 2026-09-21 · Saif Ul Islam")
    core = sum(1 for s in DECK if not s.divider and not s.tag.startswith("BACKUP")
               and s.tag != "SUMMARY")
    print(f"wrote {out}  ({len(DECK) + 1} slides · theme={THEME} · ~{core} core slides)")
