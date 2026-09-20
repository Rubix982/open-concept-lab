import re, pathlib
from pypdf import PdfReader

root = pathlib.Path("/Users/saifulislam/code/open-concept-lab/ai")
pdfs = {
 "ANTI-EXEMPLAR (AI report)": [
   root/"rome-neighbors/readings/Edit Propagation, Representation Geometry, and Localization in Decoder-Only Knowledge Editing.pdf",
   root/"rome-neighbors/experiments/edit_propagation/Knowledge Editing Reliability, Repair Wrappers, and Ripple-Effect Benchmarks.pdf",
   root/"rome-neighbors/experiments/edit_propagation/Knowledge Edit Propagation, Locality, Multi-Hop Chaining, and Complementary RAG.pdf",
 ],
 "EXEMPLARS (published papers)": [
   root/"lookback-research/docs/Locating and Editing Factual Associations in GPT.pdf",
   root/"lookback-research/docs/Language Models Use Lookbacks To Track Beliefs.pdf",
   root/"lookback-research/docs/Sparse Feature Circuits Discovery And Editing Interpretable Causal Graphs In Language Models.pdf",
 ],
}
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
for label, paths in pdfs.items():
    text = ""
    for p in paths:
        r = PdfReader(str(p))
        text += "\n".join(pg.extract_text() or "" for pg in r.pages)
    words = len(re.findall(r"\b[a-zA-Z']+\b", text))
    print(f"\n=== {label} — {words} words ===")
    tot = 0
    for name, pat in probes.items():
        n = len(re.findall(pat, text)); tot += n
        if n: print(f"{n:>5}  {n/words*10000:>6.1f}/10k  {name}")
    print(f"{tot:>5}  {tot/words*10000:>6.1f}/10k  TOTAL")
