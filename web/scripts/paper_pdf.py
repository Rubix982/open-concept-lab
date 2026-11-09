#!/usr/bin/env python3
"""Build a submission-shaped PDF from a notebook paper page.

The page is the source. There is no second copy of the paper in LaTeX, because
two copies of one paper drift and the drift is invisible until someone reads
both. Everything here resolves the page's components into plain markdown, hands
that to pandoc, and wraps the result in a two-column article class.

    python3 scripts/paper_pdf.py notebook/edit-reach/paper.md
    python3 scripts/paper_pdf.py notebook/edit-reach/paper.md --keep-tex

Needs: pandoc, tectonic, rsvg-convert. Figures are SVG and LaTeX cannot include
an SVG, so each one is converted to PDF first and cached beside the output.

What it does NOT do: reproduce the web layout. A printed paper has no contents
rail, no hover, no links to a ledger page. Where the page points at something
only the site can give, the PDF says so rather than pretending.
"""
from __future__ import annotations

import argparse
import html
import pathlib
import re
import shutil
import subprocess
import sys

try:
    import yaml
except ImportError:
    sys.exit("needs pyyaml: pip install pyyaml")

WEB = pathlib.Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- front matter

def split_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.index("\n---", 3)
    return yaml.safe_load(text[3:end]) or {}, text[end + 4 :]


def papers() -> dict:
    data = yaml.safe_load((WEB / "data" / "papers.yml").read_text())
    return data or {}


def first_author(authors: str) -> str:
    first = authors.split(",")[0].strip()
    return f"{first} et al." if len(authors.split(",")) > 2 else first


# ---------------------------------------------------------------- components

def strip_jsx_attr(block: str, name: str) -> str | None:
    """Read one attribute off a JSX tag. Handles "..." and {<>...</>}."""
    m = re.search(rf'{name}=\{{<>(.*?)</>\}}', block, re.S)
    if m:
        return m.group(1)
    m = re.search(rf'{name}="([^"]*)"', block, re.S)
    return m.group(1) if m else None


def jsx_to_markdown(s: str) -> str:
    """Inline JSX and HTML left inside a caption or a table cell."""
    s = re.sub(r"<b>(.*?)</b>", r"**\1**", s, flags=re.S)
    s = re.sub(r"<i>(.*?)</i>", r"*\1*", s, flags=re.S)
    s = re.sub(r"<strong>(.*?)</strong>", r"**\1**", s, flags=re.S)
    s = re.sub(r"<em>(.*?)</em>", r"*\1*", s, flags=re.S)
    s = re.sub(r"<code>(.*?)</code>", r"`\1`", s, flags=re.S)
    s = re.sub(r'<span className="f">(.*?)</span>', r" (\1)", s, flags=re.S)
    s = re.sub(r"</?(?:span|div|>|)>", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(" ".join(s.split()))


def resolve_cites(body: str, bib: dict, used: list[str]) -> str:
    def one(m: re.Match) -> str:
        pid = m.group(1)
        paper = bib.get(pid)
        if not paper:
            return f"[{pid}?]"
        if pid not in used:
            used.append(pid)
        name = first_author(paper["authors"])
        if "narrative" in m.group(0):
            return f"{name} ({paper['year']})"
        return f"({name}, {paper['year']})"

    return re.sub(r'<Cite id="([^"]+)"[^/]*/>', one, body)


def html_table_to_markdown(block: str) -> str:
    """A <Data>/<thead>/<tbody> table, as a pipe table."""
    heads = [jsx_to_markdown(c) for c in re.findall(r"<th[^>]*>(.*?)</th>", block, re.S)]
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", block, re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if cells:
            rows.append([jsx_to_markdown(c) for c in cells])
    if not heads and not rows:
        return ""
    width = len(heads) or max(len(r) for r in rows)
    heads = heads or [""] * width
    out = ["| " + " | ".join(heads) + " |", "|" + "|".join([" --- "] * width) + "|"]
    for r in rows:
        r = r + [""] * (width - len(r))
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def convert_figure(block: str, assets: pathlib.Path, n: int) -> str:
    caption = strip_jsx_attr(block, "caption") or ""
    caption = jsx_to_markdown(caption)
    src = strip_jsx_attr(block, "src")

    if src:
        svg = WEB / "static" / src.lstrip("/")
    else:
        inner = re.search(r"(<svg\b.*?</svg>)", block, re.S)
        if not inner:
            return f"*(figure {n} omitted: no source)*\n"
        svg = assets / f"inline-{n}.svg"
        # JSX camelCase attributes are not SVG attributes; rsvg wants the real ones.
        text = inner.group(1)
        for a, b in [
            ("fontFamily", "font-family"), ("fontSize", "font-size"),
            ("fontWeight", "font-weight"), ("letterSpacing", "letter-spacing"),
            ("textAnchor", "text-anchor"), ("strokeWidth", "stroke-width"),
            ("strokeDasharray", "stroke-dasharray"), ("strokeLinecap", "stroke-linecap"),
            ("viewBox", "viewBox"), ("className", "class"),
        ]:
            text = text.replace(a + "=", b + "=")
        # A CSS variable has no value outside the browser; fall back to ink.
        text = re.sub(r"var\(--ocl-paper[^)]*\)", "#ffffff", text)
        text = re.sub(r"var\(--ocl-rule[^)]*\)", "#999999", text)
        text = re.sub(r"var\(--ocl-ink-faint\)", "#666666", text)
        text = re.sub(r"var\(--ocl-ink-muted\)", "#444444", text)
        text = re.sub(r"var\(--ocl-ink\)", "#111111", text)
        text = re.sub(r"var\(--ocl-link\)", "#4338a8", text)
        text = re.sub(r"var\(--ocl-oxide\)", "#a4442f", text)
        text = re.sub(r"var\(--ocl-held-ink\)", "#336847", text)
        text = re.sub(r"var\(--ocl-[a-z-]+\)", "#666666", text)
        svg.write_text(text)

    if not svg.exists():
        return f"*(figure {n} omitted: {svg} not found)*\n"

    pdf = assets / (svg.stem + ".pdf")
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(pdf), str(svg)], check=True)
    wide = "wide" in block or src is not None
    env = "figure*" if wide else "figure"
    width = "\\textwidth" if wide else "\\columnwidth"
    return (
        f"\n```{{=latex}}\n\\begin{{{env}}}[t]\n\\centering\n"
        f"\\includegraphics[width={width}]{{{pdf.name}}}\n"
        f"\\caption{{{latex_escape(caption)}}}\n\\end{{{env}}}\n```\n"
    )


