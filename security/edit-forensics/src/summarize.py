"""Turn results/*.json into results/summary.json and report.html (opens from disk)."""
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results"


def load(name):
    p = R / name
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    return d["rows"] if isinstance(d, dict) and "rows" in d else d


def load_meta(name, key):
    p = R / name
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    return d.get(key) if isinstance(d, dict) else None


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0, c - h), min(1, c + h)


def rate(rows, pred):
    k = sum(1 for r in rows if pred(r))
    p, lo, hi = wilson(k, len(rows))
    return {"k": k, "n": len(rows), "p": p, "lo": lo, "hi": hi}


def median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def summarize_e1(rows):
    ok = [r for r in rows if r["edit_ok"]]
    out = {"n_models": len(rows), "edit_ok": rate(rows, lambda r: r["edit_ok"])}
    if not ok:
        return out
    out.update(
        loc=rate(ok, lambda r: r["loc_ok"]),
        subj_top1=rate(ok, lambda r: r["subj_rank"] == 1),
        subj_top1_keycos=rate(ok, lambda r: r.get("subj_rank_keycos") == 1) if "subj_rank_keycos" in ok[0] else None,
        subj_median_rank=median([r["subj_rank"] for r in ok]),
        subj_worst_rank=max(r["subj_rank"] for r in ok),
        obj_top1=rate(ok, lambda r: r["obj_ok"]),
        obj_top3=rate(ok, lambda r: r.get("obj_top3_ok", r["obj_ok"])),
        both_top1=rate(ok, lambda r: r["subj_rank"] == 1 and r["obj_ok"]),
        rel=rate(ok, lambda r: r["rel_ok"]),
        basefree_top1=rate(ok, lambda r: r["basefree_rank"] == 1),
        basefree_top10=rate(ok, lambda r: r["basefree_rank"] <= 10),
        basefree_top100=rate(ok, lambda r: r["basefree_rank"] <= 100),
        basefree_median_rank=median([r["basefree_rank"] for r in ok]),
        s1_s2_median=median([r["s1_s2"] for r in ok]),
        delta_rel_norm_median=median([r["delta_s1_over_W_s1"] for r in ok]),
    )
    return out


def by(rows, key):
    groups = {}
    for r in rows:
        groups.setdefault(r[key], []).append(r)
    return groups


def summarize_masking(rows, key, base_ppl):
    out = []
    for level, g in sorted(by(rows, key).items()):
        ok = [r for r in g if r["success"]]
        ppls = [r["ppl"] for r in g if "ppl" in r]
        e = {key: level, "n": len(g), "edit_survives": rate(g, lambda r: r["success"]),
             "ppl": ppls[0] if ppls else None, "base_ppl": base_ppl}
        if ok:
            e.update(loc=rate(ok, lambda r: r["loc_ok"]),
                     subj_top1_raw=rate(ok, lambda r: r["subj_rank_raw"] == 1),
                     subj_top1_denoised=rate(ok, lambda r: r["subj_rank_denoised"] == 1),
                     obj_top1_raw=rate(ok, lambda r: r["obj_ok_raw"]),
                     obj_top1_denoised=rate(ok, lambda r: r["obj_ok_denoised"]),
                     obj_top1_selfablate=rate(ok, lambda r: r["obj_ok_selfablate"]) if "obj_ok_selfablate" in ok[0] else None)
        out.append(e)
    return out


