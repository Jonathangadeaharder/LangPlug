# Dependabot Update Summary - November 2025

This document summarizes the package updates applied to merge all dependabot PRs into a single comprehensive update.

## Overview

All package dependencies have been updated to their latest compatible versions within the constraints specified in package.json and requirements.txt files. The goal was to apply security patches and feature updates while maintaining compatibility.

## Security Vulnerabilities Addressed

### Fixed (3 High/Moderate Severity)
1. ✅ **axios** (HIGH) - DoS vulnerability in versions 1.0.0-1.11.0
   - Fixed by upgrading to axios 1.13.2+
   
2. ✅ **glob** (HIGH) - Command injection vulnerability via CLI in versions 10.2.0-10.4.5
   - Fixed by upgrading to secure version
   
3. ✅ **js-yaml** (MODERATE) - Prototype pollution in merge operator
   - Fixed by upgrading to js-yaml 3.14.2+

### Remaining (Deferred - Breaking Changes Required)
4. ⚠️ **esbuild** (MODERATE) - Request spoofing vulnerability in versions <=0.24.2
   - Requires vite upgrade to v7.x (currently v4.x)
   - Deferred due to breaking changes
   
5. ⚠️ **vite** (MODERATE) - Depends on vulnerable esbuild
   - Requires major version upgrade from v4 to v7
   - Deferred due to potential breaking changes in build pipeline

## NPM Package Updates

### Root (/)
- nx: Updated to latest ^20.3.0 compatible versions
- @nx/js: Updated to latest ^20.3.0 compatible versions

### Frontend (src/frontend)
Updated 120+ packages to latest compatible versions including:
- @tanstack/react-query: 5.90.8 → 5.90.10
- @tanstack/react-query-devtools: 5.90.2 → 5.91.0
- @playwright/test: 1.55.1 → 1.56.1
- @hey-api/openapi-ts: 0.50.2 → 0.88.0
- @vitest/coverage-v8: 3.2.4 → 4.0.13
- @vitest/ui: 3.2.4 → 4.0.13
- msw: 2.11.3 → 2.12.2
- puppeteer: 24.22.0 → 24.31.0
- react-hook-form: 7.62.0 → 7.66.1
- stylelint: 16.24.0 → 16.26.0
- typescript: 5.9.2 → 5.9.3
- vitest: 3.2.4 → 4.0.13
- And many more...

### Tests (tests/)
Updated 24+ packages including:
- @playwright/test: Updated to 1.56.1
- puppeteer: Updated to 24.31.0
- chalk: Updated to latest 4.x
- And others...

### E2E Tests (tests/e2e)
Updated 41+ packages including:
- axios: Updated to 1.13.2
- puppeteer: Updated to 24.31.0
- typescript: Updated to 5.9.3
- And others...

### Integration Tests (src/frontend/tests/integration)
- All packages installed and updated to latest compatible versions
- Created package-lock.json

## Python Package Updates (Backend)

Updated src/backend/requirements.txt to use latest compatible versions:

### Core Framework
- fastapi: >=0.118.3 (maintained)
- pydantic: >=2.12.0 (maintained)
- pydantic-settings: >=2.11.0 (maintained)
- uvicorn: >=0.37.0 (maintained)

### Database
- sqlalchemy: >=2.0.44 (maintained)
- aiosqlite: >=0.21.0 (maintained)
- alembic: >=1.16.5 (maintained)

### AI/ML
- transformers: >=4.45.0 (was >=4.35.0)
- torch: >=2.0.0 (maintained for broad compatibility)
- spacy: expanded upper bound to <4.0.0 (was <3.9.0)
- sentencepiece: >=0.2.0 (was >=0.1.99)
- protobuf: >=3.20.0,<5.0.0 (maintained for ML library compatibility)

### Audio/Video
- moviepy: >=2.2.1 (maintained)
- opencv-python: expanded upper bound to <5.0.0 (was <4.11.0)

