#!/bin/bash
# Setup robust code quality system for MarketPilot

set -e

echo "🚀 Setting up MarketPilot Code Quality System"
echo "============================================="

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  No virtual environment detected. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install frontend dependencies
echo "🎨 Installing frontend dependencies..."
cd dashboard_frontend
npm install
cd ..

# Setup pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
pre-commit install
pre-commit run --all-files || echo "Some pre-commit checks failed (this is normal on first run)"

# Create test directories if they don't exist
echo "📁 Creating test directories..."
mkdir -p tests/{unit,integration,smoke}
mkdir -p logs

# Create basic test files if they don't exist
if [ ! -f "tests/__init__.py" ]; then
    echo "📝 Creating basic test structure..."
    cat > tests/__init__.py << 'EOF'
# MarketPilot Test Suite
EOF

    cat > tests/conftest.py << 'EOF'
"""Pytest configuration for MarketPilot tests."""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "test_mode": True,
        "redis_host": "localhost",
        "redis_port": 6379
    }
EOF

    cat > tests/test_smoke.py << 'EOF'
"""Smoke tests for MarketPilot."""

import pytest
from pathlib import Path

@pytest.mark.smoke
def test_imports():
    """Test that main modules can be imported."""
    try:
        from config.unified_config_manager import get_config
        from utils.redis_manager import get_redis_manager
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

@pytest.mark.smoke
def test_config_loading():
    """Test that configuration can be loaded."""
    try:
        from config.unified_config_manager import get_config
        config = get_config("dca")
        assert isinstance(config, dict)
    except Exception as e:
        pytest.fail(f"Config loading failed: {e}")

@pytest.mark.smoke
def test_redis_connection():
    """Test Redis connection."""
    try:
        from utils.redis_manager import get_redis_manager
        redis_manager = get_redis_manager()
        # Don't actually ping Redis in tests, just test the manager creation
        assert redis_manager is not None
    except Exception as e:
        pytest.fail(f"Redis manager creation failed: {e}")
EOF
fi

# Run initial quality checks
echo "🔍 Running initial quality checks..."
make check-syntax || echo "Some syntax issues found (will be fixed by formatting)"

# Format code
echo "🎨 Formatting code..."
make format

# Run quick smoke test
echo "💨 Running quick smoke test..."
make quick-smoke || echo "Some tests failed (this is normal on first run)"

echo ""
echo "✅ Code quality system setup complete!"
echo ""
echo "📋 Available commands:"
echo "  make help           - Show all available commands"
echo "  make quick-smoke    - Run quick smoke test"
echo "  make ci-fast        - Run fast CI checks"
echo "  make ci-full        - Run full CI checks"
echo "  make format         - Format code"
echo "  make lint           - Run linting"
echo "  make type           - Run type checking"
echo "  make test           - Run all tests"
echo "  make precommit      - Run pre-commit checks"
echo ""
echo "🚀 Ready for development!"
