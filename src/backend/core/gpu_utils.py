"""
GPU and CUDA utilities for AI/ML services.

Provides centralized GPU detection, validation, and error messaging
to eliminate code duplication across services.
"""

from __future__ import annotations

import os

from core.config.logging_config import get_logger

logger = get_logger(__name__)


def check_cuda_availability(service_name: str = "Service") -> bool:
    """
    Check CUDA availability and log appropriate warnings or errors.

    Args:
        service_name: Name of the service checking CUDA (for logging)

    Returns:
        True if CUDA is available, False otherwise

    Raises:
        RuntimeError: If LANGPLUG_REQUIRE_CUDA=true but CUDA is not available
    """
    try:
        import torch

        cuda_available = torch.cuda.is_available()
    except ImportError:
        logger.warning("PyTorch not available - cannot check CUDA", service=service_name)
        cuda_available = False

    require_cuda = os.environ.get("LANGPLUG_REQUIRE_CUDA", "false").lower() == "true"

    if not cuda_available:
        warning_msg = (
            "[CUDA WARNING] CUDA is not available. Running on CPU (slower performance).\n"
            "To use GPU acceleration:\n"
            "  1. Install NVIDIA GPU drivers\n"
            "  2. Install PyTorch with CUDA: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121\n"
            '  3. Verify with: python -c "import torch; print(torch.cuda.is_available())"\n'
            "Set LANGPLUG_REQUIRE_CUDA=true to make CUDA required"
        )

        if require_cuda:
            logger.error("CUDA required but not available", service=service_name)
            raise RuntimeError(f"[{service_name}] CUDA required but not available")
        else:
            logger.warning("CUDA not available, using CPU mode", service=service_name)

    return cuda_available


def get_device_str(device: str | int | None = None, fallback_to_cpu: bool = True) -> str:
    """
    Get normalized device string ('cuda' or 'cpu').

    Args:
        device: Device preference ('cuda', 'cpu', or None for auto-detect)
        fallback_to_cpu: If True, fall back to 'cpu' when CUDA unavailable

    Returns:
        Device string: 'cuda' if available, 'cpu' otherwise

    Raises:
        RuntimeError: If CUDA is required but unavailable (when fallback_to_cpu=False)
    """
    if device is None:
        # Auto-detect
        return "cuda" if check_cuda_availability("Auto-detect") else "cpu"

    if device == "cuda" or (isinstance(device, int) and device >= 0):
        if check_cuda_availability("Device Check"):
            return "cuda"
        elif fallback_to_cpu:
            logger.warning("CUDA requested but unavailable - falling back to CPU")
            return "cpu"
        else:
            raise RuntimeError("CUDA device requested but not available")

    return "cpu"


def get_device_id(device: str | int | None = None) -> int:
    """
    Convert device specification to device ID for PyTorch/Transformers.

    Args:
        device: Device specification ('cuda', 'cpu', or GPU index)

    Returns:
        Device ID: 0 for CUDA (default GPU), -1 for CPU
    """
    device_str = get_device_str(device)
    return 0 if device_str == "cuda" else -1
