"""
Path Utilities

Cross-platform path handling with WSL/Windows compatibility.
"""

from pathlib import Path


def ensure_accessible_path(path: Path, logger=None) -> Path:
    """Ensure path is accessible, converting WSL/Windows paths if needed.
    
    Args:
        path: Path to check and potentially convert
        logger: Optional logger for debug messages
        
    Returns:
        Accessible path (converted if necessary)
    """
    # Resolve relative paths first
    if not path.is_absolute():
        path = path.resolve()
        if logger:
            logger.debug("Resolved relative path", path=str(path))

    # If path exists and is accessible, return as-is
    if path.exists() and path.is_dir():
        if logger:
            logger.debug("Path accessible", path=str(path))
        return path

    # Try WSL to Windows conversion (/mnt/c/ -> C:/)
    path_str = str(path)
    if path_str.startswith("/mnt/"):
        # Extract drive letter (e.g., /mnt/c/ -> C:/)
        parts = path_str.split("/")
        if len(parts) >= 3:
            drive = parts[2].upper()
            rest = "/".join(parts[3:])
            windows_path_str = f"{drive}:/{rest}".replace("/", "\\")
            windows_path = Path(windows_path_str)
            if windows_path.exists() and windows_path.is_dir():
                if logger:
                    logger.debug("Converted WSL to Windows path", original=path_str, converted=str(windows_path))
                return windows_path

    # Try Windows to WSL conversion (C:/ -> /mnt/c/)
    if len(path_str) >= 2 and path_str[1] == ":":
        drive = path_str[0].lower()
        rest = path_str[2:].replace("\\", "/")
        wsl_path_str = f"/mnt/{drive}{rest}"
        wsl_path = Path(wsl_path_str)
        if wsl_path.exists() and wsl_path.is_dir():
            if logger:
                logger.debug("Converted Windows to WSL path", original=path_str, converted=str(wsl_path))
            return wsl_path

    # Log warning if path is not accessible
    if logger:
        logger.warning("Path not accessible", path=path_str)
    return path


def get_project_root() -> Path:
    """Get the project root directory.
    
    Returns:
        Path to the project root (contains src/, videos/, etc.)
    """
    # This file is at: src/backend/core/config/path_utils.py
    # Project root is 5 levels up
    return Path(__file__).resolve().parent.parent.parent.parent.parent
