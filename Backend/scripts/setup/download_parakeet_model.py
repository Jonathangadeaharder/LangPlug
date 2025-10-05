#!/usr/bin/env python3
"""
Pre-download NeMo Parakeet model to avoid test timeouts.
"""

import logging
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_parakeet_model():
    """Download the Parakeet model for testing"""
    try:
        logger.info("Importing NeMo ASR...")
        import nemo.collections.asr as nemo_asr

        model_name = "nvidia/parakeet-tdt-0.6b-v3"
        logger.info(f"Downloading model: {model_name}")

        # This will download and cache the model
        model = nemo_asr.models.ASRModel.from_pretrained(model_name)
        logger.info("Model downloaded successfully!")

        # Clean up to free memory
        del model
        logger.info("Model download completed and memory cleaned up.")

        return True

    except ImportError as e:
        logger.error(f"NeMo not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        return False


if __name__ == "__main__":
    success = download_parakeet_model()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
