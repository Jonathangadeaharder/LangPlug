#!/usr/bin/env python3
"""
Pre-commit hook integration for quality gates
Automatically runs quality checks before commits
"""

import subprocess
import sys
from pathlib import Path


def run_quality_gates():
    """Run quality gates and return success status"""
    try:
        # Get the project root (Backend directory)
        script_path = Path(__file__).resolve()
        backend_root = script_path.parent.parent.parent

        # Run quality gates
        result = subprocess.run(
            [sys.executable, str(backend_root / "tests" / "monitoring" / "quality_gates.py")],
            check=False,
            cwd=backend_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("[SUCCESS] Quality gates passed - commit allowed")
            return True
        else:
            print("[BLOCKED] Quality gates failed - commit blocked")
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return False

    except Exception as e:
        print(f"[ERROR] Failed to run quality gates: {e}")
        print("[WARNING] Allowing commit due to quality gate execution error")
        return True  # Allow commit on error to avoid blocking development


def install_git_hook():
    """Install this script as a Git pre-commit hook"""
    try:
        # Find Git hooks directory
        git_root = subprocess.check_output(["git", "rev-parse", "--git-dir"], text=True).strip()
        hooks_dir = Path(git_root) / "hooks"
        hook_file = hooks_dir / "pre-commit"

        # Create hook script content
        hook_content = """#!/bin/bash
# Auto-generated pre-commit hook for quality gates
cd "$(git rev-parse --show-toplevel)/Backend"
python tests/monitoring/pre_commit_hook.py
"""

        # Write hook file
        with open(hook_file, "w") as f:
            f.write(hook_content)

        # Make executable (on Unix systems)
        try:
            hook_file.chmod(0o755)
        except AttributeError:
            pass  # Windows doesn't have chmod

        print(f"[INFO] Git pre-commit hook installed at {hook_file}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to install Git hook: {e}")
        return False


def main():
    """Main pre-commit hook function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        # Install mode
        success = install_git_hook()
        sys.exit(0 if success else 1)
    else:
        # Hook execution mode
        success = run_quality_gates()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
