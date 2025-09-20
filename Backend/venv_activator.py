#!/usr/bin/env python3
"""
Virtual Environment Auto-Activator for LangPlug Backend

This module automatically activates the backend virtual environment if not already active.
Usage: Import this module at the top of any Python file that needs the backend environment.

Example:
    from venv_activator import activate_venv
    activate_venv()
    
    # Or as a one-liner:
    import venv_activator; venv_activator.activate_venv()
"""

import os
import sys
from pathlib import Path


def _detect_wsl() -> bool:
    try:
        if os.environ.get('WSL_DISTRO_NAME'):
            return True
        with open('/proc/version', encoding='utf-8') as f:
            return 'Microsoft' in f.read()
    except Exception:
        return False


def activate_venv():
    """Activate a backend virtualenv suitable for the current platform.

    - Windows: prefer `api_venv` or `.venv-win`
    - Linux/macOS: prefer `.venv-unix`; on WSL: `.venv-wsl`
    - Avoid activating Windows venvs on Unix to prevent binary incompatibilities.

    Set AUTO_CREATE_VENV=1 to auto-create a local venv if none is found.
    """
    backend_dir = Path(__file__).parent
    is_windows = sys.platform.startswith('win') or os.name == 'nt'
    is_wsl = (not is_windows) and _detect_wsl()

    # If already inside a venv, do not override (unless it's obviously wrong platform)
    current_python = Path(sys.executable)
    if is_windows and ('api_venv' in str(current_python) or '.venv-win' in str(current_python)):
        return

    # Candidates by platform
    if is_windows:
        candidates = [
            backend_dir / 'api_venv',
            backend_dir / '.venv-win',
            backend_dir / 'venv',
            backend_dir / 'env',
        ]
        valid = lambda p: (p / 'Scripts' / 'python.exe').exists()
    else:
        env_name = '.venv-wsl' if is_wsl else '.venv-unix'
        candidates = [
            backend_dir / env_name,
            backend_dir / '.venv',
            backend_dir / 'venv',
            backend_dir / 'env',
        ]
        valid = lambda p: (p / 'bin' / 'python').exists()

    venv_path = None
    for path in candidates:
        if path.exists() and valid(path):
            venv_path = path
            break

    if not venv_path and os.environ.get('AUTO_CREATE_VENV') == '1':
        # Create a minimal venv for this platform using system Python
        try:
            import subprocess
            # Use Python 3.11 instead of current_python which might be broken
            python_exe = r"C:\Users\jogah\AppData\Local\Programs\Python311\python.exe"
            if not Path(python_exe).exists():
                # Try to find Python in common locations
                common_python_paths = [
                    r"C:\Python311\python.exe",
                    r"C:\Program Files\Python311\python.exe",
                    r"C:\Program Files (x86)\Python311\python.exe",
                    r"C:\Users\Jonandrop\AppData\Local\Programs\Python\Python311\python.exe"
                ]
                for path in common_python_paths:
                    if Path(path).exists():
                        python_exe = path
                        break
                else:
                    # If we can't find a specific Python 3.11, try using the current Python
                    python_exe = sys.executable
            if Path(python_exe).exists():
                env_to_create = candidates[0]
                subprocess.check_call([python_exe, '-m', 'venv', str(env_to_create)])
                venv_path = env_to_create
        except Exception:
            venv_path = None

    if venv_path:
        _activate_venv_in_place(venv_path)


def _activate_venv_in_place(venv_path):
    """Activate virtual environment by modifying sys.path and environment variables."""
    venv_path = Path(venv_path)

    # Set VIRTUAL_ENV environment variable
    os.environ['VIRTUAL_ENV'] = str(venv_path)

    # Remove existing PYTHONHOME if set (can interfere with venv)
    if 'PYTHONHOME' in os.environ:
        del os.environ['PYTHONHOME']

    # Determine site-packages path
    if (venv_path / 'Scripts').exists():  # Windows
        site_packages = venv_path / 'Lib' / 'site-packages'
        scripts_dir = venv_path / 'Scripts'
    else:  # Unix-like
        # Find the correct Python version directory
        lib_dir = venv_path / 'lib'
        if lib_dir.exists():
            python_dirs = [d for d in lib_dir.iterdir() if d.name.startswith('python')]
            if python_dirs:
                site_packages = python_dirs[0] / 'site-packages'
            else:
                site_packages = lib_dir / 'site-packages'
        else:
            site_packages = venv_path / 'lib' / 'site-packages'
        scripts_dir = venv_path / 'bin'

    # Add site-packages to sys.path if not already present
    site_packages_str = str(site_packages)
    if site_packages.exists() and site_packages_str not in sys.path:
        sys.path.insert(0, site_packages_str)

    # Update PATH to include venv scripts directory
    if scripts_dir.exists():
        scripts_str = str(scripts_dir)
        current_path = os.environ.get('PATH', '')
        if scripts_str not in current_path:
            os.environ['PATH'] = scripts_str + os.pathsep + current_path

    # Avoid printing in automated test environments
    if os.environ.get('LANGPLUG_DEBUG_VENV') == '1':
        print(f"Virtual environment activated in-place: {venv_path}")


# Auto-activate when this module is imported
activate_venv()
