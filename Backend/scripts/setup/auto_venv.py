# One-liner virtual environment activator for LangPlug Backend
# Usage: Add this line at the top of any Python file that needs the backend environment:
# import auto_venv

from __future__ import annotations

import os
import sys
from pathlib import Path


def _candidate_venv_dirs(backend_dir: Path) -> list[Path]:
    """Return potential virtual environment directories to probe."""

    return [
        backend_dir / "venv",
        backend_dir / "env",
        backend_dir / ".venv",
        backend_dir.parent / "venv",
        backend_dir.parent / "env",
        backend_dir.parent / ".venv",
    ]


def _python_path_from_venv(venv_dir: Path) -> Path | None:
    """Locate the Python executable for the given virtual environment."""

    if os.name == "nt":
        candidate = venv_dir / "Scripts" / "python.exe"
    else:
        candidate = venv_dir / "bin" / "python"

    return candidate if candidate.exists() else None


def _activate_backend_venv() -> None:
    """Exec into the backend virtual environment if not already active."""

    if "VIRTUAL_ENV" in os.environ:
        return

    backend_dir = Path(__file__).parent
    for venv_dir in _candidate_venv_dirs(backend_dir):
        python_path = _python_path_from_venv(venv_dir)
        if python_path:
            os.execv(str(python_path), [str(python_path), *sys.argv])  # noqa: S606
            return


_activate_backend_venv()
