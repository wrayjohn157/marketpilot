#!/bin/bash
# Setup cron-based execution (minimal systemd dependency)

echo "🚀 Setting up MarketPilot with minimal systemd dependency"
echo "=================================================="

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory
mkdir -p logs

# Make scripts executable
chmod +x standalone_runner.py
chmod +x data/rolling_indicators_standalone.py
chmod +x dca/smart_dca_core.py
chmod +x fork/fork_runner.py

echo "✅ Scripts made executable"

# Create cron jobs
echo "📅 Setting up cron jobs..."

# Create cron file
cat > marketpilot_cron << EOF
# MarketPilot Trading System Cron Jobs
# Run every minute for continuous operation

# Indicators - every 2 minutes
*/2 * * * * cd $SCRIPT_DIR && python3 data/rolling_indicators_standalone.py >> logs/indicators.log 2>&1

# DCA - every 30 seconds (using sleep for sub-minute intervals)
* * * * * cd $SCRIPT_DIR && python3 dca/smart_dca_core.py >> logs/dca.log 2>&1
* * * * * sleep 30 && cd $SCRIPT_DIR && python3 dca/smart_dca_core.py >> logs/dca.log 2>&1

# Fork Detection - every 2 minutes
*/2 * * * * cd $SCRIPT_DIR && python3 fork/fork_runner.py >> logs/fork.log 2>&1

# Health Check - every 5 minutes
*/5 * * * * cd $SCRIPT_DIR && python3 -c "from utils.redis_manager import get_redis_manager; r = get_redis_manager(); print('Redis OK:', r.ping())" >> logs/health.log 2>&1

# Log rotation - daily at midnight
0 0 * * * find $SCRIPT_DIR/logs -name "*.log" -mtime +7 -delete
EOF

echo "✅ Cron jobs created"

# Install cron jobs
crontab marketpilot_cron
echo "✅ Cron jobs installed"

# Create startup script
cat > start_marketpilot.sh << 'EOF'
#!/bin/bash
# Start MarketPilot services

echo "🚀 Starting MarketPilot..."

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️ Redis not running, starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

# Check Redis connection
python3 -c "from utils.redis_manager import get_redis_manager; r = get_redis_manager(); print('Redis OK:', r.ping())"

echo "✅ MarketPilot services started"
echo "📊 Check logs in: logs/"
echo "🛑 To stop: crontab -r"
EOF

chmod +x start_marketpilot.sh

# Create stop script
cat > stop_marketpilot.sh << 'EOF'
#!/bin/bash
# Stop MarketPilot services

echo "🛑 Stopping MarketPilot..."

# Remove cron jobs
crontab -r

# Kill any running Python processes
pkill -f "marketpilot"
pkill -f "rolling_indicators"
pkill -f "smart_dca"
pkill -f "fork_runner"

echo "✅ MarketPilot stopped"
EOF

chmod +x stop_marketpilot.sh

# Create status script
cat > status_marketpilot.sh << 'EOF'
#!/bin/bash
# Check MarketPilot status

echo "📊 MarketPilot Status"
echo "===================="

# Check cron jobs
echo "Cron Jobs:"
crontab -l | grep -E "(indicators|dca|fork|health)" || echo "No cron jobs found"

echo ""
echo "Processes:"
ps aux | grep -E "(rolling_indicators|smart_dca|fork_runner)" | grep -v grep || echo "No processes running"

echo ""
echo "Recent Logs:"
echo "Indicators:"
tail -5 logs/indicators.log 2>/dev/null || echo "No indicator logs"
echo ""
echo "DCA:"
tail -5 logs/dca.log 2>/dev/null || echo "No DCA logs"
echo ""
echo "Fork:"
tail -5 logs/fork.log 2>/dev/null || echo "No fork logs"
EOF

chmod +x status_marketpilot.sh

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Available commands:"
echo "  ./start_marketpilot.sh  - Start all services"
echo "  ./stop_marketpilot.sh   - Stop all services"
echo "  ./status_marketpilot.sh - Check status"
echo "  ./standalone_runner.py  - Run all services in one process"
echo ""
echo "📁 Logs will be saved to: logs/"
echo "🔄 Services will run automatically via cron"
echo ""
echo "🚀 To start: ./start_marketpilot.sh"
