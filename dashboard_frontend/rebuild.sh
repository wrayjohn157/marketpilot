#!/bin/bash
# rebuild.sh - Rebuilds React frontend and restarts Nginx

echo "🔨 Building React frontend..."
npm run build || { echo "❌ Build failed."; exit 1; }

echo "🚀 Restarting Nginx..."
sudo systemctl restart nginx || { echo "❌ Failed to restart Nginx."; exit 1; }

echo "✅ Frontend rebuilt and Nginx restarted."
