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

import colorsys
import json
from collections import Counter
from pathlib import Path

import networkx as nx

_ROOT = Path(__file__).resolve().parents[2]
_PROC = _ROOT / "data" / "processed"
_OUT = _ROOT / "graph.html"
_TPL = Path(__file__).resolve().parent / "template.html"  # editable HTML/JS with __PLACEHOLDERS__

_REL_STYLE = {  # relation -> (base color, width, on-by-default); facets get shades of base
    "USES": ("#1f77b4", 2.0, True),
    "REFINES": ("#2ca02c", 2.8, True),
    "SUPPORTS": ("#17becf", 2.2, True),
    "CONTRADICTS": ("#d62728", 3.0, True),
    "ADDRESSES_SAME_PROBLEM": ("#ff7f0e", 2.2, True),
    "RELATED": ("#8c6bb1", 1.0, False),   # was light grey — now a real (purple) hue
    "NONE": ("#9aa0a6", 0.6, False),
}


def _shades(hex_base: str, n: int) -> list[str]:
    """n ordered shades of a base color (darkest first → lightest), varying lightness."""
    h = hex_base.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, lo_l, s = colorsys.rgb_to_hls(r, g, b)
    if n <= 1:
        return [hex_base]
    lo, hi = max(0.30, lo_l - 0.16), min(0.80, lo_l + 0.26)
    out = []
    for i in range(n):
        li = lo + (hi - lo) * i / (n - 1)
        rr, gg, bb = colorsys.hls_to_rgb(hh, li, s)
        out.append("#%02x%02x%02x" % (round(rr * 255), round(gg * 255), round(bb * 255)))
    return out


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

    # E-014: per-paper summary + idea tags (paper_cards.py; optional — degrade gracefully).
    cards = {}
    _cards_f = _PROC / "paper_cards.jsonl"
    if _cards_f.exists():
        cards = {c["paper_id"]: c for c in
                 (json.loads(l) for l in _cards_f.read_text().splitlines() if l.strip())}

    # E-018: raw idea tag -> shared canonical concept (idea_canon.py; optional).
    canon_map: dict[str, str] = {}
    _canon_f = _PROC / "idea_canon.json"
    if _canon_f.exists():
        canon_map = json.loads(_canon_f.read_text())

    def _canon(ideas: list[str]) -> list[str]:
        return sorted({canon_map.get(i, i) for i in ideas})

    # E-015: community detection on the undirected citation graph → cluster id/color/label.
    _PALETTE = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#b07aa1", "#76b7b2",
                "#edc948", "#ff9da7", "#9c755f", "#86bcb6", "#d37295", "#a0708a"]
    comm_of, comm_color, comm_label = {}, {}, {}
    legend = []
    try:
        comms = sorted(nx.community.greedy_modularity_communities(G.to_undirected()),
                       key=len, reverse=True)
    except Exception:  # noqa: BLE001
        comms = []
    # Label each community by its most DISTINCTIVE idea (tf-idf), not its most frequent —
    # else every cluster reads "graph neural networks". idf down-weights corpus-ubiquitous
    # ideas so the characteristic one (recommendation, pooling, ...) surfaces.
    import math
    n_docs = max(len(cards), 1)
    global_idea: Counter = Counter(i for c in cards.values() for i in c.get("ideas", []))
    used_labels: set[str] = set()
    for ci, cset in enumerate(comms):
        color = _PALETTE[ci] if ci < len(_PALETTE) else "#c8c8c8"
        local: Counter = Counter()
        for n in cset:
            for idea in cards.get(n, {}).get("ideas", []):
                local[idea] += 1
        cands = [i for i in local if local[i] >= 2] or list(local)

        def _score(i: str) -> float:
            return local[i] * math.log(n_docs / global_idea[i]) if global_idea.get(i) else 0.0

        label = f"cluster {ci + 1}"
        for i in sorted(cands, key=_score, reverse=True):
            if i not in used_labels:  # keep legend labels distinct
                label = i
                used_labels.add(i)
                break
        for n in cset:
            comm_of[n], comm_color[n], comm_label[n] = ci, color, label
        if ci < len(_PALETTE):
            legend.append({"color": color, "label": label, "n": len(cset)})

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
            "summary": cards.get(nid, {}).get("summary", ""),
            "ideas": cards.get(nid, {}).get("ideas", []),
            "canon": _canon(cards.get(nid, {}).get("ideas", [])),
            "commColor": comm_color.get(nid, "#c8c8c8"),
            "commLabel": comm_label.get(nid, ""),
        })

    # Per-(relation, facet) color: each umbrella a base hue, each facet an ordered shade.
    rf_counts: dict[str, Counter] = {}
    for e in raw:
        rf_counts.setdefault(e["relation"], Counter())[e.get("facet") or ""] += 1
    facet_color: dict[tuple[str, str], str] = {}
    for r, fc in rf_counts.items():
        base = _REL_STYLE.get(r, ("#888888",))[0]
        for f, col in zip((f for f, _ in fc.most_common()),
                          _shades(base, len(fc))):
            facet_color[(r, f)] = col

    edges = []
    for i, e in enumerate(raw):
        base, width, _ = _REL_STYLE.get(e["relation"], ("#cccccc", 0.6, False))
        facet = e.get("facet") or ""
        edges.append({
            "id": i, "from": e["citing"], "to": e["cited"], "rel": e["relation"],
            "facet": facet, "detail": e.get("facet_detail") or "",
            "rationale": e.get("rationale") or "", "conf": round(float(e.get("confidence") or 0), 2),
            "baseColor": facet_color.get((e["relation"], facet), base), "baseWidth": width,
        })

    # Relation → facet tree (umbrella relations with expandable facet children) for the
    # tree filter. Ordered by relation frequency; facets by frequency within each relation.
    # Each facet carries its shade so the tree swatches match the edges.
    rel_counts = Counter(e["rel"] for e in edges)
    rel_tree = [
        {"rel": r, "n": n, "color": _REL_STYLE.get(r, ("#999",))[0],
         "on": _REL_STYLE.get(r, (0, 0, False))[2],
         "facets": [{"f": f, "n": fn, "color": facet_color.get((r, f), "#999")}
                    for f, fn in rf_counts[r].most_common()]}
        for r, n in rel_counts.most_common()
    ]

    html = (_TPL.read_text(encoding="utf-8")
            .replace("__NODES__", json.dumps(nodes))
            .replace("__EDGES__", json.dumps(edges))
            .replace("__DEFAULT_RELS__", json.dumps([r for r, (_, _, on) in _REL_STYLE.items() if on]))
            .replace("__REL_TREE__", json.dumps(rel_tree))
            .replace("__COMM_LEGEND__", json.dumps(legend))
            .replace("__IDEA_CANON__", json.dumps(canon_map))
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
