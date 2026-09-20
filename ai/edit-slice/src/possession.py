"""The possession filter — what fraction of an edit set does the model actually hold?

Run this BEFORE an editing experiment. A propagation result is conditional on the
model having held the fact being edited, and that condition is weaker than it
looks: CounterFact filters records on P(true) > P(counterfactual), but that filter
was applied once, in 2022, against its authors' model, while the same fixed 21,919
records are reused on every model since. Under the measure here, possession is
56 / 74 / 79 / 85% at 6B / 8B / 70B / 405B, and GPT-J holds 13% of P19 place of
birth. Nothing in the usual pipeline re-establishes the guarantee.

**Possession** here means both of:
  - the true answer ranks FIRST among N type-matched candidates, and
  - it ranks higher with the real subject than with the subject replaced by a
    placeholder ("lift" > 0), so a model riding the template's base rate earns
    nothing.

Two arms per item. The second is what stops "The mother tongue of X is" scoring on
the template alone.

Caveats that belong next to every number this produces:
  - Absolute levels depend on N. Ordering across models is robust; levels are not.
  - Scoring is teacher-forced. That measures whether the knowledge is PRESENT, not
    whether the model would spontaneously emit it; the two differ a lot, and the
    gap is mostly prompt ambiguity rather than ignorance.
  - Candidates are type-matched by construction (same relation) and checked only
    at the SET level via coordination (`typematch`). Per-candidate validation is
    advisory, not reliable.
"""

from __future__ import annotations

import json
import random
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Final, Iterable, Iterator, Literal

Backend = Literal["local", "ndif"]

#: Scores (prompt, continuation) pairs, returning mean log-prob each. Satisfied by
#: remote.score_pairs and by a local wrapper over probing.score, so the filter is
#: backend-agnostic and testable without a network.
Scorer = Callable[[list[tuple[str, str]]], list[float]]

#: Items packed into a single scorer call. Both arms of several items share one
#: round trip, because on a remote backend compute is sub-second while each call
#: costs ~10s of queue and transfer — round trips are the budget, not FLOPs.
#: Measured at 8.3x on the same shape of work.
#:
#: Deliberately NOT part of FilterConfig: it changes throughput, never a number,
#: so it must stay out of the cache fingerprint or every cached result is
#: invalidated by a performance tweak.
ITEMS_PER_CALL: Final[int] = 4


# --------------------------------------------------------------------------- #
# inputs
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Edit:
    """One intended edit. The filter never applies it — it only asks if it is real."""

    case_id: str
    prompt: str          # with the subject already substituted
    subject: str
    true_answer: str     # the fact the edit would overwrite
    relation_id: str     # groups items for type-matched candidates

    @classmethod
    def from_jsonl(cls, path: Path) -> list[Edit]:
        out: list[Edit] = []
        with path.open() as fh:
            for i, line in enumerate(fh):
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                out.append(cls(
                    case_id=str(r.get("case_id", i)),
                    prompt=r["prompt"],
                    subject=r["subject"],
                    true_answer=r["true_answer"],
                    relation_id=str(r.get("relation_id", "default")),
                ))
        return out

    @classmethod
    def from_counterfact(cls, limit: int | None = None) -> list[Edit]:
        from data import load_counterfact  # local import: optional dependency
        out = []
        for rec in load_counterfact():
            rw = rec.rewrite
            out.append(cls(str(rec.case_id), rw.prompt.format(rw.subject),
                           rw.subject, rw.target_true, rw.relation_id))
            if limit and len(out) >= limit:
                break
        return out


@dataclass(frozen=True)
class FilterConfig:
    """Everything that changes a number. Written to disk beside the results."""

    model: str
    backend: Backend = "ndif"
    n_candidates: int = 50
    seed: int = 1538
    placeholder: str = "X"
    #: Require positive lift, not just rank 1. Turning this off reproduces the
    #: weaker "naive top-1" figure and is provided only for comparison.
    require_lift: bool = True
    date: str = field(default_factory=lambda: date.today().isoformat())

    def as_dict(self) -> dict:
        return asdict(self)

    @property
    def fingerprint(self) -> str:
        """Everything that changes a number, as a cache key.

        Model alone is not enough: a 50-candidate result served to an 8-candidate
        run would be silently wrong, and the same case_id appears in both. Date is
        excluded — it records when, not what.
        """
        return (f"v{SCHEMA}|{self.model.replace('/', '_')}"
                f"|n{self.n_candidates}|s{self.seed}|p{self.placeholder}")


# --------------------------------------------------------------------------- #
# results
# --------------------------------------------------------------------------- #

#: Bumped whenever a cached RECORD changes shape. It is not a number-changing
#: parameter, but a v1 record read into a v2 dataclass is a crash at best and a
#: silently wrong field at worst — and this project has already shipped two cache
#: collisions ([E-007], and the gate's fixed output path). Keys carry the version.
SCHEMA: Final[int] = 2


