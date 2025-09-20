#!/usr/bin/env bash
# DEPRECATED: Use `python scripts/run_postgres_tests.py` instead
# This script will be removed in a future release
set -euo pipefail

# Run backend tests against a local Postgres instance.
# Requires: docker and docker compose (v2), Python test deps installed.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/.."

cd "$BACKEND_DIR"

echo "[Postgres] Starting dockerized Postgres (if not already running)..."
docker compose -f docker-compose.postgresql.yml up -d db

export USE_TEST_POSTGRES=1
export TEST_POSTGRES_URL=${TEST_POSTGRES_URL:-"postgresql+asyncpg://langplug_user:langplug_password@localhost:5432/langplug"}

echo "[Postgres] Using TEST_POSTGRES_URL=$TEST_POSTGRES_URL"
echo "[Pytest] Running full suite with 60s per-test timeout..."
pytest -v

echo "[Done] Tests completed. To stop Postgres:"
echo "  docker compose -f docker-compose.postgresql.yml stop db"

