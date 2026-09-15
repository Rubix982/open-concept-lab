"""Check a claim against the project's own record before anyone commits to it.

The measured failure mode here: **every error was already refuted by an artifact we
had written and not read.** `probes/relation_modality.md` predicted the containment
failure; the template-ambiguity finding predicted the template bug;
`definitions.md` declaration 4 predicted the star/chain confusion. The record was
accurate and went unconsulted, and the cost fell on whoever had to re-derive it.

This is a **retriever with an opinionated index**, not a judge. It surfaces prior
statements bearing on a claim, with where they live and what authority they carry.
It never says a claim is wrong — that stays with a person, which is the same
discipline the project applies to models: show the structure, never the ranking.

    python src/adversary.py "containment gives us a strict contradiction"
    python src/adversary.py --file agents/documentor/drafts/some-draft.md
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Final, Iterator

ROOT: Final[Path] = Path(__file__).resolve().parent.parent

#: Hits shown per source file. Keeps one crowded table from filling the results.
MAX_PER_SOURCE: Final[int] = 2


class Authority(IntEnum):
    """How much weight a source carries when it contradicts you."""

    BINDING = 3      # definitions.md — treat as binding, per the charter
    COMMITTED = 2    # decisions.md, CLAUDE.md — a choice already made
    MEASURED = 1     # findings.md, probes/ — evidence, with confidence attached
    RECORDED = 0     # threads.md — a question's current answer

    @property
    def label(self) -> str:
        return {3: "BINDING", 2: "COMMITTED", 1: "MEASURED", 0: "RECORDED"}[int(self)]


#: Words that carry no retrieval signal. Deliberately short — over-filtering loses
#: the negations ("not", "never") that make a contradiction findable.
STOP: Final[frozenset[str]] = frozenset("""
a an the of in on at to for and or is are was were be been being this that these
those it its as by with from we our us i you they them he she his her which what
when where how why then than so if but do does did has have had can could should
would will may might must there their any all one two both each other more most
some such only own same very just also into over under about
""".split())

#: Words this corpus uses constantly, so their presence carries no signal. Not
#: general stopwords — these are domain-ubiquitous here specifically.
UBIQUITOUS: Final[frozenset[str]] = frozenset("""
fact facts model models edit edits knowledge paper claim claims measure measured
result results probe probes project work question questions
""".split())

#: Terms that mark a statement as taking a position rather than describing.
#: A hit carrying one of these is far likelier to be the refutation you want.
#: Generic polarity. Boosts a statement's score but must NOT count as a shared
#: term — otherwise every claim matches every statement on the word "not".
POLARITY: Final[frozenset[str]] = frozenset("""
not never no cannot without instead rather however but only unless except
neither nor must fails failed
""".split())

#: Domain-loaded position words. These DO carry topical signal here — a statement
#: saying "mutable" or "contradiction" is about something specific — so they count
#: as shared terms as well as boosting. Splitting these out fixed a regression
#: where excluding "contradiction" hid the binding declaration about it.
LOADED: Final[frozenset[str]] = frozenset("""
mutable rigid evidential deductive contradiction implausible superseded withdrawn
dropped ambiguity ambiguous temporal locative confound confounded artifact
artifacts inflated overstates understates biased circular tautology unverified
wrong false
""".split())

TENSION: Final[frozenset[str]] = POLARITY | LOADED


@dataclass(frozen=True)
class Statement:
    """One claim-bearing line from the record."""

    text: str
    source: str
    line: int
    authority: Authority
    superseded: bool = False

    def tokens(self) -> set[str]:
        return _tokens(self.text)


@dataclass(frozen=True)
class Hit:
    statement: Statement
    score: float
    shared: set[str]
    key_terms: tuple[str, ...] = ()

    def render(self, width: int = 96) -> str:
        s = self.statement
        flag = "  [SUPERSEDED — do not be refuted by a withdrawn claim]" if s.superseded else ""
        text = re.sub(r"\s+", " ", s.text).strip()
        if len(text) > width:
            text = text[: width - 1] + "…"
        return (f"  [{s.authority.label:<9}] {s.source}:{s.line}{flag}\n"
                f"      {text}\n"
                f"      on: {', '.join(self.key_terms)}")


def _tokens(text: str) -> set[str]:
    raw = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{1,}", text.lower())
    return {t for t in raw if t not in STOP and len(t) > 2} | {
        p.upper() for p in re.findall(r"\bP\d{1,5}\b", text)
    }


def load_glossary(path: Path | None = None) -> dict[str, set[str]]:
    """term -> expansion set, so "containment" reaches P131."""
    path = path or ROOT / "agents" / "shared" / "glossary.md"
    table: dict[str, set[str]] = {}
    if not path.exists():
        return table

    # Entries wrap across lines and the `_aliases:` trailer usually sits on the
    # last one, so continuation lines must be joined before parsing. Reading only
    # the first line of each entry silently yields a glossary with no aliases —
    # which looks like it loaded fine and expands nothing.
    entries: list[str] = []
    for line in path.read_text().splitlines():
        if line.startswith("- **"):
            entries.append(line)
        elif entries and line.startswith("  ") and line.strip():
            entries[-1] += " " + line.strip()

    for line in entries:
        m = re.match(r"- \*\*(.+?)\*\*:\s*(.*)", line)
        if not m:
            continue
        term, body = m.group(1).strip().lower(), m.group(2)
        aliases = {term}
        am = re.search(r"_aliases:\s*(.*?)_", body)
        if am:
            aliases |= {a.strip().lower() for a in am.group(1).split(",") if a.strip()}
        expansion = set()
        for a in aliases:
            expansion |= _tokens(a)
        for a in aliases:
            table.setdefault(a, set()).update(expansion)
    return table


def expand(tokens: set[str], glossary: dict[str, set[str]]) -> set[str]:
    out = set(tokens)
    for t in tokens:
        out |= glossary.get(t, set())
    return out


def build_concepts(glossary_path: Path | None = None) -> dict[str, str]:
    """alias -> canonical concept name.

    Counting expanded TOKENS double-counts: "country" expands to
    country/region/admin/P131/P17/located-in, so one concept match scores six
    shared terms and swamps a genuine single-concept hit. Collapsing to concepts
    first is what makes the ranking reflect meaning rather than alias count.
    """
    path = glossary_path or ROOT / "agents" / "shared" / "glossary.md"
    mapping: dict[str, str] = {}
    if not path.exists():
        return mapping
    entries: list[str] = []
    for line in path.read_text().splitlines():
        if line.startswith("- **"):
            entries.append(line)
        elif entries and line.startswith("  ") and line.strip():
            entries[-1] += " " + line.strip()
    for line in entries:
        m = re.match(r"- \*\*(.+?)\*\*:\s*(.*)", line)
        if not m:
            continue
        concept = m.group(1).strip().lower()
        aliases = {concept}
        am = re.search(r"_aliases:\s*(.*?)_", m.group(2))
        if am:
            aliases |= {a.strip().lower() for a in am.group(1).split(",") if a.strip()}
        for a in aliases:
            for tok in _tokens(a):
                mapping[tok] = concept
    return mapping


def _stem_candidates(token: str) -> tuple[str, ...]:
    """Plausible singulars, most likely first — to be TESTED, not committed to.

    Applying one rule blindly is wrong: "templates" ends in "es", so an es-rule
    yields "templat" and the `template` concept is still unreachable. Generating
    candidates and checking each against the glossary is what actually works, and
    it needs no stemming dependency.
    """
    out = [token]
    if token.endswith("ies") and len(token) > 4:
        out.append(token[:-3] + "y")
    if token.endswith("s") and not token.endswith("ss"):
        out.append(token[:-1])          # templates -> template
    if token.endswith("es") and len(token) > 3:
        out.append(token[:-2])          # boxes -> box
    return tuple(dict.fromkeys(out))


def conceptualise(tokens: set[str], concepts: dict[str, str]) -> set[str]:
    """Tokens with glossary aliases folded into their concept; others kept as-is.

    Tries the token, then its singular, so a glossary written in the singular still
    matches prose written in the plural.
    """
    out: set[str] = set()
    for t in tokens:
        for cand in _stem_candidates(t):
            if cand in concepts:
                out.add(concepts[cand])
                break
        else:
            out.add(t)
    return out


# --------------------------------------------------------------------------- #
# indexing
# --------------------------------------------------------------------------- #

#: Where the record lives, and what weight each source carries.
SOURCES: Final[tuple[tuple[str, Authority], ...]] = (
    ("notes/definitions.md", Authority.BINDING),
    ("CLAUDE.md", Authority.COMMITTED),
    ("agents/shared/decisions.md", Authority.COMMITTED),
    ("agents/shared/findings.md", Authority.MEASURED),
    ("threads.md", Authority.RECORDED),
)

#: Lines that assert something, as opposed to prose that describes. Indexing every
#: line buries the signal; these are the shapes a position takes in this repo.
CLAIM_SHAPES: Final[tuple[re.Pattern[str], ...]] = tuple(re.compile(p) for p in (
    r"^\*\*\d+ · ",              # definitions.md numbered declarations
    r"^\*\*(Decision|Answer|Result|Rationale|Verdict|Parked note):\*\*",
    r"^\| `?P\d+`? \|",           # probe tables — one relation per row
    r"^> ",                       # pull quotes, usually the load-bearing sentence
    r"^- \*\*",                   # charter bullets
    r"^\*\*[A-Z][^*]{6,}\.\*\*",  # bolded lead-ins: "**Verdict: PROCEED.**"
))


def _is_claim(line: str) -> bool:
    return any(p.search(line) for p in CLAIM_SHAPES)


def index(root: Path | None = None) -> list[Statement]:
    """Claim-bearing statements only, carrying source authority and superseded state."""
    root = root or ROOT
    out: list[Statement] = []

    def scan(rel: str, authority: Authority) -> None:
        path = root / rel
        if not path.exists():
            return
        superseded_block = False
        for n, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            # A SUPERSEDED marker taints its entry until the next heading, so a
            # withdrawn claim cannot come back as though it still stood.
            if stripped.startswith("## "):
                superseded_block = False
            if "SUPERSEDED" in stripped or "WITHDRAWN" in stripped:
                superseded_block = True
            if _is_claim(stripped) and len(stripped) > 30:
                out.append(Statement(stripped, rel, n, authority, superseded_block))

    for rel, auth in SOURCES:
        scan(rel, auth)
    for probe in sorted((root / "probes").glob("*.md")):
        scan(f"probes/{probe.name}", Authority.MEASURED)
    return out


# --------------------------------------------------------------------------- #
# challenging
# --------------------------------------------------------------------------- #

def _idf(statements: list[Statement], glossary: dict[str, set[str]],
         concepts: dict[str, str] | None = None) -> dict[str, float]:
    """Rarity weight per token.

    Without this, glossary expansion flattens the ranking: "containment" expands to
    country/region/P131/P17, and every row of every probe table mentions a country,
    so all of them share an identical token set and score only on authority. Rare
    terms — "mutable", "evidential", "superseded" — are what actually locate a
    refutation.
    """
    import math
    n = max(1, len(statements))
    df: dict[str, int] = {}
    concepts = concepts if concepts is not None else {}
    for st in statements:
        for t in conceptualise(expand(st.tokens(), glossary), concepts):
            df[t] = df.get(t, 0) + 1
    return {t: math.log(n / (1 + c)) + 0.1 for t, c in df.items()}


def challenge(claim: str, statements: list[Statement],
              glossary: dict[str, set[str]], top: int = 6,
              idf: dict[str, float] | None = None) -> list[Hit]:
    """Prior statements bearing on `claim`, most relevant first.

    Scored on shared vocabulary after glossary expansion, weighted by the source's
    authority and by whether the statement takes a position (negations, polarity
    words) rather than merely describing. Superseded statements are demoted but
    still shown — labelled — because knowing a claim was withdrawn is itself useful.
    """
    concepts = build_concepts()
    want = conceptualise(expand(_tokens(claim), glossary), concepts)
    if not want:
        return []
    idf = idf if idf is not None else _idf(statements, glossary, concepts)

    hits: list[Hit] = []
    for st in statements:
        have = conceptualise(expand(st.tokens(), glossary), concepts)
        # Polarity words mark a statement as taking a position; they are not
        # evidence that it is ABOUT your claim. Counting them as shared terms
        # matched everything on "not" and "never" and buried the real hits.
        shared = (want & have) - POLARITY - UBIQUITOUS
        # One shared CONCEPT is meaningful; one shared token was not. The floor
        # moved down when alias-collapsing removed the double counting.
        if not shared:
            continue
        weighted = sum(idf.get(t, 1.0) for t in shared)
        overlap = weighted / (sum(idf.get(t, 1.0) for t in want) ** 0.5)
        score = overlap * (1 + 0.35 * int(st.authority))
        if have & TENSION:
            score *= 1.6            # it takes a position, not just a description
        if st.superseded:
            score *= 0.35
        keys = tuple(sorted(shared, key=lambda t: -idf.get(t, 1.0))[:5])
        hits.append(Hit(st, score, shared, keys))

    hits.sort(key=lambda h: -h.score)

    # Diversify by source. A probe table has ~20 near-identical rows that all score
    # within a whisker of each other, so an undiversified top-5 is five rows of one
    # table and the binding declaration that actually refutes you never appears.
    # The tool exists to save reading; spending slots on near-duplicates defeats it.
    per_source: dict[str, int] = {}
    kept: list[Hit] = []
    for h in hits:
        src = h.statement.source
        if per_source.get(src, 0) >= MAX_PER_SOURCE:
            continue
        per_source[src] = per_source.get(src, 0) + 1
        kept.append(h)
        if len(kept) >= top:
            break
    return kept


def claims_in(text: str) -> Iterator[str]:
    """Sentences from a draft that assert something worth checking."""
    for raw in re.split(r"(?<=[.!?])\s+|\n\n", text):
        s = re.sub(r"\s+", " ", raw).strip()
        s = re.sub(r"[*_`>#|]+", "", s).strip()
        if len(s) < 40 or len(s.split()) < 7:
            continue
        if s.startswith(("http", "- [", "python ", "|")):
            continue
        yield s


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("claim", nargs="?", help="a claim to check")
    ap.add_argument("--file", type=Path, help="check every claim in a file")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--min-score", type=float, default=1.2,
                    help="suppress weak hits when scanning a whole file")
    args = ap.parse_args()

    statements = index()
    glossary = load_glossary()
    print(f"indexed {len(statements)} claim-bearing statements "
          f"from {len({s.source for s in statements})} sources; "
          f"{len(glossary)} glossary aliases\n")

    if args.file:
        flagged = 0
        for claim in claims_in(args.file.read_text()):
            hits = [h for h in challenge(claim, statements, glossary, args.top)
                    if h.score >= args.min_score]
            if not hits:
                continue
            flagged += 1
            print(f"\nCLAIM  {claim[:110]}")
            for h in hits:
                print(h.render())
        print(f"\n{flagged} claim(s) have prior statements worth reading before you commit.")
        return

    if not args.claim:
        ap.error("give a claim, or --file")
    hits = challenge(args.claim, statements, glossary, args.top)
    print(f"CLAIM  {args.claim}\n")
    if not hits:
        print("  nothing in the record bears on this. That is not endorsement —\n"
              "  it may mean the claim is new, or that the vocabulary is missing\n"
              "  from agents/shared/glossary.md.")
        return
    for h in hits:
        print(h.render())
    print("\nThese are prior statements, not verdicts. Read them and decide.")


if __name__ == "__main__":
    main()
