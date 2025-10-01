#!/bin/bash

# Setup pre-commit hook for contract validation

HOOKS_DIR=".git/hooks"
HOOK_FILE="$HOOKS_DIR/pre-commit"

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Create or update pre-commit hook
cat > "$HOOK_FILE" << 'EOF'
#!/bin/bash

echo "🔍 Running pre-commit contract validation..."

# Check if we're in the project root
if [ ! -f "openapi_spec.json" ] && [ ! -d "Backend" ]; then
    echo "❌ Please run this from the project root directory"
    exit 1
fi

# Function to check if backend files changed
backend_changed() {
    git diff --cached --name-only | grep -q "^Backend/"
}

# Function to check if API-related files changed
api_files_changed() {
    git diff --cached --name-only | grep -qE "(Backend/.*\.py|Frontend/src/.*api.*|Frontend/src/.*client.*|openapi_spec\.json)"
}

# If backend or API files changed, validate contracts
if backend_changed || api_files_changed; then
    echo "🔄 API-related files changed, validating contracts..."

    # Update OpenAPI spec if backend changed
    if backend_changed; then
        echo "📝 Backend changed, updating OpenAPI spec..."
        cd Backend
        python export_openapi.py
        cd ..

        # Add the updated spec to the commit
        git add openapi_spec.json
    fi

    # Run contract validation
    cd Frontend
    npm run validate-contract
    VALIDATION_RESULT=$?
    cd ..

    if [ $VALIDATION_RESULT -ne 0 ]; then
        echo "❌ Contract validation failed. Please fix issues before committing."
        echo ""
        echo "💡 You can run these commands to resolve issues:"
        echo "   cd Backend && python export_openapi.py"
        echo "   cd Frontend && npm run generate-client"
        echo "   cd Frontend && npm run validate-contract"
        exit 1
    fi

    echo "✅ Contract validation passed"
fi

echo "🎉 Pre-commit checks completed successfully"
EOF

# Make the hook executable
chmod +x "$HOOK_FILE"

echo "✅ Pre-commit hook installed successfully!"
echo ""
echo "The hook will now:"
echo "  • Detect changes to API-related files"
echo "  • Update OpenAPI spec when backend changes"
echo "  • Validate contract compatibility"
echo "  • Prevent commits if validation fails"
echo ""
echo "💡 Test it with: git commit --dry-run"