def delongtable(tex: str) -> str:
    r"""Pandoc emits every table as a longtable; longtable cannot run in two
    columns. Each becomes a spanning `table*` with an ordinary `tabular`.

    The column specification contains braces of its own -- `@{}>{\raggedright}p{..}@{}`
    -- so it is read by counting braces rather than by matching to the first `}`.
    An earlier version used a regular expression there, and on a table pandoc
    wrote without a caption it silently dropped the specification and the header
    row with it, leaving a tabular whose first data row was its own format.

    Pandoc repeats the header between \endfirsthead and \endhead so a table that
    breaks across pages reprints it. A tabular does not break, so the repeat goes.
    """
    OPEN = r"\begin{longtable}"
    CLOSE = r"\end{longtable}"
    out, i = [], 0
    while True:
        a = tex.find(OPEN, i)
        if a == -1:
            out.append(tex[i:])
            break
        out.append(tex[i:a])

        j = tex.index("{", a + len(OPEN) - 1)
        depth, k = 0, j
        while k < len(tex):
            if tex[k] == "{":
                depth += 1
            elif tex[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        cols = tex[j + 1 : k]

        close = tex.index(CLOSE, k)
        inner = tex[k + 1 : close]
        i = close + len(CLOSE)

        cap = ""
        m = re.search(r"\\caption\{(.*?)\}\\tabularnewline", inner, re.S)
        if m:
            cap = m.group(1)
            inner = inner.replace(m.group(0), "")

        inner = re.sub(r"\\endfirsthead.*?\\endhead", "", inner, flags=re.S)
        for marker in (r"\endfirsthead", r"\endhead", r"\endlastfoot",
                       r"\noalign{}", r"\bottomrule"):
            inner = inner.replace(marker, "")
        inner = "\n".join(ln for ln in inner.splitlines() if ln.strip())

        caption = "\\caption{" + cap + "}\n" if cap else ""
        out.append(
            "\\begin{table*}[t]\n\\centering\\small\n"
            "\\begin{tabular}{" + cols + "}\n" + inner + "\n\\bottomrule\n\\end{tabular}\n"
            + caption + "\\end{table*}\n"
        )
    return "".join(out)


def latex_escape(s: str) -> str:
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                 ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}")]:
        s = s.replace(a, b)
    return s


