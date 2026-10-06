"""Query embedder for the minimal deployment: the same model as embedder/ (all-MiniLM-L6-v2,
384 dimensions, L2-normalised), run with ONNX Runtime through fastembed instead of PyTorch, so it
needs ~200 MB instead of ~1.5 GB. Production only embeds visitors' searches (one short text each);
the million-plus stored vectors are computed on a development machine and shipped in a golden
dataset. Same API as embedder/ for what the server uses:
    POST /embed/batch  {"texts": [...]}  ->  {"embeddings": [[...], ...]}
    GET  /health                         ->  {"status": "healthy", "model": ...}
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from fastembed import TextEmbedding

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CACHE = os.environ.get("FASTEMBED_CACHE", "/models")
model = TextEmbedding(MODEL, cache_dir=CACHE, threads=int(os.environ.get("THREADS", "2")))
MAX_TEXTS = 256


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/health":
            return self._send(200, {"status": "healthy", "model": MODEL})
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path not in ("/embed/batch", "/embed"):
            return self._send(404, {"error": "not found"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
        except ValueError:
            return self._send(400, {"error": "invalid JSON"})
        texts = body.get("texts") if self.path == "/embed/batch" else [body.get("text", "")]
        if not isinstance(texts, list) or not texts or len(texts) > MAX_TEXTS:
            return self._send(400, {"error": f"texts: 1 to {MAX_TEXTS} strings"})
        vectors = [v.tolist() for v in model.embed([str(t) for t in texts])]
        if self.path == "/embed":
            return self._send(200, {"embedding": vectors[0]})
        self._send(200, {"embeddings": vectors})

    def log_message(self, fmt: str, *args) -> None:
        pass


if __name__ == "__main__":
    print(f"embedder-lite on :8000 ({MODEL}, ONNX)", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
