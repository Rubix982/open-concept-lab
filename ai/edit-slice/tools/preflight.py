"""Gates that must pass before a run is allowed to touch the network, cheapest first.

    python3 tools/preflight.py agents/engineer/workspace/run_e033.py -- --relation birthplace
    python3 tools/preflight.py --all          # every runner, static gates only

Ported from ~/code/janaan/tools/pipeline/batch.py, whose ordering is the whole idea:

    the pipeline's own logic first (seconds): a broken change was otherwise found an
    hour into a batch

This project has lost time to exactly that, three times, and twice AFTER a run had already
produced numbers:

  * a partial delta cache read as complete, scoring 29 subjects against 9 deltas   [E-033]
  * `layer` missing from a scores cache key, so L13 would have loaded L5's numbers  [E-033]
  * a flaky node read as an oversized batch, parking for minutes a chunk at a time  [E-033]

None of those raise. They produce plausible numbers, which is the dangerous shape. Each
gate below exists because one of them got through.

Gates refuse; they do not warn. A gate that warns is a gate nobody reads at 3am.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(ROOT, ".venv/bin/python")


class Gate:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.passed: list[str] = []

    def check(self, name: str, ok: bool, detail: str = "") -> bool:
        (self.passed if ok else self.failures).append(f"{name}: {detail}" if detail else name)
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")
        return ok


def gate_lint(g: Gate, paths: list[str]) -> None:
    r = subprocess.run(["ruff", "check", "--line-length", "100", *paths],
                       capture_output=True, text=True)
    g.check("lint", r.returncode == 0, (r.stdout or r.stderr).strip().splitlines()[-1][:90]
            if r.returncode else "")


def gate_imports(g: Gate, path: str) -> None:
    """Import the runner without running it. Catches a missing name before NDIF does."""
    env = dict(os.environ, PYTHONPATH=f"{ROOT}/src:{ROOT}/agents/engineer/workspace")
    mod = os.path.splitext(os.path.basename(path))[0]
    r = subprocess.run([PY, "-c", f"import {mod}"], capture_output=True, text=True,
                       cwd=os.path.dirname(path), env=env)
    g.check("imports", r.returncode == 0,
            (r.stderr.strip().splitlines() or [""])[-1][:90] if r.returncode else "")


def gate_cache_keys(g: Gate, path: str, fatal: bool = True) -> None:
    """Cache keys in one file must agree about which parameters they carry.

    The first version of this gate demanded every CLI flag appear in every key, which
    flagged `--gate-n` against a delta cache it cannot affect: noise, and a gate nobody
    reads is a gate that does not work. The rule that actually catches [E-033] is
    **internal consistency**. That bug was precisely a disagreement inside one file —

        E033_deltas_{tag}_L{LAYER}_s{steps}.pt     carried the layer
        E033_scores_{tag}_s{steps}.json            did not

    so a layer-13 run loaded layer-5 scores and reported them as new. A parameter that
    one key in a file thinks matters, and another omits, is the shape to refuse.

    `fingerprint` counts as carrying everything — `possession.FilterConfig.fingerprint`
    is this project's canonical "everything that changes a number".
    """
    src = open(path, encoding="utf-8").read()
    keys = [k for k in re.findall(r'f"([^"\n]*?(?:cache|E0\d\d)[^"\n]*?)"', src)
            + re.findall(r"f'([^'\n]*?(?:cache|E0\d\d)[^'\n]*?)'", src)
            if "{" in k and (".pt" in k or ".json" in k)]
    if not keys:
        return g.check("cache keys agree on parameters", True, "no cache keys") and None
    fields: list[set[str]] = []
    for k in keys:
        f = set(re.findall(r"\{([a-zA-Z_][\w]*)", k))
        if "fingerprint" in k:
            f.add("*fingerprint*")
        fields.append({x.lower().lstrip("_") for x in f})
    if any("*fingerprint*" in f for f in fields):
        return g.check("cache keys agree on parameters", True,
                       f"{len(keys)} key(s), fingerprint-keyed") and None
    union = set().union(*fields)
    # a parameter some key carries and another drops — the [E-033] shape
    disagree = {p for p in union if sum(p in f for f in fields) not in (0, len(fields))}
    ok = not disagree
    detail = (f"{sorted(disagree)} in some keys, absent from others"
              if disagree else f"{len(keys)} key(s) agree on {sorted(union)}")
    if ok or fatal:
        g.check("cache keys agree on parameters", ok, detail)
    else:
        print(f"  note  cache keys disagree — {detail}")


def gate_cache_completeness(g: Gate, path: str, fatal: bool = True) -> None:
    """A cache load must test completeness, not existence.

    [E-033]'s first relaunch loaded 9 of 29 deltas, logged "cached", skipped optimisation
    and walked into scoring short. The fix is a subset test; this gate asserts one is
    present wherever a .pt cache is loaded.
    """
    src = open(path, encoding="utf-8").read()
    loads_pt = bool(re.search(r"torch\.load\(", src))
    if not loads_pt:
        return g.check("cache completeness tested", True, "no .pt cache loaded") and None
    # Any form that compares what is wanted against what is loaded counts. The first
    # version recognised only `<= set(...)` and refused a correct `want - set(...)` test,
    # which is how a gate teaches people to route around it.
    tests = bool(re.search(r"<=\s*set\(|issubset|len\(cached\)\s*>=|set\(cached\)|"
                           r"want\s*-\s*set\(|missing\s*=|-\s*set\(\w+\)", src))
    detail = ("" if tests else "torch.load present with no subset/length test — "
                                "a partial cache will read as complete")
    if tests or fatal:
        g.check("cache completeness tested", tests, detail)
    else:
        print(f"  note  cache completeness untested — {detail}")


def gate_report_dryrun(g: Gate, path: str) -> None:
    """RUN the run's own reporting path against known-answer data.

    Not "does a dry-run exist" — janaan's batch.py runs `test_pipeline.py` first precisely
    because a check that is only present is a check nobody has executed. The baseline case
    feeds a PUBLISHED result back through `report` and requires the published verdict: the
    dangerous bug is the one that agrees with you, and a reporting path verified only on
    data you invented can still agree with you.
    """
    name = os.path.splitext(os.path.basename(path))[0]
    dry = os.path.join(ROOT, "tools/dryruns", f"dryrun_{name.replace('run_', '')}.py")
    has_report = bool(re.search(r"^def report\(", open(path, encoding="utf-8").read(), re.M))
    if not has_report:
        return g.check("report path dry-run", True, "no report() to dry-run") and None
    if not os.path.exists(dry):
        return g.check("report path dry-run", False,
                       f"no tools/dryruns/{os.path.basename(dry)} — verdict bands never "
                       f"exercised") and None
    r = subprocess.run([PY, dry], capture_output=True, text=True, timeout=300)
    g.check("report path dry-run", r.returncode == 0,
            os.path.basename(dry) if r.returncode == 0
            else (r.stderr.strip().splitlines() or [""])[-1][:88])


def gate_remote_smoke(g: Gate, model: str) -> None:
    """One real round trip. Distinguishes "NDIF is down" from "my code is wrong" in 10s."""
    t0 = time.time()
    r = subprocess.run([PY, os.path.join(ROOT, "agents/engineer/workspace/ndif_health.py"),
                        model], capture_output=True, text=True, timeout=300)
    ok = r.returncode == 0 and "answer:" in r.stdout
    g.check(f"remote smoke ({model.split('/')[-1]})", ok,
            f"{time.time() - t0:.0f}s" if ok else (r.stderr.strip().splitlines() or [""])[-1][:80])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runner", nargs="?")
    ap.add_argument("--all", action="store_true", help="static gates over every runner")
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B")
    ap.add_argument("--no-remote", action="store_true")
    a = ap.parse_args()

    g = Gate()
    if a.all:
        runners = sorted(glob.glob(os.path.join(ROOT, "agents/engineer/workspace/run_e*.py")))
        print(f"static gates over {len(runners)} runners\n")
        gate_lint(g, runners + [os.path.join(ROOT, "tools/triage.py")])
        # Historical runners are REPORTED, not refused. Their runs are closed and their
        # numbers are recorded; refusing them would make the tool unusable on day one,
        # which is how a gate gets switched off. Only the runner being preflighted is
        # held to the bar.
        for rp in runners:
            print(f"\n{os.path.basename(rp)}")
            gate_cache_keys(g, rp, fatal=False)
            gate_cache_completeness(g, rp, fatal=False)
    else:
        if not a.runner:
            ap.error("give a runner, or --all")
        print(f"preflight: {os.path.basename(a.runner)}\n")
        gate_lint(g, [a.runner])
        gate_imports(g, a.runner)
        gate_cache_keys(g, a.runner)
        gate_cache_completeness(g, a.runner)
        gate_report_dryrun(g, a.runner)
        if not a.no_remote:
            gate_remote_smoke(g, a.model)

    print()
    if g.failures:
        print(f"REFUSED — {len(g.failures)} gate(s) failed, {len(g.passed)} passed")
        for f in g.failures:
            print(f"    {f}")
        print("\nNothing has touched the network. Fix these first.")
        return 1
    print(f"all {len(g.passed)} gates pass — safe to run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
