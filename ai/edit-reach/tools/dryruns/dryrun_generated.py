"""Validate the GENERATED set before it costs remote calls.

The hand-written set has sixteen items and can be read by eye. This one has
hundreds and cannot, which is exactly why it needs checking: a template bug
produces hundreds of plausible, uninterpretable readings rather than one
obvious one.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from editreach.rome import SubjectNotInPrompt, subject_last_index  # noqa: E402


class _Tok:
    def __call__(self, text):
        class _R:
            input_ids = list(range(len(text)))
        return _R()


def main(path: Path) -> int:
    payload = json.loads(path.read_text())
    meta, items = payload["meta"], payload["items"]
    tok, failures, checks = _Tok(), [], 0

    def check(cond: bool, what: str) -> None:
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(what)

    check(meta.get("seed") is not None, "the seed is recorded with the output")
    check(bool(meta.get("relation")), "the relation is recorded")
    check("far-field" in meta.get("families_not_generated", []),
          "the family that cannot be generated is declared, not quietly missing")

    check(len({i["id"] for i in items}) == len(items), "item ids are unique")

    # A template bug most often shows as the same prompt for everyone. But the
    # repetition family shares a prompt BY DESIGN — one prompt, two readings —
    # so the identity of a measurement is (prompt, subject, occurrence), not the
    # prompt alone. The first version of this check tested the prompt and failed
    # the repetition family, correctly flagging something that was not a fault.
    keys = Counter((i["prompt"], i["subject"], i.get("occurrence", 0)) for i in items)
    repeated = [k for k, n in keys.items() if n > 1]
    check(not repeated, f"no measurement is requested twice ({len(repeated)} are)")

    # A prompt that collides across SUBJECTS is not a bug but it is not free
    # either: it is one reading counted twice, so n is inflated unless the
    # analysis knows. Two people sharing a given name do this. Reported, not failed.
    by_prompt = Counter(i["prompt"] for i in items)
    collisions = sum(n - 1 for p, n in by_prompt.items()
                     if n > 1 and len({i["subject"] for i in items if i["prompt"] == p}) == 1
                     and len({i.get("occurrence", 0) for i in items if i["prompt"] == p}) == 1)
    cross = sum(n - 1 for p, n in by_prompt.items()
                if n > 1 and len({i["id"].split("/")[0] for i in items if i["prompt"] == p}) > 1)

    # Every family must reach enough subjects to say anything beyond existence.
    per_family = Counter(i["family"] for i in items)
    for fam, n in per_family.items():
        check(n >= 10, f"{fam}: {n} items, enough to be more than an anecdote")

    subjects_per_family: dict[str, set[str]] = {}
    for i in items:
        subjects_per_family.setdefault(i["family"], set()).add(i["id"].split("/")[0])
    for fam, subs in subjects_per_family.items():
        check(len(subs) >= 10, f"{fam}: spans {len(subs)} subjects, not one repeated")

    # The index must resolve for every item, at the occurrence it declares.
    for i in items:
        try:
            idx = subject_last_index(tok, i["prompt"], i["subject"],
                                     occurrence=i.get("occurrence", 0))
            check(idx >= 0, f"{i['id']}: index resolves")
        except (SubjectNotInPrompt, IndexError) as e:
            failures.append(f"{i['id']}: index failed -> {type(e).__name__} {e}")
            checks += 1

    # Regime must match the mention actually read, not the prompt.
    for i in items:
        n = i["prompt"].count(i["subject"])
        occ = i.get("occurrence", 0)
        at_prefix = (occ in (0, -n)) and i["prompt"].startswith(i["subject"])
        if i["regime"] == "prefix-sharing":
            check(at_prefix, f"{i['id']}: reads a mention at the prefix")
        else:
            check(not at_prefix, f"{i['id']}: reads a mention with text before it")

    # Repetition pairs must actually differ, or the family tests nothing.
    pairs: dict[str, dict[str, dict]] = {}
    for i in items:
        if i["family"] == "repetition":
            sid, kind = i["id"].split("/")
            pairs.setdefault(sid, {})[kind] = i
    for sid, got in pairs.items():
        check(set(got) == {"repeat-first", "repeat-last"}, f"{sid}: both halves present")
        if set(got) == {"repeat-first", "repeat-last"}:
            a, b = got["repeat-first"], got["repeat-last"]
            check(a["prompt"] == b["prompt"], f"{sid}: the pair shares one prompt")
            check(subject_last_index(tok, a["prompt"], a["subject"], occurrence=a["occurrence"])
                  != subject_last_index(tok, b["prompt"], b["subject"], occurrence=b["occurrence"]),
                  f"{sid}: the two readings land on different tokens")

    # The floor item must name someone else, or it is not a floor.
    for i in items:
        if i["id"].endswith("/anchor-floor"):
            check(i["subject"] != i["id"].split("/")[0].replace("_", " "),
                  f"{i['id']}: uses a different subject")

    # A confusable must be a different person, not the subject spelled differently.
    for i in items:
        if i["family"] == "discrimination":
            check(i["subject"] != i["id"].split("/")[0].replace("_", " "),
                  f"{i['id']}: confusable is a different person")

    # An all-open set cannot fail. Bands must be a real fraction of it.
    banded = sum(1 for i in items if i["band"] is not None)
    check(banded >= len(items) // 5, f"{banded}/{len(items)} carry a falsifiable band")

    print(f"{checks - len(failures)}/{checks} checks passed")
    for f in failures[:20]:
        print(f"  FAIL  {f}")
    if len(failures) > 20:
        print(f"  ... and {len(failures) - 20} more")
    if not failures:
        print(f"\n{len(items)} items, {len(subjects_per_family.get('position', []))} subjects, "
              f"seed {meta['seed']}, relation {meta['relation']}.")
        print(f"{banded} with a band to violate. Zero remote calls made.")
        if cross:
            print(f"\nNote: {cross} prompts are shared by more than one subject — two "
                  f"people with the same given name produce the same alias probe, and a "
                  f"floor item can draw a name another subject also drew. That is one "
                  f"reading serving two items, so the effective n is {len(items) - cross}, "
                  f"not {len(items)}. Carry that into any rate.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "probes/generated.json")))
