#!/usr/bin/env python3
"""
Start Backend with full model loading and progress display
Shows detailed progress for AI model downloads and initialization
"""

import os
import sys

# Ensure we're not in testing mode - we want to load models
if "TESTING" in os.environ:
    del os.environ["TESTING"]

# Add Backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Kill any process on the target port first
import uvicorn
from cleanup_port import kill_process_on_port

from core.config import settings

if __name__ == "__main__":
    # Use environment variable or default to 8000
    port = int(os.environ.get("LANGPLUG_PORT", settings.port))
    host = settings.host

    # Clean up the port first
    kill_process_on_port(port)

    # Run with detailed logging
    uvicorn.run("core.app:app", host=host, port=port, log_level="info", reload=False, access_log=True)
