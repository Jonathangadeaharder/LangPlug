# Code Quality Metrics Guide

This guide explains the comprehensive code quality metrics available for the LangPlug Backend and how to use them to maintain a healthy codebase.

## Quick Start

```bash
# Generate comprehensive metrics report
make metrics

# Or individual metrics
make metrics-cc      # Cyclomatic complexity
make metrics-mi      # Maintainability index
make metrics-cog     # Cognitive complexity
```

For Windows PowerShell:

```powershell
.\quality.ps1 metrics
.\quality.ps1 metrics-cc
```

## Metrics Overview

### 1. Cyclomatic Complexity (CC)

**What it measures**: Number of independent paths through code
**Tool**: Radon
**Command**: `make metrics-cc` or `radon cc . -a -s`

**Interpretation**:

- **A (1-5)**: Low complexity - Simple, easy to test ✅
- **B (6-10)**: Moderate complexity - Still manageable
- **C (11-20)**: Complex - Consider refactoring
- **D (21-30)**: High complexity - Difficult to maintain ⚠️
- **E (31-40)**: Very high complexity - Serious refactoring needed ❌
- **F (41+)**: Extremely complex - Critical refactoring required 🚨

**Target**: Keep functions at **A** or **B** (complexity ≤ 10)

**Example Output**:

```
services/vocabulary_service.py
    M 35:4 VocabularyService.get_word_info - A (1)
    M 92:4 VocabularyService.get_vocabulary_level - A (3)
```

**How to improve**:

- Break large functions into smaller ones
- Reduce nested if/else statements
- Extract complex conditions into named functions
- Use guard clauses (early returns)

### 2. Maintainability Index (MI)

**What it measures**: Overall code maintainability score (0-100)
**Tool**: Radon
**Command**: `make metrics-mi` or `radon mi . -s`

**Formula**: Based on Halstead Volume, Cyclomatic Complexity, and Lines of Code

**Interpretation**:

- **A (85-100)**: Highly maintainable ✅
- **B (65-85)**: Moderately maintainable
- **C (50-65)**: Difficult to maintain ⚠️
- **D (0-50)**: Extremely difficult to maintain ❌

**Target**: Maintain **≥ 65** (B rating or better)

**Example Output**:

```
services/vocabulary_service.py - A (78.45)
core/database.py - B (68.23)
```

**How to improve**:

- Reduce cyclomatic complexity
- Shorten functions (< 50 lines)
- Add clear comments for complex logic
- Reduce code duplication

### 3. Cognitive Complexity

**What it measures**: How hard code is to understand (not just number of paths)
**Tool**: Lizard
**Command**: `make metrics-cog` or `lizard . -l python -w`

**Interpretation**:

- Considers nesting depth, recursion, and control flow
- Higher cognitive complexity = harder to understand
- Target: Keep functions **< 15**

**Example Output**:

```
================================================
  NLOC    CCN   token  PARAM  length  location
------------------------------------------------
     45      3    210      4      48  process_video@services/processing.py:120-168
```

- **NLOC**: Non-comment lines of code
- **CCN**: Cyclomatic Complexity Number
- **token**: Number of tokens (operators + operands)
- **PARAM**: Number of parameters
- **length**: Total lines

**How to improve**:

- Reduce nesting levels
- Extract nested logic into separate functions
- Simplify Boolean expressions
- Avoid deep callback chains

### 4. Halstead Metrics

**What it measures**: Program difficulty, effort, and predicted bugs
**Tool**: Radon
**Command**: `make metrics-hal` or `radon hal . -f`

**Key Metrics**:

- **h1/h2**: Unique/total operators
- **N1/N2**: Unique/total operands
- **Vocabulary**: h1 + h2
- **Length**: N1 + N2
- **Volume**: Measure of code size
- **Difficulty**: How hard to write/understand
- **Effort**: Mental effort required
- **Bugs**: Estimated number of errors

**Interpretation**:

- Lower difficulty = easier to understand
- Lower effort = less complex
- Bugs estimate helps prioritize testing

**How to improve**:

- Simplify complex expressions
- Use meaningful variable names
- Reduce number of operators
- Break down large functions

### 5. Lines of Code (LOC)

**What it measures**: Physical, logical, and comment lines
**Tool**: Radon
**Command**: `make metrics-loc` or `radon raw . -s`

**Metrics**:

- **LOC**: Physical lines (including blanks)
- **LLOC**: Logical lines of code
- **SLOC**: Source lines (excludes blanks)
- **Comments**: Comment lines
- **Multi**: Multi-line strings
- **Blank**: Blank lines

**Targets**:

- **Functions**: < 50 LLOC
- **Classes**: < 300 LLOC
- **Modules**: < 500 LLOC
- **Comment Ratio**: 10-30%

**Example Output**:

```
services/vocabulary_service.py
    LOC: 350
    LLOC: 180
    SLOC: 285
    Comments: 45
    Multi: 10
    Blank: 20
```

