# Quick Reference: Project Cleanup

**See [CODE_SIMPLIFICATION_ROADMAP.md](CODE_SIMPLIFICATION_ROADMAP.md) for comprehensive details**

---

## ⚡ Quick Start (1 Hour)

### Option 1: Run Automated Script

```bash
cd /mnt/c/Users/Jonandrop/IdeaProjects/LangPlug
bash scripts/cleanup_project.sh
```

**Result**: 150MB freed, .gitignore updated

### Option 2: Manual Cleanup Commands

```bash
# Delete cache directories (135MB)
rm -rf Backend/.mypy_cache Backend/.pytest_cache Backend/.ruff_cache Backend/.benchmarks Backend/htmlcov Backend/logs
rm -rf .mypy_cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Delete log files (13MB)
rm -f repomix_output.txt Frontend/frontend.log Backend/backend.log Backend/test_output.txt

# Delete duplicate coverage reports (2MB)
rm -f Backend/coverage*.json Backend/bandit_report.json

# Delete test artifacts
rm -f Backend/test*.srt Backend/*.backup commit_message.txt server_state.json
rm -rf Frontend/playwright-report Frontend/test-results

# Verify
git status
```

---

## 🔴 Critical Issues to Fix

### 1. Version Suffix Violation

```bash
# Location: Backend/services/vocabulary/vocabulary_service_new.py
# Action: Rename to vocabulary_service.py
cd Backend/services/vocabulary
git mv vocabulary_service_new.py vocabulary_service.py

# Update imports
grep -r "vocabulary_service_new" Backend/
# Manually update each import
```

### 2. Duplicate Logging (2 implementations)

```bash
# Keep: Backend/services/logging/ (6 files, more complete)
# Delete: Backend/services/loggingservice/ (2 files)
rm -rf Backend/services/loggingservice/

# Update imports
grep -r "from services.loggingservice" Backend/
# Change to: from services.logging
```

### 3. Duplicate Repositories (2 locations)

```bash
# Keep: Backend/database/repositories/ (13 files, canonical)
# Delete: Backend/services/repository/ (3 files)
rm -rf Backend/services/repository/

# Update imports
grep -r "from services.repository" Backend/
# Change to: from database.repositories
```

---

## 📊 Current State Summary

| Issue                     | Count | Disk Usage |
| ------------------------- | ----- | ---------- |
| Cache directories         | 7     | 135MB      |
| Log/output files          | 4     | 13MB       |
| Coverage reports          | 7     | 2MB        |
| Documentation files       | 88    | -          |
| Version suffix files      | 1+    | -          |
| UUID data directories     | 27    | -          |
| Scripts in Backend root   | 22    | -          |
| Duplicate implementations | 4     | -          |

---

## 🎯 Top 10 Priority Tasks

1. ✅ Delete cache directories → **135MB freed**
2. ✅ Delete log files → **13MB freed**
3. ✅ Delete duplicate coverage reports → **2MB freed**
4. ✅ Update .gitignore → Prevents re-accumulation
5. ❌ Rename vocabulary_service_new.py → Fixes CLAUDE.md violation
6. ❌ Consolidate logging implementations → Single source of truth
7. ❌ Consolidate repositories → Single source of truth
8. ❌ Move 22 scripts from Backend root → Cleaner structure
9. ❌ Delete 27 UUID directories in data/ → Cleaner data dir
10. ❌ Consolidate 88 docs → 20 docs → Easier navigation

---

## 📁 File Organization Target

**Backend Root (After)**:

```
Backend/
├── main.py              # FastAPI entry point
├── run_backend.py       # Main launcher
├── setup.py             # Standard Python file
├── pyproject.toml       # Project config
├── requirements.txt     # Dependencies
├── alembic.ini          # DB migrations
├── Dockerfile           # Container
├── Makefile             # Build commands
├── README.md            # Documentation
└── ... (config files only)
```

**Scripts (After)**:

```
Backend/scripts/
├── analysis/            # analyze_coverage.py, metrics_report.py
├── database/            # apply_schema.py, apply_search_indexes.py
├── setup/               # download_parakeet_model.py, install_spacy_models.py
├── utils/               # cleanup_port.py, export_openapi.py
└── debug/               # verify_admin_login.py, check_users.py
```

---

## ✅ Verification Commands

After cleanup, verify success:

```bash
# Check freed space
du -sh Backend/.mypy_cache Backend/htmlcov Backend/logs
# Should error: "No such file or directory"

# Count remaining cache
find . -type d -name __pycache__ | wc -l
# Should be 0 or very few (venv only)

# Check git status
git status
# Should show only deletions, no new untracked files

# Verify no version suffixes
find Backend -name "*_new.*" -o -name "*_old.*" -o -name "*_v2.*"
# Should return empty after fix

# Check for duplicate implementations
ls -la Backend/services/logging* Backend/services/repository Backend/database/repositories
# Should show only one of each
```

---

## 🚨 What NOT to Delete

**Keep these**:

- `api_venv/` - Virtual environment (in .gitignore)
- `.git/` - Git repository
- `.github/` - GitHub workflows
- `node_modules/` - Node packages (in .gitignore)
- `data/*.csv` - Actual vocabulary data
- `.env.testing` - Test environment config
- `.coveragerc` - Coverage config
- Translation/Transcription interfaces - Legitimate polymorphism

---

## 📚 Next Steps After Cleanup

1. **Review changes**: `git status` and `git diff`
2. **Run tests**: Ensure nothing broke
3. **Commit cleanup**: `git add . && git commit -m "chore: clean up cache and temporary files"`
4. **Move to Phase 1**: Fix critical code violations
5. **Continue roadmap**: Follow CODE_SIMPLIFICATION_ROADMAP.md

---

**Quick Links**:

- Full Roadmap: [CODE_SIMPLIFICATION_ROADMAP.md](CODE_SIMPLIFICATION_ROADMAP.md)
- Existing Roadmap: [REFACTORING_ROADMAP.md](REFACTORING_ROADMAP.md)
- Coding Standards: [CLAUDE.md](CLAUDE.md)

**Total Effort**: 240 tasks, 145-186 hours
**Immediate Impact**: 150MB freed in <2 hours
**Test Impact**: 89 test quality tasks, 92-116 hours

**Note**: Half of total effort is improving test architecture (pyramid, mocks, E2E)
