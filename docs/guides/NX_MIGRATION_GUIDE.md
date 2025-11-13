# Nx Monorepo Migration Guide

This guide explains how to use the new Nx monorepo tooling that was set up in Phase 1.

## What is Nx?

Nx is a smart monorepo build system that provides:

- **Intelligent caching**: Don't rebuild/retest unchanged code
- **Affected commands**: Only run tasks on projects affected by your changes
- **Parallel execution**: Run independent tasks concurrently
- **Dependency graph**: Visualize relationships between projects
- **Consistent interface**: Same commands for frontend and backend

## Quick Start

### Local Development

```bash
# Run frontend dev server
npm run frontend:dev

# Run backend tests
npm run backend:test

# Run all tests
npm run test

# Run only affected tests (based on git changes)
npm run test:affected

# Run linting on all projects
npm run lint

# View dependency graph
npm run graph
```

### Using Nx directly

```bash
# Run specific target for specific project
npx nx test frontend
npx nx lint backend

# Run target for all projects
npx nx run-many --target=test --all

# Run target for affected projects only
npx nx affected --target=test

# See what's affected by your changes
npx nx affected:graph
```

## Project Configuration

### Frontend (`src/frontend/project.json`)

Available targets:
- `dev` - Start Vite dev server
- `build` - Build production bundle
- `test` - Run Vitest unit tests
- `test:e2e` - Run Playwright E2E tests
- `lint` - ESLint
- `typecheck` - TypeScript type checking
- `quality` - Run all quality checks
- `format` - Prettier formatting

### Backend (`src/backend/project.json`)

Available targets:
- `test` - Run all pytest tests
- `test:unit` - Run unit tests only
- `test:integration` - Run integration tests only
- `lint` - Ruff linting
- `typecheck` - MyPy type checking
- `quality` - Run all quality checks
- `format` - Ruff formatting

**Important - Virtual Environment:**
Backend commands assume the Python virtual environment is already activated. Before running any backend Nx tasks, activate the venv:

```bash
# Windows (PowerShell)
. src/backend/api_venv/Scripts/activate

# macOS/Linux
source src/backend/api_venv/bin/activate

# Then run Nx commands
npx nx test backend
```

This approach ensures cross-platform compatibility - the same commands work on Windows, macOS, and Linux without modification.

## Caching

Nx caches task outputs to avoid redundant work:

- **Local cache**: `.cache/nx/` (gitignored)
- **Cached operations**: `build`, `test`, `lint`, `typecheck`, `quality`

### How it works

1. First run: `npx nx test frontend` → Runs tests, caches results
2. No changes: `npx nx test frontend` → Retrieves from cache (instant)
3. Code changes: `npx nx test frontend` → Runs tests, updates cache

### Clear cache

```bash
# Clear Nx cache
npx nx reset

# Or manually delete
rm -rf .cache/nx
```

## Affected Commands

Nx can detect which projects are affected by your changes:

```bash
# See affected projects
npx nx affected:graph

# Test only affected projects
npx nx affected --target=test

# Lint only affected projects
npx nx affected --target=lint

# Build only affected projects
npx nx affected --target=build
```

**Base for comparison:**
- In CI: Compares against `master` branch
- Locally: Compares against your last commit

## GitHub Actions Integration

### Current Workflows (Not migrated yet)

The existing workflows still work as before:
- `tests.yml` - Full test suite (backend + frontend)
- `unit-tests.yml` - Unit tests only
- `code-quality.yml` - Linting and quality checks
- `fast-tests.yml` - Quick smoke tests

### New Nx Workflow (Example)

`nx-affected.yml` demonstrates how to use Nx in CI:
- Only runs tasks on affected projects
- Significantly faster for small PRs
- Same coverage as full test suite

### Migration Strategy (Future)

When ready to migrate existing workflows:

#### Option 1: Gradual Migration (Recommended)

1. Keep existing workflows for now
2. Use `nx-affected.yml` for PR checks
3. Gradually migrate individual workflows
4. Remove old workflows once confident

#### Option 2: Full Migration

Replace workflow test commands with Nx:

```yaml
# Before
- name: Run pytest
  run: pytest tests/ -v

# After
- name: Run pytest with Nx
  run: npx nx test backend
```

**Benefits:**
- Automatic caching in CI
- Only test affected projects
- Faster CI runs

## Dependency Graph

Visualize project relationships:

```bash
# Open interactive graph in browser
npm run graph

# Or use Nx directly
npx nx graph

# See affected graph for current changes
npx nx affected:graph
```

## Configuration Files

### Root Configuration

- `package.json` - Root package with Nx scripts
- `nx.json` - Nx configuration (caching, task defaults)
- `.nxignore` - Files to exclude from Nx processing

### Project Configuration

- `src/frontend/project.json` - Frontend Nx targets
- `src/backend/project.json` - Backend Nx targets

## Advanced Usage

### Custom Task Dependencies

Tasks can depend on other tasks:

```json
{
  "targets": {
    "quality": {
      "dependsOn": ["lint", "typecheck"],
      "cache": true
    }
  }
}
```

When you run `nx quality frontend`, it automatically runs `lint` and `typecheck` first.

### Parallel Execution

Control parallelism:

```bash
# Default: 2 parallel tasks (configured in nx.json)
npx nx run-many --target=test --all

# Custom parallelism
npx nx run-many --target=test --all --parallel=4

# No parallelism
npx nx run-many --target=test --all --parallel=1
```

### Named Inputs

Nx tracks file changes to determine affected projects:

- `default` - All project files
- `production` - Exclude tests, configs, docs
- `sharedGlobals` - GitHub workflow files (affect all projects)

Configure in `nx.json` under `namedInputs`.

## Troubleshooting

### Cache issues

If you suspect cache is stale:

```bash
# Clear Nx cache
npx nx reset

# Skip cache for specific run
npx nx test frontend --skip-nx-cache
```

### "Project not found" errors

Ensure `project.json` exists in project directory:

```bash
ls -la src/frontend/project.json
ls -la src/backend/project.json
```

### Task execution errors

Run with verbose output:

```bash
npx nx test frontend --verbose
```

## Performance Benefits

Expected improvements:

### Local Development

- **Cache hits**: ~90% of repeated tasks (instant)
- **Affected tests**: 50-80% reduction in test time for small changes
- **Parallel execution**: 2x faster when running multiple targets

### CI/CD

- **PR builds**: 40-70% faster (only test affected code)
- **Cache sharing**: With Nx Cloud (optional), share cache across CI runs
- **Smart rebuilds**: Only rebuild changed projects

## Next Steps

1. **Try it locally**:
   ```bash
   npm run test:affected
   npm run graph
   ```

2. **Monitor CI**: Watch `nx-affected.yml` workflow in PRs

3. **Optimize further**: Consider Nx Cloud for distributed caching (optional)

4. **Migrate workflows**: Gradually update existing GitHub Actions workflows

## Resources

- [Nx Documentation](https://nx.dev)
- [Nx Affected Commands](https://nx.dev/concepts/affected)
- [Nx Caching](https://nx.dev/concepts/how-caching-works)
- [Nx Cloud](https://nx.app/) (optional - distributed caching)
