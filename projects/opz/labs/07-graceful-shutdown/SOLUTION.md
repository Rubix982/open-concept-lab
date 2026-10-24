# Lab 07 · Solution (spoilers)

## Why it took 10 seconds

`CMD ["python", "app.py"]` makes Python **PID 1** in the container. The kernel
protects PID 1: any signal it hasn't installed a handler for is dropped, except
SIGKILL. Python doesn't handle SIGTERM by default, so `docker stop`'s SIGTERM
did nothing. Docker waited 10 seconds, then sent SIGKILL. Exit code 137 = 128 + 9 (SIGKILL).

Kubernetes is the same with a 30-second grace period. Every pod in every rollout
waits 30 seconds and then dies hard.

## The quick fix, and why it isn't enough

Run an init process as PID 1: `docker run --init`, or `tini` in the image as
`ENTRYPOINT ["tini", "--"]`. tini forwards SIGTERM to Python, and Python, no
longer PID 1, uses the default action: **die immediately**. The container now
stops in under a second, but the in-flight report is cut off and the exit code is
143 (128 + 15). Fast and rude. `check.sh` fails it on purpose.

(A shell-form `CMD python app.py` is worse: `/bin/sh` becomes PID 1 and doesn't
forward signals to its child at all.)

## The real fix

Handle SIGTERM in the app: stop accepting, drain what's in flight, exit 0.

```python
import signal
import threading
...
if __name__ == "__main__":
    print(f"report service on :{PORT} (pid {os.getpid()})", flush=True)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = False  # let in-flight requests finish on close

    def on_sigterm(signum: int, frame: object) -> None:
        print("SIGTERM: draining", flush=True)
        # shutdown() waits for serve_forever() to return, so it can't run on
        # the thread that is inside serve_forever(); hand it to another one.
        threading.Thread(target=server.shutdown).start()

    signal.signal(signal.SIGTERM, on_sigterm)
    server.serve_forever()
    server.server_close()  # joins the request threads still running
    print("drained, exiting", flush=True)
```

- `ThreadingHTTPServer` sets `daemon_threads = True`, meaning "don't wait for
  request threads at exit". Setting it to `False` makes `server_close()` join them.
- Calling `server.shutdown()` directly in the handler deadlocks. The handler runs
  on the main thread, which is inside `serve_forever()`, and `shutdown()` waits for
  that loop to finish. Hence the extra thread.

The stop now takes as long as the slowest in-flight request (about 2.5s here), and
the exit code is 0.

## Details worth knowing

- **Keep tini anyway** if the app starts child processes: PID 1 also has to reap
  zombie children, which Python won't do. tini plus a SIGTERM handler is the usual setup.
- **The grace period is a ceiling.** If a request can take 60s, a 30s grace period
  still cuts it. Set `terminationGracePeriodSeconds` above your slowest request,
  or put a deadline on requests.
- **Kubernetes has a race this lab doesn't show.** The pod gets SIGTERM at the same
  time it's removed from the Service's endpoints, and kube-proxy/ingress take a
  moment to notice, so new requests can still arrive *after* SIGTERM. The usual
  fix is a `preStop` hook that sleeps a few seconds before the signal, so traffic
  drains first.
- **What this doesn't cover:** long-lived connections (websockets, streams) and
  background jobs. Those need their own "finish or hand back the work" logic,
  for example re-queueing a job instead of dropping it.
