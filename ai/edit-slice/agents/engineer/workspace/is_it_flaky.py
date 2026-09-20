"""Is the whitelist error deterministic or intermittent? Same call, six times."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from remote import _quiet_stdout, connect  # noqa: E402

m = connect("meta-llama/Llama-3.1-8B")
P = "Maurice de Vlaminck was born in the city of"
ok = 0
for i in range(6):
    try:
        with _quiet_stdout(), m.trace(P, remote=True):
            a = m.model.layers[5].mlp.down_proj.input.half().save()
        ok += 1
        print(f"  attempt {i+1}: OK   {tuple(a.shape)}")
    except Exception as e:
        print(f"  attempt {i+1}: FAIL {str(e).splitlines()[-1][:60]}")
print(f"\n{ok}/6 succeeded — deterministic failure would be 0/6, flaky is anything between")
