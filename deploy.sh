#!/bin/bash
# One-Click MarketPilot Deployment Script
# Run this on your new VPS for complete setup

set -e  # Exit on any error

echo "🚀 MarketPilot One-Click Deployment Starting..."

# Get the current IP address
CURRENT_IP=$(curl -s ifconfig.me)
echo "🌐 Detected IP: $CURRENT_IP"

# Step 1: Install all dependencies
echo "📦 Installing dependencies..."
chmod +x install_dependencies.sh
./install_dependencies.sh

# Step 2: Clean up unnecessary files
echo "🧹 Cleaning up files..."
chmod +x cleanup_for_migration.sh
./cleanup_for_migration.sh

# Step 3: Create necessary directories
echo "📁 Creating directories..."
mkdir -p config/credentials
mkdir -p logs

# Step 4: Update frontend configuration with current IP
echo "🔧 Updating frontend configuration..."
cd dashboard_frontend

# Update API URL in environment files
sed -i "s/REACT_APP_API_URL=.*/REACT_APP_API_URL=http:\/\/$CURRENT_IP:3001/" .env.production
sed -i "s/REACT_APP_API_URL=.*/REACT_APP_API_URL=http:\/\/$CURRENT_IP:3001/" .env.development

# Update API base URL in the source code
sed -i "s|http://155.138.202.35:3001|http://$CURRENT_IP:3001|g" src/lib/api.js

# Build frontend
echo "🏗️ Building frontend..."
npm install
npm run build

# Update Nginx configuration with current IP
echo "🔧 Updating Nginx configuration..."
sed -i "s/155.138.202.35/$CURRENT_IP/g" nginx-with-proxy.conf

# Build and start frontend container
echo "🐳 Starting frontend container..."
docker stop marketpilot-frontend 2>/dev/null || true
docker rm marketpilot-frontend 2>/dev/null || true
docker run -d --name marketpilot-frontend -p 3001:80 -v $(pwd)/build:/usr/share/nginx/html -v $(pwd)/nginx-with-proxy.conf:/etc/nginx/conf.d/default.conf nginx

cd ..

# Step 5: Create systemd service for backend
echo "⚙️ Creating backend service..."
sudo tee /etc/systemd/system/marketpilot-backend.service > /dev/null <<EOF
[Unit]
Description=MarketPilot Backend API
After=network.target redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python modular_dashboard_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start backend
echo "🔄 Starting backend service..."
sudo systemctl daemon-reload
sudo systemctl enable marketpilot-backend
sudo systemctl start marketpilot-backend

# Step 6: Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Step 7: Health check
echo "🏥 Running health check..."
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed"
    echo "📋 Backend logs:"
    sudo journalctl -u marketpilot-backend --no-pager -n 20
fi

if curl -s http://localhost:3001 > /dev/null; then
    echo "✅ Frontend health check passed"
else
    echo "❌ Frontend health check failed"
    echo "📋 Frontend logs:"
    docker logs marketpilot-frontend
fi

# Step 8: Display access information
echo ""
echo "🎉 MarketPilot Deployment Complete!"
echo "=================================="
echo "🌐 Frontend: http://$CURRENT_IP:3001"
echo "🔧 Backend API: http://$CURRENT_IP:8001"
echo "📚 API Docs: http://$CURRENT_IP:8001/docs"
echo ""
echo "🔑 Next Steps:"
echo "1. Copy your credentials to config/credentials/"
echo "2. Restart backend: sudo systemctl restart marketpilot-backend"
echo "3. Check logs: sudo journalctl -u marketpilot-backend -f"
echo ""
echo "🛠️ Management Commands:"
echo "• Backend: sudo systemctl start/stop/restart marketpilot-backend"
echo "• Frontend: docker start/stop/restart marketpilot-frontend"
echo "• Logs: sudo journalctl -u marketpilot-backend -f"
echo "• Status: sudo systemctl status marketpilot-backend"
