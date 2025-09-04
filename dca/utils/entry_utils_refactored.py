#!/usr/bin/env python3
"""Refactored entry utilities with centralized credential management."""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator

from config.unified_config_manager import (
    get_all_configs,
    get_all_paths,
    get_config,
    get_path,
)
from utils.credential_manager import CredentialError, get_3commas_credentials
from utils.redis_manager import get_redis_manager

logger = logging.getLogger(__name__)


class ThreeCommasAPI:
    """3Commas API client with centralized credential management."""

    def __init__(self, profile: str = "default"):
        """Initialize 3Commas API client.

        Args:
            profile: Credential profile name
        """
        self.profile = profile
        self._credentials = None
        self._redis_client = None

    @property
    def credentials(self) -> Dict[str, Any]:
        """Get 3Commas credentials."""
        if self._credentials is None:
            try:
                self._credentials = get_3commas_credentials(self.profile)
            except CredentialError as e:
                logger.error(f"Failed to load 3Commas credentials: {e}")
                raise
        return self._credentials

    @property
    def redis_client(self) -> redis.Redis:
        """Get Redis client."""
        if self._redis_client is None:
            try:
                self._redis_client = get_redis_manager()
            except redis.ConnectionError as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self._redis_client = None
        return self._redis_client

    def _generate_signature(self, path: str) -> str:
        """Generate API signature for 3Commas.

        Args:
            path: API path

        Returns:
            Generated signature
        """
        return hmac.new(
            self.credentials["3commas_api_secret"].encode(),
            path.encode(),
            hashlib.sha256,
        ).hexdigest()

    def _make_request(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to 3Commas API.

        Args:
            path: API path
            params: Query parameters

        Returns:
            API response data
        """
        url = f"https://api.3commas.io{path}"
        signature = self._generate_signature(path)

        headers = {
            "Apikey": self.credentials["3commas_api_key"],
            "Signature": signature,
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"3Commas API request failed: {e}")
            raise

    def get_live_trades(self) -> List[Dict[str, Any]]:
        """Get live trades from 3Commas.

        Returns:
            List of live trades
        """
        try:
            bot_id = self.credentials["3commas_bot_id"]
            all_deals = []
            page = 1

            while True:
                query = f"limit=1000&scope=active&bot_id={bot_id}&page={page}"
                path = f"/public/api/ver1/deals?{query}"

                response_data = self._make_request(path)
                deals = response_data.get("data", [])

                if not deals:
                    break

                all_deals.extend(deals)
                page += 1

            # Normalize deal data
            return self._normalize_trades(all_deals)

        except Exception as e:
            logger.error(f"Failed to fetch live trades: {e}")
            return []

    def _normalize_trades(self, deals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize trade data.

        Args:
            deals: Raw deal data from API

        Returns:
            Normalized trade data
        """
        for deal in deals:
            # Calculate average entry price
            try:
                if deal.get("bought_volume", 0) > 0:
                    avg_price = float(deal["bought_amount"]) / float(
                        deal["bought_volume"]
                    )
                else:
                    avg_price = None
            except (ValueError, TypeError, ZeroDivisionError) as e:
                logger.warning(
                    f"Failed to calculate average price for deal {deal.get('id', 'unknown')}: {e}"
                )
                avg_price = None

            deal["avg_entry_price"] = avg_price

        return deals

    def send_dca_signal(self, pair: str, volume: float = 15.0) -> bool:
        """Send DCA signal to 3Commas.

        Args:
            pair: Trading pair
            volume: Volume to add

        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "action": "add_funds_in_quote",
                "message_type": "bot",
                "bot_id": self.credentials["3commas_bot_id"],
                "email_token": self.credentials.get("3commas_email_token"),
                "delay_seconds": 0,
                "pair": pair,
                "volume": volume,
            }

            url = "https://app.3commas.io/trade_signal/trading_view"
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(f"✅ DCA signal sent for {pair} | Volume: {volume} USDT")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to send DCA signal for {pair}: {e}")
            return False
        except KeyError as e:
            logger.error(f"Missing credential: {e}")
            return False


def get_live_3c_trades(profile: str = "default") -> List[Dict[str, Any]]:
    """Get live 3Commas trades (legacy compatibility).

    Args:
        profile: Credential profile name

    Returns:
        List of live trades
    """
    api = ThreeCommasAPI(profile)
    return api.get_live_trades()


def send_dca_signal(pair: str, volume: float = 15.0, profile: str = "default") -> bool:
    """Send DCA signal (legacy compatibility).

    Args:
        pair: Trading pair
        volume: Volume to add
        profile: Credential profile name

    Returns:
        True if successful, False otherwise
    """
    api = ThreeCommasAPI(profile)
    return api.send_dca_signal(pair, volume)


def get_latest_indicators(symbol: str, tf: str = "15m") -> Optional[Dict[str, Any]]:
    """Get latest indicators for a symbol.

    Args:
        symbol: Trading symbol
        tf: Timeframe

    Returns:
        Indicator data or None
    """
    try:
        snapshot_base = get_path("snapshots")
        today = datetime.utcnow().strftime("%Y-%m-%d")
        indicator_path = (
            snapshot_base / today / f"{symbol.upper()}_{tf}_indicators.json"
        )

        if not indicator_path.exists():
            logger.warning(f"No indicators found for {symbol} at {indicator_path}")
            return None

        with open(indicator_path, "r") as f:
            return json.load(f)

    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load indicators for {symbol}: {e}")
        return None


def load_fork_entry_score(symbol: str, deal_id: int) -> Optional[Dict[str, Any]]:
    """Load fork entry score for a symbol and deal.

    Args:
        symbol: Trading symbol
        deal_id: Deal identifier

    Returns:
        Fork entry score data or None
    """
    try:
        fork_history = get_path("fork_history")
        score_path = fork_history / f"{symbol}_{deal_id}_score.json"

        if not score_path.exists():
            return None

        with open(score_path, "r") as f:
            return json.load(f)

    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load fork entry score for {symbol}_{deal_id}: {e}")
        return None


def simulate_new_avg_price(
    current_avg: float, current_volume: float, new_price: float, new_volume: float
) -> float:
    """Simulate new average price after adding volume.

    Args:
        current_avg: Current average price
        current_volume: Current volume
        new_price: New price to add
        new_volume: New volume to add

    Returns:
        New average price
    """
    if current_volume <= 0:
        return new_price

    total_amount = (current_avg * current_volume) + (new_price * new_volume)
    total_volume = current_volume + new_volume

    return total_amount / total_volume if total_volume > 0 else current_avg


def get_rsi_slope(prices: List[float], period: int = 14) -> float:
    """Calculate RSI slope.

    Args:
        prices: Price data
        period: RSI period

    Returns:
        RSI slope
    """
    if len(prices) < period + 1:
        return 0.0

    try:
        df = pd.DataFrame({"close": prices})
        rsi = RSIIndicator(df["close"], window=period).rsi()

        if len(rsi) < 2:
            return 0.0

        return float(rsi.iloc[-1] - rsi.iloc[-2])
    except Exception as e:
        logger.warning(f"Failed to calculate RSI slope: {e}")
        return 0.0


def get_macd_lift(
    prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> float:
    """Calculate MACD lift.

    Args:
        prices: Price data
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period

    Returns:
        MACD lift
    """
    if len(prices) < slow + signal:
        return 0.0

    try:
        df = pd.DataFrame({"close": prices})
        macd = MACD(df["close"], window_fast=fast, window_slow=slow, window_sign=signal)

        macd_line = macd.macd()
        signal_line = macd.macd_signal()

        if len(macd_line) < 2 or len(signal_line) < 2:
            return 0.0

        current_hist = macd_line.iloc[-1] - signal_line.iloc[-1]
        previous_hist = macd_line.iloc[-2] - signal_line.iloc[-2]

        return float(current_hist - previous_hist)
    except Exception as e:
        logger.warning(f"Failed to calculate MACD lift: {e}")
        return 0.0


def save_entry_score_to_redis(
    symbol: str, deal_id: int, score_data: Dict[str, Any]
) -> bool:
    """Save entry score to Redis.

    Args:
        symbol: Trading symbol
        deal_id: Deal identifier
        score_data: Score data to save

    Returns:
        True if successful, False otherwise
    """
    try:
        api = ThreeCommasAPI()
        if api.redis_client is None:
            return False

        key = f"entry_score:{symbol}:{deal_id}"
        api.redis_client.setex(key, 3600, json.dumps(score_data))  # 1 hour TTL
        return True
    except Exception as e:
        logger.error(f"Failed to save entry score to Redis: {e}")
        return False


def load_entry_score_from_redis(symbol: str, deal_id: int) -> Optional[Dict[str, Any]]:
    """Load entry score from Redis.

    Args:
        symbol: Trading symbol
        deal_id: Deal identifier

    Returns:
        Score data or None
    """
    try:
        api = ThreeCommasAPI()
        if api.redis_client is None:
            return None

        key = f"entry_score:{symbol}:{deal_id}"
        data = api.redis_client.get(key)

        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to load entry score from Redis: {e}")
        return None
