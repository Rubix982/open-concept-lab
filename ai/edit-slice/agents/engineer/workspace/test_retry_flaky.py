"""Does retrying() now absorb the intermittent whitelist rejection?"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402

log = setup("test_retry_flaky", config={"check": "whitelist error is retryable"})
m = connect("meta-llama/Llama-3.1-8B")
P = "Maurice de Vlaminck was born in the city of"


def once():
    with _quiet_stdout(), m.trace(P, remote=True):
        a = m.model.layers[5].mlp.down_proj.input.half().save()
    with _quiet_stdout():
        return tuple(a.shape)


ok = 0
for i in range(6):
    try:
        shape = retrying(once, what="probe key")
        ok += 1
        log.info("call %d: OK %s", i + 1, shape)
    except Exception as exc:  # noqa: BLE001
        log.error("call %d: FAILED past all retries — %s", i + 1, str(exc)[:70])
log.info("%d/6 calls succeeded with retrying() (bare calls were 3/6)", ok)
