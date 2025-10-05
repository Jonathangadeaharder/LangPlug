#!/bin/bash

# LangPlug Project Cleanup Script
# Removes cache files, logs, test artifacts, and temporary files
# See CODE_SIMPLIFICATION_ROADMAP.md for details

set -e  # Exit on error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "========================================="
echo "LangPlug Project Cleanup Script"
echo "========================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo ""

# Function to safely delete directory
delete_dir() {
    local dir=$1
    if [ -d "$dir" ]; then
        echo "Deleting: $dir"
        rm -rf "$dir"
        echo "  ✓ Deleted"
    else
        echo "  ⊗ Not found: $dir"
    fi
}

# Function to safely delete file
delete_file() {
    local file=$1
    if [ -f "$file" ]; then
        echo "Deleting: $file"
        rm -f "$file"
        echo "  ✓ Deleted"
    else
        echo "  ⊗ Not found: $file"
    fi
}

echo "========================================="
echo "Phase 1: Delete Cache Directories"
echo "========================================="
echo ""

# Python cache
delete_dir "Backend/.mypy_cache"
delete_dir ".mypy_cache"
delete_dir "Backend/.pytest_cache"
delete_dir "Backend/.ruff_cache"
delete_dir "Backend/.benchmarks"

# Find and delete __pycache__ directories
echo ""
echo "Deleting all __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "  ✓ Done"

echo ""
echo "========================================="
echo "Phase 2: Delete Coverage Reports"
echo "========================================="
echo ""

delete_dir "Backend/htmlcov"
delete_file "Backend/coverage.json"
delete_file "Backend/coverage_final.json"
delete_file "Backend/coverage_new.json"
delete_file "Backend/bandit_report.json"

# Delete old coverage snapshots
echo ""
echo "Deleting old coverage snapshots..."
find Backend/tests/reports -name "coverage_snapshot_*.json" -delete 2>/dev/null || true
echo "  ✓ Done"

echo ""
echo "========================================="
echo "Phase 3: Delete Log Files"
echo "========================================="
echo ""

delete_dir "Backend/logs"
delete_file "Backend/backend.log"
delete_file "Backend/test_output.txt"
delete_file "Frontend/frontend.log"
delete_file "repomix_output.txt"

echo ""
echo "========================================="
echo "Phase 4: Delete Test Artifacts"
echo "========================================="
echo ""

delete_file "Backend/test.srt"
delete_file "Backend/test_chunk.srt"
delete_file "Backend/.env.backup"
delete_file "Backend/pytest.ini.backup"
delete_file "Backend/simulate_ci.py"
delete_dir "Frontend/playwright-report"
delete_dir "Frontend/test-results"
delete_file "commit_message.txt"
delete_file "server_state.json"

echo ""
echo "========================================="
echo "Phase 5: Verify .gitignore"
echo "========================================="
echo ""

echo "Checking .gitignore for required patterns..."

GITIGNORE_FILE=".gitignore"
PATTERNS_TO_ADD=(
    ".mypy_cache/"
    ".ruff_cache/"
    ".benchmarks/"
    "htmlcov/"
    "coverage*.json"
    "*_report.json"
    "*_snapshot_*.json"
    "*.backup"
    "*.bak"
    "test-results/"
    "playwright-report/"
    "server_state.json"
)

MISSING_PATTERNS=()
for pattern in "${PATTERNS_TO_ADD[@]}"; do
    if ! grep -q "$pattern" "$GITIGNORE_FILE" 2>/dev/null; then
        MISSING_PATTERNS+=("$pattern")
    fi
done

if [ ${#MISSING_PATTERNS[@]} -eq 0 ]; then
    echo "  ✓ All patterns already in .gitignore"
else
    echo "  ⚠ Missing patterns detected:"
    for pattern in "${MISSING_PATTERNS[@]}"; do
        echo "    - $pattern"
    done
    echo ""
    echo "  Adding missing patterns to .gitignore..."
    echo "" >> "$GITIGNORE_FILE"
    echo "# Added by cleanup script $(date +%Y-%m-%d)" >> "$GITIGNORE_FILE"
    for pattern in "${MISSING_PATTERNS[@]}"; do
        echo "$pattern" >> "$GITIGNORE_FILE"
    done
    echo "  ✓ Updated .gitignore"
fi

echo ""
echo "========================================="
echo "Cleanup Complete!"
echo "========================================="
echo ""

# Calculate freed space (approximate)
echo "Summary:"
echo "  ✓ Cache directories removed"
echo "  ✓ Log files deleted"
echo "  ✓ Coverage reports cleaned"
echo "  ✓ Test artifacts removed"
echo "  ✓ .gitignore updated"
echo ""
echo "Estimated disk space freed: ~150MB+"
echo ""
echo "Next steps:"
echo "  1. Run: git status"
echo "  2. Review changes"
echo "  3. If satisfied, commit: git add . && git commit -m 'chore: clean up cache and temporary files'"
echo ""
echo "For more cleanup tasks, see: CODE_SIMPLIFICATION_ROADMAP.md"
echo ""
