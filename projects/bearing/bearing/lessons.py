"""Rules earned by being wrong. Each carries the incident that produced it.

The most portable thing a project owns is not its results — it is the scar tissue. A new
project that inherits this list does not have to re-earn it, and a person returning after
a week away does not have to remember it.

Derived from two projects: `edit-slice` (research) and `janaan` (production pipeline).
Where a rule is mechanically checkable, `check` names the function that does it; where it
is a discipline, `check` is None and it is here to be read.

Read them:
    python -m bearing --lessons
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lesson:
    rule: str
    incident: str
    cost: str
    check: str | None = None


LESSONS: list[Lesson] = [
    Lesson(
        rule="Check the premise before pricing the work. A claim quantified over a class "
             "with no instance inspected is the cheapest thing to verify and the most "
             "expensive thing to be wrong about.",
        incident="§7 asserted 'every propagation benchmark probes with prompts that begin "
                 "with the subject' having inspected none, and a week was priced on top. "
                 "Downloading the canonical benchmark and counting took twenty minutes: "
                 "44 of 46,754 prompts are subject-initial. 0.09%.",
        cost="a week of planned work, which turned out not to exist",
        check="unchecked_universal"),
    Lesson(
        rule="A gate that warns is a gate nobody reads. Refuse, or delete it.",
        incident="preflight's first cache rule demanded every CLI flag appear in every "
                 "cache key and flagged --gate-n against a delta cache it cannot affect.",
        cost="noise that would have trained us to skip the output"),
    Lesson(
        rule="A check written in one project's dialect will libel every project that "
             "speaks another.",
        incident="bearing's `still_checking` knew only edit-slice's vocabulary and read "
                 "janaan's critique ledger — a document that is ENTIRELY corrections — as "
                 "evidence nobody was checking.",
        cost="a false accusation on the second project it ever ran on"),
    Lesson(
        rule="A cache trusted because the file exists is how a partial run reports itself "
             "as a whole one. Test completeness, never existence.",
        incident="a relaunch loaded 9 of 29 deltas, logged 'cached', skipped optimisation "
                 "and walked into scoring short. Nothing raised.",
        cost="a run that would have produced plausible wrong numbers"),
    Lesson(
        rule="Everything that changes a number belongs in the cache key.",
        incident="a scores cache keyed on (model, relation, steps) omitted `layer`, so a "
                 "layer-13 run would have loaded layer-5 scores and reported them as new.",
        cost="caught before it ran; it would have been undetectable afterwards"),
    Lesson(
        rule="A measurement that changes between runs is not a measurement.",
        incident="max() over a SET broke ties nondeterministically; two runs of the same "
                 "counting script differed by 15 prompts.",
        cost="fifteen prompts, and the credibility of every number beside them"),
    Lesson(
        rule="Prose written before a result describes the result you expected.",
        incident="a runner closed with 'a fall in reach alongside a rise in strength' — "
                 "written anticipating one outcome, fired on the other, and described the "
                 "data backwards while printing it correctly.",
        cost="a wrong sentence in a correct log"),
    Lesson(
        rule="A ceiling is the only thing that catches a job which hangs without failing.",
        incident="two jobs sat in NDIF's RECEIVED state, never queued and never erroring, "
                 "for 135 and 144 hours. No exception, so the retry logic never fired.",
        cost="six days, against under a minute of CPU"),
    Lesson(
        rule="An abstract under-reports overlap and over-reports applicability. It sells "
             "the contribution and buries the setting.",
        incident="two papers were cited from their abstracts. Reading them moved both "
                 "claims — one overlapped more of our work than credited, the other had "
                 "our subject matter explicitly outside its stated scope.",
        cost="two claims in the packet, corrected eight hours after being written"),
    Lesson(
        rule="Dry-run the reporting path against a PUBLISHED result before trusting a new "
             "one. The dangerous bug is the one that agrees with you.",
        incident="a report helper that returned only held items stood in for 'all scored "
                 "items'. It would not have crashed; it would have printed 100% in every "
                 "cell and read as spectacular confirmation.",
        cost="caught by one query; it was one query from being published"),
    Lesson(
        rule="Name the confound and you have still not controlled it.",
        incident="a ticket named its baseline confound in writing while the code it "
                 "commissioned still computed on drops. The headline was wrong and "
                 "retracted.",
        cost="a published conclusion, withdrawn"),
    Lesson(
        rule="Before attributing a failure to your change, re-run the thing that worked.",
        incident="four consecutive failures were blamed on four code changes. The cause "
                 "was a backend rejecting half of all traces, node-dependently — measured "
                 "at 3 successes in 6 attempts of one unchanged call.",
        cost="four retracted constraints and the time spent deriving them"),
]


def by_check(name: str) -> list[Lesson]:
    return [x for x in LESSONS if x.check == name]


def render() -> str:
    out = [f"{len(LESSONS)} rules, each earned by being wrong.", "=" * 72, ""]
    for n, x in enumerate(LESSONS, 1):
        out.append(f"{n:>2}. {x.rule}")
        out.append(f"    how: {x.incident}")
        out.append(f"    cost: {x.cost}")
        if x.check:
            out.append(f"    checked by: {x.check}")
        out.append("")
    return "\n".join(out)
