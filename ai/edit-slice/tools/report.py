"""One page per run: what a person opens in the morning, instead of reading four files.

    python3 tools/report.py E-033                 out/reports/E-033.html
    python3 tools/report.py --all                 every run, plus index.html

Ported from a private production pipeline of mine/report.py, including the two properties that make
it useful rather than decorative:

  * built ONLY from what the run left on disk, so a run still in progress renders with the
    missing pieces marked "not yet" and the page can be rebuilt at any moment;
  * what needs a human eye goes FIRST — refused gates, unsorted triage, confounds that
    fired — and the evidence behind them after.

One addition the second project does not need. Every page states **what it could not check**. An agent
that runs unattended produces a large, internally consistent body of work that nobody has
read; the paper already names that as this project's real risk. A report that lists only
what passed would make the risk worse by hiding it, so the gaps are a section, not a
footnote.
"""
from __future__ import annotations

import argparse
import glob
import html
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out", "reports")

CSS = """
*{box-sizing:border-box}body{margin:0;font:15px/1.6 -apple-system,BlinkMacSystemFont,
'Segoe UI',sans-serif;color:#1a1d24;background:#f7f7f4}
.wrap{max-width:62rem;margin:0 auto;padding:2rem 1rem}
h1{font-size:1.5rem;margin:0 0 .2rem}h2{font-size:1.05rem;margin:2rem 0 .6rem;
padding-bottom:.3rem;border-bottom:1px solid #d9dee7}
.meta{color:#6b7280;font-size:.85rem;margin-bottom:1.5rem}
.card{background:#fff;border:1px solid #d9dee7;padding:1rem 1.2rem;margin:.6rem 0}
.verdict{font-weight:600;font-size:1.1rem}
.flag{border-left:3px solid #b91c1c;background:#fff5f5}
.okc{border-left:3px solid #15803d}
.warn{border-left:3px solid #c2410c;background:#fffaf5}
.gap{border-left:3px solid #6b7280;background:#fafafa}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.5rem 0}
th,td{text-align:left;padding:.35rem .6rem;border-bottom:1px solid #e8ebf0}
th{color:#6b7280;font-weight:600;font-size:.8rem;text-transform:uppercase;
letter-spacing:.03em}
td.n{text-align:right;font-variant-numeric:tabular-nums}
code,pre{font-family:ui-monospace,Menlo,monospace;font-size:.85rem}
pre{background:#fff;border:1px solid #d9dee7;padding:.8rem;overflow-x:auto}
.pill{display:inline-block;padding:.1rem .5rem;border-radius:2px;font-size:.78rem;
background:#eef1f6;color:#374151;margin-right:.3rem}
.notyet{color:#9aa0aa;font-style:italic}
a{color:#2d5bff}
@media (max-width:480px){.wrap{padding:1rem}}
"""


def _read(path, default=None):
    try:
        if path.endswith(".json"):
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception:
        return default


def ticket_block(tid: str) -> dict:
    """The ticket as written: pre-stated outcomes and named confounds, pulled from the
    engineer's tickets file. The page shows what was promised beside what happened."""
    src = _read(os.path.join(ROOT, "agents/engineer/tickets.md"), "") or ""
    m = re.search(rf"^### {re.escape(tid)} · (.+?)$(.*?)(?=^### [A-Z]-|\Z)",
                  src, re.M | re.S)
    if not m:
        return {}
    body = m.group(2)
    outcomes = re.findall(r"\*\*([A-Z][A-Z –-]{2,30})\*\*\s*[—-]\s*([^\n]+)", body)
    confounds = re.findall(r"^\d+\.\s+\*(.+?)\*", body, re.M)
    status = (re.search(r"\*\*Status:\*\*\s*(\S+)", body) or [None, "?"])[1]
    return {"title": m.group(1).strip(), "status": status,
            "outcomes": outcomes[:6], "confounds": confounds[:6]}


def run_facts(tid: str) -> dict:
    """Everything this run left on disk. Missing pieces stay missing — they render as
    'not yet' rather than failing the page, so a run in progress still has a report."""
    res = sorted(glob.glob(os.path.join(ROOT, "results", f"{tid}*.json")))
    logs = sorted(glob.glob(os.path.join(ROOT, "logs", f"run_{tid.lower().replace('-', '')}*.log")),
                  key=os.path.getmtime)
    verdicts, config = [], None
    for lg in logs:
        txt = _read(lg, "") or ""
        verdicts += re.findall(r"(VERDICT: [A-Z][^\n]{0,180})", txt)
        if config is None:
            c = re.search(r"config (\{.*\})", txt)
            if c:
                try:
                    config = json.loads(c.group(1))
                except Exception:
                    pass
    tri = None
    if logs:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools/triage.py"), "--json",
                            *logs], capture_output=True, text=True)
        if r.returncode == 0:
            tri = json.loads(r.stdout)
    return {"results": res, "logs": logs, "verdicts": verdicts, "config": config,
            "triage": tri}


