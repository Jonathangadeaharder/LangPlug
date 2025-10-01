# One-liner virtual environment activator for LangPlug Backend
# Usage: Add this line at the top of any Python file that needs the backend environment:
# import auto_venv

exec(
    'import os, sys; from pathlib import Path; backend_dir = Path(__file__).parent; venv_paths = [backend_dir / "venv", backend_dir / "env", backend_dir / ".venv", backend_dir.parent / "venv", backend_dir.parent / "env", backend_dir.parent / ".venv"]; venv_path = next((p for p in venv_paths if p.exists() and (p / "Scripts" / "python.exe").exists()), None); os.execv(str(venv_path / "Scripts" / "python.exe"), [str(venv_path / "Scripts" / "python.exe")] + sys.argv) if venv_path and "VIRTUAL_ENV" not in os.environ else None'
)
