#!/usr/bin/env bash
cd "$(dirname "$0")" && docker compose down -v --rmi local
