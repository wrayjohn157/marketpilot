#!/bin/bash
# Quick smoke test for development

set -e

echo "💨 Running quick smoke test..."

# Check Python syntax
echo "🔍 Checking Python syntax..."
find core dca fork indicators ml pipeline utils data dashboard_backend -name "*.py" -exec python3 -m py_compile {} \; || {
    echo "❌ Syntax errors found"
    exit 1
}

# Run smoke tests
echo "🧪 Running smoke tests..."
python3 -m pytest tests/ -v -m smoke --tb=short || {
    echo "❌ Smoke tests failed"
    exit 1
}

echo "✅ Quick smoke test passed!"
