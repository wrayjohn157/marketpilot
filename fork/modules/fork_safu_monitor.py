from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging
import os
import sys

from ta.momentum import RSIIndicator
from ta.trend import MACD
import pandas as pd
import requests
import yaml

import hashlib
import hmac
from utils.credential_manager import get_3commas_credentials
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs
from config.unified_config_manager import get_config



#!/usr/bin/env python3
from
 pathlib import Path

# === Dynamic Paths (Market7 style) ===
BASE_DIR = get_path("base")  # ~/market7
CONFIG_PATH = BASE_DIR / "config" / "paper_cred.json"
SAFU_CONFIG_PATH = get_path("fork_safu_config")
SNAPSHOT_BASE = get_path("snapshots")

# === Credentials ===
with open(CONFIG_PATH) as f:
    creds = json.load(f)
TG_BOT_TOKEN = creds["telegram_bot_token"]
TG_CHAT_ID = creds["telegram_chat_id"]
API_KEY = creds["3commas_api_key"]
API_SECRET = creds["3commas_api_secret"]
BOT_ID = creds["3commas_bot_id"]
BASE_URL = "https://api.3commas.io"

# === SAFU Config ===
with open(SAFU_CONFIG_PATH) as f:
    safu_cfg = yaml.safe_load(f)
THRESHOLD = safu_cfg.get("min_score", 0.4)
ALERTS_ENABLED = safu_cfg.get("telegram_alerts", True)
AUTO_CLOSE_ENABLED = safu_cfg.get("auto_close", False)
WEIGHTS = safu_cfg.get("weights", {})

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Functions ===

def send_telegram(msg: Any) -> Any:
    if not ALERTS_ENABLED:
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        logging.warning(f"[TG] Error: {e}")

def generate_signature(path: str) -> str:
    return hmac.new(API_SECRET.encode(), path.encode(), hashlib.sha256).hexdigest()

def fetch_open_trades() -> Any:
    page = 1
    all_trades = []
    while True:
        url_path = f"/public/api/ver1/deals?bot_id={BOT_ID}&limit=100&offset={(page-1)*100}&scope=active"
        headers = {
            "ApiKey": API_KEY,
            "Signature": generate_signature(url_path),
            "Accept": "application/json"
        }
        try:
            resp = requests.get(BASE_URL + url_path, headers=headers, timeout=10)
            if resp.status_code != 200:
                logging.warning(f"[3C] Fetch error {resp.status_code}: {resp.text}")
                break
            deals = resp.json()
            logging.info(f"[3C] Fetched page {page}: {len(deals)} deals")
            all_trades.extend(deals)
            if len(deals) < 100:
                break
            page += 1
        except Exception as e:
            logging.warning(f"[3C] Fetch failed on page {page}: {e}")
            break
    logging.info(f"[3C] Total deals returned: {len(all_trades)}")
    return all_trades

def load_indicators_from_disk(symbol: Any, tf: Any = "15m") -> Any:
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    path = SNAPSHOT_BASE / date_str / f"{symbol}_{tf}_klines.json"
    if not path.exists():
        logging.warning(f"[Fallback] Kline file not found: {path}")
        return {}

    try:
        with open(path) as f:
            raw = json.load(f)

        df = pd.DataFrame(raw, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "num_trades",
            "taker_base_volume", "taker_quote_volume", "ignore"
        ])

        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        if len(df) < 50:
            return {}

        macd = MACD(df["close"])
        rsi = RSIIndicator(df["close"])

        volume_ma = df["volume"].rolling(20).mean()
        volume_change = (df["volume"].iloc[-1] - volume_ma.iloc[-1]) / volume_ma.iloc[-1] * 100

        return {
            "MACD_diff": macd.macd_diff().iloc[-1],
            "RSI14": rsi.rsi().iloc[-1],
            "VWAP": (df["volume"] * df["close"]).cumsum().iloc[-1] / df["volume"].cumsum().iloc[-1],
            "volume_drop_pct": max(0.0, -volume_change)
        }

    except Exception as e:
        logging.warning(f"[Fallback] Error loading indicators from disk for {symbol}: {e}")
        return {}

