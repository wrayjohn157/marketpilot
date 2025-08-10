from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pathlib import Path
import json
import redis

from config.config_loader import PATHS

# === FastAPI ===
app = FastAPI()

# === Redis ===
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# === Allow CORS from anywhere (or restrict to your domain) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Route imports ===
from unified_fork_metrics import get_fork_trade_metrics
from dca_status import router as dca_router
from ml_confidence_api import router as ml_confidence_router
from refresh_price_api import router as price_refresh_router
from dca_trades_api import router as dca_trades_api_router
from config_routes.fork_score_config_api import router as fork_score_config_router
from config_routes.dca_config_api import router as dca_config_router
from config_routes.tv_screener_config_api import router as tv_screener_config_router
from eval_routes import dca_eval_api
from config_routes import safu_config_api
from sim_routes.sim_dca_strategies import router as sim_dca_strategy_router
from eval_routes.price_series_api import router as price_series_router
from sim_routes.dca_simulate_route import router as dca_simulate_router
from dashboard_backend.sim_routes.sim_dca_config_api import router as sim_dca_router
from dashboard_backend.anal.capital_routes import router as capital_router

app.include_router(dca_router)
app.include_router(ml_confidence_router)
app.include_router(price_refresh_router)
app.include_router(dca_trades_api_router)
app.include_router(fork_score_config_router, prefix="/config")
app.include_router(dca_config_router, prefix="/config")
app.include_router(tv_screener_config_router, prefix="/config")
app.include_router(dca_eval_api.router)
app.include_router(safu_config_api.router, prefix="/config")
app.include_router(price_series_router)
app.include_router(dca_simulate_router)
app.include_router(sim_dca_strategy_router)
app.include_router(sim_dca_router)
app.include_router(capital_router, prefix="/api") #app.include_router(capital_router)

@app.get("/", response_class=HTMLResponse)
def root():
    return f"""
    <html>
        <head><title>Market7 Dashboard API</title></head>
        <body>
            <h2>🚀 Market7 Dashboard Backend</h2>
            <p>Available Endpoints:</p>
            <ul>
                <li><a href="/active-trades">/active-trades</a></li>
                <li><a href="/3commas/metrics">/3commas/metrics</a></li>
                <li><a href="/dca-trades-active" target="_blank">/dca-trades-active</a></li>
                <li><a href="/btc/context" target="_blank">/btc/context</a></li>
                <li><a href="/ml/confidence" target="_blank">/ml/confidence</a></li>
            </ul>
            <p><small>Server time: <code>{datetime.utcnow().isoformat()}</code></small></p>
        </body>
    </html>
    """


@app.get("/btc/context")
def get_btc_context():
    def parse_float(val):
        try:
            if val is None:
                return 0.0
            return float(str(val).replace("np.float64(", "").replace(")", ""))
        except:
            return 0.0

    return {
        "status": r.get("btc_condition") or "UNKNOWN",
        "rsi": parse_float(r.get("BTC_15m_RSI14")),
        "adx": parse_float(r.get("BTC_1h_ADX14")),
        "ema": parse_float(r.get("BTC_1h_EMA50")),
        "close": parse_float(r.get("BTC_1h_latest_close")),
    }


@app.get("/fork/metrics")
def serve_cached_metrics():
    path = PATHS["dashboard_cache"] / "fork_metrics.json"
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


@app.get("/active-trades")
def active_trades():
    raw = r.get("active_trades")
    if not raw:
        return []

    try:
        entries = json.loads(raw)
    except:
        return []

    trades = []
    for entry in entries:
        parts = entry.split("_")
        if len(parts) == 2:
            symbol = parts[1] + parts[0]
        else:
            symbol = entry

        score_raw = r.get(f"trade_health:{symbol}")
        try:
            score = int(score_raw) if score_raw else None
        except:
            score = None

        trades.append({"symbol": symbol, "score": score})

    return trades


@app.get("/trade-health/{symbol}")
def trade_health(symbol: str):
    redis_key = f"trade_health:{symbol.upper()}"
    raw = r.get(redis_key)

    if not raw:
        return {"error": "No data"}

    try:
        return {"symbol": symbol.upper(), "score": int(raw)}
    except:
        return {"error": "Invalid format"}


@app.get("/3commas/metrics")
def threecommas_metrics():
    from threecommas_metrics import get_3commas_metrics

    return get_3commas_metrics()
