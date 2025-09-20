# Script Migration Guide

This document explains the consolidation of duplicate cross-platform scripts into unified Python solutions.

## Problem

The project had duplicate scripts for the same functionality:
- `generate-ts-client.sh` and `generate-ts-client.bat`
- `Backend/scripts/run_tests_postgres.sh` and `Backend/scripts/run_tests_postgres.ps1`

This created maintenance overhead and potential inconsistencies.

## Solution

Replaced duplicate scripts with cross-platform Python alternatives:

### 1. TypeScript Client Generation

**Old scripts (deprecated):**
- `generate-ts-client.sh`
- `generate-ts-client.bat`

**New unified script:**
```bash
python scripts/generate_typescript_client.py
```

**Usage:**
```bash
# Generate TypeScript client
python scripts/generate_typescript_client.py

# Clean generated files
python scripts/generate_typescript_client.py --clean
```

### 2. PostgreSQL Test Runner

**Old scripts (deprecated):**
- `Backend/scripts/run_tests_postgres.sh`
- `Backend/scripts/run_tests_postgres.ps1`

**New unified script:**
```bash
python scripts/run_postgres_tests.py
```

**Usage:**
```bash
# Run tests against PostgreSQL
python scripts/run_postgres_tests.py

# Clean up PostgreSQL containers
python scripts/run_postgres_tests.py --cleanup
```

## Benefits

1. **Single Source of Truth**: One script per functionality
2. **Cross-Platform**: Works on Windows, macOS, and Linux
3. **Better Error Handling**: Comprehensive error messages and validation
4. **Maintainable**: Only need to update one file for changes
5. **Professional**: Industry-standard approach using Python for tooling

## Migration Path

1. **Immediate**: Start using the new Python scripts
2. **Phase Out**: The old scripts are marked deprecated but still work
3. **Remove**: Old scripts will be removed in a future release

### For CI/CD Systems

Update your build scripts to use the new commands:

```yaml
# Old
- run: ./generate-ts-client.sh

# New
- run: python scripts/generate_typescript_client.py
```

```yaml
# Old
- run: Backend/scripts/run_tests_postgres.sh

# New  
- run: python scripts/run_postgres_tests.py
```

## Requirements

- Python 3.7+ (already required by the project)
- All existing dependencies (Docker, npm, etc.)

No additional setup required - the Python scripts use the same underlying tools.
