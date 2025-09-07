#!/bin/bash
# MarketPilot Canonical Status Script
# Shows status of all MarketPilot services

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "📊 MarketPilot Canonical System Status"
echo "======================================"

# Check backend
log_info "Checking backend..."
if curl -s http://localhost:8000/health &> /dev/null; then
    BACKEND_STATUS=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "unknown")
    log_success "Backend: Running (Status: $BACKEND_STATUS)"
else
    log_error "Backend: Not responding"
fi

# Check frontend
log_info "Checking frontend..."
if curl -s http://localhost:3000 &> /dev/null; then
    log_success "Frontend: Running"
else
    log_warning "Frontend: Not responding"
fi

# Check Redis
log_info "Checking Redis..."
if redis-cli ping &> /dev/null; then
    log_success "Redis: Running"
else
    log_error "Redis: Not running"
fi

# Check PostgreSQL
log_info "Checking PostgreSQL..."
if pg_isready &> /dev/null; then
    log_success "PostgreSQL: Running"
else
    log_error "PostgreSQL: Not running"
fi

# Check processes
echo ""
log_info "Process Status:"
MODULAR_BACKEND=$(ps aux | grep modular_backend.py | grep -v grep | wc -l)
FRONTEND=$(ps aux | grep "npm start" | grep -v grep | wc -l)

if [ "$MODULAR_BACKEND" -gt 0 ]; then
    log_success "Modular Backend: Running"
else
    log_error "Modular Backend: Not running"
fi

if [ "$FRONTEND" -gt 0 ]; then
    log_success "Frontend: Running"
else
    log_warning "Frontend: Not running"
fi

# Check API endpoints
echo ""
log_info "API Endpoints:"
echo "  Health:        http://localhost:8000/health"
echo "  Active Trades: http://localhost:8000/active-trades"
echo "  BTC Context:   http://localhost:8000/api/btc/context"
echo "  Fork Metrics:  http://localhost:8000/fork/metrics"
echo "  3commas:       http://localhost:8000/3commas/metrics"
echo "  API Docs:      http://localhost:8000/docs"

# Show recent data
echo ""
log_info "Recent Data:"
if curl -s http://localhost:8000/active-trades &> /dev/null; then
    ACTIVE_TRADES=$(curl -s http://localhost:8000/active-trades | jq '. | length' 2>/dev/null || echo "0")
    log_success "Active Trades: $ACTIVE_TRADES"
else
    log_error "Active Trades: Unable to fetch"
fi

if curl -s http://localhost:8000/3commas/metrics &> /dev/null; then
    PNL=$(curl -s http://localhost:8000/3commas/metrics | jq -r '.metrics.open_pnl // "unknown"' 2>/dev/null || echo "unknown")
    log_success "3commas P&L: $PNL"
else
    log_error "3commas Data: Unable to fetch"
fi

echo ""
log_info "Commands:"
echo "  Start:  ./start_canonical.sh"
echo "  Stop:   ./stop_canonical.sh"
echo "  Status: ./status_canonical.sh"


