"""Send requests to the orders API (through NGINX).

    python3 tools/attack.py normal         # an ordinary 3-item order
    python3 tools/attack.py big [MB]       # a valid order padded to MB megabytes (default 150)
    python3 tools/attack.py nested [DEPTH] # 200 KB of nested lists, DEPTH deep (default 100000)

The memory limit on the app container (256 MB) keeps this from hurting your Mac.
"""

import json
import os
import subprocess
import sys
import tempfile

HOST = "127.0.0.1"
PORT = int(os.environ.get("LAB16_PORT", "8016"))


def post(body: bytes) -> tuple[int, str]:
    # curl, because it sends "Expect: 100-continue" for big bodies and so hears an
    # early 413 instead of failing halfway through the upload.
    with tempfile.NamedTemporaryFile(suffix=".json") as f:
        f.write(body)
        f.flush()
        out = subprocess.run(
            ["curl", "-s", "-m", "60", "-w", "\n%{http_code}", "-H", "Content-Type: application/json",
             "--data-binary", f"@{f.name}", f"http://{HOST}:{PORT}/api/orders"],
            capture_output=True, text=True,
        ).stdout
    text, _, code = out.rpartition("\n")
    return int(code or 0), " ".join(text.split())


def main() -> None:
    kind = sys.argv[1] if len(sys.argv) > 1 else "normal"
    if kind == "normal":
        body = json.dumps({"customer": "c_17", "items": [{"sku": "A1"}, {"sku": "B2"}, {"sku": "C3"}]}).encode()
    elif kind == "big":
        mb = int(sys.argv[2]) if len(sys.argv) > 2 else 150
        # a million short strings: small on the wire, many Python objects once parsed
        chunk = '"' + "x" * 8 + '",'
        n = mb * 1024 * 1024 // len(chunk)
        body = ('{"customer":"c_17","note":[' + chunk * n + '"end"],"items":[]}').encode()
    elif kind == "nested":
        depth = int(sys.argv[2]) if len(sys.argv) > 2 else 100_000
        body = ('{"customer":"c_17","items":' + "[" * depth + "]" * depth + "}").encode()
    else:
        sys.exit(__doc__)
    status, text = post(body)
    print(f"{kind:6} ({len(body) / 1024 / 1024:.1f} MB) -> HTTP {status} {text[:120]}")


if __name__ == "__main__":
    main()
