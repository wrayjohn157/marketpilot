#!/bin/bash
# Market7 Start Script

echo "🚀 Starting Market7 Trading System..."

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 Starting with Docker Compose..."
    docker-compose -f deploy/docker-compose.yml up -d
elif command -v python3 &> /dev/null; then
    echo "🐍 Starting with Python..."
    # Start backend
    python3 dashboard_backend/main_fixed.py &
    BACKEND_PID=$!

    # Start frontend
    cd dashboard_frontend
    npm start &
    FRONTEND_PID=$!

    echo "Backend PID: $BACKEND_PID"
    echo "Frontend PID: $FRONTEND_PID"
    echo "Press Ctrl+C to stop all services"

    # Wait for interrupt
    trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
    wait
else
    echo "❌ Neither Docker nor Python found. Please install one of them."
    exit 1
fi
