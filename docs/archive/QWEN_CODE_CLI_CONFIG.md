# DEPRECATED: Qwen Code CLI Configuration Guide

**⚠️ DEPRECATION NOTICE**: This file has been consolidated into the unified AI Development Guide.

**👉 Use instead**: `AI_DEVELOPMENT_GUIDE.md` - Comprehensive guide for all AI coding assistants

---

# Original: Qwen Code CLI Configuration Guide

This document explains the directory exclusion configuration for Qwen Code CLI in the LangPlug project.

## Overview

Qwen Code CLI has been configured to ignore specific directories and file types to improve search performance and focus on relevant code files. The configuration uses a combination of:

1. **Project-specific settings** in `.qwen/settings.json`
2. **Git ignore patterns** via `respectGitIgnore: true`
3. **Enhanced .gitignore patterns** for comprehensive exclusion

## Configuration Files

### 1. Qwen Code CLI Settings (`.qwen/settings.json`)

The main configuration file includes:

#### File Filtering Options:
- `respectGitIgnore: true` - Honors all patterns in .gitignore files
- `enableRecursiveFileSearch: true` - Enables deep directory traversal
- `excludePatterns` - Explicit patterns to exclude
- `includePatterns` - File types to include in searches

#### Key Excluded Directories:
- **Dependencies**: `node_modules`, `venv`, `env`, virtual environments
- **Build outputs**: `dist`, `build`, `out`, `.next`, `.nuxt`
- **Cache directories**: `.cache`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`
- **IDE files**: `.idea`, `.vscode`, editor-specific files
- **Logs and temporary**: `logs`, `tmp`, `temp`, `cache`
- **Media files**: Video files (`.mp4`, `.avi`, etc.), archives
- **Database files**: `.db`, `.sqlite`, `.sqlite3` and related files
- **Backup files**: `.backup`, `.bak`, `.old`, backup directories

#### Included File Types:
- Source code: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`
- Configuration: `.json`, `.yml`, `.yaml`, `.toml`, `.ini`
- Documentation: `.md`, `.txt`
- Web files: `.html`, `.css`, `.scss`
- Package files: `package.json`, `requirements.txt`, etc.

### 2. Enhanced .gitignore Patterns

Additional patterns added to `.gitignore`:

```gitignore
# Qwen Code CLI
.qwen/cache/
.qwen/logs/
.qwen/temp/

# Additional development tools
.swc/
.turbo/
.rush/
.pnp.*
.yarn/

# IDE and editor specific
*.sublime-*
.vscode/settings.json
.vscode/tasks.json
.vscode/launch.json
.vscode/extensions.json
.history/

# Package managers
pnpm-lock.yaml
bun.lockb

# Build tools
.parcel-cache/
.rollup.cache/
.rts2_cache*/
.rpt2_cache*/

# Testing
.jest/
.vitest/
test-results/
playwright-report/
blob-report/
playwright/.cache/
```

## Project-Specific Exclusions

Based on the LangPlug project structure analysis, the following directories are specifically excluded:

### Backend Directory:
- `Backend/venv/` - Python virtual environment
- `Backend/data/*.db*` - Database files and WAL files
- `Backend/videos/` - Video content directory
- `Backend/__pycache__/` - Python bytecode cache
- `Backend/.pytest_cache/` - Pytest cache

### Frontend Directory:
- `Frontend/node_modules/` - Node.js dependencies (if present)
- `Frontend/dist/` - Build output
- Build tool caches

### Root Level:
- `videos/` - Video content directory
- `.claude/` - Claude AI configuration
- Various log and temporary files

## Performance Optimizations

The configuration includes performance settings:

```json
{
  "performance": {
    "enableCaching": true,
    "cacheTimeout": 300,
    "maxConcurrentOperations": 4
  },
  "codeAnalysis": {
    "enableSemanticSearch": true,
    "indexingDepth": 3,
    "respectFileSize": true,
    "maxFileSize": "1MB"
  }
}
```

## Testing the Configuration

To verify the configuration is working:

### 1. Check Qwen Code CLI Recognition
```bash
# Navigate to project root
cd c:\Users\Jonandrop\IdeaProjects\LangPlug

# Verify Qwen Code CLI recognizes the configuration
qwen --help
```

### 2. Test Search Exclusions
```bash
# These searches should NOT return results from excluded directories:
qwen search "import" --include-pattern="*.py"
# Should not show results from venv/, __pycache__/, etc.

qwen search "node_modules" 
# Should not find actual node_modules directories in search results

qwen search "*.db"
# Should not return database files from Backend/data/
```

### 3. Test Search Inclusions
```bash
# These searches should work normally:
qwen search "FastAPI" --include-pattern="*.py"
# Should find FastAPI imports in Backend source files

qwen search "React" --include-pattern="*.tsx"
# Should find React components in Frontend/src/

qwen search "export" --include-pattern="*.ts"
# Should find TypeScript exports
```

### 4. Verify File Filtering
```bash
# List files that Qwen Code CLI will index:
qwen list-files
# Should exclude all patterns defined in settings.json
```

## Configuration Hierarchy

Qwen Code CLI uses this configuration priority order:
1. Command-line arguments (highest priority)
2. Environment variables
3. **Project settings** (`.qwen/settings.json`) ← Our configuration
4. User settings (`~/.qwen/settings.json`)
5. System settings
6. Default settings (lowest priority)

## Troubleshooting

### If exclusions aren't working:
1. Verify `.qwen/settings.json` syntax is valid JSON
2. Check that `respectGitIgnore` is set to `true`
3. Ensure `.gitignore` patterns are correctly formatted
4. Try clearing Qwen Code CLI cache: `qwen clear-cache`

### If searches are too slow:
1. Add more specific `excludePatterns`
2. Reduce `indexingDepth` in `codeAnalysis`
3. Lower `maxFileSize` limit
4. Increase `cacheTimeout` for better caching

### If important files are excluded:
1. Add specific patterns to `includePatterns`
2. Use more specific `excludePatterns` instead of broad wildcards
3. Check `.gitignore` for overly broad patterns

## Maintenance

Regularly review and update:
1. **New dependencies**: Add new package manager directories
2. **Build tools**: Add new build output directories
3. **IDE changes**: Update IDE-specific exclusions
4. **Project growth**: Adjust performance settings as needed

The configuration is designed to be comprehensive yet maintainable, focusing on excluding non-source files while preserving all relevant code and configuration files for effective code search and analysis.