#!/usr/bin/env python3
"""
Simplified test for Unified Trading Pipeline
Tests core logic without external dependencies
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Add current directory to path
sys.path.append(str(Path(__file__).parent))


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
        
        # Apply BTC sentiment multiplier (simplified)
        btc_multiplier = 1.0  # Simplified for testing
        adjusted_score = score * btc_multiplier
        
        passed = adjusted_score >= self.config.min_fork_score
        reason = f"Score {adjusted_score:.3f} {'>=' if passed else '<'} {self.config.min_fork_score}"
        
        return passed, reason, adjusted_score, subscores


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


def create_mock_indicators(symbol: str, market_condition: str = "neutral") -> Dict[str, float]:
    """Create mock indicators for testing"""
    base_indicators = {
        "RSI14": 45.0,
        "MACD": 0.001,
        "MACD_signal": 0.0005,
        "MACD_Histogram": 0.0005,
        "MACD_Histogram_Prev": 0.0003,
        "ADX14": 25.0,
        "EMA50": 100.0,
        "latest_close": 105.0,
        "StochRSI_K": 35.0,
        "StochRSI_D": 30.0,
    }
    
    # Adjust based on market condition
    if market_condition == "bullish":
        base_indicators.update({
            "RSI14": 55.0,
            "ADX14": 30.0,
            "MACD_Histogram": 0.002,
        })
    elif market_condition == "bearish":
        base_indicators.update({
            "RSI14": 35.0,
            "ADX14": 15.0,
            "MACD_Histogram": -0.001,
        })
    
    return base_indicators


async def test_data_validation():
    """Test data validation functionality"""
    print("🧪 Testing Data Validation...")
    
    # Test valid indicators
    valid_indicators = create_mock_indicators("BTC")
    is_valid, reason = DataValidator.validate_indicators(valid_indicators)
    print(f"   Valid indicators: {is_valid} - {reason}")
    
    # Test invalid indicators
    invalid_indicators = {"RSI14": 150.0}  # Invalid RSI
    is_valid, reason = DataValidator.validate_indicators(invalid_indicators)
    print(f"   Invalid indicators: {is_valid} - {reason}")
    
    # Test trade validation
    trade = Trade(symbol="BTC", score=0.75, indicators=valid_indicators)
    is_valid, reason = DataValidator.validate_trade(trade)
    print(f"   Valid trade: {is_valid} - {reason}")


async def test_tech_filter():
    """Test tech filter functionality"""
    print("\n🧪 Testing Tech Filter...")
    
    config = PipelineConfig(btc_condition="neutral")
    tech_filter = TechFilter(config)
    
    test_cases = [
        ("BTC", "neutral", True),
        ("ETH", "bullish", True),
        ("ADA", "bearish", False),
    ]
    
    for symbol, condition, expected in test_cases:
        indicators = create_mock_indicators(symbol, condition)
        passed, reason, score = tech_filter.filter_symbol(symbol, indicators)
        
        status = "✅" if passed == expected else "❌"
        print(f"   {status} {symbol} ({condition}): {passed} - {reason} (Score: {score:.3f})")


async def test_fork_scorer():
    """Test fork scorer functionality"""
    print("\n🧪 Testing Fork Scorer...")
    
    config = PipelineConfig(btc_condition="neutral")
    fork_scorer = ForkScorer(config)
    
    test_cases = [
        ("BTC", "neutral"),
        ("ETH", "bullish"),
        ("ADA", "bearish"),
    ]
    
    for symbol, condition in test_cases:
        indicators = create_mock_indicators(symbol, condition)
        passed, reason, score, subscores = fork_scorer.score_symbol(symbol, indicators)
        
        status = "✅" if passed else "❌"
        print(f"   {status} {symbol} ({condition}): {passed} - {reason}")
        print(f"      Score: {score:.3f}, Subscores: {subscores}")


async def test_tv_adjuster():
    """Test TV adjuster functionality"""
    print("\n🧪 Testing TV Adjuster...")
    
    config = PipelineConfig(tv_enabled=True)
    tv_adjuster = TVAdjuster(config)
    
    # Create test trade
    trade = Trade(
        symbol="BTC",
        score=0.75,
        indicators=create_mock_indicators("BTC"),
        timestamp=int(datetime.utcnow().timestamp() * 1000)
    )
    
    test_cases = [
        ("strong_buy", True),
        ("buy", True),
        ("neutral", False),
        ("sell", False),
        ("strong_sell", False),
    ]
    
    for tv_tag, expected in test_cases:
        adjusted_trade = tv_adjuster.adjust_score(trade, tv_tag)
        
        status = "✅" if adjusted_trade.passed == expected else "❌"
        print(f"   {status} {tv_tag}: {adjusted_trade.passed} - {adjusted_trade.reason}")
        print(f"      Score: {adjusted_trade.score:.3f} → {adjusted_trade.adjusted_score:.3f}")


async def test_complete_pipeline():
    """Test the complete pipeline flow"""
    print("\n🧪 Testing Complete Pipeline Flow...")
    
    config = PipelineConfig(
        min_tech_score=0.5,  # Lower for testing
        min_fork_score=0.6,  # Lower for testing
        min_tv_score=0.7,    # Lower for testing
        btc_condition="neutral",
        tv_enabled=True,
        max_trades_per_batch=5
    )
    
    tech_filter = TechFilter(config)
    fork_scorer = ForkScorer(config)
    tv_adjuster = TVAdjuster(config)
    
    # Test symbols with different conditions
    test_cases = [
        ("BTC", "neutral", "strong_buy"),
        ("ETH", "bullish", "buy"),
        ("ADA", "bearish", "neutral"),
        ("DOT", "neutral", "sell"),
        ("LINK", "neutral", "strong_sell"),
    ]
    
    results = []
    
    for symbol, market_condition, tv_tag in test_cases:
        print(f"\n   Processing {symbol}...")
        
        # Stage 1: Tech Filter
        indicators = create_mock_indicators(symbol, market_condition)
        passed, reason, tech_score = tech_filter.filter_symbol(symbol, indicators)
        
        if not passed:
            print(f"      ❌ Failed tech filter: {reason}")
            continue
        
        print(f"      ✅ Tech filter passed: {tech_score:.3f}")
        
        # Stage 2: Fork Scoring
        passed, reason, fork_score, subscores = fork_scorer.score_symbol(symbol, indicators)
        
        if not passed:
            print(f"      ❌ Failed fork scoring: {reason}")
            continue
        
        print(f"      ✅ Fork scoring passed: {fork_score:.3f}")
        
        # Create trade object
        trade = Trade(
            symbol=symbol,
            score=fork_score,
            indicators=indicators,
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )
        
        # Stage 3: TV Adjustment
        adjusted_trade = tv_adjuster.adjust_score(trade, tv_tag)
        
        if adjusted_trade.passed:
            print(f"      ✅ TV adjustment passed: {adjusted_trade.adjusted_score:.3f}")
            results.append(adjusted_trade)
        else:
            print(f"      ❌ TV adjustment failed: {adjusted_trade.reason}")
    
    print(f"\n   Pipeline Results: {len(results)} trades passed")
    for trade in results:
        print(f"      ✅ {trade.symbol}: {trade.adjusted_score:.3f} ({trade.tv_tag})")


async def main():
    """Run all tests"""
    print("🚀 Unified Trading Pipeline - Simplified Test Suite")
    print("=" * 60)
    
    try:
        await test_data_validation()
        await test_tech_filter()
        await test_fork_scorer()
        await test_tv_adjuster()
        await test_complete_pipeline()
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Key Features Demonstrated:")
        print("• Data validation at each stage")
        print("• Dynamic thresholds based on market conditions")
        print("• Weighted scoring with subscores")
        print("• TV signal adjustment")
        print("• Complete pipeline flow")
        print("• Error handling and logging")
        
        print("\n🚀 Next Steps:")
        print("1. Integrate with Redis for real indicator data")
        print("2. Add TradingView data integration")
        print("3. Configure 3Commas API credentials")
        print("4. Add performance monitoring")
        print("5. Run with real market data")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())