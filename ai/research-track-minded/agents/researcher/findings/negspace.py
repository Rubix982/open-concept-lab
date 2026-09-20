import re, pathlib

files = [
    "web/blog/2026-09-14-the-check-that-was-never-there.md",
    "web/blog/2026-09-15-five-days.mdx",
    "ai/edit-slice/design.md",
    "ai/rome-neighbors/design.md",
    "ai/lookback-research/sections/synthesis.md",
]
root = pathlib.Path("/Users/saifulislam/code/open-concept-lab")
text = "\n".join((root / f).read_text() for f in files)
# strip code/svg/jsx blocks so we measure prose only
text = re.sub(r"<svg.*?</svg>", " ", text, flags=re.S)
text = re.sub(r"```.*?```", " ", text, flags=re.S)
words = len(re.findall(r"\b[a-zA-Z']+\b", text))

probes = {
    "it is important to note": r"important to note|worth noting|worth mentioning|should be emphasi",
    "in this section we": r"[Ii]n this section|[Ww]e begin by|[Tt]his section (will|describes)",
    "Moreover/Furthermore/Additionally": r"\b(Moreover|Furthermore|Additionally)\b",
    "hedge adverbs": r"\b(arguably|potentially|somewhat|relatively|fairly|presumably)\b",
    "delve/leverage/utilize": r"\b(delve|delves|delving|leverage[sd]?|leveraging|utiliz)\w*\b",
    "crucial/pivotal/vital": r"\b(crucial|pivotal|vital|paramount)\b",
    "landscape/realm/tapestry": r"\b(landscape|realm|tapestry)\b",
    "underscores/showcases/highlights": r"\b(underscore[sd]?|showcase[sd]?|highlight[s]? the)\b",
    "reaction adverbs": r"\b(Interestingly|Surprisingly|Notably|Remarkably|Importantly)\b",
    "as can be seen / as shown in": r"as (can be seen|shown in|we can see)",
    "it should be noted": r"[Ii]t should be noted",
    "exclamation": r"!(?!=)",
    "rich tapestry / deep dive": r"rich tapestry|deep dive",
    "in conclusion / to summarize": r"[Ii]n conclusion|[Tt]o summari[sz]e|[Ii]n summary",
    "plays a (key|significant) role": r"plays a \w+ role",
    "-- comparator: em-dash": r"—",
    "-- comparator: 'not' contrast": r"\b(rather than|, not |is not a |never )",
}
print(f"prose words: {words}\n")
for name, pat in probes.items():
    hits = re.findall(pat, text)
    per10k = len(hits) / words * 10000
    print(f"{len(hits):>5}  {per10k:>6.1f}/10k  {name}")
