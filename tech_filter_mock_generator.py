#!/usr/bin/env python3
"""
Tech Filter Mock Data Generator
Generates realistic technical indicators based on actual trade data
"""

import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests

from utils.redis_manager import get_redis_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechFilterMockGenerator:
    def __init__(self):
        self.redis = get_redis_manager()
        self.api_base_url = "http://155.138.202.35:8001"

    def get_active_trades(self) -> List[Dict]:
        """Get active trades from our API"""
        try:
            response = requests.get(
                f"{self.api_base_url}/dca-trades-active", timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("dca_trades", [])
        except Exception as e:
            logger.error(f"Failed to get active trades: {e}")
            return []

    def generate_realistic_indicators(self, trade: Dict) -> Dict[str, Any]:
        """Generate realistic technical indicators based on trade data"""
        symbol = trade.get("symbol", "BTC").replace("USDT_", "")
        current_price = trade.get("current_price", 100000)
        entry_price = trade.get("avg_entry_price", current_price)
        open_pnl = trade.get("open_pnl", 0)
        confidence_score = trade.get("confidence_score", 0.5)

        # Calculate price change percentage
        price_change_pct = ((current_price - entry_price) / entry_price) * 100

        # Generate RSI based on price momentum and confidence
        base_rsi = 50
        if price_change_pct > 2:
            base_rsi = 65 + random.uniform(-5, 5)  # Bullish momentum
        elif price_change_pct < -2:
            base_rsi = 35 + random.uniform(-5, 5)  # Bearish momentum
        else:
            base_rsi = 45 + random.uniform(-10, 10)  # Neutral

        # Adjust RSI based on confidence
        if confidence_score > 0.7:
            base_rsi += 5  # Higher confidence = more extreme RSI
        elif confidence_score < 0.3:
            base_rsi -= 5  # Lower confidence = more neutral RSI

        rsi = max(0, min(100, base_rsi))

        # Generate MACD based on price trend
        macd = (current_price - entry_price) / entry_price * 1000
        macd_signal = macd * 0.8 + random.uniform(-0.1, 0.1)
        macd_histogram = macd - macd_signal

        # Generate ADX based on volatility and trend strength
        volatility = abs(price_change_pct)
        if volatility > 5:
            adx = 35 + random.uniform(-5, 10)  # High volatility = strong trend
        elif volatility > 2:
            adx = 25 + random.uniform(-5, 5)  # Medium volatility
        else:
            adx = 15 + random.uniform(-5, 5)  # Low volatility

        adx = max(0, min(50, adx))

        # Generate EMAs
        ema_20 = current_price * (1 + random.uniform(-0.02, 0.02))
        ema_50 = current_price * (1 + random.uniform(-0.03, 0.03))
        ema_200 = current_price * (1 + random.uniform(-0.05, 0.05))

        # Generate Stochastic RSI
        stoch_rsi_k = rsi + random.uniform(-10, 10)
        stoch_rsi_d = stoch_rsi_k + random.uniform(-5, 5)

        # Generate ATR based on volatility
        atr = current_price * (volatility / 100) * random.uniform(0.8, 1.2)

        # Generate PSAR
        psar = current_price * (1 + random.uniform(-0.01, 0.01))

        # Determine market status
        if rsi > 70 and adx > 25:
            status = "BEARISH"
        elif rsi < 30 and adx > 25:
            status = "BULLISH"
        elif adx > 25:
            status = "TRENDING"
        else:
            status = "NEUTRAL"

        return {
            "symbol": symbol,
            "timeframe": "1h",
            "timestamp": int(time.time()),
            "price": {
                "close": current_price,
                "high": current_price * (1 + random.uniform(0, 0.02)),
                "low": current_price * (1 - random.uniform(0, 0.02)),
                "volume": trade.get("bought_amount", 0) * random.uniform(0.8, 1.2),
            },
            "indicators": {
                "rsi": round(rsi, 2),
                "macd": round(macd, 4),
                "macd_signal": round(macd_signal, 4),
                "macd_histogram": round(macd_histogram, 4),
                "adx": round(adx, 2),
                "ema_20": round(ema_20, 2),
                "ema_50": round(ema_50, 2),
                "ema_200": round(ema_200, 2),
                "stoch_rsi_k": round(stoch_rsi_k, 2),
                "stoch_rsi_d": round(stoch_rsi_d, 2),
                "atr": round(atr, 2),
                "psar": round(psar, 2),
            },
            "market_status": status,
            "trade_context": {
                "entry_price": entry_price,
                "current_price": current_price,
                "open_pnl": open_pnl,
                "price_change_pct": round(price_change_pct, 2),
                "confidence_score": confidence_score,
            },
        }

    def save_to_redis(self, symbol: str, indicators: Dict):
        """Save indicators to Redis with proper keys"""
        try:
            # Save individual indicators
            for indicator_name, value in indicators["indicators"].items():
                key = f"tech_filter:{symbol}:1h:{indicator_name}"
                self.redis.set_cache(key, str(value), ttl=3600)  # 1 hour TTL

            # Save complete indicator set
            key = f"tech_filter:{symbol}:1h:complete"
            self.redis.set_cache(key, json.dumps(indicators), ttl=3600)

            logger.info(f"Saved {symbol} indicators to Redis")

        except Exception as e:
            logger.error(f"Failed to save {symbol} to Redis: {e}")

    def generate_tech_filter_score(self, indicators: Dict) -> float:
        """Generate tech filter score (0-1) based on indicators"""
        score = 0.5  # Base score

        rsi = indicators["indicators"]["rsi"]
        macd = indicators["indicators"]["macd"]
        macd_signal = indicators["indicators"]["macd_signal"]
        adx = indicators["indicators"]["adx"]
        ema_50 = indicators["indicators"]["ema_50"]
        current_price = indicators["price"]["close"]

        # RSI scoring
        if 30 <= rsi <= 70:
            score += 0.1  # Good RSI range
        elif rsi < 30:
            score += 0.2  # Oversold (buying opportunity)
        elif rsi > 70:
            score -= 0.2  # Overbought (selling opportunity)

        # MACD scoring
        if macd > macd_signal:
            score += 0.15  # Bullish MACD
        else:
            score -= 0.15  # Bearish MACD

        # ADX scoring
        if adx > 25:
            score += 0.1  # Strong trend
        elif adx < 15:
            score -= 0.1  # Weak trend

        # Price vs EMA scoring
        if current_price > ema_50:
            score += 0.1  # Above EMA50
        else:
            score -= 0.1  # Below EMA50

        # Clamp to 0-1 range
        return max(0, min(1, score))

    def collect_and_process(self):
        """Main collection and processing loop"""
        logger.info("🚀 Starting tech filter data collection")

        try:
            # Get active trades
            trades = self.get_active_trades()
            if not trades:
                logger.warning("No active trades found")
                return

            logger.info(f"Processing {len(trades)} active trades")

            for trade in trades:
                try:
                    # Generate indicators
                    indicators = self.generate_realistic_indicators(trade)

                    # Generate tech filter score
                    tech_score = self.generate_tech_filter_score(indicators)
                    indicators["tech_filter_score"] = round(tech_score, 3)

                    # Save to Redis
                    symbol = indicators["symbol"]
                    self.save_to_redis(symbol, indicators)

                    logger.info(
                        f"✅ {symbol}: RSI={indicators['indicators']['rsi']}, "
                        f"MACD={indicators['indicators']['macd']:.4f}, "
                        f"ADX={indicators['indicators']['adx']}, "
                        f"Score={tech_score:.3f}"
                    )

                except Exception as e:
                    logger.error(
                        f"Error processing trade {trade.get('deal_id', 'unknown')}: {e}"
                    )
                    continue

            logger.info("✅ Tech filter data collection complete")

        except Exception as e:
            logger.error(f"Error in collection loop: {e}")


def main():
    generator = TechFilterMockGenerator()
    generator.collect_and_process()


if __name__ == "__main__":
    main()