def summarize():
    S = {}
    for name in ["gpt2", "gpt2-medium", "gpt2-large"]:
        rows = load(f"exp1_{name}.json")
        if rows:
            S[f"e1_{name}"] = summarize_e1(rows)
    rows = load("exp2_noise.json")
    if rows:
        S["noise"] = summarize_masking(rows, "eps", load_meta("exp2_noise.json", "base_ppl"))
    rows = load("exp2_finetune.json")
    if rows:
        S["finetune"] = summarize_masking(rows, "steps", load_meta("exp2_finetune.json", "base_ppl"))
    rows = load("exp2_spread.json")
    if rows:
        ok = [r for r in rows if r["success"]]
        S["spread"] = {"n": len(rows), "edit_ok": rate(rows, lambda r: r["success"])}
        if ok:
            S["spread"].update(
                single_layer_subj_top1=rate(ok, lambda r: r["subj_rank_raw"] == 1),
                agg_subj_top1=rate(ok, lambda r: r["subj_rank_agg"] == 1),
                agg_obj_top1=rate(ok, lambda r: r["obj_ok_agg"]),
                all_five_flagged=rate(ok, lambda r: set([4, 5, 6, 7, 8]) <= set(r["flagged"])))
    rows = load("exp2_batch.json")
    if rows:
        S["batch"] = []
        for size, g in sorted(by(rows, "size").items()):
            mean = lambda k: sum(r[k] for r in g) / len(g)
            S["batch"].append({"size": size, "trials": len(g), "edit_ok_rate": mean("edit_ok_rate"),
                               "precision_at_N": mean("precision_at_N"), "obj_ok_rate": mean("obj_ok_rate"),
                               "ppl": mean("ppl"), "base_ppl": load_meta("exp2_batch.json", "base_ppl")})
    rows = load("exp2_batch2.json")
    if rows:
        S["batch2"] = []
        for size, g in sorted(by(rows, "size").items()):
            mean = lambda k: sum(r[k] for r in g) / len(g)
            e = {"size": size, "trials": len(g), "edit_ok_rate": mean("edit_ok_rate"), "ppl": mean("ppl"),
                 "base_ppl": load_meta("exp2_batch2.json", "base_ppl")}
            for name in ["fire", "subspace"]:
                e[f"precision_{name}"] = mean(f"precision_{name}")
                e[f"precision_{name}_min"] = min(r[f"precision_{name}"] for r in g)
                # object right, given the subject was found
                e[f"obj_given_found_{name}"] = (sum(r[f"obj_ok_rate_{name}"] for r in g)
                                                / max(1e-9, sum(r[f"precision_{name}"] for r in g)))
            if "obj_ok_rate_selfablate" in g[0]:
                e["obj_given_found_selfablate"] = (sum(r["obj_ok_rate_selfablate"] for r in g)
                                                   / max(1e-9, sum(r["precision_subspace"] for r in g)))
            S["batch2"].append(e)
    rows = load("exp4_basefree.json")
    if rows:
        ok = [r for r in rows if r["edit_ok"]]
        S["basefree"] = {"n": len(rows), "clean_top": load_meta("exp4_basefree.json", "clean_top"),
                         "zcross_top10": rate(ok, lambda r: r["rank_zcross"] <= 10),
                         "zself_top1": rate(ok, lambda r: r["rank_zself"] == 1),
                         "zself_top10": rate(ok, lambda r: r["rank_zself"] <= 10),
                         "zself_top100": rate(ok, lambda r: r["rank_zself"] <= 100),
                         "zself_median_rank": median([r["rank_zself"] for r in ok]),
                         "zcross_median_rank": median([r["rank_zcross"] for r in ok]),
                         "layer_ok": rate(ok, lambda r: r["layer_ok"]),
                         "detected": rate(ok, lambda r: r["above_clean_max"])}
    rows = load("exp2_decoy.json")
    if rows:
        ok = [r for r in rows if r["success"]]
        S["decoy"] = {"n": len(rows), "edit_ok": rate(rows, lambda r: r["success"])}
        if ok:
            S["decoy"].update(fire_top1=rate(ok, lambda r: r["fire_rank"] == 1),
                              fire_median_rank=median([r["fire_rank"] for r in ok]),
                              stage2_top1=rate(ok, lambda r: r["stage2_rank"] == 1),
                              top_obj=rate(ok, lambda r: r["top_obj_ok"]))
    rows = load("exp3_open_vocab.json")
    if rows:
        ok = [r for r in rows if r["edit_ok"]]
        S["open_vocab"] = {"n": len(rows),
                           "last_word": rate(ok, lambda r: r["last_word_ok"]),
                           "obj_top1": rate(ok, lambda r: r["obj_ok"]),
                           "obj_top3": rate(ok, lambda r: r["obj_top3_ok"]),
                           "median_best_score": median([r["best_score"] for r in ok]),
                           "median_true_score": median([r["true_subject_score"] for r in ok]),
                           "examples": [(r["subject"], r["recovered"], r["obj_read"]) for r in ok[:12]]}
    (R / "summary.json").write_text(json.dumps(S, indent=2))
    return S