### 6. Code Duplication

**What it measures**: Repeated code blocks
**Tool**: (Manual detection with `grep` or use SonarQube/CodeClimate)

**Target**: < 5% duplication

**How to find**:

```bash
# Find similar code patterns manually
grep -r "def process_" services/
```

**How to improve**:

- Extract common code into utilities
- Use inheritance/composition
- Apply DRY (Don't Repeat Yourself)
- Create reusable abstractions

### 7. Test Coverage

**What it measures**: Percentage of code executed by tests
**Tool**: coverage.py (pytest-cov)
**Command**: `make test-cov`

**Targets**:

- **Overall**: ≥ 80%
- **Critical Code**: 100%
- **Business Logic**: ≥ 90%
- **Utilities**: ≥ 70%

**View Report**:

```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### 8. Type Coverage

**What it measures**: Percentage of code with type annotations
**Tool**: MyPy
**Command**: `make type-check`

**Interpretation**:

- Shows untyped functions/variables
- Helps catch type errors early
- Improves IDE support

**Target**: ≥ 90% type coverage

**How to improve**:

- Add type hints to function signatures
- Type annotate variables where not obvious
- Use `typing` module for complex types
- Enable strict mode incrementally

### 9. Security Vulnerabilities

**What it measures**: Security issues and code patterns
**Tool**: Bandit
**Command**: `make security`

**Severity Levels**:

- **High**: Critical security issues - fix immediately
- **Medium**: Potential security problems - review
- **Low**: Best practice violations - consider fixing

**Common Issues**:

- SQL injection risks
- Hardcoded secrets
- Use of weak crypto
- Insecure temp file usage
- Shell injection vulnerabilities

### 10. Complexity Trends Over Time

**What it measures**: How metrics change over commits
**Tool**: Wily
**Command**: `make metrics-trend`

**Setup** (first time):

```bash
wily build .
```

**View Trends**:

```bash
wily report .
wily graph services/vocabulary_service.py
```

**Benefits**:

- Track if complexity is increasing
- Identify problem areas early
- Measure impact of refactoring
- Prevent technical debt accumulation

## Comprehensive Metrics Report

Run the comprehensive report to see all metrics:

```bash
make metrics
# or
python metrics_report.py
```

This generates a complete report including:

- Cyclomatic complexity summary
- Maintainability index
- Halstead metrics
- LOC analysis
- Cognitive complexity
- Type coverage
- Test coverage
- Security scan
- Linting statistics

## Interpreting Combined Metrics

### Healthy Code Profile

- **CC**: Mostly A/B ratings
- **MI**: ≥ 65
- **Test Coverage**: ≥ 80%
- **Type Coverage**: ≥ 90%
- **Security**: No high/medium issues
- **Duplication**: < 5%

### Warning Signs

- **High CC** + **Low MI**: Complex, hard to maintain
- **Low Test Coverage** + **High CC**: Risky, hard to test
- **Many Security Issues**: Security vulnerabilities
- **High Duplication**: Poor code reuse

## CI/CD Integration

Add to your CI pipeline:

```yaml
- name: Code Metrics Check
  run: |
    python metrics_report.py
    # Fail if metrics below threshold
    radon cc . --total-average --min A
    radon mi . --min B
```

## Best Practices

1. **Regular Monitoring**: Run metrics weekly
2. **Set Thresholds**: Define acceptable ranges
3. **Track Trends**: Use Wily to monitor changes
4. **Refactor Proactively**: Address issues early
5. **Code Reviews**: Check metrics for new code
6. **Automate**: Include in CI/CD pipeline
7. **Balance**: Don't over-optimize; focus on real issues

## Quick Reference

| Metric                | Tool   | Target     | Command            |
| --------------------- | ------ | ---------- | ------------------ |
| Cyclomatic Complexity | Radon  | ≤ 10 (A/B) | `make metrics-cc`  |
| Maintainability Index | Radon  | ≥ 65 (B+)  | `make metrics-mi`  |
| Cognitive Complexity  | Lizard | < 15       | `make metrics-cog` |
| Test Coverage         | Pytest | ≥ 80%      | `make test-cov`    |
| Type Coverage         | MyPy   | ≥ 90%      | `make type-check`  |
| Security Issues       | Bandit | 0 High/Med | `make security`    |
| LOC per Function      | Radon  | < 50       | `make metrics-loc` |

## Further Reading

- [Radon Documentation](https://radon.readthedocs.io/)
- [Lizard Documentation](https://github.com/terryyin/lizard)
- [Wily Documentation](https://wily.readthedocs.io/)
- [Cyclomatic Complexity Explained](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [Maintainability Index](https://docs.microsoft.com/en-us/visualstudio/code-quality/code-metrics-values)
- [Cognitive Complexity Paper](https://www.sonarsource.com/docs/CognitiveComplexity.pdf)
