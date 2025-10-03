#!/usr/bin/env pwsh
# DEPRECATED: Use `python scripts/run_postgres_tests.py` instead
# This script will be removed in a future release
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Run backend tests against a local Postgres instance on Windows.
# Requires: Docker Desktop with Compose, Python test deps installed.

$ScriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$BackendDir = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $BackendDir

Write-Host "[Postgres] Starting dockerized Postgres (if not already running)..."
docker compose -f docker-compose.postgresql.yml up -d db | Out-Null

$env:USE_TEST_POSTGRES = "1"
if (-not $env:TEST_POSTGRES_URL) {
  $env:TEST_POSTGRES_URL = "postgresql+asyncpg://langplug_user:langplug_password@localhost:5432/langplug"
}

Write-Host "[Postgres] Using TEST_POSTGRES_URL=$($env:TEST_POSTGRES_URL)"
Write-Host "[Pytest] Running full suite with 60s per-test timeout..."
python -m pytest -v

Write-Host "[Done] Tests completed. To stop Postgres:"
Write-Host "  docker compose -f docker-compose.postgresql.yml stop db"
