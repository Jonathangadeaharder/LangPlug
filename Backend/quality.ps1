# PowerShell script for code quality checks
# Usage: .\quality.ps1 [command]

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Activate virtual environment
. .\api_venv\Scripts\Activate.ps1

function Show-Help {
    Write-Host "LangPlug Backend - Code Quality Tools" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\quality.ps1 [command]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Available Commands:" -ForegroundColor Green
    Write-Host ""
    Write-Host "Code Quality:"
    Write-Host "  all              - Run all quality checks (lint + format + type + security)"
    Write-Host "  lint             - Run Ruff linter"
    Write-Host "  lint-fix         - Run Ruff linter with auto-fix"
    Write-Host "  format           - Format code with Ruff"
    Write-Host "  format-check     - Check formatting without changes"
    Write-Host "  type             - Run MyPy type checker"
    Write-Host "  security         - Run Bandit security scanner"
    Write-Host "  secrets          - Check for committed secrets"
    Write-Host ""
    Write-Host "Code Metrics:"
    Write-Host "  metrics          - Generate comprehensive metrics report"
    Write-Host "  metrics-cc       - Cyclomatic complexity analysis"
    Write-Host "  metrics-mi       - Maintainability index"
    Write-Host "  metrics-cog      - Cognitive complexity (Lizard)"
    Write-Host ""
    Write-Host "Pre-commit:"
    Write-Host "  pre-commit       - Run all pre-commit hooks"
    Write-Host "  pre-commit-install - Install pre-commit hooks"
    Write-Host ""
    Write-Host "Testing:"
    Write-Host "  test             - Run all tests"
    Write-Host "  test-unit        - Run unit tests only"
    Write-Host "  test-cov         - Run tests with coverage"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\quality.ps1 all          # Run all checks"
    Write-Host "  .\quality.ps1 lint-fix     # Fix linting issues"
    Write-Host "  .\quality.ps1 test         # Run tests"
    Write-Host ""
}

function Run-All {
    Write-Host "Running all quality checks..." -ForegroundColor Cyan
    Run-LintFix
    Run-Format
    Run-Type
    Run-Security
    Write-Host "✅ All quality checks completed!" -ForegroundColor Green
}

function Run-Lint {
    Write-Host "Running Ruff linter..." -ForegroundColor Cyan
    ruff check .
}

function Run-LintFix {
    Write-Host "Running Ruff linter with auto-fix..." -ForegroundColor Cyan
    ruff check . --fix
}

function Run-Format {
    Write-Host "Formatting code with Ruff..." -ForegroundColor Cyan
    ruff format .
}

function Run-FormatCheck {
    Write-Host "Checking code formatting..." -ForegroundColor Cyan
    ruff format --check .
}

function Run-Type {
    Write-Host "Running MyPy type checker..." -ForegroundColor Cyan
    mypy .
}

function Run-Security {
    Write-Host "Running Bandit security scanner..." -ForegroundColor Cyan
    bandit -r . -c pyproject.toml
}

function Run-Secrets {
    Write-Host "Checking for secrets..." -ForegroundColor Cyan
    detect-secrets scan
}

function Run-PreCommit {
    Write-Host "Running pre-commit hooks..." -ForegroundColor Cyan
    pre-commit run --all-files
}

function Install-PreCommit {
    Write-Host "Installing pre-commit hooks..." -ForegroundColor Cyan
    pre-commit install
}

function Run-Test {
    Write-Host "Running all tests..." -ForegroundColor Cyan
    pytest
}

function Run-TestUnit {
    Write-Host "Running unit tests..." -ForegroundColor Cyan
    pytest tests/unit/
}

function Run-TestCov {
    Write-Host "Running tests with coverage..." -ForegroundColor Cyan
    pytest --cov=. --cov-report=html --cov-report=term
}

function Run-Metrics {
    Write-Host "Generating comprehensive metrics report..." -ForegroundColor Cyan
    python metrics_report.py
}

function Run-MetricsCC {
    Write-Host "Cyclomatic Complexity Analysis..." -ForegroundColor Cyan
    radon cc . -a -s
}

function Run-MetricsMI {
    Write-Host "Maintainability Index..." -ForegroundColor Cyan
    radon mi . -s
}

function Run-MetricsCog {
    Write-Host "Cognitive Complexity (Lizard)..." -ForegroundColor Cyan
    lizard . -l python -w
}

# Execute command
switch ($Command.ToLower()) {
    "all"                { Run-All }
    "lint"               { Run-Lint }
    "lint-fix"           { Run-LintFix }
    "format"             { Run-Format }
    "format-check"       { Run-FormatCheck }
    "type"               { Run-Type }
    "security"           { Run-Security }
    "secrets"            { Run-Secrets }
    "pre-commit"         { Run-PreCommit }
    "pre-commit-install" { Install-PreCommit }
    "test"               { Run-Test }
    "test-unit"          { Run-TestUnit }
    "test-cov"           { Run-TestCov }
    "metrics"            { Run-Metrics }
    "metrics-cc"         { Run-MetricsCC }
    "metrics-mi"         { Run-MetricsMI }
    "metrics-cog"        { Run-MetricsCog }
    "help"               { Show-Help }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
        exit 1
    }
}
