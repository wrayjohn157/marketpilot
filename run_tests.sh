#!/bin/bash
# Comprehensive test suite

set -e

echo "🧪 Running comprehensive test suite..."

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install pytest pytest-cov pytest-mock pytest-asyncio pytest-xdist
    pip install black isort ruff mypy pre-commit safety bandit
else
    source venv/bin/activate
fi

# Code quality checks
echo "🔍 Running code quality checks..."
make ci-fast

# Frontend checks
echo "🎨 Running frontend checks..."
cd dashboard_frontend
npm install
npm run lint
npm test -- --coverage --watchAll=false
npm run build
cd ..

# Security checks
echo "🔒 Running security checks..."
safety check --file requirements.txt
bandit -r core dca fork indicators ml pipeline utils data dashboard_backend

echo "✅ Comprehensive test suite passed!"