def fork_safu_score(token: Any, price_pct: Any) -> Any:
    score = 1.0
    try:
        if token["RSI14"] is not None and token["RSI14"] < 35:
            score -= WEIGHTS.get("token_rsi_below_35", 0)
        if token["MACD_diff"] is not None and token["MACD_diff"] < 0:
            score -= WEIGHTS.get("token_macd_bearish", 0)
        if token["VWAP"] is not None and token["price"] < token["VWAP"]:
            score -= WEIGHTS.get("token_price_below_vwap", 0)
        if token["volume_drop_pct"] is not None and token["volume_drop_pct"] > 20:
            score -= WEIGHTS.get("token_volume_drop", 0)

        if price_pct < -6:
            score -= WEIGHTS.get("drawdown_gt_6", 0)
        if price_pct < -7:
            score -= WEIGHTS.get("drawdown_gt_7", 0)

    except Exception as e:
        logging.warning(f"[SAFU] Scoring error for token {token}: {e}")
        return 0.0

    return round(max(0.0, score), 3)

def panic_sell(deal_id: Any) -> Any:
    url_path = f"/public/api/ver1/deals/{deal_id}/panic_sell"
    headers = {
        "ApiKey": API_KEY,
        "Signature": generate_signature(url_path),
        "Accept": "application/json"
    }
    try:
        resp = requests.post(BASE_URL + url_path, headers=headers, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        logging.warning(f"[3C] Panic sell error: {e}")
        return False

def analyze_trade(trade: Any) -> Any:
    symbol_3c = trade["pair"]
    symbol = symbol_3c.replace("USDT_", "")
    entry_price = float(trade.get("bought_average") or trade.get("base_order_average_price") or 0)
    current_price = float(trade.get("current_price") or 0)

    if entry_price == 0 or current_price == 0:
        logging.warning(f"[Skip] {symbol_3c} → Missing entry/current price")
        return

    price_pct = round((current_price - entry_price) / entry_price * 100, 2)

    indicators = load_indicators_from_disk(symbol)
    if not indicators:
        logging.warning(f"[Skip] {symbol_3c} → No indicators available")
        return

    token = {
        "price": current_price,
        "MACD_diff": indicators.get("MACD_diff"),
        "RSI14": indicators.get("RSI14"),
        "VWAP": indicators.get("VWAP"),
        "volume_drop_pct": indicators.get("volume_drop_pct")
    }

    score = fork_safu_score(token, price_pct)
    logging.info(f"{symbol_3c} SAFE | Score: {score} | PnL: {price_pct}%")

    if score < THRESHOLD:
        msg = (
            f"🚨 <b>SAFU Triggered</b>\n"
            f"📉 <b>{symbol_3c}</b> | PnL: <code>{price_pct:.2f}%</code>\n"
            f"❗ Score: <code>{score}</code>\n"
            f"🔻 RSI: <code>{token['RSI14']}</code> | MACD: <code>{token['MACD_diff']}</code>\n"
            f"⚠️ VWAP Drop: {'YES' if token['price'] < token['VWAP'] else 'NO'}"
        )
        send_telegram(msg)

        if AUTO_CLOSE_ENABLED:
            success = panic_sell(trade["id"])
            logging.info(f"[AUTO-CLOSE] {symbol_3c} → {'✅ Closed' if success else '❌ Failed'}")

def main() -> Any:
    trades = fetch_open_trades()
    logging.info(f"🔍 Checking {len(trades)} active deals (scope=active)...")
    for trade in trades:
        try:
            analyze_trade(trade)
        except Exception as e:
            logging.warning(f"[Trade] Error on {trade.get('pair')}: {e}")

if __name__ == "__main__":
    main()
