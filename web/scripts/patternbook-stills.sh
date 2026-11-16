#!/usr/bin/env bash
# Screenshots of the pages agents built in patternbook's tests, for /graphics/patternbook.
#
# Each page in projects/patternbook/runs/c*/ is loaded at a 1280-wide desktop window and the
# top 1280×1440 is saved as static/img/graphics/patternbook/<card>-<page>.webp. The judge saw
# the pages on a desktop screen, so a desktop still is closer to what was judged than a live
# preview squeezed to card width.
#
# Local only, and run by hand after adding a run: it needs a Chromium (the one Playwright
# caches is found automatically, or set CHROME=/path/to/chrome) and cwebp
# (`brew install webp`). The stills are committed, so the site build doesn't need either.
#
#   scripts/patternbook-stills.sh            # every page
#   scripts/patternbook-stills.sh c011       # one card's pages

set -euo pipefail

site="$(cd "$(dirname "$0")/.." && pwd)"
runs="$site/../projects/patternbook/runs"
out="$site/static/img/graphics/patternbook"
mkdir -p "$out"

chrome="${CHROME:-}"
if [[ -z "$chrome" ]]; then
  chrome="$(ls -d "$HOME"/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-mac-arm64/chrome-headless-shell 2>/dev/null | sort -V | tail -1 || true)"
fi
[[ -x "$chrome" ]] || { echo "no Chromium found; set CHROME=/path/to/chrome" >&2; exit 1; }
command -v cwebp >/dev/null || { echo "cwebp not found: brew install webp" >&2; exit 1; }

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

shopt -s nullglob
for dir in "$runs"/${1:-c*}/; do
  card="$(basename "$dir")"
  for page in "$dir"*.html; do
    name="$(basename "$page" .html)"
    [[ "$card/$name" == "c010/sheet" ]] && continue # the judge's contact sheet, not a built page
    "$chrome" --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
      --window-size=1280,1440 --virtual-time-budget=4000 \
      --screenshot="$tmp/shot.png" "file://$page" >/dev/null 2>&1
    cwebp -quiet -q 78 -resize 960 0 "$tmp/shot.png" -o "$out/$card-$name.webp"
    echo "  $card/$name.html -> img/graphics/patternbook/$card-$name.webp"
  done
done
