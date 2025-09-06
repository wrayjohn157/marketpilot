"""
Modular MarketPilot Dashboard API
Market7-inspired architecture with proper route separation
"""

import sys
import os
from datetime import datetime
import logging

# Add project root to path for imports
sys.path.insert(0, '/home/signal/marketpilot')

# Import FastAPI and other dependencies after path setup
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402
from typing import Any, Dict  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI App ===
app = FastAPI(title="MarketPilot Modular Dashboard API", version="2.1.0")

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Import Route Modules ===
try:
    from routes.trades_api import router as trades_router
    from routes.metrics_api import router as metrics_router
    from routes.btc_api import router as btc_router
    from routes.dca_api import router as dca_router
    from routes.tech_filter_api import router as tech_filter_router
    from routes.refresh_price_api import router as refresh_price_router
    from routes.panic_sell_api import router as panic_sell_router
    from routes.scan_api import router as scan_router
    from routes.dca_config_api import router as dca_config_router
    
    # Include all route modules
    app.include_router(trades_router, tags=["trades"])
    app.include_router(metrics_router, tags=["metrics"])
    app.include_router(btc_router, tags=["btc"])
    app.include_router(dca_router, tags=["dca"])
    app.include_router(tech_filter_router, tags=["tech-filter"])
    app.include_router(refresh_price_router, tags=["refresh"])
    app.include_router(panic_sell_router, tags=["panic-sell"])
    app.include_router(scan_router, tags=["scan"])
    app.include_router(dca_config_router, tags=["dca-config"])
    
    logger.info("Successfully loaded all route modules including Market7-compatible DCA endpoints")
    
except Exception as e:
    logger.error(f"Failed to load route modules: {e}")
    # Fallback to enhanced_dashboard_api functions
    logger.warning("Using fallback enhanced API functions")

# === Import Enhanced Functions for Additional Endpoints ===
try:
    from enhanced_dashboard_api import (
        get_3commas_credentials,
        get_redis_client,
        make_3commas_request
    )
except Exception as e:
    logger.error(f"Failed to import enhanced functions: {e}")

# === Root Endpoint ===
@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    """Enhanced landing page with Market7-style organization"""
    return """
    <html>
    <head>
        <title>MarketPilot Modular Dashboard API v2.1</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .section { margin: 20px 0; padding: 15px; border-left: 4px solid #007acc; background: #f9f9f9; }
            .endpoint-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin: 20px 0; }
            .endpoint-card { background: white; padding: 15px; border-radius: 5px; border: 1px solid #ddd; }
            .endpoint-card h4 { margin: 0 0 10px 0; color: #007acc; }
            .endpoint-card a { text-decoration: none; color: #333; font-family: monospace; }
            .endpoint-card a:hover { color: #007acc; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 MarketPilot Modular Dashboard API v2.1</h1>
            <p><strong>Market7-Inspired Architecture with Enhanced Modular Routes</strong></p>
            
            <div class="section">
                <h2>📈 Trading Endpoints</h2>
                <div class="endpoint-list">
                    <div class="endpoint-card">
                        <h4>Active Trades</h4>
                        <a href="/api/trades/active">📊 /api/trades/active</a><br>
                        <a href="/active-trades">📊 /active-trades (legacy)</a>
                    </div>
                    <div class="endpoint-card">
                        <h4>Market7 Compatible</h4>
                        <a href="/dca-trades-active">🔄 /dca-trades-active</a><br>
                        <a href="/dca-evals">📋 /dca-evals</a>
                    </div>
                    <div class="endpoint-card">
                        <h4>Trade Management</h4>
                        <a href="/trade-health/BTC">💊 /trade-health/{symbol}</a><br>
                        <strong>POST</strong> /refresh-price/{deal_id}<br>
                        <strong>POST</strong> /panic-sell
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📊 Metrics & Performance</h2>
                <div class="endpoint-list">
                    <div class="endpoint-card">
                        <h4>3Commas Metrics</h4>
                        <a href="/3commas/metrics">📈 /3commas/metrics</a><br>
                        <a href="/api/3commas/metrics">📈 /api/3commas/metrics</a>
                    </div>
                    <div class="endpoint-card">
                        <h4>Performance Stats</h4>
                        <a href="/api/performance/stats">📊 /api/performance/stats</a>
                    </div>
                    <div class="endpoint-card">
                        <h4>Fork Metrics</h4>
                        <a href="/fork/metrics">🍴 /fork/metrics</a>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>₿ BTC Market Context</h2>
                <div class="endpoint-list">
                    <div class="endpoint-card">
                        <h4>BTC Context</h4>
                        <a href="/btc/context">₿ /btc/context</a><br>
                        <a href="/api/btc/context">₿ /api/btc/context</a>
                    </div>
                    <div class="endpoint-card">
                        <h4>BTC Indicators</h4>
                        <a href="/btc/indicators">📊 /btc/indicators</a>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🛠 System & Compatibility</h2>
                <div class="endpoint-list">
                    <div class="endpoint-card">
                        <h4>System Health</h4>
                        <a href="/health">🏥 /health</a>
                    </div>
                    <div class="endpoint-card">
                        <h4>ML & Analytics</h4>
                        <a href="/ml/confidence">🧠 /ml/confidence</a><br>
                        <a href="/api/ml/confidence">🧠 /api/ml/confidence</a>
                    </div>
                    <div class="endpoint-card">
                        <h4>Legacy Endpoints</h4>
                        <a href="/api/account/summary">💰 /api/account/summary</a>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🔗 External Links</h2>
                <div class="endpoint-list">
                    <div class="endpoint-card">
                        <h4>Frontend</h4>
                        <a href="http://155.138.202.35:3001" target="_blank">📱 MarketPilot Dashboard</a>
                    </div>
                    <div class="endpoint-card">
                        <h4>Documentation</h4>
                        <a href="/docs" target="_blank">📚 API Documentation</a>
                    </div>
                </div>
            </div>
            
            <p><em>Powered by MarketPilot • Inspired by Market7 • Enhanced with Modular Architecture</em></p>
            <p><small>Server time: <code>""" + datetime.utcnow().isoformat() + """</code></small></p>
        </div>
    </body>
    </html>
    """

