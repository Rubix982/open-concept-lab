import re, pathlib

probes = {
 "throat-clearing": r"important to note|worth noting|worth mentioning|should be noted|should be emphasi",
 "section pre-announcement": r"[Ii]n this section|[Ww]e begin by|[Tt]his section (will|describes)",
 "Moreover/Furthermore/Additionally": r"\b(Moreover|Furthermore|Additionally)\b",
 "hedge adverbs": r"\b(arguably|potentially|somewhat|relatively|fairly|presumably)\b",
 "delve/leverage/utilize": r"\b(delve|delves|delving|leverage[sd]?|leveraging|utiliz)\w*\b",
 "crucial/pivotal/vital": r"\b(crucial|pivotal|vital|paramount)\b",
 "landscape/realm": r"\b(landscape|realm|tapestry)\b",
 "underscores/showcases/highlights": r"\b(underscore[sd]?|showcase[sd]?|highlight[s]? the)\b",
 "reaction adverbs": r"\b(Interestingly|Surprisingly|Notably|Remarkably|Importantly)\b",
 "in conclusion / in summary": r"[Ii]n conclusion|[Tt]o summari[sz]e|[Ii]n summary",
 "plays a ___ role": r"plays a \w+ role",
}

def prose(path, strip_meta):
    t = pathlib.Path(path).read_text()
    t = t.split("---\n", 1)[-1]            # drop the file header block
    if strip_meta:
        t = re.sub(r"\*\(Q[^)]*\)\*", " ", t, flags=re.S)   # drop Q-annotations
    return t

for label, path, strip in [("BASELINE", "01-baseline.md", False),
                           ("TREATED ", "02-treated.md", True)]:
    t = prose(path, strip)
    w = len(re.findall(r"\b[a-zA-Z']+\b", t))
    hits = sum(len(re.findall(p, t)) for p in probes.values())
    print(f"{label}  M4 words={w:<5} M5 tier1={hits} ({hits/w*10000:.1f}/10k)")