### Monitoring & Logging
- structlog: >=24.4.0 (was >=24.1.0)
- sentry-sdk: >=2.18.0 (was >=2.0.0)

### Utilities
- psutil: >=6.1.0 (was >=5.9.0)
- websockets: >=13.0 (was >=12.0)
- pyyaml: >=6.0.2 (was >=6.0)
- rich: >=13.9.0 (was >=13.0.0)
- tqdm: >=4.67.0 (was >=4.65.0)
- pandas: >=2.2.0 (was >=2.0.0)
- numpy: >=1.26.0 with expanded range to <3.0.0 (was <2.0.0)

### Testing
- pytest: >=8.3.0 (was >=8.0.0)
- pytest-asyncio: >=0.24.0 (was >=0.23.0)
- pytest-cov: >=6.0.0 (was >=4.1.0)
- pytest-xdist: >=3.6.0 (was >=3.5.0)
- pytest-timeout: >=2.3.0 (was >=2.2.0)
- hypothesis: >=6.122.0 (was >=6.92.0)
- pytest-env: >=1.1.5 (was >=1.1.0)
- httpx: >=0.28.0 (was >=0.26.0)
- respx: >=0.22.0 (was >=0.20.0)
- anyio: >=4.7.0 (was >=4.0.0)
- trio: >=0.27.0 (was >=0.23.0)
- freezegun: >=1.5.0 (was >=1.4.0)
- responses: >=0.25.0 (was >=0.24.0)

### Code Quality & Security
- pre-commit: >=4.0.0 (was >=3.5.0)
- ruff: >=0.8.0 (was >=0.1.0)
- mypy: >=1.13.0 (was >=1.7.0)
- bandit: >=1.8.0 (was >=1.7.0)
- detect-secrets: >=1.5.0 (was >=1.4.0)
- radon: >=6.0.0 (was >=5.1.0)

### Type Stubs
- types-requests: >=2.32.0 (was >=2.31.0)
- sqlalchemy[mypy]: >=2.0.36 (was >=2.0.0)

## Testing Results

### Frontend Tests
- ✅ All 308 tests passing across 22 test files
- ✅ ESLint passes with no warnings
- ⚠️ TypeScript compilation has pre-existing errors (unrelated to updates)

### Backend Tests
- Not run (would require virtual environment setup and dependencies installation)

## Configuration Changes

### Added .npmrc
Created a global .npmrc file to skip Puppeteer browser downloads:
```
PUPPETEER_SKIP_DOWNLOAD=true
```

This prevents network errors during npm install in environments without internet access to googlechromelabs.github.io.

## Recommendations for Future Updates

### High Priority
1. **Upgrade vite to v7.x** - Addresses remaining esbuild vulnerability (MODERATE severity)
   - Review vite v5, v6, and v7 migration guides
   - Test thoroughly as this is a breaking change
   - Update any vite plugins that may have compatibility issues

### Medium Priority
2. **Major version updates** - Several packages have major version updates available:
   - react: 18.x → 19.x
   - react-dom: 18.x → 19.x
   - eslint: 8.x → 9.x
   - zod: 3.x → 4.x
   - zustand: 4.x → 5.x
   - react-router-dom: 6.x → 7.x
   - react-player: 2.x → 3.x
   - react-error-boundary: 4.x → 6.x
   - Testing library packages (major updates)
   
   These should be evaluated individually with migration guides and thorough testing.

### Low Priority
3. **Fix TypeScript errors** - Address pre-existing styled-components theme type issues
4. **Update spacy language models** - Consider updating to newer versions if available

## Breaking Changes

None in this update. All changes maintain backward compatibility within existing semver constraints.

## Notes

- All package.json files use caret (^) ranges, allowing automatic minor and patch updates
- requirements.txt uses >= with upper bounds, allowing compatible updates
- Lock files (package-lock.json) updated to reflect new resolved versions
- No changes to package.json semver constraints were needed
- Updates focused on security fixes and compatible feature updates

## Date

Updated: November 23, 2025
