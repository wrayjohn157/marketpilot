#!/bin/bash
# MarketPilot Canonical Stop Script
# Stops all MarketPilot services cleanly

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo "🛑 Stopping MarketPilot Canonical System"
echo "========================================"

# Stop modular backend
log_info "Stopping modular backend..."
if pkill -f modular_backend.py; then
    log_success "Modular backend stopped"
else
    log_info "No modular backend process found"
fi

# Stop frontend
log_info "Stopping frontend..."
if pkill -f "npm start"; then
    log_success "Frontend stopped"
else
    log_info "No frontend process found"
fi

# Stop any other MarketPilot processes
log_info "Stopping other MarketPilot processes..."
pkill -f "start_full_system.py" 2>/dev/null || true
pkill -f "standalone_runner.py" 2>/dev/null || true
pkill -f "dashboard_backend/main.py" 2>/dev/null || true

# Check if processes are still running
REMAINING=$(ps aux | grep -E "(modular_backend|npm start|start_full_system|standalone_runner)" | grep -v grep | wc -l)

if [ "$REMAINING" -eq 0 ]; then
    log_success "All MarketPilot services stopped"
else
    log_info "Some processes may still be running. Check with: ps aux | grep python"
fi

echo ""
log_success "MarketPilot Canonical System Stopped!"
echo ""
echo "🔧 To restart: ./start_canonical.sh"
echo "📊 To check status: curl http://localhost:8000/health"
