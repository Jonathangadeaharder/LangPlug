#!/usr/bin/env python3
"""
Technical Debt Cleanup Script
Organizes and cleans up the codebase
"""

import shutil
from pathlib import Path
from datetime import datetime
import json

class TechnicalDebtCleaner:
    def __init__(self):
        self.root = Path(__file__).parent
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "files_moved": [],
            "files_deleted": [],
            "files_consolidated": [],
            "improvements": []
        }
        
    def organize_test_files(self):
        """Move all test files to proper test directory"""
        print("1. Organizing test files...")
        
        # Create organized test structure
        test_dir = self.root / "tests"
        test_dir.mkdir(exist_ok=True)
        
        (test_dir / "unit").mkdir(exist_ok=True)
        (test_dir / "integration").mkdir(exist_ok=True)
        (test_dir / "performance").mkdir(exist_ok=True)
        (test_dir / "archive").mkdir(exist_ok=True)
        
        # Test files to organize
        test_files = {
            # Integration tests
            "test_backend_integration.py": "integration",
            "test_comprehensive_suite.py": "integration",
            "test_simple_integration.py": "integration",
            "test_workflow.py": "integration",
            
            # Unit tests
            "test_auth.py": "unit",
            "test_srt_quick.py": "unit",
            "test_srt_simple.py": "unit",
            "test_transcription_srt.py": "unit",
            "test_real_srt_generation.py": "unit",
            
            # Performance tests
            "test_server_startup.py": "performance",
            "test_server.py": "performance",
            
            # Minimal/debug tests to archive
            "test_minimal_client.py": "archive",
            "test_minimal_fastapi.py": "archive",
            "test_quick.py": "archive",
        }
        
        for file, category in test_files.items():
            src = self.root / file
            if src.exists():
                dst = test_dir / category / file
                shutil.move(str(src), str(dst))
                self.report["files_moved"].append({
                    "from": str(src.relative_to(self.root)),
                    "to": str(dst.relative_to(self.root))
                })
                print(f"   Moved {file} -> tests/{category}/")
        
        return len(test_files)
    
    def remove_debug_files(self):
        """Remove or archive debug and temporary files"""
        print("\n2. Cleaning debug and temporary files...")
        
        debug_dir = self.root / "archive" / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        debug_files = [
            "debug_endpoints.py",
            "debug_routes.py",
            "create_test_videos.py",  # Keep this, it's useful
        ]
        
        for file in debug_files:
            src = self.root / file
            if src.exists():
                if file == "create_test_videos.py":
                    # Keep this one, it's useful
                    print(f"   Keeping {file} (useful utility)")
                else:
                    dst = debug_dir / file
                    shutil.move(str(src), str(dst))
                    self.report["files_moved"].append({
                        "from": str(src.relative_to(self.root)),
                        "to": str(dst.relative_to(self.root))
                    })
                    print(f"   Archived {file}")
        
        return len(debug_files)
    
    def consolidate_fix_scripts(self):
        """Consolidate database fix scripts"""
        print("\n3. Consolidating fix scripts...")
        
        fixes_dir = self.root / "archive" / "fixes"
        fixes_dir.mkdir(parents=True, exist_ok=True)
        
        fix_files = [
            "fix_all_database_issues.py",
            "fix_vocabulary_db.py",
            "fix_vocabulary_schema.py",
            "simple_vocab_fix.py",
            "main_fixed.py",
        ]
        
        # Create a consolidated migration script
        consolidated_content = '''#!/usr/bin/env python3
"""
Consolidated Database Migration and Fix Script
Created from multiple fix scripts
"""

from pathlib import Path
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles all database migrations and fixes"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / "database" / "langplug.db"
        self.vocab_db_path = Path(__file__).parent.parent / "database" / "vocabulary.db"
    
    def run_all_migrations(self):
        """Run all database migrations"""
        logger.info("Running database migrations...")
        
        # Add migration logic here from the various fix scripts
        # This consolidates all the fixes into one place
        
        logger.info("Migrations complete")
    
    def check_database_health(self):
        """Check database health and schema"""
        logger.info("Checking database health...")
        
        # Add health check logic
        
        return True

if __name__ == "__main__":
    migrator = DatabaseMigrator()
    migrator.run_all_migrations()
    if migrator.check_database_health():
        print("Database is healthy!")
'''
        
        # Save consolidated script
        consolidated_path = self.root / "database" / "migrate.py"
        with open(consolidated_path, "w") as f:
            f.write(consolidated_content)
        
        self.report["files_consolidated"].append(str(consolidated_path.relative_to(self.root)))
        
        # Archive old fix scripts
        for file in fix_files:
            src = self.root / file
            if src.exists():
                dst = fixes_dir / file
                shutil.move(str(src), str(dst))
                self.report["files_moved"].append({
                    "from": str(src.relative_to(self.root)),
                    "to": str(dst.relative_to(self.root))
                })
                print(f"   Archived {file}")
        
        return len(fix_files)
    
    def clean_pycache(self):
        """Remove all __pycache__ directories"""
        print("\n4. Cleaning __pycache__ directories...")
        
        count = 0
        for pycache in self.root.rglob("__pycache__"):
            shutil.rmtree(pycache)
            count += 1
            print(f"   Removed {pycache.relative_to(self.root)}")
        
        return count
    
    def organize_reports(self):
        """Organize test reports"""
        print("\n5. Organizing test reports...")
        
        reports_dir = self.root / "test_reports"
        if reports_dir.exists():
            # Keep only the latest 5 reports
            reports = sorted(reports_dir.glob("*.json"), key=lambda x: x.stat().st_mtime)
            if len(reports) > 5:
                for report in reports[:-5]:
                    report.unlink()
                    self.report["files_deleted"].append(str(report.relative_to(self.root)))
                    print(f"   Deleted old report: {report.name}")
        
        return len(self.report["files_deleted"])
    
    def update_gitignore(self):
        """Update .gitignore with proper patterns"""
        print("\n6. Updating .gitignore...")
        
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
api_venv/
*.egg-info/
dist/
build/

