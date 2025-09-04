#!/usr/bin/env python3
"""
Test script for Unified Trading Pipeline
Tests the streamlined Tech Filter → Fork → TV flow
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from pipeline.unified_trading_pipeline import (
    DataValidator,
    ForkScorer,
    PipelineConfig,
    TechFilter,
    Trade,
    TVAdjuster,
    UnifiedTradingPipeline,
)


def create_mock_indicators(
    symbol: str, market_condition: str = "neutral"
) -> Dict[str, float]:
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
        base_indicators.update(
            {
                "RSI14": 55.0,
                "ADX14": 30.0,
                "MACD_Histogram": 0.002,
            }
        )
    elif market_condition == "bearish":
        base_indicators.update(
            {
                "RSI14": 35.0,
                "ADX14": 15.0,
                "MACD_Histogram": -0.001,
            }
        )

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
        print(
            f"   {status} {symbol} ({condition}): {passed} - {reason} (Score: {score:.3f})"
        )


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
        timestamp=int(datetime.utcnow().timestamp() * 1000),
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
        print(
            f"   {status} {tv_tag}: {adjusted_trade.passed} - {adjusted_trade.reason}"
        )
        print(
            f"      Score: {adjusted_trade.score:.3f} → {adjusted_trade.adjusted_score:.3f}"
        )


async def test_unified_pipeline():
    """Test the complete unified pipeline"""
    print("\n🧪 Testing Unified Pipeline...")

    config = PipelineConfig(
        min_tech_score=0.5,  # Lower for testing
        min_fork_score=0.6,  # Lower for testing
        min_tv_score=0.7,  # Lower for testing
        btc_condition="neutral",
        tv_enabled=True,
        max_trades_per_batch=5,
    )

    pipeline = UnifiedTradingPipeline(config)

    # Mock the indicator and TV data retrieval
    async def mock_get_indicators(symbol: str):
        return create_mock_indicators(symbol, "neutral")

    async def mock_get_tv_tag(symbol: str):
        tv_tags = {
            "BTC": "strong_buy",
            "ETH": "buy",
            "ADA": "neutral",
            "DOT": "sell",
            "LINK": "strong_sell",
        }
        return tv_tags.get(symbol, "neutral")

    # Replace the async methods
    pipeline._get_indicators = mock_get_indicators
    pipeline._get_tv_tag = mock_get_tv_tag

    # Test symbols
    symbols = ["BTC", "ETH", "ADA", "DOT", "LINK"]

    print(f"   Processing {len(symbols)} symbols...")
    results = await pipeline.process_symbols(symbols)

    print(f"   Results: {len(results)} trades executed")
    for trade in results:
        print(f"      ✅ {trade.symbol}: {trade.adjusted_score:.3f} - {trade.reason}")


async def test_performance():
    """Test pipeline performance"""
    print("\n🧪 Testing Performance...")

    config = PipelineConfig(
        min_tech_score=0.5,
        min_fork_score=0.6,
        min_tv_score=0.7,
        btc_condition="neutral",
        tv_enabled=True,
        max_trades_per_batch=20,
    )

    pipeline = UnifiedTradingPipeline(config)

    # Mock methods
    async def mock_get_indicators(symbol: str):
        return create_mock_indicators(symbol, "neutral")

    async def mock_get_tv_tag(symbol: str):
        return "neutral"

    pipeline._get_indicators = mock_get_indicators
    pipeline._get_tv_tag = mock_get_tv_tag

    # Test with more symbols
    symbols = [f"SYMBOL{i}" for i in range(50)]

    start_time = datetime.utcnow()
    results = await pipeline.process_symbols(symbols)
    end_time = datetime.utcnow()

    duration = (end_time - start_time).total_seconds()
    throughput = len(symbols) / duration if duration > 0 else 0

    print(f"   Processed {len(symbols)} symbols in {duration:.2f} seconds")
    print(f"   Throughput: {throughput:.2f} symbols/second")
    print(f"   Results: {len(results)} trades executed")


async def main():
    """Run all tests"""
    print("🚀 Unified Trading Pipeline - Test Suite")
    print("=" * 60)

    try:
        await test_data_validation()
        await test_tech_filter()
        await test_fork_scorer()
        await test_tv_adjuster()
        await test_unified_pipeline()
        await test_performance()

        print("\n✅ All tests completed successfully!")
        print("\n📋 Key Features Demonstrated:")
        print("• Data validation at each stage")
        print("• Dynamic thresholds based on market conditions")
        print("• Weighted scoring with subscores")
        print("• TV signal adjustment")
        print("• Error handling and logging")
        print("• Performance monitoring")

        print("\n🚀 Next Steps:")
        print("1. Configure Redis with real indicator data")
        print("2. Set up TradingView data integration")
        print("3. Configure 3Commas API credentials")
        print("4. Run with real market data")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
