"""
Export OpenAPI specification to JSON file
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.app import create_app


def export_openapi():
    """Export the current OpenAPI specification to a JSON file"""
    app = create_app()
    openapi_spec = app.openapi()

    # Write to project root
    output_path = project_root.parent / "openapi_spec.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_spec, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    export_openapi()