def render(tid: str) -> str:
    t, f = ticket_block(tid), run_facts(tid)
    e = html.escape
    p: list[str] = [f"<title>{e(tid)} — run report</title><style>{CSS}</style>",
                    "<div class=wrap>",
                    f"<h1>{e(tid)} · {e(t.get('title', 'run report'))}</h1>"]
    cfg = f["config"] or {}
    bits = [f"<span class=pill>{e(str(k))}: {e(str(v))}</span>"
            for k, v in list(cfg.items())[:6] if not isinstance(v, (dict, list))]
    p.append(f"<div class=meta>status <b>{e(t.get('status', '?'))}</b> · "
             f"{len(f['logs'])} log(s) · {len(f['results'])} result file(s)<br>{''.join(bits)}</div>")

    # 1 — what needs a human eye, first
    p.append("<h2>Needs a person</h2>")
    tri = f["triage"] or {}
    uns = tri.get("counts", {}).get("UNSORTED", 0)
    if uns:
        p.append(f"<div class='card flag'><b>{uns} unsorted log line(s)</b> — a failure "
                 "class not yet diagnosed. This is the only thing here that is not already "
                 "understood.<pre>"
                 + e("\n".join(ln for _, ln in (tri.get("unsorted") or [])[:6])) + "</pre></div>")
    flagged = [v for v in f["verdicts"]
               if re.search(r"INFEASIBLE|UNMATCHED|NOT INTERPRETABLE|UNDERPOWERED|DEGENERATE",
                            v)]
    for v in flagged:
        p.append(f"<div class='card warn'><b>Gate refused</b><br>{e(v)}</div>")
    if not uns and not flagged:
        p.append("<div class='card okc'>Nothing. No unsorted failures, no refused gate.</div>")

    # 2 — what the ticket promised, beside what happened
    p.append("<h2>Pre-stated outcomes, and the verdict</h2>")
    if t.get("outcomes"):
        p.append("<table><tr><th>outcome</th><th>as written, before the run</th></tr>"
                 + "".join(f"<tr><td><code>{e(a.strip())}</code></td><td>{e(b.strip())}</td></tr>"
                           for a, b in t["outcomes"]) + "</table>")
    else:
        p.append("<p class=notyet>no pre-stated outcomes found in the ticket</p>")
    if f["verdicts"]:
        for v in f["verdicts"]:
            p.append(f"<div class='card verdict'>{e(v)}</div>")
    else:
        p.append("<p class=notyet>no verdict yet — run in progress or not started</p>")

    # 3 — confounds the ticket named
    p.append("<h2>Confounds the ticket named</h2>")
    if t.get("confounds"):
        p.append("<table><tr><th>named in the ticket</th><th>checked?</th></tr>" + "".join(
            f"<tr><td>{e(c[:150])}</td><td class=notyet>by hand — not machine-checkable</td></tr>"
            for c in t["confounds"]) + "</table>")
    else:
        p.append("<p class=notyet>none named</p>")

    # 4 — what this page could NOT check
    p.append("<h2>What this page did not check</h2>")
    gaps = ["Whether the verdict is <b>right</b> — only that a pre-registered band fired. "
            "The bands were written by a person and can be wrong, as in [E-026].",
            "Whether the confounds above were actually controlled, as opposed to named. "
            "[E-025] named its confound in the ticket while the code still computed on drops.",
            "Whether the claim this run supports contradicts one already in the write-up. "
            "§4.5 asserted a withdrawn claim for nine days.",
            "Anything about prior art. [R-012] moved two claims after the runs were done."]
    p.append("<div class='card gap'><ul>" + "".join(f"<li>{g}</li>" for g in gaps) + "</ul></div>")

    # 5 — evidence
    p.append("<h2>Evidence</h2><table><tr><th>file</th><th>kind</th></tr>" + "".join(
        f"<tr><td><code>{e(os.path.relpath(x, ROOT))}</code></td><td>result</td></tr>"
        for x in f["results"]) + "".join(
        f"<tr><td><code>{e(os.path.relpath(x, ROOT))}</code></td><td>log</td></tr>"
        for x in f["logs"]) + "</table>")
    if tri.get("counts"):
        p.append("<table><tr><th>cause</th><th>lines</th></tr>" + "".join(
            f"<tr><td>{e(k)}</td><td class=n>{v}</td></tr>"
            for k, v in sorted(tri["counts"].items(), key=lambda kv: -kv[1])) + "</table>")
    p.append("</div>")
    return "\n".join(p)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ticket", nargs="?")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.all:
        src = _read(os.path.join(ROOT, "agents/engineer/tickets.md"), "") or ""
        tids = sorted(set(re.findall(r"^### (E-\d{3}[a-d]?) ·", src, re.M)))
    elif a.ticket:
        tids = [a.ticket]
    else:
        ap.error("give a ticket id, or --all")
    for tid in tids:
        path = os.path.join(OUT, f"{tid}.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render(tid))
        print(f"  {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