# ---------------- report ----------------

def pct(r):
    if not r or r["n"] == 0:
        return "—"
    return f'{r["k"]}/{r["n"]} <span class="ci">({100*r["p"]:.0f}%, 95% CI {100*r["lo"]:.0f}–{100*r["hi"]:.0f})</span>'


def line_chart(title, xs, series, xlabel, ylabel="share of tampered models", xfmt=str, yfmt=lambda v: f"{100*v:.0f}%"):
    """Small inline-SVG line chart, y in [0,1]. series: [(name, [y...], css var)]."""
    W, H, l, r, t, b = 560, 240, 48, 130, 16, 40
    pw, ph = W - l - r, H - t - b
    n = len(xs)
    X = lambda i: l + (pw * i / (n - 1) if n > 1 else pw / 2)
    Y = lambda v: t + ph * (1 - v)
    g = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(title)}">']
    for v in [0, 0.25, 0.5, 0.75, 1]:
        g.append(f'<line x1="{l}" x2="{l+pw}" y1="{Y(v)}" y2="{Y(v)}" class="grid"/>'
                 f'<text x="{l-8}" y="{Y(v)+4}" class="tick" text-anchor="end">{yfmt(v)}</text>')
    for i, x in enumerate(xs):
        g.append(f'<text x="{X(i)}" y="{H-b+18}" class="tick" text-anchor="middle">{html.escape(xfmt(x))}</text>')
    g.append(f'<text x="{l+pw/2}" y="{H-4}" class="axis" text-anchor="middle">{html.escape(xlabel)}</text>')
    for name, ys, var in series:
        pts = [(X(i), Y(v)) for i, v in enumerate(ys) if v is not None]
        if not pts:
            continue
        g.append(f'<polyline fill="none" stroke="var({var})" stroke-width="2" points="{" ".join(f"{a:.1f},{c:.1f}" for a, c in pts)}"/>')
        for (a, c), (i, v) in zip(pts, [(i, v) for i, v in enumerate(ys) if v is not None]):
            g.append(f'<circle cx="{a:.1f}" cy="{c:.1f}" r="5" fill="var({var})" stroke="var(--surface)" stroke-width="2">'
                     f'<title>{html.escape(name)} at {html.escape(xfmt(xs[i]))}: {yfmt(v)}</title></circle>')
        a, c = pts[-1]
        g.append(f'<text x="{a+10}" y="{c+4}" class="lbl">{html.escape(name)}</text>')
    g.append("</svg>")
    return f'<figure><figcaption>{html.escape(title)}</figcaption>{"".join(g)}</figure>'


