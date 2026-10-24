# Lab 11 · Solution (spoilers)

## What was wrong

Three separate problems:

1. **`COPY . .` came before the installs.** Docker caches each instruction as a
   layer, and a changed layer invalidates every layer after it. Since `app.py` is
   in `.`, any code edit invalidated the copy layer, and so the `apt-get` and
   `pip install` layers after it ran from scratch every time.
2. **`build-essential` shipped to production.** gcc, g++, make and their headers
   add roughly 500 MB, and every one of them is something an attacker who gets a
   shell can use. Nothing at run time compiles anything.
3. **Nothing needed compiling anyway.** numpy and pandas publish pre-built wheels
   for Linux on arm64 and amd64, and `pip install` printed `.whl` for both.

## The fix

```dockerfile
# Stage 1: install dependencies into a virtualenv.
FROM python:3.12-slim AS build
RUN python -m venv /venv
COPY requirements.txt .
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: only the runtime, the virtualenv, and the code.
FROM python:3.12-slim
COPY --from=build /venv /venv
ENV PATH=/venv/bin:$PATH
WORKDIR /app
COPY app.py .
EXPOSE 8011
CMD ["python", "app.py"]
```

- `requirements.txt` is copied and installed **before** the code, so a code
  change reuses the cached install layer. Only an actual dependency change
  reinstalls.
- The final stage starts clean from `-slim` and copies only `/venv`. Anything
  else the build stage needed (compilers, headers, pip's cache) stays behind.

Before → after, measured on an M2: see the numbers `check.sh` prints, and put
them in your retro.

## Details worth knowing

- **Reordering alone isn't enough.** Moving `COPY requirements.txt` up fixes the
  rebuild time, but the image is still nearly 1 GB and full of compilers. `check.sh`
  fails it for that.
- **When you do need a compiler** (a package with no wheel for your platform,
  like some on Alpine/musl), install `build-essential` in the *build* stage,
  build wheels there, and copy the wheels or the venv out. The tools never reach
  production.
- **`.dockerignore`** keeps `.git`, `.venv`, data files and secrets out of the
  build context. Fewer files sent to the builder, and fewer reasons for
  `COPY` to miss the cache. It also stops a `.env` being baked in (lab 01).
- **Pick the base on purpose.** `python:3.12` (no suffix) is built on Debian's
  `buildpack-deps` and already contains gcc and hundreds of `-dev` packages, about
  1 GB before your code. `-slim` is the usual runtime base; `-alpine` is smaller
  still but uses musl, so many wheels don't apply and pip falls back to compiling.
- **`--no-cache-dir`** stops pip storing its download cache inside the layer.
- **Pin the base image too** (`python:3.12-slim@sha256:…`) if you want builds
  that are reproducible and not just fast. Otherwise a new base image upstream
  invalidates every layer.
- **What this doesn't cover:** CI runners usually start with an empty Docker
  cache, so the layer order only helps there once you give the runner a cache
  (`--cache-from` with a registry, or BuildKit's GitHub Actions cache).
