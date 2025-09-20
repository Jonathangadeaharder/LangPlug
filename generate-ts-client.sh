#!/bin/bash
# DEPRECATED: Use `python scripts/generate_typescript_client.py` instead
# This script will be removed in a future release
# Generate TypeScript client from OpenAPI spec

# Export OpenAPI spec from backend
echo "Exporting OpenAPI specification..."
cd Backend
api_venv/Scripts/python.exe -c "from core.app import create_app; import json; app = create_app(); spec = app.openapi(); open('../openapi_spec.json', 'w').write(json.dumps(spec, indent=2))"
cd ..

# Generate TypeScript client
echo "Generating TypeScript client..."
cd Frontend
npm run generate-client
cd ..

echo "TypeScript client generation complete!"