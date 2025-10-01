# Makefile for LangPlug Backend
# Provides convenient commands for code quality, testing, and development

.PHONY: help install quality lint format type-check security test clean metrics

# Default target - show help
help:
	@echo "LangPlug Backend - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          - Install all dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make install-ml       - Install ML dependencies (heavy)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make quality          - Run all quality checks (lint + format + type + security)"
	@echo "  make lint             - Run Ruff linter"
	@echo "  make lint-fix         - Run Ruff linter with auto-fix"
	@echo "  make format           - Format code with Ruff"
	@echo "  make format-check     - Check formatting without changes"
	@echo "  make type-check       - Run MyPy type checker"
	@echo "  make security         - Run Bandit security scanner"
	@echo "  make secrets          - Check for committed secrets"
	@echo ""
	@echo "Code Metrics & Analysis:"
	@echo "  make metrics          - Generate comprehensive metrics report"
	@echo "  make metrics-cc       - Cyclomatic complexity analysis"
	@echo "  make metrics-mi       - Maintainability index"
	@echo "  make metrics-hal      - Halstead complexity metrics"
	@echo "  make metrics-loc      - Lines of code analysis"
	@echo "  make metrics-cog      - Cognitive complexity (Lizard)"
	@echo "  make metrics-trend    - Track complexity trends over time (Wily)"
	@echo ""
	@echo "Pre-commit:"
	@echo "  make pre-commit       - Run all pre-commit hooks"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-update  - Update pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-cov         - Run tests with coverage"
	@echo "  make test-fast        - Run tests in parallel (fast)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Remove cache and temp files"
	@echo "  make clean-all        - Deep clean (including venv)"
	@echo ""

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

install-ml:
	pip install -r requirements-ml.txt

# Code quality targets
quality: lint-fix format type-check security
	@echo "✅ All quality checks passed!"

lint:
	ruff check .

lint-fix:
	ruff check . --fix

format:
	ruff format .

format-check:
	ruff format --check .

type-check:
	mypy .

security:
	bandit -r . -c pyproject.toml

secrets:
	detect-secrets scan

# Pre-commit targets
pre-commit:
	pre-commit run --all-files

pre-commit-install:
	pre-commit install

pre-commit-update:
	pre-commit autoupdate

# Testing targets
test:
	pytest

test-unit:
	pytest tests/unit/

test-integration:
	pytest tests/integration/

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term

test-fast:
	pytest -n auto

# Cleanup targets
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -f .coverage
	rm -f coverage.json

clean-all: clean
	rm -rf api_venv/
	rm -rf venv/

# Development server
dev:
	uvicorn core.app:app --reload --host 0.0.0.0 --port 8000

# Database migrations
db-migrate:
	alembic upgrade head

db-revision:
	alembic revision --autogenerate -m "$(message)"

db-downgrade:
	alembic downgrade -1

# Code metrics targets
metrics:
	python metrics_report.py

metrics-cc:
	@echo "Cyclomatic Complexity Analysis:"
	radon cc . -a -s

metrics-mi:
	@echo "Maintainability Index:"
	radon mi . -s

metrics-hal:
	@echo "Halstead Complexity Metrics:"
	radon hal . -f

metrics-loc:
	@echo "Lines of Code Analysis:"
	radon raw . -s

metrics-cog:
	@echo "Cognitive Complexity (Lizard):"
	lizard . -l python -w

metrics-trend:
	@echo "Complexity Trends (Wily):"
	@echo "First time setup: wily build ."
	@echo "View report: wily report ."
	wily report .
