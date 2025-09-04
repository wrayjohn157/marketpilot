#!/bin/bash
# Market7 Stop Script

echo "🛑 Stopping Market7 Trading System..."

# Stop Docker containers
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    docker-compose -f deploy/docker-compose.yml down
fi

# Stop Python processes
pkill -f "main_fixed.py"
pkill -f "npm start"

echo "✅ All services stopped"
