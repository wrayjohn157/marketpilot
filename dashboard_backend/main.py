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

app.include_router(dca_router)
app.include_router(ml_confidence_router)
app.include_router(price_refresh_router)
app.include_router(dca_trades_api_router)
app.include_router(fork_score_config_router, prefix="/config")
app.include_router(dca_config_router, prefix="/config") 
#app.include_router(dca_config_router) 

@app.get("/", response_class=HTMLResponse)
def root():
    return f"""
    <html>
        <head><title>Market7 Dashboard API</title></head>
        <body>
            <h2>🚀 Market7 Dashboard Backend</h2>
            <p>Available Endpoints:</p>
            <ul>
                <li><a href="/metrics">/metrics</a></li>
                <li><a href="/active-trades">/active-trades</a></li>
                <li><a href="/all-trade-health">/all-trade-health</a></li>
                <li><a href="/active-trades-detailed">/active-trades-detailed</a></li>
                <li><a href="/backtest/summary">/backtest/summary</a></li>
                <li><a href="/backtest/summary/&lt;YYYY-MM-DD&gt;">/backtest/summary/&lt;YYYY-MM-DD&gt;</a></li>
                <li><a href="/3commas/metrics">/3commas/metrics</a></li>
                <li><a href="/fork/metrics" target="_blank">/fork/metrics</a></li>
                <li><a href="/dca-trades-active" target="_blank">/dca-trades-active</a></li>
                <li><a href="/btc/context" target="_blank">/btc/context</a></li>
                <li><a href="/ml/confidence" target="_blank">/ml/confidence</a></li>
            </ul>
            <p><small>Server time: <code>{datetime.utcnow().isoformat()}</code></small></p>
        </body>
    </html>
    """

@app.get("/metrics")
def metrics():
    return {
        "btc_market_condition": r.get("btc_condition"),
        "last_scan_full": r.get("last_scan_full"),
        "last_scan_vol": r.get("last_scan_vol"),
        "last_scan_tech": r.get("last_scan_tech"),
        "last_scan_rrr": r.get("last_scan_rrr"),
        "volume_filter_count": r.get("volume_filter_count"),
        "tech_filter_count_in": r.get("tech_filter_count_in"),
        "tech_filter_count_out": r.get("tech_filter_count_out"),
        "rrr_filter_count_in": r.get("rrr_filter_count_in"),
        "rrr_filter_count_out": r.get("rrr_filter_count_out"),
        "last_sent_trades": r.get("last_sent_trades"),
        "active_trades": r.get("active_trades_count"),
        "final_trade_queue": r.get("final_trade_queue_count"),
        "timestamp": datetime.utcnow().isoformat()
    }

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
        "close": parse_float(r.get("BTC_1h_latest_close"))
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

        trades.append({
            "symbol": symbol,
            "score": score
        })

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

@app.get("/all-trade-health")
def all_trade_health():
    keys = r.keys("trade_health:*")
    data = []

    for key in keys:
        try:
            score = int(r.get(key))
            symbol = key.replace("trade_health:", "")
            data.append({
                "symbol": symbol,
                "score": score
            })
        except:
            continue

    return data

@app.get("/active-trades-detailed")
def active_trades_detailed():
    def flag_to_emoji(*flags):
        total = sum([f for f in flags if isinstance(f, int)])
        if total == 0:
            return "✅"
        elif total == 1:
            return "⚠️"
        else:
            return "❌"

    def get_flag(key):
        val = r.get(key)
        try:
            return int(val) if val else 0
        except:
            return 0

    trade_keys = r.keys("trade_health:*")
    trades = []

    for key in trade_keys:
        symbol = key.replace("trade_health:", "")
        score_raw = r.get(key)
        if not score_raw:
            continue

        try:
            score = int(score_raw)
        except:
            score = 0

        indicators = {
            "macd": flag_to_emoji(get_flag(f"macd_weakness:{symbol}:15m"), get_flag(f"macd_weakness:{symbol}:1h")),
            "rsi": flag_to_emoji(get_flag(f"rsi_weakness:{symbol}:15m"), get_flag(f"rsi_weakness:{symbol}:1h")),
            "ema": flag_to_emoji(get_flag(f"ema_breakdown:{symbol}"), get_flag(f"ema_death_cross:{symbol}")),
            "adx": flag_to_emoji(get_flag(f"adx_bearish:{symbol}:1h")),
            "vwap": flag_to_emoji(get_flag(f"vwap_breakdown:{symbol}")),
            "momentum": flag_to_emoji(get_flag(f"momentum_loss:{symbol}")),
            "atr": flag_to_emoji(get_flag(f"atr_drop:{symbol}:1h"))
        }

        if score >= 8:
            status = "healthy"
        elif score >= 4:
            status = "weakening"
        else:
            status = "critically_weak"

        trades.append({
            "symbol": symbol,
            "score": score,
            "status": status,
            "indicators": indicators
        })

    return {
        "count": len(trades),
        "trades": trades
    }

@app.get("/3commas/metrics")
def threecommas_metrics():
    from threecommas_metrics import get_3commas_metrics
    return get_3commas_metrics()

@app.get("/backtest/summary")
def get_backtest_summary():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    summary_path = PATHS["backtest_summary_path"] / f"{today}_summary.json"
    if not summary_path.exists():
        return {"error": f"Summary for {today} not found."}
    try:
        with open(summary_path, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

@app.get("/backtest/summary/{date}")
def get_summary_by_date(date: str):
    summary_path = PATHS["backtest_summary_path"] / f"{date}_summary.json"
    if not summary_path.exists():
        return {"error": f"Summary for {date} not found."}
    try:
        with open(summary_path, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}
