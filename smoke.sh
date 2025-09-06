#!/bin/bash
# Full smoke test

set -e

echo "💨 Running full smoke test..."

# Format check
echo "🎨 Checking code format..."
black --check core dca fork indicators ml pipeline utils data dashboard_backend || {
    echo "❌ Code formatting issues found"
    exit 1
}

# Lint check
echo "🔍 Running linting..."
ruff check core dca fork indicators ml pipeline utils data dashboard_backend || {
    echo "❌ Linting issues found"
    exit 1
}

# Type check
echo "🔬 Running type checking..."
mypy core dca fork indicators ml pipeline utils data dashboard_backend --ignore-missing-imports || {
    echo "❌ Type checking issues found"
    exit 1
}

# Run tests
echo "🧪 Running tests..."
python3 -m pytest tests/ -v --tb=short || {
    echo "❌ Tests failed"
    exit 1
}

# Frontend tests
echo "🎨 Running frontend tests..."
cd dashboard_frontend
npm test -- --coverage --watchAll=false || {
    echo "❌ Frontend tests failed"
    exit 1
}

echo "✅ Full smoke test passed!"
