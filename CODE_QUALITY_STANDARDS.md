# LangPlug Code Quality Standards

This document outlines the comprehensive code quality tools, metrics, and standards enforced across the LangPlug project (Python Backend + React Frontend).

## Overview

LangPlug maintains professional code quality through:

- **Automated linting** and formatting
- **Comprehensive metrics** tracking
- **Security scanning**
- **Test coverage** enforcement
- **Type safety** checking
- **Complexity monitoring**

## Backend (Python) Quality Stack

### Tools Installed

| Tool               | Purpose                 | Command                    |
| ------------------ | ----------------------- | -------------------------- |
| **Ruff**           | Fast linter + formatter | `make lint`, `make format` |
| **MyPy**           | Static type checking    | `make type-check`          |
| **Bandit**         | Security scanning       | `make security`            |
| **Radon**          | Complexity metrics      | `make metrics-cc`          |
| **Lizard**         | Cognitive complexity    | `make metrics-cog`         |
| **Wily**           | Complexity trends       | `make metrics-trend`       |
| **Pytest**         | Testing + coverage      | `make test-cov`            |
| **detect-secrets** | Secret detection        | `make secrets`             |

### Quick Commands

```bash
# Backend directory
cd Backend

# Run all quality checks
make quality

# Generate comprehensive metrics
make metrics

# Individual metrics
make metrics-cc    # Cyclomatic complexity
make metrics-mi    # Maintainability index
make metrics-hal   # Halstead metrics
make metrics-loc   # Lines of code
make metrics-cog   # Cognitive complexity

# Windows PowerShell
.\quality.ps1 all
.\quality.ps1 metrics
```

### Quality Standards

| Metric                | Target     | Tool   |
| --------------------- | ---------- | ------ |
| Cyclomatic Complexity | ≤ 10 (A/B) | Radon  |
| Maintainability Index | ≥ 65 (B+)  | Radon  |
| Cognitive Complexity  | < 15       | Lizard |
| Test Coverage         | ≥ 80%      | Pytest |
| Type Coverage         | ≥ 90%      | MyPy   |
| Security Issues       | 0 High/Med | Bandit |
| Lines per Function    | < 50       | Radon  |
| Code Duplication      | < 5%       | Manual |

### Documentation

- **Comprehensive Guide**: `Backend/CODE_METRICS_GUIDE.md`
- **Tool Configuration**: `Backend/pyproject.toml`
- **Metrics Script**: `Backend/metrics_report.py`

## Frontend (React/TypeScript) Quality Stack

### Tools Installed

| Tool           | Purpose                   | Command                         |
| -------------- | ------------------------- | ------------------------------- |
| **ESLint**     | Linting (React, TS, a11y) | `npm run lint`                  |
| **Prettier**   | Code formatting           | `npm run format`                |
| **TypeScript** | Type checking             | `npm run typecheck`             |
| **Stylelint**  | CSS-in-JS linting         | `npm run style`                 |
| **Semgrep**    | Security patterns         | `semgrep --config .semgrep.yml` |
| **Lizard**     | Complexity analysis       | `npm run metrics:complexity`    |
| **JSCPD**      | Duplication detection     | `npm run metrics:duplication`   |
| **Vitest**     | Testing + coverage        | `npm run coverage`              |

### Quick Commands

```bash
# Frontend directory
cd Frontend

# Run all quality checks
npm run quality

# Fix auto-fixable issues
npm run quality:fix

# Generate comprehensive metrics
npm run metrics

# Individual metrics
npm run metrics:complexity     # Complexity analysis
npm run metrics:duplication    # Code duplication
npm run metrics:type-coverage  # TypeScript coverage
```

### Quality Standards

| Metric                | Target     | Tool     |
| --------------------- | ---------- | -------- |
| ESLint Errors         | 0          | ESLint   |
| Cyclomatic Complexity | < 10       | Lizard   |
| Function Length       | < 50 lines | Lizard   |
| Code Duplication      | < 5%       | JSCPD    |
| Test Coverage         | ≥ 80%      | Vitest   |
| TypeScript Errors     | 0          | TSC      |
| Accessibility Issues  | 0          | jsx-a11y |

### Documentation

- **Tool Guide**: `Frontend/QUALITY_TOOLS.md`
- **ESLint Config**: `Frontend/.eslintrc.cjs`
- **Prettier Config**: `Frontend/.prettierrc`
- **Metrics Script**: `Frontend/metrics-report.js`

## Metrics Explained

### 1. Cyclomatic Complexity (CC)

**What**: Number of independent paths through code
**Target**: ≤ 10
**Why**: Simple code is easier to test and maintain

### 2. Cognitive Complexity

**What**: How hard code is to understand
**Target**: < 15
**Why**: Measures real-world difficulty beyond simple path counting

### 3. Maintainability Index (MI)

**What**: Overall maintainability score (0-100)
**Target**: ≥ 65
**Why**: Combines complexity, LOC, and Halstead into one score

### 4. Halstead Metrics

