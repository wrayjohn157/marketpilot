#!/usr/bin/env python3
"""
Test script for the DCA Simulation System
Verifies that all components work correctly
"""

import sys
from pathlib import Path
import logging

# Add simulation paths
sys.path.append(str(Path(__file__).resolve().parent))

from core.data_manager import HistoricalDataManager
from core.dca_simulator import DCASimulator
from core.parameter_tuner import ParameterTuner

# === Logging ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_data_manager():
    """Test the historical data manager"""
    logger.info("Testing HistoricalDataManager...")
    
    try:
        data_manager = HistoricalDataManager()
        
        # Test symbol loading
        symbols = data_manager.get_available_symbols()
        logger.info(f"Found {len(symbols)} symbols")
        
        # Test timeframe loading
        timeframes = data_manager.get_available_timeframes()
        logger.info(f"Available timeframes: {timeframes}")
        
        # Test data loading (small sample)
        if symbols:
            symbol = symbols[0]  # Use first available symbol
            end_time = 1640995200000  # 2022-01-01
            start_time = end_time - (24 * 60 * 60 * 1000)  # 1 day
            
            df = data_manager.load_klines(symbol, "1h", start_time, end_time)
            logger.info(f"Loaded {len(df)} candles for {symbol}")
            
            # Test data quality
            quality = data_manager.validate_data_quality(df)
            logger.info(f"Data quality: {quality['quality_score']:.2f}")
            
            return True
        else:
            logger.warning("No symbols available for testing")
            return False
            
    except Exception as e:
        logger.error(f"Data manager test failed: {e}")
        return False

def test_dca_simulator():
    """Test the DCA simulator"""
    logger.info("Testing DCASimulator...")
    
    try:
        simulator = DCASimulator()
        
        # Test simulation with mock data
        mock_params = {
            "confidence_threshold": 0.6,
            "min_drawdown_pct": 2.0,
            "rsi_oversold_threshold": 30,
            "base_dca_volume": 100,
            "max_dca_count": 5,
            "max_trade_usdt": 1000
        }
        
        # Use a known good symbol and timeframe
        symbol = "BTCUSDT"
        entry_time = 1640995200000  # 2022-01-01
        timeframe = "1h"
        
        result = simulator.simulate(
            symbol=symbol,
            entry_time=entry_time,
            timeframe=timeframe,
            dca_params=mock_params,
            simulation_days=7  # Short simulation for testing
        )
        
        if result:
            logger.info("Simulation completed successfully")
            logger.info(f"DCA points: {len(result.get('dca_points', []))}")
            logger.info(f"Final P&L: {result.get('performance_metrics', {}).get('final_pnl_pct', 0):.2f}%")
            return True
        else:
            logger.error("Simulation returned no results")
            return False
            
    except Exception as e:
        logger.error(f"DCA simulator test failed: {e}")
        return False

def test_parameter_tuner():
    """Test the parameter tuner"""
    logger.info("Testing ParameterTuner...")
    
    try:
        tuner = ParameterTuner()
        
        # Test with small parameter ranges
        parameter_ranges = {
            "confidence_threshold": [0.5, 0.6, 0.7],
            "min_drawdown_pct": [2.0, 3.0],
            "base_dca_volume": [100, 150]
        }
        
        symbol = "BTCUSDT"
        entry_time = 1640995200000
        timeframe = "1h"
        
        results = tuner.grid_search(
            symbol=symbol,
            entry_time=entry_time,
            timeframe=timeframe,
            parameter_ranges=parameter_ranges,
            simulation_days=3,  # Very short for testing
            max_combinations=10
        )
        
        if results:
            logger.info(f"Optimization completed: {len(results)} results")
            if results:
                best = results[0]
                logger.info(f"Best score: {best.get('performance_score', 0):.4f}")
            return True
        else:
            logger.error("Optimization returned no results")
            return False
            
    except Exception as e:
        logger.error(f"Parameter tuner test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting DCA Simulation System tests...")
    
    tests = [
        ("Data Manager", test_data_manager),
        ("DCA Simulator", test_dca_simulator),
        ("Parameter Tuner", test_parameter_tuner)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} test...")
        logger.info(f"{'='*50}")
        
        success = test_func()
        results.append((test_name, success))
        
        if success:
            logger.info(f"✅ {test_name} test PASSED")
        else:
            logger.error(f"❌ {test_name} test FAILED")
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Simulation system is ready.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the logs.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)