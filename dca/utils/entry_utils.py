#!/usr/bin/env python3

import json
import requests
import redis
import pandas as pd
import hmac
import hashlib
from datetime import datetime
from pathlib import Path
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator

# === Paths ===
CRED_PATH = Path("/home/signal/market7/config/paper_cred.json")
SNAPSHOT_BASE = Path("/home/signal/market7/data/snapshots")
FORK_HISTORY = Path("/home/signal/market7/output/fork_history")
BTC_LOG_PATH = Path("/home/signal/market7/live/btc_logs")

# === Redis Setup ===
REDIS = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# === 3Commas Trade Fetch (Paginated) ===
def get_live_3c_trades():
    try:
        with open(CRED_PATH, "r") as f:
            creds = json.load(f)

        BOT_ID = creds["3commas_bot_id"]
        API_KEY = creds["3commas_api_key"]
        API_SECRET = creds["3commas_api_secret"]

        all_deals = []
        page = 1
        while True:
            query = f"limit=1000&scope=active&bot_id={BOT_ID}&page={page}"
            path = f"/public/api/ver1/deals?{query}"
            url = f"https://api.3commas.io{path}"
            signature = hmac.new(API_SECRET.encode(), path.encode(), hashlib.sha256).hexdigest()
            headers = {
                "Apikey": API_KEY,
                "Signature": signature
            }

            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                print(f"[ERROR] 3Commas API error: {resp.status_code}")
                break
            deals = resp.json()
            if not deals:
                break
            all_deals.extend(deals)
            if len(deals) < 1000:
                break
            page += 1

        # Normalize fields for downstream use
        for deal in all_deals:
            deal["symbol"] = deal.get("pair")
            deal["deal_id"] = deal.get("id")

            avg_price = deal.get("bought_average_price")
            if not avg_price and deal.get("bought_amount") and deal.get("bought_volume"):
                try:
                    avg_price = float(deal["bought_amount"]) / float(deal["bought_volume"])
                except Exception:
                    avg_price = None

            deal["avg_entry_price"] = float(avg_price) if avg_price else None

        return all_deals

    except Exception as e:
        print(f"[ERROR] Failed to fetch 3Commas live trades: {e}")
        return []
        print("[DEBUG] 3C Trade Normalization Active")

def send_dca_signal(pair, volume=15):
    try:
        with open(CRED_PATH, "r") as f:
            creds = json.load(f)

        payload = {
            "action": "add_funds_in_quote",
            "message_type": "bot",
            "bot_id": creds["3commas_bot_id"],
            "email_token": creds["3commas_email_token"],
            "delay_seconds": 0,
            "pair": pair,
            "volume": volume
        }

        url = "https://app.3commas.io/trade_signal/trading_view"
        print(f"[DEBUG] Sending DCA payload: {json.dumps(payload)}")
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        print(f"✅ DCA signal sent for {pair} | Volume: {volume} USDT")
    except Exception as e:
        print(f"[ERROR] Failed to send DCA signal for {pair}: {e}")

def get_latest_indicators(symbol, tf="15m"):
    path = SNAPSHOT_BASE / datetime.utcnow().strftime("%Y-%m-%d") / f"{symbol}_{tf}_klines.json"
    if not path.exists():
        print(f"[WARN] Missing snapshot for {symbol}")
        return {}

    try:
        with open(path) as f:
            raw = json.load(f)
        if len(raw) < 50:
            print(f"[WARN] Not enough candles to compute indicators for {symbol}")
            return {}

        df = pd.DataFrame(raw, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "num_trades",
            "taker_base_volume", "taker_quote_volume", "ignore"
        ])
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})

        rsi_val = RSIIndicator(df["close"]).rsi().iloc[-1]
        macd_val = MACD(df["close"]).macd_diff().iloc[-1]
        adx_val = ADXIndicator(df["high"], df["low"], df["close"]).adx().iloc[-1]

        return {
            "rsi": round(float(rsi_val), 2),
            "macd_histogram": round(float(macd_val), 5),
            "adx": round(float(adx_val), 2)
        }

    except Exception as e:
        print(f"[ERROR] Could not compute indicators for {symbol}: {e}")
        return {}

def get_rsi_slope(symbol, tf="15m", window=3):
    try:
        path = SNAPSHOT_BASE / datetime.utcnow().strftime("%Y-%m-%d") / f"{symbol}_{tf}_klines.json"
        if not path.exists():
            return 0.0
        df = pd.read_json(path)
        close = df.iloc[:, 4].astype(float)
        rsi_series = RSIIndicator(close).rsi().dropna()
        if len(rsi_series) < window:
            return 0.0
        slope = rsi_series.iloc[-1] - rsi_series.iloc[-window]
        return round(slope, 4)
    except Exception as e:
        print(f"[ERROR] RSI slope error for {symbol}: {e}")
        return 0.0

def get_macd_lift(symbol, tf="15m", window=3):
    try:
        path = SNAPSHOT_BASE / datetime.utcnow().strftime("%Y-%m-%d") / f"{symbol}_{tf}_klines.json"
        if not path.exists():
            return 0.0
        df = pd.read_json(path)
        close = df.iloc[:, 4].astype(float)
        macd_series = MACD(close).macd_diff().dropna()
        if len(macd_series) < window:
            return 0.0
        lift = macd_series.iloc[-1] - macd_series.iloc[-window]
        return round(lift, 5)
    except Exception as e:
        print(f"[ERROR] MACD lift error for {symbol}: {e}")
        return 0.0

def load_fork_entry_score(symbol, entry_ts):
    best_match = None
    smallest_delta = float("inf")

    for folder in sorted(FORK_HISTORY.glob("*")):
        path = folder / "fork_scores.jsonl"
        if not path.exists():
            continue
        with open(path) as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("symbol") != symbol:
                    continue
                score_ts_raw = obj.get("timestamp")
                if not score_ts_raw or not str(score_ts_raw).isdigit():
                    continue
                record_ts = int(score_ts_raw)
                if record_ts > entry_ts:
                    continue
                delta = entry_ts - record_ts
                if delta < smallest_delta:
                    smallest_delta = delta
                    best_match = obj

    if best_match and "score" in best_match:
        return round(float(best_match["score"]), 4)

    print(f"[WARN] No matching entry score found for {symbol} at ts={entry_ts}")
    return None

def simulate_new_avg_price(current_avg, added_usdt, current_price):
    try:
        tokens = added_usdt / current_price
        new_total_usdt = current_avg * tokens + added_usdt
        new_total_tokens = tokens * 2
        return new_total_usdt / new_total_tokens
    except Exception as e:
        print(f"[ERROR] Failed to simulate BE price: {e}")
        return current_avg

def load_btc_market_condition():
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        path = BTC_LOG_PATH / today / "btc_snapshots.jsonl"
        if not path.exists():
            return None
        with open(path) as f:
            lines = f.readlines()
        latest = json.loads(lines[-1])
        return latest.get("market_condition")
    except Exception as e:
        print(f"[WARN] Failed to load BTC condition: {e}")
        return None

# === Redis Entry Score Utilities ===
def save_entry_score_to_redis(deal_id, score):
    try:
        key = f"FORK_ENTRY_SCORE:{deal_id}"
        REDIS.set(key, score)
    except Exception as e:
        print(f"[WARN] Failed to save entry score to Redis: {e}")

def load_entry_score_from_redis(deal_id):
    try:
        key = f"FORK_ENTRY_SCORE:{deal_id}"
        value = REDIS.get(key)
        if value is not None:
            return round(float(value), 4)
    except Exception as e:
        print(f"[WARN] Failed to load entry score from Redis: {e}")
    return None
