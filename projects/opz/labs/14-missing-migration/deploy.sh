#!/usr/bin/env bash
# The deploy pipeline. Usage: ./deploy.sh v2   (or ./deploy.sh v1 to roll back)
# Builds the requested version's image and swaps the running app to it.
set -euo pipefail
cd "$(dirname "$0")"
VERSION="${1:?usage: ./deploy.sh v1|v2}"

docker build -q -t "opz-lab14-app:$VERSION" "app/$VERSION" >/dev/null

# Migrations are run by hand after the deploy: docker compose run --rm migrate
APP_VERSION="$VERSION" docker compose up -d app

echo "deployed $VERSION"
