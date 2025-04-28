import json
import time
import hmac
import hashlib
import requests
from datetime import datetime
from pathlib import Path

# Paths
CANDIDATE_PATH = Path("/home/signal/market6/output/final_fork_rrr_trades.json")
SNAPSHOT_BASE = Path("/home/signal/market6/data/snapshots")
RESULTS_BASE = Path("/home/signal/market6/live/logs")
REGISTRY_PATH = RESULTS_BASE / "fork_registry.json"
CRED_PATH = Path("/home/signal/market6/config/paper_cred.json")

# Constants
DEDUP_EXPIRY_SECONDS = 3600 * 6  # 6 hours


def compute_score_hash(indicators):
    keys = ["macd_histogram", "stoch_rsi_cross", "rsi_recovery", "adx_rising", "ema_price_reclaim"]
    return "_".join([f"{k}:{indicators.get(k, 0)}" for k in keys])


def get_day_folder(entry_time):
    day = datetime.utcfromtimestamp(entry_time).strftime("%Y-%m-%d")
    folder = RESULTS_BASE / day
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_entry_price(symbol, entry_ts):
    date_str = datetime.utcfromtimestamp(entry_ts).strftime("%Y-%m-%d")
    base = symbol.replace("USDT", "") if symbol.endswith("USDT") else symbol
    filename = f"{base}_15m_klines.json"
    filepath = SNAPSHOT_BASE / date_str / filename

    if not filepath.exists():
        print(f"[WARN] Snapshot not found: {filepath}")
        return None

    with open(filepath, "r") as f:
        klines = json.load(f)

    fallback_price = None
    for kline in klines:
        candle_ts = kline[0] // 1000
        if candle_ts <= entry_ts:
            fallback_price = float(kline[4])
        else:
            break

    return fallback_price


def save_daily_entry(entry):
    folder = get_day_folder(entry["entry_time"])
    out_path = folder / "completed_forks.jsonl"
    with open(out_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def load_registry():
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r") as f:
            return json.load(f)
    return {}


def save_registry(registry):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)


def get_live_3c_symbols():
    with open(CRED_PATH, "r") as f:
        creds = json.load(f)

    BOT_ID = creds["3commas_bot_id"]
    API_KEY = creds["3commas_api_key"]
    API_SECRET = creds["3commas_api_secret"]
    full_path = "/public/api/ver1/deals?scope=active"
    url = "https://api.3commas.io" + full_path
    signature = hmac.new(API_SECRET.encode(), full_path.encode(), hashlib.sha256).hexdigest()

    headers = {
        "Apikey": API_KEY,
        "Signature": signature
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        deals = res.json()

        symbols = set()
        for d in deals:
            if d.get("bot_id") == BOT_ID and d.get("status") == "bought":
                pair = d.get("pair", "")
                if pair.startswith("USDT_"):
                    symbols.add(pair.split("_")[1] + "USDT")
        return symbols

    except Exception as e:
        print(f"[ERROR] Failed to pull 3Commas trades: {e}")
        return set()


def get_ml_features_from_entry(symbol, timeframe="15m"):
    """
    Loads the most recent kline snapshot for a symbol and extracts
    the ML feature set used for xgb_model.pkl prediction.
    """
    import pandas as pd
    from datetime import datetime

    SNAPSHOT_DIR = "/home/signal/market6/data/snapshots"
    today = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"{symbol}_{timeframe}_klines.json"
    filepath = Path(SNAPSHOT_DIR) / today / filename

    if not filepath.exists():
        print(f"[WARN] Missing kline snapshot for {symbol}: {filepath}")
        return None

    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        if len(data) < 2:
            print(f"[WARN] Not enough candles for {symbol}")
            return None

        # Use latest candle
        latest = data[-1]
        prev = data[-2]
        close = float(latest[4])

        features = {
            "fork_score.indicators.EMA50": float(latest[5]),
            "fork_score.indicators.EMA200": float(latest[6]),
            "fork_score.indicators.RSI14": float(latest[7]),
            "fork_score.indicators.ADX14": float(latest[8]),
            "fork_score.indicators.QQE": float(latest[9]),
            "fork_score.indicators.PSAR": float(latest[10]),
            "fork_score.indicators.ATR": float(latest[11]),
            "fork_score.indicators.StochRSI_K": float(latest[12]),
            "fork_score.indicators.StochRSI_D": float(latest[13]),
            "fork_score.indicators.MACD": float(latest[14]),
            "fork_score.indicators.MACD_signal": float(latest[15]),
            "fork_score.indicators.MACD_diff": float(latest[16]),
            "fork_score.indicators.MACD_Histogram": float(latest[17]),
            "fork_score.indicators.MACD_Histogram_Prev": float(prev[17]),
            "fork_score.indicators.MACD_lift": float(latest[17]) - float(prev[17]),
            "btc_entry.rsi": float(latest[18]),
            "btc_entry.adx": float(latest[19]),
            "btc_entry.macd_histogram": float(latest[20]),
            "btc_entry.ema_50": float(latest[21]),
            "btc_entry.ema_200": float(latest[22]),
            "btc_entry.market_condition_num": int(latest[23]),
        }

        return features
    except Exception as e:
        print(f"[ERROR] Failed to extract features for {symbol}: {e}")
        return None
