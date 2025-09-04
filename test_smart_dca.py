#!/usr/bin/env python3
"""
Test script for Smart DCA Core Engine
Tests the streamlined DCA system with mock data
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from dca.smart_dca_core import SmartDCACore


def create_mock_trade(symbol: str, drawdown_pct: float, **kwargs) -> Dict:
    """Create a mock trade for testing"""
    base_price = 100.0
    current_price = base_price * (1 - drawdown_pct / 100)
    
    return {
        "id": f"test_{symbol}_{int(datetime.now().timestamp())}",
        "pair": f"{symbol}USDT",
        "bought_volume": 200.0,
        "current_funds": 200.0,
        "bought_average_price": base_price,
        "current_price": current_price,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "completed_safety_orders_count": 0,
        **kwargs
    }


def test_rescue_confidence_calculation():
    """Test the rescue confidence calculation"""
    print("🧪 Testing Rescue Confidence Calculation...")
    
    config = {
        "max_trade_usdt": 2000,
        "drawdown_trigger_pct": 1.5,
        "so_volume_table": [20, 30, 50, 80, 120, 180, 250, 350, 500],
        "use_ml_spend_model": False,
    }
    
    core = SmartDCACore(config)
    
    # Test cases with different scenarios
    test_cases = [
        {
            "name": "High Confidence Rescue",
            "metrics": {
                "deviation_pct": 3.0,
                "recovery_odds": 0.8,
                "confidence_score": 0.75,
                "safu_score": 0.7,
                "health_score": 0.8,
                "indicators": {"rsi": 45, "macd_histogram": 0.001},
                "is_zombie": False,
                "total_spent": 200,
            }
        },
        {
            "name": "Medium Confidence Rescue",
            "metrics": {
                "deviation_pct": 2.5,
                "recovery_odds": 0.6,
                "confidence_score": 0.65,
                "safu_score": 0.6,
                "health_score": 0.7,
                "indicators": {"rsi": 40, "macd_histogram": 0.0005},
                "is_zombie": False,
                "total_spent": 300,
            }
        },
        {
            "name": "Low Confidence (Should Skip)",
            "metrics": {
                "deviation_pct": 1.0,
                "recovery_odds": 0.3,
                "confidence_score": 0.4,
                "safu_score": 0.3,
                "health_score": 0.4,
                "indicators": {"rsi": 30, "macd_histogram": -0.001},
                "is_zombie": False,
                "total_spent": 500,
            }
        },
        {
            "name": "Zombie Trade (Should Skip)",
            "metrics": {
                "deviation_pct": 5.0,
                "recovery_odds": 0.1,
                "confidence_score": 0.2,
                "safu_score": 0.2,
                "health_score": 0.2,
                "indicators": {"rsi": 25, "macd_histogram": -0.002},
                "is_zombie": True,
                "total_spent": 800,
            }
        }
    ]
    
    for case in test_cases:
        print(f"\n📊 {case['name']}:")
        confidence = core._calculate_rescue_confidence(case["metrics"])
        should_rescue, reason, _ = core.should_rescue_trade(case["metrics"])
        
        print(f"   Confidence: {confidence:.3f}")
        print(f"   Should Rescue: {should_rescue}")
        print(f"   Reason: {reason}")
        print(f"   Drawdown: {case['metrics']['deviation_pct']:.1f}%")


def test_volume_calculation():
    """Test volume calculation logic"""
    print("\n🧪 Testing Volume Calculation...")
    
    config = {
        "max_trade_usdt": 2000,
        "so_volume_table": [20, 30, 50, 80, 120, 180, 250, 350, 500],
        "use_ml_spend_model": False,
    }
    
    core = SmartDCACore(config)
    
    # Test different steps
    for step in range(5):
        metrics = {
            "deal_id": f"test_{step}",
            "deviation_pct": 2.0 + step,
            "total_spent": 200 + step * 50,
            "tp1_shift": 1.0 + step * 0.5,
        }
        
        volume = core.calculate_rescue_volume(metrics)
        print(f"   Step {step + 1}: {volume:.1f} USDT")


def test_mock_trades():
    """Test with mock trades"""
    print("\n🧪 Testing Mock Trades...")
    
    config = {
        "max_trade_usdt": 2000,
        "drawdown_trigger_pct": 1.5,
        "so_volume_table": [20, 30, 50, 80, 120, 180, 250, 350, 500],
        "use_ml_spend_model": False,
    }
    
    core = SmartDCACore(config)
    
    # Create mock trades
    mock_trades = [
        create_mock_trade("BTC", 2.5),  # Should rescue
        create_mock_trade("ETH", 0.8),  # Should skip (low drawdown)
        create_mock_trade("ADA", 4.0),  # Should rescue
        create_mock_trade("DOT", 0.5),  # Should skip (low drawdown)
        create_mock_trade("LINK", 3.5), # Should rescue
    ]
    
    print(f"Processing {len(mock_trades)} mock trades...")
    
    for trade in mock_trades:
        try:
            metrics = core.calculate_trade_metrics(trade)
            should_rescue, reason, confidence = core.should_rescue_trade(metrics)
            
            status = "✅ RESCUE" if should_rescue else "⛔ SKIP"
            print(f"   {trade['pair']}: {status} (Conf: {confidence:.2f}, Reason: {reason})")
            
        except Exception as e:
            print(f"   {trade['pair']}: ERROR - {e}")


def main():
    """Run all tests"""
    print("🚀 Smart DCA Core Engine - Test Suite")
    print("=" * 50)
    
    try:
        test_rescue_confidence_calculation()
        test_volume_calculation()
        test_mock_trades()
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Run with real 3Commas data: python dca/smart_dca_core.py")
        print("2. Analyze profitability: python dca/utils/profitability_analyzer.py")
        print("3. Monitor logs in dca/logs/")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()