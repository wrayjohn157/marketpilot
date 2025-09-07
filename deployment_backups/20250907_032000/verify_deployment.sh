#!/bin/bash
# Deployment Verification Script
# Run this after deployment to ensure everything is working

echo "🔍 Verifying MarketPilot deployment..."

# Test backend health
echo "Testing backend health..."
curl -s http://localhost:8000/health || echo "❌ Backend health check failed"

# Test API endpoints
echo "Testing API endpoints..."
curl -s http://localhost:8000/api/trades/active > /dev/null && echo "✅ Active trades API working" || echo "❌ Active trades API failed"
curl -s http://localhost:8000/api/3commas/metrics > /dev/null && echo "✅ 3Commas API working" || echo "❌ 3Commas API failed"
curl -s http://localhost:8000/config/dca > /dev/null && echo "✅ DCA config API working" || echo "❌ DCA config API failed"

# Test frontend proxy
echo "Testing frontend proxy..."
curl -s http://localhost:3000/api/trades/active > /dev/null && echo "✅ Frontend proxy working" || echo "❌ Frontend proxy failed"

echo "🎉 Deployment verification complete!"
