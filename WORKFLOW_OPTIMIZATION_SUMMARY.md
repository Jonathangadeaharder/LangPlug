# GitHub Actions Workflow Optimization Summary

**Date**: 2025-10-12
**Reason**: Monthly GitHub Actions minutes limit reached

## Problem
All GitHub workflows were failing immediately with empty steps due to exhausted Actions minutes quota.

## Root Causes Identified
1. **Monthly rate limit hit**: Free tier provides 2,000 minutes/month
2. **Too many active workflows**: 14 workflows running on every push/PR
3. **Large test matrices**: Multiple OS/shard combinations consuming minutes quickly
4. **No paths-ignore**: Workflows running even for documentation-only changes

## Actions Taken

### 1. Disabled Non-Essential Workflows (12 workflows)

**Disabled workflows:**
- `fast-tests.yml` - Redundant with unit-tests
- `tests.yml` (CI) - Redundant with unit-tests
- `tests-nightly.yml` - Scheduled tests can wait
- `code-quality.yml` - Can run locally with ruff/eslint
- `security-scan.yml` - Can run monthly instead
- `contract-tests.yml` - Can run less frequently
- `status-dashboard.yml` - Nice-to-have, not critical
- `deploy.yml` - Only needed for actual deployments
- `deploy-frontend.yml` - Only needed for actual deployments
- `create-release.yml` - Only needed for releases
- `docs-check.yml` - Can run locally
- `test-minimal.yml` - Debug workflow, removed

**Command used:**
```bash
gh workflow disable <workflow-name>
```

### 2. Made E2E Tests Manual-Only

**Before:**
```yaml
on:
  push:
    branches: [main, master, develop]
  pull_request:
    branches: [main, master, develop]
  workflow_dispatch:
```

**After:**
```yaml
on:
  workflow_dispatch:  # Manual trigger only to conserve Actions minutes
```

**Impact**: E2E tests (30 min runtime on Windows) now only run when explicitly triggered.

### 3. Optimized Unit Tests with paths-ignore

**Added to unit-tests.yml:**
```yaml
on:
  push:
    branches: [main, master]
    paths-ignore:
      - '**.md'          # Documentation
      - 'docs/**'        # Documentation folder
      - '.github/**.md'  # Workflow docs
      - 'plans/**'       # Planning documents
      - 'scripts/**'     # Development scripts
      - '.vscode/**'     # Editor config
      - '.idea/**'       # Editor config
```

**Impact**: Unit tests will NOT run for documentation-only changes, saving minutes.

## Results

### Before Optimization
- **Active workflows**: 14
- **Runs per push**: ~14 workflows × multiple jobs = 30+ jobs
- **Estimated minutes per push**: 50-100 minutes
- **Status**: Monthly limit exhausted

### After Optimization
- **Active workflows**: 2 (unit-tests + e2e-manual)
- **Runs per push**: 2 jobs (backend + frontend unit tests)
- **Estimated minutes per push**: 5-10 minutes
- **Status**: **90% reduction in minutes usage**

## Remaining Active Workflows

### 1. Unit Tests (`unit-tests.yml`)
- **Trigger**: Push to main/master, PRs (with paths-ignore)
- **Jobs**: 2 (backend + frontend)
- **Runtime**: ~5 minutes total
- **Critical**: Yes - provides quick feedback on PRs

### 2. E2E Tests (`e2e-tests.yml`)
- **Trigger**: Manual only (workflow_dispatch)
- **Jobs**: 1 (Windows-based full E2E)
- **Runtime**: ~30 minutes
- **Critical**: Yes, but run on-demand

## How to Use

### Running Unit Tests
Unit tests run automatically on:
- Every push to main/master
- Every pull request
- **Exception**: Skips if only docs/scripts changed

### Running E2E Tests Manually
```bash
# Via gh CLI
gh workflow run e2e-tests.yml

# Via GitHub UI
Actions → End-to-End Tests → Run workflow
```

### Re-enabling Disabled Workflows
If you need any disabled workflow temporarily:
```bash
gh workflow enable <workflow-name>
# Run it
gh workflow run <workflow-name>
# Disable again when done
gh workflow disable <workflow-name>
```

## Monthly Minutes Management

### Current Limits
- **Free tier**: 2,000 minutes/month
- **Pro tier**: 3,000 minutes/month
- **Minutes reset**: 1st of each month

### Estimated New Usage
- **Unit tests per push**: ~5 minutes
- **E2E tests (manual)**: ~30 minutes
- **Estimated monthly usage**: ~300-500 minutes (with 2-3 E2E runs)
- **Buffer**: 1,500+ minutes remaining

### Tips to Conserve Minutes
1. **Batch commits**: Combine multiple small changes before pushing
2. **Draft PRs**: Open PRs as drafts to skip workflows initially
3. **Local testing**: Run tests locally before pushing
4. **Manual E2E**: Only run E2E tests before important releases

## Re-enabling Workflows Later

When minutes reset (November 1st), you can re-enable workflows:

```bash
# Re-enable critical workflows
gh workflow enable tests.yml              # Main CI
gh workflow enable fast-tests.yml         # Fast feedback
gh workflow enable code-quality.yml       # Code quality
gh workflow enable security-scan.yml      # Security

# Keep disabled until needed
# - deploy.yml (only for releases)
# - tests-nightly.yml (scheduled, not urgent)
# - contract-tests.yml (run less frequently)
```

## Summary

**Workflow optimization complete!** ✅

- Reduced active workflows from **14 to 2**
- Reduced minutes per push by **~90%**
- Maintained essential testing coverage
- E2E tests available on-demand
- Fixed workflow bugs (defaults.run.working-directory issue)

**Next reset**: November 1st, 2025
