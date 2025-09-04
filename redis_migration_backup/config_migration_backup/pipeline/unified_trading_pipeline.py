#!/usr/bin/env python3
"""
Unified Trading Pipeline - Streamlined Tech Filter → Fork → TV Flow
Replaces fragmented pipeline with unified, error-resistant system
"""

import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import yaml
from dataclasses import dataclass
from enum import Enum

from config.config_loader import PATHS
from utils.credential_manager import get_3commas_credentials
from utils.redis_manager import get_redis_manager, RedisKeyManager



class PipelineStage(Enum):
    TECH_FILTER = "tech_filter"
    FORK_SCORE = "fork_score"
    TV_ADJUST = "tv_adjust"
    EXECUTE = "execute"


@dataclass
class Trade:
    symbol: str
    score: float
    indicators: Dict[str, Any]
    tv_tag: Optional[str] = None
    tv_kicker: float = 0.0
    adjusted_score: float = 0.0
    passed: bool = False
    timestamp: int = 0
    reason: str = ""


@dataclass
class PipelineConfig:
    min_tech_score: float = 0.6
    min_fork_score: float = 0.73
    min_tv_score: float = 0.8
    btc_condition: str = "neutral"
    tv_enabled: bool = True
    max_trades_per_batch: int = 10


class DataValidator:
    """Validates data at each pipeline stage"""
    
    @staticmethod
    def validate_indicators(indicators: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate indicator data quality"""
        required_keys = ['RSI14', 'MACD', 'ADX14', 'EMA50']
        missing_keys = [key for key in required_keys if key not in indicators]
        
        if missing_keys:
            return False, f"Missing indicators: {missing_keys}"
        
        # Check for reasonable values
        if not (0 <= indicators.get('RSI14', 0) <= 100):
            return False, "RSI14 out of range"
        
        if indicators.get('ADX14', 0) < 0:
            return False, "ADX14 negative"
        
        return True, "Valid"
    
    @staticmethod
    def validate_trade(trade: Trade) -> Tuple[bool, str]:
        """Validate trade before execution"""
        if not trade.symbol:
            return False, "Missing symbol"
        
        if trade.score < 0 or trade.score > 1:
            return False, f"Invalid score: {trade.score}"
        
        if trade.adjusted_score < 0:
            return False, f"Invalid adjusted score: {trade.adjusted_score}"
        
        return True, "Valid"


class TechFilter:
    """Streamlined technical indicator filtering"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
        
        # Dynamic thresholds based on market condition
        self.thresholds = {
            "neutral": {
                "rsi_range": [35, 65],
                "adx_min": 20,
                "macd_hist_min": 0.0,
            },
            "bullish": {
                "rsi_max": 75,
                "adx_min": 25,
                "macd_hist_min": 0.001,
            },
            "bearish": {
                "rsi_max": 45,
                "adx_min": 15,
                "macd_hist_min": -0.001,
            }
        }
    
    def filter_symbol(self, symbol: str, indicators: Dict[str, Any]) -> Tuple[bool, str, float]:
        """Filter symbol based on technical indicators"""
        # Validate indicators
        is_valid, reason = DataValidator.validate_indicators(indicators)
        if not is_valid:
            return False, reason, 0.0
        
        # Get thresholds for current market condition
        thresholds = self.thresholds.get(self.config.btc_condition, self.thresholds["neutral"])
        
        # Calculate tech score
        score = 0.0
        reasons = []
        
        # RSI check
        rsi = indicators.get('RSI14', 50)
        if 'rsi_range' in thresholds:
            rsi_min, rsi_max = thresholds['rsi_range']
            if rsi_min <= rsi <= rsi_max:
                score += 0.3
            else:
                reasons.append(f"RSI {rsi} not in range {rsi_min}-{rsi_max}")
        elif 'rsi_max' in thresholds:
            if rsi <= thresholds['rsi_max']:
                score += 0.3
            else:
                reasons.append(f"RSI {rsi} > {thresholds['rsi_max']}")
        
        # ADX check
        adx = indicators.get('ADX14', 0)
        adx_min = thresholds.get('adx_min', 20)
        if adx >= adx_min:
            score += 0.3
        else:
            reasons.append(f"ADX {adx} < {adx_min}")
        
        # MACD check
        macd_hist = indicators.get('MACD_Histogram', 0)
        macd_hist_min = thresholds.get('macd_hist_min', 0)
        if macd_hist >= macd_hist_min:
            score += 0.4
        else:
            reasons.append(f"MACD Hist {macd_hist} < {macd_hist_min}")
        
        passed = score >= self.config.min_tech_score
        reason = "; ".join(reasons) if not passed else "Passed tech filter"
        
        return passed, reason, score


class ForkScorer:
    """Advanced fork scoring with ML-like features"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
        
        # Dynamic weights based on market condition
        self.weights = {
            "neutral": {
                "macd_histogram": 0.25,
                "rsi_recovery": 0.20,
                "stoch_cross": 0.15,
                "adx_rising": 0.20,
                "ema_reclaim": 0.20,
            },
            "bullish": {
                "macd_histogram": 0.30,
                "rsi_recovery": 0.15,
                "stoch_cross": 0.20,
                "adx_rising": 0.25,
                "ema_reclaim": 0.10,
            },
            "bearish": {
                "macd_histogram": 0.20,
                "rsi_recovery": 0.30,
                "stoch_cross": 0.20,
                "adx_rising": 0.15,
                "ema_reclaim": 0.15,
            }
        }
    
    def score_symbol(self, symbol: str, indicators: Dict[str, Any]) -> Tuple[bool, str, float, Dict[str, float]]:
        """Score symbol for fork potential"""
        # Get weights for current market condition
        weights = self.weights.get(self.config.btc_condition, self.weights["neutral"])
        
        # Calculate subscores
        subscores = {}
        
        # MACD Histogram
        macd = indicators.get('MACD', 0)
        macd_signal = indicators.get('MACD_signal', 0)
        macd_hist = indicators.get('MACD_Histogram', 0)
        macd_hist_prev = indicators.get('MACD_Histogram_Prev', 0)
        
        if macd > macd_signal and macd_hist > macd_hist_prev:
            subscores['macd_histogram'] = 1.0
        else:
            subscores['macd_histogram'] = 0.0
        
        # RSI Recovery
        rsi = indicators.get('RSI14', 50)
        subscores['rsi_recovery'] = min(max((rsi - 30) / 20, 0), 1)
        
        # Stochastic Cross
        stoch_k = indicators.get('StochRSI_K', 50)
        stoch_d = indicators.get('StochRSI_D', 50)
        if stoch_k > stoch_d and stoch_k < 80:
            subscores['stoch_cross'] = min(max((stoch_k - stoch_d) / 25, 0), 1)
        else:
            subscores['stoch_cross'] = 0.0
        
        # ADX Rising
        adx = indicators.get('ADX14', 0)
        subscores['adx_rising'] = min(adx / 20, 1.0) if adx > 10 else 0.0
        
        # EMA Price Reclaim
        price = indicators.get('latest_close', 0)
        ema50 = indicators.get('EMA50', 0)
        subscores['ema_reclaim'] = 1.0 if price > ema50 else 0.0
        
        # Calculate weighted score
        score = sum(subscores[key] * weights.get(key, 0) for key in subscores)
        
        # Apply BTC sentiment multiplier
        btc_multiplier = self._get_btc_multiplier()
        adjusted_score = score * btc_multiplier
        
        passed = adjusted_score >= self.config.min_fork_score
        reason = f"Score {adjusted_score:.3f} {'>=' if passed else '<'} {self.config.min_fork_score}"
        
        return passed, reason, adjusted_score, subscores
    
    def _get_btc_multiplier(self) -> float:
        """Get BTC sentiment multiplier"""
        try:
            btc_price = float(self.redis.get("indicators:BTC:1h:latest_close") or 0)
            btc_ema50 = float(self.redis.get("indicators:BTC:1h:EMA50") or 0)
            btc_rsi = float(self.redis.get("indicators:BTC:15m:RSI14") or 50)
            btc_adx = float(self.redis.get("indicators:BTC:1h:ADX14") or 0)
            
            multiplier = 1.0
            
            if btc_price > btc_ema50 and btc_adx > 20:
                multiplier += 0.10
            elif btc_price > btc_ema50:
                multiplier += 0.05
            elif btc_price < btc_ema50 and btc_adx > 15:
                multiplier -= 0.05
            
            if btc_rsi < 35:
                multiplier -= 0.05
            
            return max(0.8, min(multiplier, 1.2))
        except Exception:
            return 1.0


class TVAdjuster:
    """TradingView signal adjustment"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        
        # TV score weights
        self.tv_weights = {
            "strong_buy": 0.30,
            "buy": 0.20,
            "neutral": 0.00,
            "sell": -0.20,
            "strong_sell": -0.30
        }
    
    def adjust_score(self, trade: Trade, tv_tag: str) -> Trade:
        """Adjust trade score based on TV signal"""
        if not self.config.tv_enabled:
            trade.adjusted_score = trade.score
            trade.reason = "TV disabled"
            return trade
        
        tv_kicker = self.tv_weights.get(tv_tag, 0.0)
        trade.tv_tag = tv_tag
        trade.tv_kicker = tv_kicker
        trade.adjusted_score = trade.score + tv_kicker
        trade.passed = trade.adjusted_score >= self.config.min_tv_score
        
        if trade.passed:
            trade.reason = f"TV adjusted: {trade.score:.3f} + {tv_kicker:.3f} = {trade.adjusted_score:.3f}"
        else:
            trade.reason = f"TV adjusted but below threshold: {trade.adjusted_score:.3f} < {self.config.min_tv_score}"
        
        return trade


class TradeExecutor:
    """Execute trades via 3Commas API"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
        
        # Load credentials
        try:
            creds = get_3commas_credentials()
            self.bot_id = creds["3commas_bot_id"]
            self.bot_id2 = creds.get("3commas_bot_id2")
            self.email_token = creds["3commas_email_token"]
        except Exception as e:
            logging.error(f"Failed to load credentials: {e}")
            self.bot_id = None
            self.bot_id2 = None
            self.email_token = None
    
    async def execute_trade(self, trade: Trade) -> bool:
        """Execute trade via 3Commas API"""
        if not self.bot_id:
            logging.error("No bot ID available for trade execution")
            return False
        
        try:
            # Format pair for 3Commas
            pair = f"USDT_{trade.symbol.replace('USDT', '')}"
            
            # Send to primary bot
            success1 = await self._send_to_bot(pair, self.bot_id)
            
            # Send to secondary bot if available
            success2 = True
            if self.bot_id2:
                success2 = await self._send_to_bot(pair, self.bot_id2)
            
            if success1 or success2:
                logging.info(f"✅ Executed trade: {trade.symbol} (Score: {trade.adjusted_score:.3f})")
                return True
            else:
                logging.error(f"❌ Failed to execute trade: {trade.symbol}")
                return False
                
        except Exception as e:
            logging.error(f"Error executing trade {trade.symbol}: {e}")
            return False
    
    async def _send_to_bot(self, pair: str, bot_id: str) -> bool:
        """Send trade signal to specific bot"""
        # Implementation would go here
        # For now, just log the action
        logging.info(f"Sending {pair} to bot {bot_id}")
        return True


class UnifiedTradingPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.tech_filter = TechFilter(config)
        self.fork_scorer = ForkScorer(config)
        self.tv_adjuster = TVAdjuster(config)
        self.executor = TradeExecutor(config)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        self.logger = logging.getLogger(__name__)
    
    async def process_symbols(self, symbols: List[str]) -> List[Trade]:
        """Process list of symbols through the complete pipeline"""
        self.logger.info(f"🚀 Starting pipeline for {len(symbols)} symbols")
        
        results = []
        
        for symbol in symbols:
            try:
                # Stage 1: Tech Filter
                indicators = await self._get_indicators(symbol)
                if not indicators:
                    self.logger.warning(f"⚠️ No indicators for {symbol}")
                    continue
                
                passed, reason, tech_score = self.tech_filter.filter_symbol(symbol, indicators)
                if not passed:
                    self.logger.info(f"❌ {symbol} failed tech filter: {reason}")
                    continue
                
                # Stage 2: Fork Scoring
                passed, reason, fork_score, subscores = self.fork_scorer.score_symbol(symbol, indicators)
                if not passed:
                    self.logger.info(f"❌ {symbol} failed fork scoring: {reason}")
                    continue
                
                # Create trade object
                trade = Trade(
                    symbol=symbol,
                    score=fork_score,
                    indicators=indicators,
                    timestamp=int(datetime.utcnow().timestamp() * 1000)
                )
                
                # Stage 3: TV Adjustment
                tv_tag = await self._get_tv_tag(symbol)
                trade = self.tv_adjuster.adjust_score(trade, tv_tag)
                
                if not trade.passed:
                    self.logger.info(f"❌ {symbol} failed TV adjustment: {trade.reason}")
                    continue
                
                # Stage 4: Execute Trade
                success = await self.executor.execute_trade(trade)
                if success:
                    results.append(trade)
                    self.logger.info(f"✅ {symbol} executed successfully")
                else:
                    self.logger.error(f"❌ {symbol} execution failed")
                
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
                continue
        
        self.logger.info(f"🎯 Pipeline complete: {len(results)} trades executed")
        return results
    
    async def _get_indicators(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get indicators for symbol from Redis"""
        try:
            redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
            data = redis.get(f"{symbol.upper()}_1h")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get indicators for {symbol}: {e}")
            return None
    
    async def _get_tv_tag(self, symbol: str) -> str:
        """Get TradingView tag for symbol"""
        try:
            # Implementation would load from TV data
            return "neutral"  # Placeholder
        except Exception:
            return "neutral"


async def main():
    """Main entry point"""
    config = PipelineConfig(
        min_tech_score=0.6,
        min_fork_score=0.73,
        min_tv_score=0.8,
        btc_condition="neutral",
        tv_enabled=True,
        max_trades_per_batch=10
    )
    
    pipeline = UnifiedTradingPipeline(config)
    
    # Example symbols to process
    symbols = ["BTC", "ETH", "ADA", "DOT", "LINK"]
    
    results = await pipeline.process_symbols(symbols)
    
    print(f"Pipeline completed: {len(results)} trades executed")


if __name__ == "__main__":
    asyncio.run(main())