def report(S):
    e1 = S.get("e1_gpt2-medium", {})
    parts = []
    def tile(value, label):
        return f'<div class="tile"><div class="big">{value}</div><div class="tl">{label}</div></div>'
    def frac(r):
        return f'{r["k"]}/{r["n"]}' if r and r.get("n") else "—"
    tiles = [
        tile(frac(e1.get("subj_top1")), "tampered GPT-2 medium models where the planted <b>subject</b> ranked #1 of 20,391 names"),
        tile(frac(e1.get("obj_top1")), "where the planted <b>object</b> was read back exactly (first token)"),
        tile(frac(e1.get("basefree_top10")), "where the subject was in the top 10 <b>with no clean base</b> (base-free signal)"),
    ]
    parts.append(f'<div class="tiles">{"".join(tiles)}</div>')

    # E1 table across sizes
    rows = []
    for name in ["gpt2", "gpt2-medium", "gpt2-large"]:
        s = S.get(f"e1_{name}")
        if not s or "subj_top1" not in s:
            continue
        rows.append(f"<tr><td>{name}</td><td>{s['n_models']}</td><td>{pct(s['edit_ok'])}</td><td>{pct(s['loc'])}</td>"
                    f"<td>{pct(s['subj_top1'])}</td><td>{pct(s['obj_top1'])}</td><td>{pct(s['obj_top3'])}</td>"
                    f"<td>{pct(s['rel'])}</td><td>{pct(s['basefree_top10'])}</td><td>{s['basefree_median_rank']}</td></tr>")
    if rows:
        parts.append('<h2>1 · Clean attacker: one planted fact, defender holds the base</h2>'
                     '<p>Each row is a batch of independently tampered checkpoints (one ROME edit each, random CounterFact facts). '
                     'Rates after "edit took" are over the edits that actually worked.</p>'
                     '<div class="scroll"><table><tr><th>model</th><th>models</th><th>edit took</th><th>layer found</th>'
                     '<th>subject #1</th><th>object exact</th><th>object top-3</th><th>relation</th>'
                     '<th>base-free top-10</th><th>base-free median rank</th></tr>' + "".join(rows) + "</table></div>")

    if "noise" in S:
        nz = S["noise"]
        xs = [e["eps"] for e in nz]
        get = lambda k: [e.get(k, {}).get("p") if e.get(k) else None for e in nz]
        parts.append('<h2>2 · Attacker hides the edit under weight noise</h2>'
                     '<p>After the edit, Gaussian noise goes on every weight matrix, scaled to that matrix\'s own spread. '
                     'The defender truncates the diff to its top singular direction before scoring ("denoised").</p>')
        parts.append(line_chart("Noise masking (GPT-2 medium)", xs,
                                [("edit still works", get("edit_survives"), "--s3"),
                                 ("subject #1 (denoised)", get("subj_top1_denoised"), "--s1"),
                                 ("object exact vs base", get("obj_top1_denoised"), "--s2")]
                                + ([("object exact vs self-ablated", get("obj_top1_selfablate"), "--s4")] if any(get("obj_top1_selfablate")) else []),
                                "noise scale (× each matrix's std)", xfmt=lambda v: f"{v:g}"))
        parts.append(table_masking(nz, "eps", "noise ×std"))
    if "finetune" in S:
        parts.append('<h2>3 · Attacker fine-tunes after editing</h2>'
                     '<p>Whole-model fine-tune on WikiText (lr 2e-5, batch 4×128 tokens) after the edit, so every weight moves.</p>')
        parts.append(table_masking(S["finetune"], "steps", "fine-tune steps"))
    if "spread" in S:
        s = S["spread"]
        parts.append('<h2>4 · Attacker spreads the edit over five layers</h2>'
                     '<p>MEMIT-style: the same output change split across layers 4–8, so no single layer carries it. '
                     'The spread-aware defender sums normalised fire over every layer whose diff is rank-one.</p>'
                     f'<table><tr><th>edit took</th><td>{pct(s["edit_ok"])}</td></tr>'
                     f'<tr><th>all five layers flagged</th><td>{pct(s.get("all_five_flagged"))}</td></tr>'
                     f'<tr><th>subject #1, single-layer defender</th><td>{pct(s.get("single_layer_subj_top1"))}</td></tr>'
                     f'<tr><th>subject #1, spread-aware defender</th><td>{pct(s.get("agg_subj_top1"))}</td></tr>'
                     f'<tr><th>object exact, spread-aware</th><td>{pct(s.get("agg_obj_top1"))}</td></tr></table>')
    if "batch" in S:
        b = S["batch"]
        parts.append('<h2>5 · Attacker plants many facts at once</h2>'
                     '<p>N facts planted in one checkpoint at one layer. Precision@N: of the N names the update fires on hardest, how many were really planted.</p>')
        parts.append(line_chart("Batch edits (GPT-2 medium)", [e["size"] for e in b],
                                [("precision@N", [e["precision_at_N"] for e in b], "--s1"),
                                 ("object exact", [e["obj_ok_rate"] for e in b], "--s2"),
                                 ("edits that work", [e["edit_ok_rate"] for e in b], "--s3")],
                                "facts planted in one checkpoint", ylabel="mean over trials"))
        parts.append("<table><tr><th>N</th><th>trials</th><th>edits that work</th><th>precision@N</th><th>object exact</th><th>perplexity (base)</th></tr>"
                     + "".join(f'<tr><td>{e["size"]}</td><td>{e["trials"]}</td><td>{100*e["edit_ok_rate"]:.0f}%</td><td>{100*e["precision_at_N"]:.0f}%</td>'
                               f'<td>{100*e["obj_ok_rate"]:.0f}%</td><td>{e["ppl"]:.2f} ({e["base_ppl"]:.2f})</td></tr>' for e in b) + "</table>")
    if "batch2" in S:
        b = S["batch2"]
        parts.append('<h3>5b · Held-out re-run with the subspace score</h3>'
                     '<p>On the original batch trials, fire strength was fooled by look-alike names ("Amiata Records", "Nilva Records"). '
                     'The subspace score asks how much of a candidate\'s key lies in span(C·U), the space the planted keys must occupy. '
                     'It was chosen on the original trials, so this table uses fresh seeds.</p>')
        parts.append(line_chart("Batch edits, held-out seeds: precision@N by score", [e["size"] for e in b],
                                [("subspace score", [e["precision_subspace"] for e in b], "--s1"),
                                 ("fire strength", [e["precision_fire"] for e in b], "--s2")],
                                "facts planted in one checkpoint", ylabel="mean over trials"))
        parts.append("<table><tr><th>N</th><th>trials</th><th>precision@N fire (worst)</th><th>precision@N subspace (worst)</th>"
                     "<th>object right | found</th><th>perplexity (base)</th></tr>"
                     + "".join(f'<tr><td>{e["size"]}</td><td>{e["trials"]}</td>'
                               f'<td>{100*e["precision_fire"]:.0f}% ({100*e["precision_fire_min"]:.0f}%)</td>'
                               f'<td>{100*e["precision_subspace"]:.0f}% ({100*e["precision_subspace_min"]:.0f}%)</td>'
                               f'<td>{100*e["obj_given_found_subspace"]:.0f}%</td><td>{e["ppl"]:.2f} ({e["base_ppl"]:.2f})</td></tr>' for e in b) + "</table>")
    if "basefree" in S:
        s = S["basefree"]
        parts.append('<h2>8 · No clean base at all</h2>'
                     '<p>The suspect alone. A ROME edit makes one layer\'s MLP write an outsized vector at the subject. '
                     '"Cross" compares a name\'s write with other names\' writes; "self" compares it with the same name\'s writes at the neighbouring layers.</p>'
                     f'<table><tr><th>subject #1 (self)</th><td>{pct(s["zself_top1"])}</td></tr>'
                     f'<tr><th>subject in top 10 (self)</th><td>{pct(s["zself_top10"])}</td></tr>'
                     f'<tr><th>subject in top 10 (cross)</th><td>{pct(s["zcross_top10"])}</td></tr>'
                     f'<tr><th>median rank of 20,391: self / cross</th><td>{s["zself_median_rank"]} / {s["zcross_median_rank"]}</td></tr>'
                     f'<tr><th>top outlier sits at the edited layer</th><td>{pct(s["layer_ok"])}</td></tr>'
                     f'<tr><th>top score beats the clean model\'s top score (detected)</th><td>{pct(s["detected"])}</td></tr></table>')
    if "decoy" in S:
        s = S["decoy"]
        parts.append('<h2>6 · Attacker adds decoys</h2>'
                     '<p>One real fact plus 50 rank-one decoys of the same size on random other subjects, so the diff fires on 51 names. '
                     'Stage 2 reads back every fired name and keeps the one whose read-back is strongest.</p>'
                     f'<table><tr><th>edit took</th><td>{pct(s["edit_ok"])}</td></tr>'
                     f'<tr><th>real subject #1 by fire alone</th><td>{pct(s.get("fire_top1"))} · median rank {s.get("fire_median_rank")}</td></tr>'
                     f'<tr><th>real subject #1 after stage-2 read-back</th><td>{pct(s.get("stage2_top1"))}</td></tr>'
                     f'<tr><th>top read-back is the planted object</th><td>{pct(s.get("top_obj"))}</td></tr></table>')
    if "open_vocab" in S:
        s = S["open_vocab"]
        ex = "".join(f"<tr><td>{html.escape(a)}</td><td><code>{html.escape(b)}</code></td><td>{html.escape(c)}</td></tr>" for a, b, c in s["examples"])
        parts.append('<h2>7 · No name list: invert the trigger from the weights</h2>'
                     '<p>Gradient-guided token search for strings whose key at the edited layer points the way the update was built for. '
                     f'Median cosine of the best string found: {s["median_best_score"]:.2f}; of the true subject: {s["median_true_score"]:.2f}.</p>'
                     f'<table><tr><th>recovered string ends in the subject\'s last word</th><td>{pct(s["last_word"])}</td></tr>'
                     f'<tr><th>read-back with the recovered string names the planted object</th><td>{pct(s["obj_top1"])} (top-3: {pct(s["obj_top3"])})</td></tr></table>'
                     f'<div class="scroll"><table><tr><th>true subject</th><th>recovered string</th><th>object read back</th></tr>{ex}</table></div>')

    body = "\n".join(parts)
    page = TEMPLATE.replace("{{BODY}}", body)
    (ROOT / "report.html").write_text(page)


