# Code Quality & Security Tools Guide

This project uses a comprehensive suite of code quality and security tools to maintain high standards. All tools are configured to work together through pre-commit hooks.

## 📋 Table of Contents

- [Tools Overview](#tools-overview)
- [Quick Start](#quick-start)
- [Tool Details](#tool-details)
- [Manual Usage](#manual-usage)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## 🛠️ Tools Overview

### Core Quality Tools

1. **Ruff** - Fast Python linter and formatter (replaces flake8, isort, black)
2. **MyPy** - Static type checker
3. **Bandit** - Security vulnerability scanner
4. **Detect-Secrets** - Prevents committing secrets

### Additional Checks

- **Pre-commit hooks** - General file format checks
- **Prettier** - YAML, JSON, Markdown formatting

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Activate virtual environment
. api_venv/Scripts/activate

# Install all tools (already done if requirements-dev.txt is installed)
pip install -r requirements-dev.txt
```

### 2. Install Pre-commit Hooks

```bash
# Install hooks (runs automatically on git commit)
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files
```

### 3. Run Individual Tools

```bash
# Ruff - Linting
ruff check .

# Ruff - Auto-fix issues
ruff check . --fix

# Ruff - Format code
ruff format .

# MyPy - Type checking
mypy .

# Bandit - Security scan
bandit -r . -c pyproject.toml
```

## 📖 Tool Details

### Ruff (Linter + Formatter)

**Purpose**: Fast Python linter and formatter that replaces flake8, isort, and black

**What it checks**:

- Code style (PEP 8)
- Import sorting
- Code formatting
- Security issues (basic)
- Common bugs and anti-patterns
- Unused variables and imports
- Complexity metrics

**Configuration**: `pyproject.toml` → `[tool.ruff]`

**Key features**:

- Line length: 120 characters
- Python 3.11+ compatibility
- Auto-fixes import order
- Removes commented-out code

**Usage**:

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .

# Check specific file
ruff check core/config.py
```

### MyPy (Type Checker)

**Purpose**: Static type checking to catch type-related bugs before runtime

**What it checks**:

- Type annotations correctness
- Type mismatches
- Missing return types
- Unreachable code
- Type inference issues

**Configuration**: `pyproject.toml` → `[tool.mypy]`

**Key settings**:

- Gradual typing enabled (not fully strict yet)
- Ignores test files and migrations
- Ignores missing imports for ML libraries

**Usage**:

```bash
# Check entire project
mypy .

# Check specific file
mypy core/config.py

# Check with strict mode
mypy --strict core/config.py
```

### Bandit (Security Scanner)

**Purpose**: Finds common security issues in Python code

**What it checks**:

- Hardcoded passwords
- SQL injection vulnerabilities
- Pickle usage (deserialization attacks)
- Weak cryptographic algorithms
- Command injection risks
- Insecure random number generation

**Configuration**: `pyproject.toml` → `[tool.bandit]`

**Excluded checks**:

- B101: Assert statements (needed for tests)

**Usage**:

```bash
# Scan entire project
bandit -r . -c pyproject.toml

# Detailed output
bandit -r . -c pyproject.toml -v

# JSON output (for CI)
bandit -r . -c pyproject.toml -f json -o bandit-report.json
```

### Detect-Secrets

**Purpose**: Prevents accidentally committing secrets (API keys, passwords, tokens)

**What it detects**:

- AWS keys
- Private keys
- High entropy strings
- Password patterns
- API tokens

**Configuration**: `.secrets.baseline`

**Usage**:

```bash
# Scan for secrets
detect-secrets scan

# Update baseline
detect-secrets scan --baseline .secrets.baseline

# Audit findings
detect-secrets audit .secrets.baseline
```

## 🔧 Manual Usage

### Run All Checks Before Commit

```bash
# Run all pre-commit hooks manually
pre-commit run --all-files
```

### Fix All Auto-fixable Issues

```bash
# Ruff: Fix linting and format
ruff check . --fix && ruff format .

# Pre-commit: Auto-fix general issues
pre-commit run --all-files
```

### Check Specific Files

```bash
# Single file with all tools
pre-commit run --files core/config.py

# Or run tools individually
ruff check core/config.py
mypy core/config.py
bandit core/config.py
```

## 🎯 Pre-commit Hook Behavior

When you run `git commit`, the following checks run automatically:

1. **Ruff Linter** - Checks code style, imports, complexity
2. **Ruff Formatter** - Formats code to standard style
3. **MyPy** - Checks type annotations (excludes tests)
4. **Bandit** - Scans for security issues (excludes tests)
5. **General Checks**:
   - Trailing whitespace removal
   - End-of-file fixer
   - YAML/JSON/TOML syntax validation
   - Large file detection (>1MB)
   - Merge conflict markers
   - Private key detection
   - Python syntax validation

6. **Detect-Secrets** - Prevents committing secrets

**Note**: If any check fails, the commit is blocked. Fix the issues and commit again.

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt

      - name: Run Ruff
        run: |
          ruff check .
          ruff format --check .

      - name: Run MyPy
        run: mypy .

      - name: Run Bandit
        run: bandit -r . -c pyproject.toml -f json -o bandit-report.json

      - name: Run Pre-commit
        run: pre-commit run --all-files
```

### GitLab CI Example

```yaml
code_quality:
  image: python:3.11
  before_script:
    - pip install -r requirements-dev.txt
  script:
    - ruff check .
    - ruff format --check .
    - mypy .
    - bandit -r . -c pyproject.toml
    - pre-commit run --all-files
```

## 🐛 Troubleshooting

### Pre-commit hooks not running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Update hooks to latest versions
pre-commit autoupdate
```

### Ruff finding too many issues

```bash
# Auto-fix what can be fixed
ruff check . --fix

# Format code
ruff format .

# Add exceptions to pyproject.toml if needed
```

### MyPy type errors

```bash
# Ignore specific errors with comments
# type: ignore[error-code]

# Add missing type stubs
pip install types-requests types-PyYAML

# Gradually enable strict mode
# Update pyproject.toml [tool.mypy] settings
```

### Bandit false positives

```bash
# Suppress specific check in code
# nosec B101

# Skip check globally in pyproject.toml
# Add to [tool.bandit] skips = ["B101"]
```

### Detect-secrets false positives

```bash
# Mark as not a secret
detect-secrets audit .secrets.baseline

# Update baseline
detect-secrets scan --baseline .secrets.baseline
```

## 📊 Configuration Files

All tools are configured in:

- **`pyproject.toml`** - Main configuration for Ruff, MyPy, Bandit, Coverage
- **`.pre-commit-config.yaml`** - Pre-commit hook configuration
- **`.secrets.baseline`** - Detect-secrets baseline
- **`requirements-dev.txt`** - Tool dependencies

## 🎓 Best Practices

1. **Run pre-commit before pushing**:

   ```bash
   pre-commit run --all-files
   ```

2. **Fix issues incrementally**:
   - Start with auto-fixable issues (Ruff)
   - Then tackle type errors (MyPy)
   - Address security issues (Bandit)

3. **Keep tools updated**:

   ```bash
   pre-commit autoupdate
   pip install --upgrade ruff mypy bandit
   ```

4. **Review tool outputs**:
   - Ruff: Focus on code smells and complexity
   - MyPy: Improve type safety gradually
   - Bandit: Never ignore security warnings without review

5. **Document exceptions**:
   - Add comments explaining why checks are skipped
   - Use `# type: ignore` sparingly with explanations
   - Document `# nosec` usage

## 📈 Continuous Improvement

### Phase 1: Basic Setup ✅

- [x] Install all tools
- [x] Configure in pyproject.toml
- [x] Set up pre-commit hooks

### Phase 2: Current (Gradual Improvement)

- [ ] Fix high-priority Bandit security issues
- [ ] Add type hints to core modules
- [ ] Reduce Ruff complexity warnings

### Phase 3: Strict Mode (Future)

- [ ] Enable MyPy strict mode
- [ ] 100% type coverage for core modules
- [ ] Zero Bandit warnings
- [ ] Custom Ruff rules for domain logic

## 🔗 Additional Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Detect-Secrets Documentation](https://github.com/Yelp/detect-secrets)

---

**Last Updated**: 2025-10-01