**What**: Program difficulty, effort, and predicted bugs
**Target**: Lower is better
**Why**: Estimates mental effort and error probability

### 5. Lines of Code (LOC)

**What**: Physical, logical, and comment lines
**Targets**:

- Functions: < 50 LLOC
- Classes: < 300 LLOC
- Files: < 500 LLOC
  **Why**: Large functions/classes are hard to understand

### 6. Code Duplication

**What**: Percentage of repeated code
**Target**: < 5%
**Why**: Duplication increases maintenance burden

### 7. Test Coverage

**What**: Percentage of code executed by tests
**Targets**:

- Overall: ≥ 80%
- Critical: 100%
  **Why**: Untested code is fragile code

### 8. Type Coverage

**What**: Percentage with type annotations
**Target**: ≥ 90%
**Why**: Types catch errors before runtime

### 9. Security Vulnerabilities

**What**: Insecure code patterns
**Target**: 0 High/Medium
**Why**: Prevent security breaches

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  backend-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          cd Backend
          pip install -r requirements-dev.txt
      - name: Run quality checks
        run: |
          cd Backend
          make quality
      - name: Check metrics thresholds
        run: |
          cd Backend
          radon cc . --total-average --min B
          radon mi . --min B
      - name: Generate metrics report
        run: |
          cd Backend
          python metrics_report.py

  frontend-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: "18"
      - name: Install dependencies
        run: |
          cd Frontend
          npm ci
      - name: Run quality checks
        run: |
          cd Frontend
          npm run quality
      - name: Run tests with coverage
        run: |
          cd Frontend
          npm run coverage
      - name: Generate metrics
        run: |
          cd Frontend
          npm run metrics
```

## Development Workflow

### Before Committing

```bash
# Backend
cd Backend
make quality              # Fix issues
make test-cov            # Ensure tests pass
make metrics-cc          # Check complexity

# Frontend
cd Frontend
npm run quality:fix      # Fix issues
npm run coverage         # Ensure tests pass
npm run metrics          # Check metrics
```

### Weekly Reviews

```bash
# Generate full reports
cd Backend && python metrics_report.py > ../reports/backend-metrics.txt
cd Frontend && npm run metrics > ../reports/frontend-metrics.txt

# Review trends
cd Backend && wily report .
```

### Refactoring Priorities

Fix code that has:

1. **High complexity** (CC > 10) + **Low test coverage** (< 60%)
2. **Low maintainability** (MI < 50)
3. **High duplication** (> 10%)
4. **Security issues** (High/Medium severity)

## Tool Configuration Files

### Backend

- `pyproject.toml` - Ruff, MyPy, Bandit config
- `Makefile` - Convenience commands
- `quality.ps1` - Windows PowerShell script
- `.pre-commit-config.yaml` - Git hooks
- `metrics_report.py` - Comprehensive metrics

### Frontend

- `.eslintrc.cjs` - ESLint configuration
- `.prettierrc` - Prettier formatting rules
- `.stylelintrc.json` - Stylelint configuration
- `.semgrep.yml` - Security rules
- `package.json` - npm scripts
- `metrics-report.js` - Comprehensive metrics

## Best Practices

### Code Complexity

- Keep functions under 10 cyclomatic complexity
- Break down complex functions into smaller ones
- Use guard clauses (early returns)
- Extract complex conditions into named functions

### Test Coverage

- Write tests for all new features
- Target 80%+ overall coverage
- 100% coverage for critical business logic
- Use behavior-focused tests (not implementation)

### Type Safety

- Use TypeScript strict mode (Frontend)
- Add type hints to all Python functions
- Avoid `any` types (TypeScript)
- Avoid `Any` types (Python)

### Security

- Never hardcode credentials
- Sanitize all user input
- Use parameterized queries
- Keep dependencies updated
- Review all Bandit/Semgrep warnings

### Maintainability

- Write self-documenting code
- Add comments for "why" not "what"
- Keep files under 500 lines
- Minimize code duplication
- Regular refactoring

## Getting Help

### Documentation

- **Backend Metrics**: `Backend/CODE_METRICS_GUIDE.md`
- **Frontend Tools**: `Frontend/QUALITY_TOOLS.md`
- **Code Quality**: This file

### External Resources

- [Radon Docs](https://radon.readthedocs.io/)
- [Lizard](https://github.com/terryyin/lizard)
- [ESLint Rules](https://eslint.org/docs/rules/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Cognitive Complexity](https://www.sonarsource.com/docs/CognitiveComplexity.pdf)

### Support

- Run `make help` (Backend) or `npm run` (Frontend) to see all commands
- Check tool-specific documentation in respective directories
- Review configuration files for customization options

## Summary

LangPlug maintains high code quality through:

- ✅ Automated linting, formatting, and type checking
- ✅ Comprehensive complexity and maintainability metrics
- ✅ Security scanning and vulnerability detection
- ✅ Test coverage tracking and enforcement
- ✅ Continuous monitoring and reporting
- ✅ Clear standards and thresholds

**Result**: Clean, maintainable, secure, and robust codebase aligned with professional standards in 2025.
