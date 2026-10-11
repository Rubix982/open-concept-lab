# Lab 01 · Solution (spoilers)

## Why it leaked

- **`ENV` is image metadata.** Anything set with `ENV` is stored in the image
  config and printed by `docker inspect` to anyone who can pull the image.
- **Layers are append-only.** `COPY . .` wrote `.env` into one layer. `RUN rm -f .env`
  adds a *new* layer that hides the file, but the earlier layer still holds it, and
  `docker save` hands over every layer.
- **No `.dockerignore`**, so `COPY . .` sent `.env` into the build context in the first place.

## Fix

`app/.dockerignore`:
```
.env
.git
```

`app/Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY app.py .
EXPOSE 8080
CMD ["python", "app.py"]
```

Give the token at run time instead: `docker run -e API_TOKEN=... lab01` or
`docker run --env-file app/.env lab01`.

## Prevention

- Copy named files instead of `COPY . .`, and always keep a `.dockerignore`.
- If a build step needs a secret (e.g. a private package index), use BuildKit's
  `RUN --mount=type=secret,id=...`. The secret is available during that step and
  never written to a layer.
- Scan images in CI: `trivy image --scanners secret <img>`, and scan the repo with gitleaks.
- **Rotate a leaked secret.** Removing it from the image doesn't help, because
  copies already pulled keep it.
