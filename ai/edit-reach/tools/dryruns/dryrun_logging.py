"""Importing a run module must not create a log file. Zero remote calls.

124 of this project's 155 committed log files were a single line naming
themselves and nothing else -- 80% of the kept record was content-free. They
came from `setup()` announcing the run at import time, which every dry-run
triggers by importing every run module, and from `run_e001` being imported as a
library by five other scripts.

The fix is in `editreach.logs`: the header is held until a real record arrives,
and the file handler is opened with `delay=True`. Both halves are needed.

This checks the property rather than the implementation, because the property
is what was violated and an implementation can be rewritten.
"""

from __future__ import annotations

import logging
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    from editreach.logs import setup, log_path, LOG_ENV_VAR

    with tempfile.TemporaryDirectory() as tmp:
        import os
        os.environ[LOG_ENV_VAR] = tmp
        here = pathlib.Path(tmp)

        log = setup("DRYRUN-A")
        path = log_path()
        assert path is not None, "log_path must name the file even before it exists"
        assert not pathlib.Path(path).exists(), \
            "setup() created a file before anything was logged"
        assert not list(here.glob("*.log")), f"setup() created {list(here.glob('*.log'))}"

        log.info("a real record")
        assert pathlib.Path(path).exists(), "a logged record did not reach the file"
        text = pathlib.Path(path).read_text()
        assert "run DRYRUN-A" in text, (
            "the held header was dropped instead of deferred -- a log that does "
            "not say what ran is the fault this module exists to prevent")
        assert "a real record" in text, "the record itself is missing"
        assert text.index("run DRYRUN-A") < text.index("a real record"), \
            "the header must precede the record it was held for"

        # config must survive deferral too.
        for h in logging.getLogger().handlers:
            h.close()
        log = setup("DRYRUN-B", config={"model": "x", "layer": 5})
        p2 = pathlib.Path(log_path())
        assert not p2.exists()
        log.warning("something")
        body = p2.read_text()
        assert '"layer": 5' in body, "config was dropped rather than deferred"

        os.environ.pop(LOG_ENV_VAR, None)

    # The whole-set property, and the wording matters. The first version of
    # this check redirected the log directory to a temp dir and asserted the
    # temp dir was empty -- which conflates "writes no log at all" with "does
    # not write into the repository". Those are different, and only the second
    # is the rule: `dryrun_e004` legitimately exercises code that logs, and
    # sends its output to a temp directory of its own precisely so the record
    # stays clean.
    #
    # So: run the others with EDITREACH_LOGS UNSET, as a person would, and
    # assert the project's own log directory is unchanged.
    import os
    env = {k: v for k, v in os.environ.items() if k != "EDITREACH_LOGS"}
    logs_dir = ROOT / "logs"
    before = {p.name for p in logs_dir.glob("*.log")} if logs_dir.exists() else set()
    others = sorted(p for p in (ROOT / "tools" / "dryruns").glob("dryrun_*.py")
                    if p.name != "dryrun_logging.py")
    for p in others:
        r = subprocess.run([sys.executable, str(p)], cwd=ROOT, env=env,
                           capture_output=True, text=True)
        assert r.returncode == 0, f"{p.name} failed:\n{r.stdout}\n{r.stderr}"
    after = {p.name for p in logs_dir.glob("*.log")} if logs_dir.exists() else set()
    made = sorted(after - before)
    for name in made:                      # leave the record as we found it
        (logs_dir / name).unlink()
    assert not made, (f"{len(others)} dry-runs wrote {len(made)} file(s) into "
                      f"{logs_dir}: {made}. A dry-run is not a run; send its "
                      f"output elsewhere with EDITREACH_LOGS.")

    # A sibling project's log directory is OUTSIDE this package's ROOT, and
    # `relative_to` raises rather than falling back. edit-slice's 79 scripts
    # all call setup() at import, so every one of them would have raised on
    # its first line. Nobody noticed because no edit-slice script has run
    # since the infrastructure moved here. Asserted as a property so the
    # fallback cannot be optimised away by someone who sees only edit-reach.
    from editreach.logs import ROOT as PKG_ROOT
    sibling = PKG_ROOT.parent / "edit-slice" / "logs"
    if sibling.exists():
        env2 = {k: v for k, v in os.environ.items()}
        env2["EDITREACH_LOGS"] = str(sibling)
        r = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, 'src');"
             "from editreach.logs import setup, log_path;"
             "setup('SIBLING'); print('ok', log_path())"],
            cwd=ROOT, env=env2, capture_output=True, text=True)
        assert r.returncode == 0, (
            "setup() failed for a sibling project's log directory:\n"
            + r.stderr.strip().splitlines()[-1] if r.stderr else r.stdout)
        assert not list(sibling.glob("SIBLING-*.log")), \
            "the sibling check left a file behind"

    print(f"dryrun_logging ok -- setup() writes nothing until a record arrives; "
          f"{len(others)} dry-runs left 0 log files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
