import logging

logger = logging.getLogger(__name__)

"""
Virtual Environment Auto-Detection Utility
Ensures Python scripts automatically use the correct virtual environment
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def ensure_venv() -> bool:
    """
    Automatically detect and switch to the project's api_venv virtual environment.
    This function should be called at the top of main Python files.
    """
    # Find project root (where api_venv should be located)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent  # Backend/../ = project root

    # Look for api_venv in multiple locations (prioritize Backend location)
    search_paths = [
        current_file.parent / "api_venv",  # Backend/api_venv (priority)
        project_root / "api_venv",  # Project root (fallback)
    ]

    venv_path = None
    python_path = None

    for search_path in search_paths:
        if search_path.exists():
            # Check for Python executable based on OS
            if os.name == "nt":  # Windows
                potential_pythons = [
                    search_path / "Scripts" / "python.exe",
                    search_path / "Scripts" / "python3.exe",
                ]
            else:  # Unix-like
                potential_pythons = [
                    search_path / "bin" / "python",
                    search_path / "bin" / "python3",
                ]

            for potential_python in potential_pythons:
                try:
                    if potential_python.exists() and potential_python.is_file():
                        venv_path = search_path
                        python_path = potential_python
                        break
                except (OSError, PermissionError):
                    # Skip if we can't access the file
                    continue

            if venv_path:
                break

    if not venv_path or not python_path:
        print("Warning: Could not find api_venv virtual environment", file=sys.stderr)
        print("Searched in:", file=sys.stderr)
        for path in search_paths:
            print(f"  - {path}", file=sys.stderr)
        return False

    # Check if we're already using the correct Python
    current_python = Path(sys.executable).resolve()
    target_python = python_path.resolve()

    if current_python == target_python:
        # Already using correct virtual environment, just set env vars
        scripts_dir = venv_path / ("Scripts" if os.name == "nt" else "bin")
        os.environ["VIRTUAL_ENV"] = str(venv_path)
        if str(scripts_dir) not in os.environ.get("PATH", ""):
            os.environ["PATH"] = (
                f"{scripts_dir}{os.pathsep}{os.environ.get('PATH', '')}"
            )
        return True

    # Setup environment variables before re-execution
    scripts_dir = venv_path / ("Scripts" if os.name == "nt" else "bin")
    os.environ["VIRTUAL_ENV"] = str(venv_path)
    os.environ["PATH"] = f"{scripts_dir}{os.pathsep}{os.environ.get('PATH', '')}"

    # Re-execute with correct Python
    logger.info(f"Switching to virtual environment: {venv_path}")
    logger.info(f"Using Python: {python_path}")

    try:
        os.execv(str(python_path), [str(python_path)] + sys.argv)
    except Exception as e:
        print(f"Error switching to virtual environment: {e}", file=sys.stderr)
        return False


def get_venv_info() -> Optional[Dict[str, Any]]:
    """
    Get information about the current virtual environment.
    Returns dict with venv details or None if not in a venv.
    """
    venv_path = os.environ.get("VIRTUAL_ENV")
    if not venv_path:
        return None

    return {
        "venv_path": venv_path,
        "python_executable": sys.executable,
        "python_version": sys.version,
        "is_venv_active": True,
    }


def print_venv_status() -> None:
    """Print current virtual environment status for debugging."""
    info = get_venv_info()

    if info:
        logger.info(f"[OK] Virtual environment active: {info['venv_path']}")
        logger.info(f"[OK] Python executable: {info['python_executable']}")
        logger.info(f"[OK] Python version: {info['python_version'].split()[0]}")
    else:
        logger.info("[WARN] No virtual environment detected")
        logger.info(f"  Current Python: {sys.executable}")


if __name__ == "__main__":
    # Test the utility
    logger.info("Virtual Environment Detection Test")
    print("=" * 40)

    logger.info("\nBefore ensure_venv():")
    print_venv_status()

    logger.info("\nRunning ensure_venv()...")
    success = ensure_venv()

    if success:
        logger.info("\nAfter ensure_venv():")
        print_venv_status()
    else:
        logger.info("Failed to setup virtual environment")