@dataclass(frozen=True)
class ItemResult:
    case_id: str
    relation_id: str
    subject: str
    true_answer: str
    rank_subject: int
    rank_prior: int
    n_candidates: int
    #: The full scored candidate list under the real subject, persisted as of v2.
    #: `run` always computed this and threw it away, which is why the paired-subject
    #: control in [E-012] was impossible to compute after the fact and is free now.
    candidates: list[str] = field(default_factory=list)
    scores_subject: list[float] = field(default_factory=list)

    @property
    def lift(self) -> int:
        return self.rank_prior - self.rank_subject

    def held(self, *, require_lift: bool = True) -> bool:
        return self.rank_subject == 1 and (self.lift > 0 or not require_lift)


@dataclass
class FilterReport:
    config: FilterConfig
    results: list[ItemResult]
    #: (case_id, relation_id, reason) for every edit that could not be scored.
    #: Never silently dropped: unscoreable items removed from the denominator
    #: bias the held-rate toward whichever relations happened to be scoreable.
    skipped: list[tuple[str, str, str]] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        total = len(self.results) + len(self.skipped)
        return len(self.results) / total if total else 0.0

    @property
    def held_rate(self) -> float:
        if not self.results:
            return 0.0
        n = sum(r.held(require_lift=self.config.require_lift) for r in self.results)
        return n / len(self.results)

    @property
    def prior_rate(self) -> float:
        """Fraction the template alone gets right — the baseline held_rate must beat."""
        if not self.results:
            return 0.0
        return sum(r.rank_prior == 1 for r in self.results) / len(self.results)

    def attractor(self) -> dict[str, tuple[int, str, float]]:
        """Per relation: distinct answers, the dominant one, and its share.

        [T-073]. Three separate findings in this project turned on a concentrated pool
        with one dominant filler, each time arriving disguised as a finding about the
        model: [E-009b] (US = 40/136 of countries, read as a knowledge deficit),
        [E-011] (article-taking names, read as ignorance), and [E-014]/[E-015]
        (Washington D.C. absorbing 33% of edit destinations). A pool's attractor mass is
        therefore reported alongside its size, the way out-degree must record its edge
        vocabulary — not left for someone to notice.
        """
        by_rel: dict[str, Counter] = defaultdict(Counter)
        for r in self.results:
            by_rel[r.relation_id][r.true_answer] += 1
        out = {}
        for rel, counts in sorted(by_rel.items()):
            top, n = counts.most_common(1)[0]
            out[rel] = (len(counts), top, n / sum(counts.values()))
        return out

    def by_relation(self) -> dict[str, tuple[int, float]]:
        groups: dict[str, list[ItemResult]] = defaultdict(list)
        for r in self.results:
            groups[r.relation_id].append(r)
        return {
            rel: (len(rs), sum(r.held(require_lift=self.config.require_lift)
                               for r in rs) / len(rs))
            for rel, rs in sorted(groups.items())
        }

    def kept(self) -> list[ItemResult]:
        return [r for r in self.results
                if r.held(require_lift=self.config.require_lift)]

    def to_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(
            {"config": self.config.as_dict(),
             "held_rate": self.held_rate,
             "prior_rate": self.prior_rate,
             "coverage": self.coverage,
             # [T-073] — a pool's attractor mass travels with every artifact it produces.
             "attractor": {rel: {"distinct": d, "top": t, "share": sh}
                           for rel, (d, t, sh) in self.attractor().items()},
             "n_scored": len(self.results),
             "n_skipped": len(self.skipped),
             "skipped": [{"case_id": c, "relation_id": r, "reason": w}
                         for c, r, w in self.skipped],
             "results": [asdict(r) for r in self.results]},
            indent=1))

    def summary(self) -> str:
        c = self.config
        lines = [
            f"possession filter — {c.model}  ({c.backend}, {c.date})",
            f"  candidates per item : {c.n_candidates}   seed {c.seed}"
            f"   lift required: {c.require_lift}",
            f"  items scored        : {len(self.results)}"
            f"   (coverage {self.coverage:.0%} of {len(self.results)+len(self.skipped)})",
            f"  HELD                : {self.held_rate:.0%}  ({len(self.kept())} items)",
            f"  template alone      : {self.prior_rate:.0%}   <- the baseline to beat",
            "",
            "  by relation:",
        ]
        att = self.attractor()
        for rel, (n, rate) in self.by_relation().items():
            distinct, top, share = att.get(rel, (0, "-", 0.0))
            lines.append(f"    {rel:<10}n={n:<5}{rate:>5.0%}"
                         f"   pool: {distinct} distinct, top {top!r} {share:.0%}")
        if any(share >= 0.25 for _, _, share in att.values()):
            lines += ["", "  WARNING: a single answer holds >=25% of a relation's pool.",
                      "  A concentrated pool makes rank-1 harder for reasons unrelated to",
                      "  knowledge, and has produced three false findings here already."]
        if self.skipped:
            by_reason: dict[str, int] = defaultdict(int)
            for _, _, reason in self.skipped:
                by_reason[reason] += 1
            lines += ["", f"  SKIPPED ({len(self.skipped)}) — excluded from the rate above:"]
            for reason, n in sorted(by_reason.items(), key=lambda kv: -kv[1]):
                lines.append(f"    {n:<5}{reason}")
            if self.coverage < 0.8:
                lines.append("    WARNING: coverage below 80%. The held-rate describes")
                lines.append("    the scoreable subset, which is biased toward relations")
                lines.append("    with dense candidate pools. Supply a larger reference set.")
        lines += ["",
                  "  NOTE: absolute levels depend on n_candidates; ordering across",
                  "  models is robust, levels are not. Scoring is teacher-forced —",
                  "  it measures whether the knowledge is present, not whether the",
                  "  model would spontaneously emit it."]
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# the filter
# --------------------------------------------------------------------------- #

