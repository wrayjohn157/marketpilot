#!/bin/bash

echo "🔄 Building Docker image for Market 6.0 Dashboard..."
docker build -t dashboard_frontend .

echo "🛑 Stopping existing dashboard container (if any)..."
docker stop dashboard 2>/dev/null && docker rm dashboard 2>/dev/null

echo "🚀 Running updated dashboard container on port 80..."
docker run -d -p 3000:80 --name dashboard --restart always dashboard_frontend

# Optional: Restart nginx if it's installed and active
if systemctl is-active --quiet nginx; then
  echo "♻️ Restarting nginx..."
  sudo systemctl restart nginx
else
  echo "⚠️ nginx not running or not installed, skipping nginx restart."
fi

echo "✅ Dashboard is now live at http://entropy157.com or http://localhost!"