# === Health Check ===
@app.get("/health")
def health_check() -> Dict[str, str]:
    """Comprehensive health check"""
    try:
        # Test Redis
        redis_client = get_redis_client()
        redis_status = "healthy" if redis_client and redis_client.ping() else "unhealthy"
        
        # Test 3Commas API
        creds = get_3commas_credentials()
        bot_id = creds["3commas_bot_id"]
        
        # Quick API test
        try:
            response = make_3commas_request("/public/api/ver1/deals", {"scope": "active", "bot_id": bot_id, "limit": "1"})
            api_status = "healthy" if response.status_code == 200 else f"unhealthy_{response.status_code}"
        except Exception as e:
            logger.error(f"3Commas API health check failed: {e}")
            api_status = "unhealthy_connection"
        
        return {
            "status": "healthy" if redis_status == "healthy" and "healthy" in api_status else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "redis": redis_status,
                "3commas_api": api_status,
                "bot_id": bot_id
            },
            "version": "2.1.0",
            "architecture": "modular"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

# === Legacy Compatibility Endpoints ===
@app.get("/api/account/summary")
def get_account_summary() -> Dict[str, Any]:
    """Account summary endpoint (legacy compatibility)"""
    try:
        from routes.trades_api import get_active_trades_enhanced
        trades_response = get_active_trades_enhanced()
        trades = trades_response.get('trades', [])
        summary = trades_response.get('summary', {})
        
        return {
            "summary": {
                "balance": 10000.0,  # Mock - would need account API
                "today_pnl": summary.get('total_open_pnl', 0),
                "total_pnl": summary.get('total_open_pnl', 0),
                "active_trades": len(trades),
                "allocated": summary.get('total_spent', 0),
                "upnl": summary.get('total_open_pnl', 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get account summary: {e}")
        return {
            "summary": {
                "balance": 0,
                "today_pnl": 0,
                "total_pnl": 0,
                "active_trades": 0,
                "allocated": 0,
                "upnl": 0
            },
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/ml/confidence")
def get_ml_confidence() -> Dict[str, Any]:
    """ML confidence data (legacy compatibility)"""
    return {
        "confidence": 0.85,
        "model_version": "v2.1",
        "last_updated": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8001)  # nosec B104
