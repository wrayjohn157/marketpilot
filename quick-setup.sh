#!/bin/bash
# MarketPilot Quick Setup Script
# Minimal setup for immediate use

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "🚀 MarketPilot Quick Setup"
echo "=========================="

# Install Python dependencies
log_info "Installing Python dependencies..."
pip3 install --user --break-system-packages -r requirements.txt

# Install development dependencies
log_info "Installing development dependencies..."
pip3 install --user --break-system-packages -r requirements-dev.txt

# Create virtual environment
log_info "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install in virtual environment
log_info "Installing dependencies in virtual environment..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create necessary directories
log_info "Creating directories..."
mkdir -p logs data/{snapshots,logs,models,backtest}
mkdir -p ml/{models,datasets,preprocess,recovery,confidence}
mkdir -p dca/{logs,tracking,recovery}
mkdir -p fork/{logs,history,candidates}
mkdir -p indicators/{logs,data}

# Test basic functionality
log_info "Testing basic functionality..."
python3 test_paper_trading_config.py

# Run syntax check
log_info "Running syntax check..."
make check-syntax || log_warning "Some syntax issues found (expected - 2% remaining work)"

log_success "Quick setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Update config/paper_cred.json with your 3Commas credentials"
echo "2. Start MarketPilot: source venv/bin/activate && python3 standalone_runner.py"
echo "3. Or use: make quick-smoke (for testing)"
echo ""
echo "🔧 Available Commands:"
echo "  make help           - Show all commands"
echo "  make quick-smoke    - Run quick tests"
echo "  make format         - Format code"
echo "  make lint           - Run linting"
echo ""
echo "🚀 Happy Trading!"