def resolve(body: str, assets: pathlib.Path, bib: dict, used: list[str]) -> str:
    # Figures first: they contain everything else.
    figs = {"n": 0}

    def fig(m: re.Match) -> str:
        figs["n"] += 1
        return convert_figure(m.group(0), assets, figs["n"])

    # `caption={<>...</>}` ends in "/>", so a plain non-greedy match for the
    # tag stops inside the caption and leaves its tail in the prose. The
    # look-behind skips the "/>" that belongs to a fragment close.
    body = re.sub(r"<Figure\b.*?(?:(?<!<)/>|</Figure>)", fig, body, flags=re.S)

    # Tables, each with its caption above it.
    def table(m: re.Match) -> str:
        block = m.group(0)
        cap = jsx_to_markdown(strip_jsx_attr(block, "caption") or "")
        md = html_table_to_markdown(block)
        return f"\n{md}\n\n: {cap}\n" if md else ""

    for tag in ("Data", "Ledger", "Runs", "Revisions", "Readiness"):
        body = re.sub(rf"<{tag}\b.*?</{tag}>", table, body, flags=re.S)

    # Row components the tables above did not reach (they are inside them).
    def finding(m: re.Match) -> str:
        b = m.group(0)
        ident = strip_jsx_attr(b, "id") or ""
        status = strip_jsx_attr(b, "status") or ""
        value = strip_jsx_attr(b, "value") or ""
        fals = jsx_to_markdown(strip_jsx_attr(b, "falsifier") or "")
        inner = re.sub(r"^<Finding\b.*?>", "", b, flags=re.S)
        inner = jsx_to_markdown(re.sub(r"</Finding>$", "", inner))
        return f"| {ident} | {inner} {fals} | {value} | {status} |"

    body = re.sub(r"<Finding\b.*?</Finding>", finding, body, flags=re.S)

    def run(m: re.Match) -> str:
        b = m.group(0)
        inner = jsx_to_markdown(re.sub(r"</Run>$", "", re.sub(r"^<Run\b.*?>", "", b, flags=re.S)))
        cols = [strip_jsx_attr(b, k) or "" for k in ("id", "model", "n", "date", "out")]
        return "| " + " | ".join([cols[0], inner] + cols[1:]) + " |"

    body = re.sub(r"<Run\b.*?</Run>", run, body, flags=re.S)

    def rev(m: re.Match) -> str:
        b = m.group(0)
        inner = jsx_to_markdown(re.sub(r"</Rev>$", "", re.sub(r"^<Rev\b.*?>", "", b, flags=re.S)))
        return f"| {strip_jsx_attr(b, 'date')} | {strip_jsx_attr(b, 'version')} | {inner} |"

    body = re.sub(r"<Rev\b.*?</Rev>", rev, body, flags=re.S)

    def check(m: re.Match) -> str:
        b = m.group(0)
        inner = jsx_to_markdown(re.sub(r"</Check>$", "", re.sub(r"^<Check\b.*?>", "", b, flags=re.S)))
        met = "yes" if re.search(r"\bmet\b", b.split(">")[0]) else "no"
        return f"| {met} | {jsx_to_markdown(strip_jsx_attr(b, 'need') or '')} | {inner} | {strip_jsx_attr(b, 'where') or ''} |"

    body = re.sub(r"<Check\b.*?</Check>", check, body, flags=re.S)

    # Inline apparatus.
    body = resolve_cites(body, bib, used)
    body = re.sub(r"<Prov id=\"([^\"]+)\"\s*/>", r"\\textsuperscript{[\1]}", body)
    body = re.sub(r"<Lead>(.*?)</Lead>", r"**\1**", body, flags=re.S)
    body = re.sub(r"<Eq[^>]*>(.*?)</Eq>", r"\1", body, flags=re.S)

    # References: the component resolves from papers.yml; here we emit the list.
    def refs(m: re.Match) -> str:
        ids = re.findall(r'"([^"]+)"', m.group(0))
        out = []
        for pid in ids:
            p = bib.get(pid)
            if not p:
                continue
            venue = f" {p['venue']}." if p.get("venue") else ""
            out.append(f"{p['authors']} ({p['year']}). *{p['title']}*.{venue}")
        return "\n\n".join(out)

    body = re.sub(r"<References\b.*?/>", refs, body, flags=re.S)

    # Anything left is a component with no print form.
    body = re.sub(r"</?Paper>", "", body)
    body = re.sub(r"<[A-Z][A-Za-z]*\b[^>]*/>", "", body)
    body = re.sub(r"</?[A-Z][A-Za-z]*\b[^>]*>", "", body)
    return body


# ---------------------------------------------------------------- the document