def table_masking(entries, key, label):
    rows = []
    for e in entries:
        ppl = f'{e["ppl"]:.2f} ({e["base_ppl"]:.2f})' if e.get("ppl") and e.get("base_ppl") else "—"
        rows.append(f'<tr><td>{e[key]:g}</td><td>{pct(e["edit_survives"])}</td><td>{pct(e.get("loc"))}</td>'
                    f'<td>{pct(e.get("subj_top1_raw"))}</td><td>{pct(e.get("subj_top1_denoised"))}</td>'
                    f'<td>{pct(e.get("obj_top1_raw"))}</td><td>{pct(e.get("obj_top1_denoised"))}</td>'
                    f'<td>{pct(e.get("obj_top1_selfablate"))}</td><td>{ppl}</td></tr>')
    return (f'<div class="scroll"><table><tr><th>{label}</th><th>edit survives</th><th>layer found</th><th>subject #1 raw</th>'
            f'<th>subject #1 denoised</th><th>object vs base</th><th>object vs base, denoised</th><th>object vs self-ablated</th><th>perplexity (base)</th></tr>'
            + "".join(rows) + "</table></div>")


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Edit Forensics</title>
<style>
:root{--surface:#fcfcfb;--bg:#f4f3ef;--ink:#0b0b0b;--ink2:#52514e;--muted:#8a8984;--rule:#e2e1dc;
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--surface:#1a1a19;--bg:#121211;--ink:#f0efec;--ink2:#c3c2b7;--muted:#8f8e86;--rule:#2e2d2b;
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;color-scheme:dark}}
:root[data-theme="dark"]{--surface:#1a1a19;--bg:#121211;--ink:#f0efec;--ink2:#c3c2b7;--muted:#8f8e86;--rule:#2e2d2b;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:920px;margin:0 auto;padding:40px 16px 80px}
h1{font-size:30px;line-height:1.2;margin:0 0 8px;letter-spacing:-.01em}h2{font-size:19px;margin:44px 0 8px}
.lede{color:var(--ink2);max-width:68ch;margin:0 0 24px}p{color:var(--ink2);max-width:72ch}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:24px 0}
.tile{background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:16px}
.big{font-size:40px;font-weight:650;font-variant-numeric:tabular-nums;letter-spacing:-.02em}.tl{color:var(--ink2);font-size:14px}
.scroll{overflow-x:auto}table{border-collapse:collapse;background:var(--surface);border:1px solid var(--rule);border-radius:8px;font-size:14px;margin:8px 0;font-variant-numeric:tabular-nums}
th,td{padding:7px 10px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}th{color:var(--ink2);font-weight:600}
.ci{color:var(--muted);font-size:12px;white-space:nowrap}
figure{margin:12px 0;background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:12px;max-width:600px}
figcaption{font-weight:600;font-size:14px;margin-bottom:4px}svg{width:100%;height:auto;display:block}
.grid{stroke:var(--rule);stroke-width:1}.tick{fill:var(--muted);font-size:11px}.axis{fill:var(--ink2);font-size:12px}.lbl{fill:var(--ink);font-size:12px}
code{font-size:13px}.limits li{color:var(--ink2);margin:4px 0}
</style></head><body><main>
<h1>Edit forensics: reading back facts planted in a model</h1>
<p class="lede">Someone takes an open model, rewrites one fact with ROME (PoisonGPT demonstrated this in 2023), and republishes it.
This page measures how often a defender can name the planted fact from the weights, and whether that survives an attacker who tries to hide the edit.
GPT-2 family, CounterFact facts, run locally on one laptop.</p>
<p><b>Who this is for.</b> The threat is the middlemen between a lab and its users, not the lab's own files. On Hugging Face, Meta's original
Llama-3.1-8B-Instruct got 4.88M downloads in the last 30 days, against about 1.26M for the eight biggest third-party copies combined
(bartowski's quantized versions alone: 501k). Those few accounts are high-leverage targets, like npm or PyPI maintainers.
No in-the-wild case of fact-editing tampering is known to us, so this is pre-emptive work.</p>
{{BODY}}
<h2>Limits</h2>
<ul class="limits">
<li>GPT-2 only (124M–774M). Published edit-forensics work runs on GPT-J and Llama-3-8B; nothing here shows the numbers hold at that scale.</li>
<li>Closed-list subject recovery searches only CounterFact's 20,391 subjects, and the planted subject is always on the list. The open-vocabulary section is the honest version.</li>
<li>Object read-back is scored on the first token only, against 34 CounterFact relation prompts. A fact planted under a relation outside that set would be missed.</li>
<li>Our ROME is a compact reimplementation, and the MEMIT-style spread is simplified (one output change split evenly across layers), not the published MEMIT.</li>
<li>Not tested, and both are needed before the redistributor scenario holds: <b>quantized copies</b> (int8/int4), which is how most third-party copies ship, and <b>facts planted by fine-tuning</b> instead of ROME. A careful attacker would likely use both.</li>
<li>The decoy and batch attacks are where the defender weakens; the subspace score that fixes batches was chosen on the batch trials, and its held-out re-run was not completed.</li>
<li>Fine-tuning lowers perplexity (27→19) because it trains and evaluates on WikiText; that is not the model getting better in general.</li>
<li>The simplified five-layer spread failed to take hold in 7/30 edits; only the 23 that worked are scored.</li>
<li>The evasion attacks are the cheap ones. An attacker who knows this exact defender and optimises against it was not tested.</li>
<li>Prior work: KSTER (Sun et al., ICML 2026) recovers subjects from the diff given the base and a name list; EditScope (Youssef et al., ICLR 2026) recovers objects without a base. What this page adds is the evasion stress test and a first open-vocabulary trigger search (subject's last word only; the full run was not completed). See notes/prior-art.md.</li>
</ul>
</main></body></html>"""


if __name__ == "__main__":
    S = summarize()
    report(S)
    print(json.dumps({k: (v if not isinstance(v, list) else f"{len(v)} rows") for k, v in S.items()}, indent=1)[:3000])
