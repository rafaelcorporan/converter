#!/bin/bash

# Pre-commit configuration validation hook
# Ensures configuration consistency before allowing commits

echo "🔍 Running pre-commit configuration validation..."

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Run configuration validation
python3 "$PROJECT_ROOT/scripts/validate_config.py" "$PROJECT_ROOT"
VALIDATION_EXIT_CODE=$?

if [ $VALIDATION_EXIT_CODE -eq 0 ]; then
    echo "✅ Pre-commit validation passed"
    exit 0
else
    echo "❌ Pre-commit validation failed"
    echo ""
    echo "💡 Fix the configuration issues above before committing."
    echo "   Run: python3 scripts/validate_config.py"
    exit 1
fi