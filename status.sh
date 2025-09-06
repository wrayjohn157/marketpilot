#!/bin/bash
# MarketPilot Status Check Script

echo "🔍 MarketPilot Status Check"
echo "=========================="

# Get current IP
CURRENT_IP=$(curl -s ifconfig.me)
echo "🌐 Server IP: $CURRENT_IP"
echo ""

# Check backend service
echo "🔧 Backend Service:"
if systemctl is-active --quiet marketpilot-backend; then
    echo "✅ Backend is running"
    echo "📊 Backend health:"
    curl -s http://localhost:8001/health | jq . 2>/dev/null || echo "❌ Health check failed"
else
    echo "❌ Backend is not running"
    echo "📋 Recent logs:"
    sudo journalctl -u marketpilot-backend --no-pager -n 5
fi
echo ""

# Check frontend container
echo "🌐 Frontend Container:"
if docker ps | grep -q marketpilot-frontend; then
    echo "✅ Frontend container is running"
    echo "📊 Frontend health:"
    curl -s http://localhost:3001 > /dev/null && echo "✅ Frontend accessible" || echo "❌ Frontend not accessible"
else
    echo "❌ Frontend container is not running"
    echo "📋 Container logs:"
    docker logs marketpilot-frontend 2>/dev/null | tail -5
fi
echo ""

# Check Redis
echo "🔴 Redis:"
if systemctl is-active --quiet redis-server; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not running"
fi
echo ""

# Check ports
echo "🔌 Port Status:"
echo "Port 3001 (Frontend): $(netstat -tlnp | grep :3001 | wc -l) connections"
echo "Port 8001 (Backend): $(netstat -tlnp | grep :8001 | wc -l) connections"
echo ""

# Display access URLs
echo "🌐 Access URLs:"
echo "Frontend: http://$CURRENT_IP:3001"
echo "Backend API: http://$CURRENT_IP:8001"
echo "API Docs: http://$CURRENT_IP:8001/docs"
echo ""

# Check credentials
echo "🔑 Credentials:"
if [ -f "config/credentials/3commas_credentials.json" ]; then
    echo "✅ 3Commas credentials found"
else
    echo "❌ 3Commas credentials missing"
fi

if [ -f "config/credentials/binance_credentials.json" ]; then
    echo "✅ Binance credentials found"
else
    echo "❌ Binance credentials missing"
fi
