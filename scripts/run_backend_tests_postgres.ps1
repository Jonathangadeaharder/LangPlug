#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Wrapper to run backend tests against Postgres from repo root (Windows PowerShell)
$ScriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location (Join-Path $RepoRoot "Backend")
./scripts/run_tests_postgres.ps1
