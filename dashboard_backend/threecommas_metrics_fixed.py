#!/usr/bin/env python3
"""
Fixed 3Commas Metrics Integration
- Uses new credential manager
- Proper error handling
- Data validation
- Retry logic
"""

import hashlib
import hmac
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# Setup logging
logger = logging.getLogger(__name__)

# === Config Loader ===
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.unified_config_manager import get_config, get_path
from utils.credential_manager import get_3commas_credentials


class ThreeCommasAPI:
    """3Commas API client with proper error handling and retry logic"""

    def __init__(self):
        self.credentials = None
        self.base_url = "https://api.3commas.io"
        self.max_retries = 3
        self.retry_delay = 1
        self._load_credentials()

    def _load_credentials(self):
        """Load 3Commas credentials using the new credential manager"""
        try:
            self.credentials = get_3commas_credentials()
            if not self.credentials:
                raise ValueError("No 3Commas credentials found")
            logger.info("3Commas credentials loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load 3Commas credentials: {e}")
            raise

    def _sign_request(self, path: str, query: str = "") -> Tuple[str, Dict[str, str]]:
        """Sign a request with HMAC-SHA256"""
        try:
            if query:
                message = f"{path}?{query}"
                url = f"{self.base_url}{path}?{query}"
            else:
                message = path
                url = f"{self.base_url}{path}"

            signature = hmac.new(
                self.credentials["3commas_api_secret"].encode("utf-8"),
                msg=message.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).hexdigest()

            headers = {
                "APIKEY": self.credentials["3commas_api_key"],
                "Signature": signature,
                "Content-Type": "application/json",
            }
            return url, headers
        except Exception as e:
            logger.error(f"Failed to sign request: {e}")
            raise

    def _make_request(
        self, path: str, query: str = "", method: str = "GET"
    ) -> Dict[str, Any]:
        """Make API request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                url, headers = self._sign_request(path, query)

                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=30)
                elif method == "POST":
                    response = requests.post(url, headers=headers, timeout=30)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"Rate limited, waiting {wait_time}s before retry {attempt + 1}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"API request failed: {response.status_code} - {response.text}"
                    )
                    if attempt == self.max_retries - 1:
                        raise Exception(
                            f"API request failed after {self.max_retries} attempts: {response.status_code}"
                        )
                    time.sleep(self.retry_delay)
                    continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay)

        raise Exception(f"Failed to make API request after {self.max_retries} attempts")

    def get_active_deals(self, bot_id: int) -> List[Dict[str, Any]]:
        """Get active deals for a bot"""
        try:
            path = "/public/api/ver1/deals"
            query = f"limit=1000&scope=active&bot_id={bot_id}"
            response = self._make_request(path, query)
            return response if isinstance(response, list) else []
        except Exception as e:
            logger.error(f"Failed to get active deals: {e}")
            return []

    def get_finished_deals(self, bot_id: int) -> List[Dict[str, Any]]:
        """Get finished deals for a bot"""
        try:
            path = "/public/api/ver1/deals"
            query = f"limit=1000&scope=finished&bot_id={bot_id}"
            response = self._make_request(path, query)
            return response if isinstance(response, list) else []
        except Exception as e:
            logger.error(f"Failed to get finished deals: {e}")
            return []

    def get_bot_stats(self, bot_id: int, account_id: int) -> Dict[str, Any]:
        """Get bot statistics"""
        try:
            path = "/public/api/ver1/bots/stats"
            query = f"bot_id={bot_id}&account_id={account_id}"
            response = self._make_request(path, query)
            return response if isinstance(response, dict) else {}
        except Exception as e:
            logger.error(f"Failed to get bot stats: {e}")
            return {}


def calculate_open_pnl(
    active_deals: List[Dict[str, Any]]
) -> Tuple[float, List[Dict[str, Any]]]:
    """Calculate open PnL for active deals"""
    total_open_pnl = 0.0
    deals_info = []

    for deal in active_deals:
        try:
            spent_amount = float(deal.get("bought_volume", 0))
            coins_bought = float(deal.get("bought_amount", 0))
            current_price = float(deal.get("current_price", 0))
            pair = deal.get("pair", "UNKNOWN")

            if spent_amount <= 0 or coins_bought <= 0:
                continue

            current_value = coins_bought * current_price
            open_pnl = current_value - spent_amount
            pnl_pct = (open_pnl / spent_amount) * 100 if spent_amount > 0 else 0

            entry_price = spent_amount / coins_bought if coins_bought > 0 else 0
            drawdown_pct = (
                ((entry_price - current_price) / entry_price) * 100
                if entry_price > 0 and current_price < entry_price
                else 0.0
            )
            drawdown_usd = (
                (entry_price - current_price) * coins_bought
                if entry_price > 0 and current_price < entry_price
                else 0.0
            )

            total_open_pnl += open_pnl
            deals_info.append(
                {
                    "id": deal.get("id", ""),
                    "pair": pair,
                    "spent_amount": round(spent_amount, 2),
                    "current_price": round(current_price, 6),
                    "entry_price": round(entry_price, 6),
                    "open_pnl": round(open_pnl, 2),
                    "open_pnl_pct": round(pnl_pct, 2),
                    "drawdown_pct": round(drawdown_pct, 2),
                    "drawdown_usd": round(drawdown_usd, 2),
                    "step": deal.get("step", 0),
                    "created_at": deal.get("created_at", ""),
                    "updated_at": deal.get("updated_at", ""),
                }
            )
        except Exception as e:
            logger.warning(
                f"Failed to calculate PnL for deal {deal.get('id', 'unknown')}: {e}"
            )
            continue

    return total_open_pnl, deals_info


def calculate_closed_deals_stats(
    finished_deals: List[Dict[str, Any]]
) -> Tuple[float, float, int, float]:
    """Calculate statistics for closed deals"""
    now = datetime.utcnow()
    last_24h = now - timedelta(days=1)
    total_realized_pnl = 0.0
    daily_realized_pnl = 0.0
    total_deals = 0
    wins = 0

    for deal in finished_deals:
        try:
            profit = float(deal.get("final_profit", 0))
            closed_at_str = deal.get("closed_at", "")

            if not closed_at_str:
                continue

            # Parse timestamp
            if closed_at_str.endswith("Z"):
                closed_at_str = closed_at_str.replace("Z", "+00:00")

            closed_at = datetime.fromisoformat(closed_at_str)

            total_realized_pnl += profit
            total_deals += 1
            if profit > 0:
                wins += 1

            if closed_at >= last_24h:
                daily_realized_pnl += profit

        except Exception as e:
            logger.warning(
                f"Failed to process closed deal {deal.get('id', 'unknown')}: {e}"
            )
            continue

    win_rate = round((wins / total_deals) * 100, 1) if total_deals > 0 else 0
    return total_realized_pnl, daily_realized_pnl, total_deals, win_rate


def get_3commas_metrics() -> Dict[str, Any]:
    """Get comprehensive 3Commas metrics"""
    try:
        # Initialize API client
        api = ThreeCommasAPI()

        # Get bot and account IDs from credentials
        bot_id = api.credentials.get("3commas_bot_id", 16017224)
        account_id = api.credentials.get("3commas_account_id", 32994602)

        logger.info(f"Fetching metrics for bot {bot_id}, account {account_id}")

        # Get data from API
        active_deals = api.get_active_deals(bot_id)
        finished_deals = api.get_finished_deals(bot_id)
        bot_stats = api.get_bot_stats(bot_id, account_id)

        # Calculate metrics
        total_open_pnl, open_deals_info = calculate_open_pnl(active_deals)
        (
            realized_pnl_alltime,
            daily_realized_pnl,
            total_deals,
            win_rate,
        ) = calculate_closed_deals_stats(finished_deals)

        # Prepare response
        response = {
            "bot_id": bot_id,
            "account_id": account_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "open_pnl": round(total_open_pnl, 2),
                "daily_realized_pnl": round(daily_realized_pnl, 2),
                "realized_pnl_alltime": round(realized_pnl_alltime, 2),
                "total_deals": total_deals,
                "win_rate": win_rate,
                "active_deals": open_deals_info,
                "active_deals_count": len(open_deals_info),
            },
            "bot_stats": bot_stats,
            "status": "success",
        }

        logger.info(
            f"Successfully fetched 3Commas metrics: {len(open_deals_info)} active deals, {total_deals} total deals"
        )
        return response

    except Exception as e:
        logger.error(f"Failed to get 3Commas metrics: {e}")
        return {
            "error": str(e),
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "open_pnl": 0,
                "daily_realized_pnl": 0,
                "realized_pnl_alltime": 0,
                "total_deals": 0,
                "win_rate": 0,
                "active_deals": [],
                "active_deals_count": 0,
            },
            "bot_stats": {},
        }


if __name__ == "__main__":
    print(json.dumps(get_3commas_metrics(), indent=2))