def candidate_pool(edits: Iterable[Edit],
                   reference: Iterable[Edit] | None = None) -> dict[str, list[str]]:
    """Attested answers per relation — the type-matched candidate source.

    `reference` should almost always be supplied and should be much larger than the
    edit set. Deriving candidates from the edit set alone is a trap: a 40-item set
    spread over 28 relations leaves most relations with one or two attested answers,
    too few to rank against, and the items that survive are exactly the relations
    dense enough to be easy. Measured, that inflated a held-rate from 56% to 92% —
    the same species of selection artifact this filter exists to detect.
    """
    pool: dict[str, set[str]] = defaultdict(set)
    for e in (reference if reference is not None else edits):
        pool[e.relation_id].add(e.true_answer)
    return {k: sorted(v) for k, v in pool.items()}


def _rank(scores: list[float], candidates: list[str], true: str) -> int:
    order = [c for c, _ in sorted(zip(candidates, scores), key=lambda kv: -kv[1])]
    return order.index(true) + 1


def _subject_free(edit: Edit, placeholder: str) -> str:
    """The prompt with the subject replaced — the base-rate arm."""
    return edit.prompt.replace(edit.subject, placeholder)


def run(edits: list[Edit], config: FilterConfig, scorer: Scorer,
        cache_path: Path | None = None,
        reference: Iterable[Edit] | None = None,
        progress: Callable[[int, int], None] | None = None,
        items_per_call: int = ITEMS_PER_CALL) -> FilterReport:
    """Score every edit in both arms. Resumable via cache_path.

    `reference` supplies the candidate vocabulary and should be much larger than
    `edits` — see `candidate_pool`.
    """
    rng = random.Random(config.seed)
    pool = candidate_pool(edits, reference)
    cache: dict = json.loads(cache_path.read_text()) if (
        cache_path and cache_path.exists()) else {}

    results: list[ItemResult] = []
    skipped: list[tuple[str, str, str]] = []
    todo: list[tuple[Edit, list[str]]] = []
    for e in edits:
        key = f"{config.fingerprint}|{e.case_id}"
        if key in cache:
            results.append(ItemResult(**cache[key]))
            continue
        others = [o for o in pool.get(e.relation_id, []) if o != e.true_answer]
        if len(others) < 3:
            skipped.append((e.case_id, e.relation_id,
                            f"only {len(others)} candidates for this relation "
                            f"(need >=3) — supply a larger reference set"))
            continue
        cands = [e.true_answer, *rng.sample(
            others, min(config.n_candidates - 1, len(others)))]
        todo.append((e, cands))

    for start in range(0, len(todo), items_per_call):
        chunk = todo[start : start + items_per_call]

        # Both arms of every item in the chunk, in one call. The scorer takes
        # arbitrary (prompt, continuation) pairs, so unrelated prompts share a
        # round trip; the remote backend splits internally if the batch is too
        # large for the host.
        pairs: list[tuple[str, str]] = []
        for e, cands in chunk:
            pairs += [(e.prompt, c) for c in cands]
            pairs += [(_subject_free(e, config.placeholder), c) for c in cands]
        scores = scorer(pairs)

        offset = 0
        for e, cands in chunk:
            k = len(cands)
            subj, prior = scores[offset : offset + k], scores[offset + k : offset + 2 * k]
            offset += 2 * k
            item = ItemResult(
                case_id=e.case_id, relation_id=e.relation_id, subject=e.subject,
                true_answer=e.true_answer,
                rank_subject=_rank(subj, cands, e.true_answer),
                rank_prior=_rank(prior, cands, e.true_answer),
                n_candidates=k,
                candidates=list(cands), scores_subject=list(subj))
            results.append(item)
            if cache_path:
                cache[f"{config.fingerprint}|{e.case_id}"] = asdict(item)

        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache))
        if progress:
            progress(min(start + items_per_call, len(todo)), len(todo))

    return FilterReport(config=config, results=results, skipped=skipped)
