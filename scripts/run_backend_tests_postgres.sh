#!/usr/bin/env bash
set -euo pipefail

# Wrapper to run backend tests against Postgres from repo root.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT/Backend"
./scripts/run_tests_postgres.sh

