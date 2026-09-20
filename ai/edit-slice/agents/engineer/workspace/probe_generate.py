"""Can we generate remotely at all? T-066 needs free generation, not ranking."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from remote import _quiet_stdout, connect, retrying  # noqa: E402

m = connect("meta-llama/Llama-3.1-8B")
P = "Maurice de Vlaminck was born in the city of"

def try_generate():
    with _quiet_stdout(), m.generate(P, remote=True, max_new_tokens=6):
        out = m.generator.output.save()
    with _quiet_stdout():
        return m.tokenizer.decode(out[0][-6:])

def try_argmax():
    with _quiet_stdout(), m.trace(P, remote=True):
        t = m.lm_head.output[0, -1].argmax(-1).save()
    with _quiet_stdout():
        return repr(m.tokenizer.decode(t))

for name, fn in (("trace + argmax (1 token)", try_argmax),
                 ("generate (6 tokens)", try_generate)):
    try:
        print(f"[OK]   {name}: {retrying(fn, what=name)}")
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {str(e).splitlines()[-1][:90]}")
