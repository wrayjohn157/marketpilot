#!/bin/bash
# MarketPilot Canonical Startup Script
# Uses the proven modular backend with real 3commas integration

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

echo "🚀 Starting MarketPilot Canonical System"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    log_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    log_info "Activating virtual environment..."
    source venv/bin/activate
fi

# Check Redis
log_info "Checking Redis..."
if ! redis-cli ping &> /dev/null; then
    log_warning "Redis not running. Starting Redis..."
    sudo systemctl start redis-server || redis-server --daemonize yes
    sleep 2
fi

# Check PostgreSQL
log_info "Checking PostgreSQL..."
if ! pg_isready &> /dev/null; then
    log_warning "PostgreSQL not running. Starting PostgreSQL..."
    sudo systemctl start postgresql
    sleep 3
fi

# Start backend
log_info "Starting modular backend..."
python3 modular_backend.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health &> /dev/null; then
    log_success "Backend started successfully (PID: $BACKEND_PID)"
else
    log_warning "Backend health check failed, but continuing..."
fi

# Start frontend if directory exists
if [ -d "dashboard_frontend" ]; then
    log_info "Starting frontend..."
    cd dashboard_frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    log_success "Frontend started (PID: $FRONTEND_PID)"
else
    log_warning "Frontend directory not found, skipping frontend startup"
fi

# Show status
echo ""
log_success "MarketPilot Canonical System Started!"
echo ""
echo "🌐 Services:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  Health:   http://localhost:8000/health"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Real 3commas Data:"
echo "  Active Trades: http://localhost:8000/active-trades"
echo "  BTC Context:   http://localhost:8000/api/btc/context"
echo "  3commas Metrics: http://localhost:8000/3commas/metrics"
echo ""
echo "🛑 To stop: pkill -f modular_backend.py && pkill -f 'npm start'"
echo ""

# Keep script running
trap "echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
