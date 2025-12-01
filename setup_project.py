#!/usr/bin/env python3
"""
Unified cross-platform setup script for LangPlug project.
Replaces separate PowerShell and Bash setup scripts.

Usage:
    python setup.py [--full] [--frontend] [--backend] [--dev] [--checks]

    --full      Install all dependencies including ML/heavy requirements
    --frontend  Setup frontend only
    --backend   Setup backend only (default if no specific target)
    --dev       Install development dependencies
    --checks    Run code quality checks (linting, formatting, tests)
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for cross-platform colored output."""

    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

    @classmethod
    def info(cls, msg):
        print(f"{cls.CYAN}[setup] {msg}{cls.RESET}")

    @classmethod
    def success(cls, msg):
        print(f"{cls.GREEN}[setup] {msg}{cls.RESET}")

    @classmethod
    def warning(cls, msg):
        print(f"{cls.YELLOW}[setup] {msg}{cls.RESET}")

    @classmethod
    def error(cls, msg):
        print(f"{cls.RED}[setup] {msg}{cls.RESET}")


class SetupManager:
    def __init__(self):
        self.repo_root = Path(__file__).parent
        self.backend_dir = self.repo_root / "src" / "backend"
        self.frontend_dir = self.repo_root / "src" / "frontend"
        self.is_windows = platform.system() == "Windows"

        # Virtual environment paths (in repo root)
        self.venv_dir = self.repo_root / "api_venv"
        if self.is_windows:
            self.python_exe = self.venv_dir / "Scripts" / "python.exe"
            self.activate_script = self.venv_dir / "Scripts" / "Activate.ps1"
        else:
            self.python_exe = self.venv_dir / "bin" / "python"
            self.activate_script = self.venv_dir / "bin" / "activate"

    def run_command(self, cmd, cwd=None, check=True):
        """Run a command and handle errors gracefully."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.repo_root,
                check=check,
                capture_output=True,
                text=True,
            )
            return result
        except subprocess.CalledProcessError as e:
            Colors.error(f"Command failed: {' '.join(cmd)}")
            Colors.error(f"Error: {e.stderr}")
            sys.exit(1)

    def setup_backend_venv(self):
        """Create and setup Python virtual environment for backend."""
        if not self.venv_dir.exists():
            Colors.info(f"Creating virtual environment at {self.venv_dir}")
            # Use the current python executable to create the venv
            self.run_command([sys.executable, "-m", "venv", str(self.venv_dir)])
        else:
            Colors.info(f"Using existing virtual environment: {self.venv_dir}")

        # Upgrade pip and wheel
        Colors.info("Upgrading pip and wheel")
        self.run_command(
            [str(self.python_exe), "-m", "pip", "install", "-U", "pip", "wheel"]
        )

    def install_backend_deps(self, full=False, dev=False):
        """Install backend Python dependencies."""
        requirements_files = []

        # Base requirements
        base_req = self.backend_dir / "requirements.txt"
        if base_req.exists():
            requirements_files.append(base_req)

        # Development requirements
        if dev:
            dev_req = self.backend_dir / "requirements-dev.txt"
            if dev_req.exists():
                requirements_files.append(dev_req)

        # ML/Heavy requirements
        if full:
            ml_req = self.backend_dir / "requirements-ml.txt"
            if ml_req.exists():
                requirements_files.append(ml_req)

        for req_file in requirements_files:
            Colors.info(f"Installing requirements from {req_file.name}")
            self.run_command(
                [str(self.python_exe), "-m", "pip", "install", "-r", str(req_file)]
            )

    def setup_frontend(self):
        """Setup frontend dependencies using npm/yarn."""
        if not self.frontend_dir.exists():
            Colors.warning("Frontend directory not found, skipping frontend setup")
            return

        Colors.info("Setting up frontend dependencies")

        # Check if yarn.lock exists, prefer yarn over npm
        if (self.frontend_dir / "yarn.lock").exists():
            Colors.info("Using Yarn for frontend dependencies")
            self.run_command(["yarn", "install"], cwd=self.frontend_dir)
        elif (self.frontend_dir / "package-lock.json").exists() or (
            self.frontend_dir / "package.json"
        ).exists():
            Colors.info("Using npm for frontend dependencies")
            self.run_command(["npm", "install"], cwd=self.frontend_dir)
        else:
            Colors.warning("No package.json found in frontend directory")

    def run_code_checks(self):
        """Run code quality checks (linting, formatting, tests)."""
        Colors.info("Running code quality checks")

        # Change to backend directory for checks
        os.chdir(self.backend_dir)

        try:
            Colors.info("Running Ruff linter...")
            self.run_command([str(self.python_exe), "-m", "ruff", "check", "."])

            Colors.info("Running Ruff formatter...")
            self.run_command([str(self.python_exe), "-m", "ruff", "format", "."])

            Colors.info("Running tests...")
            self.run_command(
                [
                    str(self.python_exe),
                    "-m",
                    "pytest",
                    "-q",
                    "-m",
                    "not slow and not performance",
                ]
            )

            Colors.success("All code quality checks passed!")
        except Exception as e:
            Colors.error(f"Code quality checks failed: {e}")
            sys.exit(1)

    def print_usage_info(self):
        """Print usage information after successful setup."""
        Colors.success("Setup completed successfully!")
        print()
        Colors.info("To activate the virtual environment:")
        if self.is_windows:
            print(f"  {self.activate_script}")
        else:
            print(f"  source {self.activate_script}")
        print()
        Colors.info("To run tests:")
        print(f"  cd {self.backend_dir}")
        print(f"  {self.python_exe} -m pytest -q -m 'not slow and not performance'")
        print()
        Colors.info("To start the backend server:")
        print(f"  cd {self.backend_dir}")
        print(
            f"  {self.python_exe} -m uvicorn core.app:app --host 0.0.0.0 --port 8000 --reload"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Unified setup script for LangPlug project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Install all dependencies including ML/heavy requirements",
    )
    parser.add_argument("--frontend", action="store_true", help="Setup frontend only")
    parser.add_argument("--backend", action="store_true", help="Setup backend only")
    parser.add_argument(
        "--dev", action="store_true", help="Install development dependencies"
    )
    parser.add_argument(
        "--checks",
        action="store_true",
        help="Run code quality checks (linting, formatting, tests)",
    )

    args = parser.parse_args()

    setup = SetupManager()

    # If no specific target is specified, default to backend
    if not any([args.frontend, args.backend, args.checks]):
        args.backend = True

    try:
        if args.backend or args.full or args.dev:
            Colors.info("Setting up backend environment")
            setup.setup_backend_venv()
            setup.install_backend_deps(full=args.full, dev=args.dev)

        if args.frontend:
            Colors.info("Setting up frontend environment")
            setup.setup_frontend()

        if args.checks:
            setup.run_code_checks()

        if not args.checks:  # Don't show usage info after running checks
            setup.print_usage_info()

    except KeyboardInterrupt:
        Colors.warning("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        Colors.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