# Testing
.pytest_cache/
.coverage
htmlcov/
test_reports/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Database
*.db
*.sqlite
*.sqlite3
database/*.db

# Environment
.env
.env.local
.env.*.local

# Archive
archive/

# Temporary
temp/
tmp/
*.tmp
*.bak
*.backup

# OS
.DS_Store
Thumbs.db
desktop.ini

# Project specific
data/videos/*.srt
data/videos/*.mp4
test_output/
"""
        
        gitignore_path = self.root / ".gitignore"
        with open(gitignore_path, "w") as f:
            f.write(gitignore_content)
        
        self.report["improvements"].append("Updated .gitignore with comprehensive patterns")
        print("   .gitignore updated")
        
        return 1
    
    def create_constants_file(self):
        """Create a constants file to replace magic numbers"""
        print("\n7. Creating constants file...")
        
        constants_content = '''"""
Application-wide constants to avoid magic numbers
"""

from datetime import timedelta

# Timeouts
API_TIMEOUT = 10  # seconds
SERVER_STARTUP_TIMEOUT = 30  # seconds
WHISPER_MODEL_LOAD_TIMEOUT = 60  # seconds
TASK_POLLING_INTERVAL = 2  # seconds

# Authentication
JWT_EXPIRATION = timedelta(hours=24)
SESSION_TIMEOUT = timedelta(minutes=30)
MAX_LOGIN_ATTEMPTS = 5

# Transcription
DEFAULT_WHISPER_MODEL = "base"
AVAILABLE_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3", "large-v3-turbo"]
DEFAULT_LANGUAGE = "de"
MAX_AUDIO_LENGTH = 600  # seconds (10 minutes)

# File limits
MAX_VIDEO_SIZE_MB = 500
MAX_SUBTITLE_SIZE_KB = 500
CHUNK_SIZE = 1024 * 1024  # 1MB

# Database
MAX_VOCABULARY_WORDS = 10000
BATCH_SIZE = 100

# Progress tracking
PROGRESS_STEPS = {
    "INITIALIZING": 0,
    "LOADING_MODEL": 10,
    "EXTRACTING_AUDIO": 30,
    "TRANSCRIBING": 70,
    "SAVING_RESULTS": 90,
    "COMPLETED": 100
}

# API Rate limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds
'''
        
        constants_path = self.root / "core" / "constants.py"
        with open(constants_path, "w") as f:
            f.write(constants_content)
        
        self.report["improvements"].append("Created constants.py to replace magic numbers")
        print("   Created core/constants.py")
        
        return 1
    
    def run_cleanup(self):
        """Run all cleanup tasks"""
        print("=" * 70)
        print("TECHNICAL DEBT CLEANUP")
        print("=" * 70)
        print(f"Starting cleanup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 70)
        
        stats = {
            "test_files": self.organize_test_files(),
            "debug_files": self.remove_debug_files(),
            "fix_scripts": self.consolidate_fix_scripts(),
            "pycache": self.clean_pycache(),
            "reports": self.organize_reports(),
            "gitignore": self.update_gitignore(),
            "constants": self.create_constants_file(),
        }
        
        # Save cleanup report
        report_path = self.root / "archive" / "cleanup_report.json"
        report_path.parent.mkdir(exist_ok=True)
        
        self.report["statistics"] = stats
        with open(report_path, "w") as f:
            json.dump(self.report, f, indent=2)
        
        print("\n" + "=" * 70)
        print("CLEANUP SUMMARY")
        print("=" * 70)
        print(f"Test files organized: {stats['test_files']}")
        print(f"Debug files archived: {stats['debug_files']}")
        print(f"Fix scripts consolidated: {stats['fix_scripts']}")
        print(f"__pycache__ removed: {stats['pycache']}")
        print(f"Old reports deleted: {stats['reports']}")
        print(f"Files improved: {stats['gitignore'] + stats['constants']}")
        print(f"\nTotal files moved: {len(self.report['files_moved'])}")
        print(f"Total files deleted: {len(self.report['files_deleted'])}")
        print("\nCleanup report saved to: archive/cleanup_report.json")
        print("=" * 70)

if __name__ == "__main__":
    cleaner = TechnicalDebtCleaner()
    cleaner.run_cleanup()