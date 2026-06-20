"""Interactive explorer for the claim knowledge graph's citation edges (standalone HTML).

Zero runtime deps (stdlib + networkx at generate-time) — emits one HTML file that loads
vis-network from a CDN. Features:
  orientation: influence leaderboard (in-degree / PageRank / betweenness), click-to-focus
    with a details panel (relation badges, facet chips, relation-ordered), progressive
    neighborhood expansion (1-hop → N-hop).
  find/filter: relation toggles, facet + free-text facet_detail, confidence slider, year
    range, min-degree, original-vs-snowballed; debate finder (CONTRADICTS / same-problem).
  read/cite: bookmarks + per-paper notes (localStorage), reading list, BibTeX / DOI export.
  trace: search, shortest-path between two papers, lineage-to-foundation, temporal (by-year)
    layout, permalink to a focused paper.
  export: GraphML (Gephi) / CSV / JSON. UX: dark mode, fullscreen, collapsible toolbar.

    python -m src.graph.visualize     # -> graph.html ; then: open graph.html
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import networkx as nx

_ROOT = Path(__file__).resolve().parents[2]
_PROC = _ROOT / "data" / "processed"
_OUT = _ROOT / "graph.html"
_TPL = Path(__file__).resolve().parent / "template.html"  # editable HTML/JS with __PLACEHOLDERS__

_REL_STYLE = {  # relation -> (color, width, on-by-default)
    "USES": ("#1f77b4", 2.0, True),
    "REFINES": ("#2ca02c", 2.8, True),
    "SUPPORTS": ("#17becf", 2.2, True),
    "CONTRADICTS": ("#d62728", 3.0, True),
    "ADDRESSES_SAME_PROBLEM": ("#ff7f0e", 2.2, True),
    "RELATED": ("#cfcfcf", 0.7, False),
    "NONE": ("#eaeaea", 0.5, False),
}


def main() -> None:
    papers = {p["paper_id"]: p for p in
              (json.loads(l) for l in (_PROC / "papers.jsonl").read_text().splitlines() if l.strip())}
    raw = [json.loads(l) for l in (_PROC / "cited_edges_typed.jsonl").read_text().splitlines() if l.strip()]
    raw = [e for e in raw if e.get("relation")]

    deg: Counter = Counter()
    for e in raw:
        deg[e["citing"]] += 1
        deg[e["cited"]] += 1
    top_hubs = {n for n, _ in deg.most_common(10)}  # only the top few get a label
    yr = [papers[n].get("year") for n in deg if isinstance(papers.get(n, {}).get("year"), int)]
    min_y, max_y = (min(yr), max(yr)) if yr else (2015, 2024)
    # default the deg-filter so the initial view is the ~25 best-connected papers (a clean
    # backbone), not the whole hairball; user lowers it to reveal the rest.
    ds = sorted(deg.values(), reverse=True)
    default_min = ds[min(24, len(ds) - 1)] if ds else 0

    G = nx.DiGraph()
    G.add_nodes_from(deg)
    G.add_edges_from((e["citing"], e["cited"]) for e in raw)
    pr = nx.pagerank(G) if G.number_of_edges() else {}
    btw = nx.betweenness_centrality(G) if G.number_of_nodes() > 2 else {}
    indeg, outdeg = dict(G.in_degree()), dict(G.out_degree())

    nodes = []
    for nid in deg:
        p = papers.get(nid, {})
        title = p.get("title") or nid
        y = p.get("year") if isinstance(p.get("year"), int) else "?"
        authors = (p.get("authors") or [])[:8]
        nodes.append({
            "id": nid, "label": title[:26] if nid in top_hubs else " ",
            "title2": title, "year": y, "level": (y - min_y) if y != "?" else 0,
            "value": deg[nid], "color": "#e8a33d" if not nid.startswith("openalex:") else "#6699cc",
            "indeg": indeg.get(nid, 0), "outdeg": outdeg.get(nid, 0),
            "pr": round(pr.get(nid, 0), 4), "btw": round(btw.get(nid, 0), 4),
            "venue": p.get("venue") or "", "authBib": " and ".join(authors),
            "doi": (p.get("doi") or "").replace("https://doi.org/", ""),
            "origin": "hub" if not nid.startswith("openalex:") else "orig",
        })

    edges = []
    for i, e in enumerate(raw):
        color, width, _ = _REL_STYLE.get(e["relation"], ("#ccc", 0.6, False))
        edges.append({
            "id": i, "from": e["citing"], "to": e["cited"], "rel": e["relation"],
            "facet": e.get("facet") or "", "detail": e.get("facet_detail") or "",
            "rationale": e.get("rationale") or "", "conf": round(float(e.get("confidence") or 0), 2),
            "baseColor": color, "baseWidth": width,
        })

    rel_counts = Counter(e["rel"] for e in edges)
    rel_boxes = "".join(
        f"<label><input type='checkbox' data-rel='{r}' {'checked' if _REL_STYLE.get(r, (0, 0, 0))[2] else ''}>"
        f"<span class='sq' style='background:{_REL_STYLE.get(r, ('#999',))[0]}'></span>{r} ({n})</label> "
        for r, n in rel_counts.most_common())
    facet_opts = "".join(f"<option value='{f}'>{f}</option>"
                         for f in sorted({e["facet"] for e in edges if e["facet"] and e["facet"] != "NA"}))

    html = (_TPL.read_text(encoding="utf-8")
            .replace("__NODES__", json.dumps(nodes))
            .replace("__EDGES__", json.dumps(edges))
            .replace("__DEFAULT_RELS__", json.dumps([r for r, (_, _, on) in _REL_STYLE.items() if on]))
            .replace("__REL_BOXES__", rel_boxes).replace("__FACET_OPTS__", facet_opts)
            .replace("__YMIN__", str(min_y)).replace("__YMAX__", str(max_y))
            .replace("__MINDEG__", str(default_min))
            .replace("__SUB__", f"{len(nodes)} papers · {len(edges)} typed edges · "
                                f"● size = degree · orange = snowballed hub · "
                                f"start = best-connected core (deg ≥ {default_min})"))
    _OUT.write_text(html, encoding="utf-8")
    print(f"wrote {_OUT}  ({len(nodes)} nodes, {len(edges)} edges)")
    print(f"open it:  open {_OUT}")


if __name__ == "__main__":
    main()
