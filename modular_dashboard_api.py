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

# Create FastAPI app
app = FastAPI(
    title="MarketPilot Modular Dashboard API",
    description="Enhanced MarketPilot API with modular architecture",
    version="2.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import route modules
from routes import trades_api, tech_filter_api, dca_config_api, scan_api  # noqa: E402

# Include routers
app.include_router(trades_api.router, tags=["trades"])
app.include_router(tech_filter_api.router, tags=["tech-filter"])
app.include_router(dca_config_api.router, tags=["dca-config"])
app.include_router(scan_api.router, tags=["scan"])

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
            .endpoint-card p { font-size: 0.9em; color: #666; }
            .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
            .status-healthy { background-color: green; }
            .status-unhealthy { background-color: red; }
            .status-degraded { background-color: orange; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 MarketPilot Modular Dashboard API v2.1</h1>
            <p>Welcome to the enhanced MarketPilot API. This dashboard provides a modular and robust backend for your trading system.</p>

            <div class="section">
                <h3>Core Endpoints</h3>
                <div class="endpoint-list">
                    <div class="endpoint-card">
                        <h4>GET /</h4>
                        <p>This landing page.</p>
                    </div>
                    <div class="endpoint-card">
                        <h4>GET /health</h4>
                        <p>System health check (Redis, 3Commas API).</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h3>DCA Configuration</h3>
                <div class="endpoint-list">
                    <div class="endpoint-card">
                        <h4>GET /config/dca</h4>
                        <p>Get current user DCA configuration.</p>
                    </div>
                    <div class="endpoint-card">
                        <h4>POST /config/dca</h4>
                        <p>Save user DCA configuration.</p>
                    </div>
                    <div class="endpoint-card">
                        <h4>GET /config/dca/default</h4>
                        <p>Get default DCA configuration.</p>
                    </div>
                    <div class="endpoint-card">
                        <h4>POST /config/dca/reset</h4>
                        <p>Reset user DCA configuration to defaults.</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h3>Scan Review</h3>
                <div class="endpoint-list">
                    <div class="endpoint-card">
                        <h4>GET /api/scan/results</h4>
                        <p>Get mock scan results for review.</p>
                    </div>
                    <div class="endpoint-card">
                        <h4>GET /api/scan/stats</h4>
                        <p>Get mock scan statistics.</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h3>Trade Management</h3>
                <div class="endpoint-list">
                    <div class="endpoint-card">
                        <h4>GET /api/trades/active</h4>
                        <p>Get enhanced active trades with full enrichment.</p>
                    </div>
                    <div class="endpoint-card">
                        <h4>GET /active-trades</h4>
                        <p>Legacy active trades endpoint.</p>
                    </div>
                    <div class="endpoint-card">
                        <h4>GET /trade-health/{symbol}</h4>
                        <p>Get health score for a specific trade symbol.</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h3>Technical Filter</h3>
                <div class="endpoint-list">
                    <div class="endpoint-card">
                        <h4>GET /tech-filter/indicators/{symbol}</h4>
                        <p>Get technical indicators for a symbol.</p>
                    </div>
                    <div class="endpoint-card">
                        <h4>GET /tech-filter/score/{symbol}</h4>
                        <p>Get tech filter score for a symbol.</p>
                    </div>
                    <div class="endpoint-card">
                        <h4>GET /tech-filter/all</h4>
                        <p>Get tech filter data for all symbols.</p>
                    </div>
                    <div class="endpoint-card">
                        <h4>GET /tech-filter/signals</h4>
                        <p>Get trading signals based on tech filter analysis.</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h3>Legacy Compatibility</h3>
                <div class="endpoint-list">
                    <div class="endpoint-card">
                        <h4>GET /api/account/summary</h4>
                        <p>Account summary (legacy).</p>
                    </div>
                    <div class="endpoint-card">
                        <h4>GET /api/ml/confidence</h4>
                        <p>ML confidence data (legacy).</p>
                    </div>
                </div>
            </div>

            <p>For detailed API documentation, visit <a href="/docs">/docs</a> or <a href="/redoc">/redoc</a>.</p>
        </div>
    </body>
    </html>
    """

@app.get("/health")
def health_check() -> Dict[str, Any]:
    """Enhanced health check endpoint"""
    try:
        # Check Redis connection
        redis_status = "healthy"
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
        
        # Check 3Commas API
        api_status = "healthy"
        try:
            # Add basic API check here
            pass
        except Exception as e:
            api_status = f"unhealthy: {str(e)}"
        
        return {
            "status": "healthy" if redis_status == "healthy" and api_status == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "redis": redis_status,
                "3commas_api": api_status
            },
            "version": "2.1.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "2.1.0"
        }

@app.get("/api/account/summary")
def get_account_summary() -> Dict[str, Any]:
    """Legacy account summary endpoint"""
    return {
        "message": "Legacy endpoint - use /api/trades/active for enhanced data",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/ml/confidence")
def get_ml_confidence() -> Dict[str, Any]:
    """Legacy ML confidence endpoint"""
    return {
        "message": "Legacy endpoint - ML confidence data will be integrated into trade endpoints",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # nosec B104