TEMPLATE = r"""\documentclass[10pt,twocolumn,a4paper]{article}
\usepackage[margin=2cm,columnsep=0.8cm]{geometry}
\usepackage{graphicx}
\graphicspath{{%(assets)s/}}
\usepackage{booktabs}
\usepackage{array}
\usepackage{calc}
\usepackage{ragged2e}
\usepackage{fvextra}
%% A console listing is wider than a 9cm column and cannot be reflowed as prose,
%% so it is broken at the column edge rather than clipped there.
\fvset{breaklines=true,breakanywhere=true,fontsize=\footnotesize}
\usepackage{amsmath}
\usepackage{microtype}
\usepackage[hidelinks]{hyperref}
\usepackage{caption}
\captionsetup{font=small,labelfont=bf}
\usepackage{titlesec}
\titleformat{\section}{\normalfont\large\bfseries}{\thesection.}{0.5em}{}
\titleformat{\subsection}{\normalfont\normalsize\bfseries}{\thesubsection}{0.5em}{}
%% The headings carry their own numbers, written into the page. Letting LaTeX
%% number them too produces "0.1  1. Introduction".
\setcounter{secnumdepth}{0}
\setlength{\parindent}{1.2em}
\setlength{\parskip}{0pt}
\usepackage{enumitem}
\setlist{nosep,leftmargin=1.2em}
\providecommand{\tightlist}{}

\title{\textbf{%(title)s}}
\author{%(author)s\\ \small %(affiliation)s}
\date{%(date)s}

\begin{document}
\twocolumn[
  \begin{@twocolumnfalse}
  \maketitle
  \begin{abstract}
  %(abstract)s
  \end{abstract}
  %(keywords)s
  \vspace{1em}
  \end{@twocolumnfalse}
]

%(body)s

\end{document}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--keep-tex", action="store_true")
    args = ap.parse_args()

    for tool in ("pandoc", "tectonic", "rsvg-convert"):
        if not shutil.which(tool):
            sys.exit(f"missing {tool}")

    page = pathlib.Path(args.page).resolve()
    fm, body = split_front_matter(page.read_text())
    entry = fm.get("paper") or {}

    # Default to where the site serves it from: a PDF nobody can download is a
    # file, not a paper.
    out = pathlib.Path(args.outdir) if args.outdir else WEB / "static" / "pdf"
    out.mkdir(parents=True, exist_ok=True)
    # The converted figures are scratch and must not sit in static/, where the
    # site would serve every one of them for nothing.
    assets = WEB / ".paper-build" / page.parent.name
    assets.mkdir(parents=True, exist_ok=True)

    bib = papers()
    used: list[str] = []

    # The abstract is the body of <Paper>; the rest is the paper.
    m = re.search(r"<Paper>(.*?)</Paper>", body, re.S)
    abstract_md = m.group(1).strip() if m else ""
    body = body[m.end() :] if m else body

    abstract_md = resolve(abstract_md, assets, bib, used)
    body_md = resolve(body, assets, bib, used)

    if entry.get("contributions"):
        items = "\n".join(f"{i+1}. {c}" for i, c in enumerate(entry["contributions"]))
        body_md = f"\\section*{{Contributions}}\n\n{items}\n\n" + body_md

    def to_latex(md: str) -> str:
        p = subprocess.run(
            ["pandoc", "-f", "markdown+raw_attribute", "-t", "latex", "--no-highlight"],
            input=md, capture_output=True, text=True, check=True,
        )
        out = delongtable(p.stdout)
        # fvextra patches Verbatim, not verbatim, and only the former breaks lines.
        out = out.replace(r"\begin{verbatim}", r"\begin{Verbatim}")
        out = out.replace(r"\end{verbatim}", r"\end{Verbatim}")
        return out

    kw = entry.get("keywords") or []
    keywords = (
        "\\noindent\\textit{Keywords} --- " + latex_escape(", ".join(kw)) if kw else ""
    )

    tex = TEMPLATE % {
        "assets": str(assets),
        "title": latex_escape(fm.get("title", page.stem)),
        "author": latex_escape(entry.get("author", "")),
        "affiliation": latex_escape(entry.get("affiliation", "")),
        "date": latex_escape(entry.get("updated", "")),
        "abstract": to_latex(abstract_md),
        "keywords": keywords,
        "body": to_latex(body_md),
    }

    tex_path = out / (page.parent.name + ".tex")
    tex_path.write_text(tex)

    r = subprocess.run(
        ["tectonic", "-X", "compile", str(tex_path), "--outdir", str(out)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        sys.exit(f"\ntectonic failed; the source is at {tex_path}")

    if not args.keep_tex:
        tex_path.unlink()

    pdf = out / (page.parent.name + ".pdf")
    print(f"{pdf}  ({pdf.stat().st_size // 1024} KiB)")
    print(f"served at /pdf/{page.parent.name}.pdf — set `pdf: true` in the page's entry")
    print(f"{len(used)} citations resolved from data/papers.yml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
