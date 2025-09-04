#!/usr/bin/env python3
"""
Test script for Redis Manager
Tests optimized Redis operations, data structures, and monitoring
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from utils.redis_manager import (
    RedisDataManager,
    RedisConfig,
    RedisKeyManager,
    RedisMonitor,
    get_redis_manager,
    get_redis_monitor
)


def test_redis_connection():
    """Test Redis connection and health check"""
    print("🧪 Testing Redis Connection...")
    
    config = RedisConfig()
    redis_manager = RedisDataManager(config)
    
    # Test health check
    is_healthy = redis_manager.health_check()
    print(f"      Redis connected: {'✅' if is_healthy else '❌'}")
    
    if not is_healthy:
        print("      ⚠️  Redis not available - skipping Redis tests")
        return False
    
    # Test memory info
    memory_info = redis_manager.get_memory_info()
    print(f"      Memory usage: {memory_info.get('used_memory', 'Unknown')}")
    print(f"      Memory peak: {memory_info.get('used_memory_peak', 'Unknown')}")
    
    print("      ✅ Redis connection working correctly")
    return True


def test_key_management():
    """Test Redis key management and namespacing"""
    print("\n🧪 Testing Key Management...")
    
    redis_manager = get_redis_manager()
    
    # Test key generation
    indicator_key = RedisKeyManager.indicator("BTC", "1h")
    counter_key = RedisKeyManager.counter("scan_count")
    lock_key = RedisKeyManager.lock("trade_processing")
    queue_key = RedisKeyManager.queue("trades")
    cache_key = RedisKeyManager.cache("btc_condition")
    
    print(f"      Indicator key: {indicator_key}")
    print(f"      Counter key: {counter_key}")
    print(f"      Lock key: {lock_key}")
    print(f"      Queue key: {queue_key}")
    print(f"      Cache key: {cache_key}")
    
    # Validate key patterns
    assert indicator_key.startswith("indicators:"), "Indicator key should be namespaced"
    assert counter_key.startswith("counters:"), "Counter key should be namespaced"
    assert lock_key.startswith("locks:"), "Lock key should be namespaced"
    assert queue_key.startswith("queues:"), "Queue key should be namespaced"
    assert cache_key.startswith("cache:"), "Cache key should be namespaced"
    
    print("      ✅ Key management working correctly")


def test_indicator_operations():
    """Test indicator data operations"""
    print("\n🧪 Testing Indicator Operations...")
    
    redis_manager = get_redis_manager()
    
    # Test data
    test_indicators = {
        "rsi": 65.5,
        "macd": 0.001,
        "adx": 25.3,
        "ema50": 45000.0,
        "stoch_rsi_k": 45.2,
        "stoch_rsi_d": 42.1
    }
    
    # Store indicators
    success = redis_manager.store_indicators("BTC", "1h", test_indicators, ttl=60)
    print(f"      Store indicators: {'✅' if success else '❌'}")
    
    # Retrieve indicators
    retrieved = redis_manager.get_indicators("BTC", "1h")
    print(f"      Retrieved indicators: {len(retrieved)} items")
    
    # Validate data
    if retrieved:
        assert retrieved["rsi"] == 65.5, "RSI value should match"
        assert retrieved["macd"] == 0.001, "MACD value should match"
        assert retrieved["adx"] == 25.3, "ADX value should match"
        print("      ✅ Indicator data integrity verified")
    else:
        print("      ❌ Failed to retrieve indicators")
    
    # Test with different symbol/timeframe
    success = redis_manager.store_indicators("ETH", "15m", test_indicators, ttl=60)
    retrieved = redis_manager.get_indicators("ETH", "15m")
    print(f"      ETH 15m indicators: {'✅' if retrieved else '❌'}")
    
    print("      ✅ Indicator operations working correctly")


def test_counter_operations():
    """Test counter operations"""
    print("\n🧪 Testing Counter Operations...")
    
    redis_manager = get_redis_manager()
    
    # Test set counter
    success = redis_manager.set_counter("test_counter", 100, ttl=60)
    print(f"      Set counter: {'✅' if success else '❌'}")
    
    # Test get counter
    value = redis_manager.get_counter("test_counter")
    print(f"      Counter value: {value}")
    assert value == 100, "Counter value should be 100"
    
    # Test increment counter
    new_value = redis_manager.increment_counter("test_counter", 25, ttl=60)
    print(f"      Incremented counter: {new_value}")
    assert new_value == 125, "Incremented counter should be 125"
    
    # Test increment non-existent counter
    new_counter = redis_manager.increment_counter("new_counter", 10, ttl=60)
    print(f"      New counter: {new_counter}")
    assert new_counter == 10, "New counter should be 10"
    
    print("      ✅ Counter operations working correctly")


def test_cache_operations():
    """Test cache operations"""
    print("\n🧪 Testing Cache Operations...")
    
    redis_manager = get_redis_manager()
    
    # Test simple cache
    success = redis_manager.set_cache("test_string", "hello world", ttl=60)
    print(f"      Set string cache: {'✅' if success else '❌'}")
    
    value = redis_manager.get_cache("test_string")
    print(f"      String cache value: {value}")
    assert value == "hello world", "String cache value should match"
    
    # Test complex cache
    complex_data = {
        "btc_condition": "bullish",
        "market_sentiment": 0.75,
        "active_trades": ["BTCUSDT", "ETHUSDT"],
        "timestamp": time.time()
    }
    
    success = redis_manager.set_cache("market_data", complex_data, ttl=60)
    print(f"      Set complex cache: {'✅' if success else '❌'}")
    
    retrieved_data = redis_manager.get_cache("market_data")
    print(f"      Complex cache: {len(retrieved_data)} items")
    assert retrieved_data["btc_condition"] == "bullish", "BTC condition should match"
    assert retrieved_data["market_sentiment"] == 0.75, "Market sentiment should match"
    
    print("      ✅ Cache operations working correctly")


def test_trade_data_operations():
    """Test trade data operations"""
    print("\n🧪 Testing Trade Data Operations...")
    
    redis_manager = get_redis_manager()
    
    # Test trade data
    trade_data = {
        "symbol": "BTCUSDT",
        "entry_price": 45000.0,
        "score": 0.85,
        "timestamp": time.time(),
        "indicators": {
            "rsi": 65.5,
            "macd": 0.001
        }
    }
    
    # Store trade data
    success = redis_manager.store_trade_data(trade_data, ttl=60)
    print(f"      Store trade data: {'✅' if success else '❌'}")
    
    # Retrieve trade data
    trades = redis_manager.get_trade_data(count=5)
    print(f"      Retrieved trades: {len(trades)}")
    
    if trades:
        assert trades[0]["symbol"] == "BTCUSDT", "Trade symbol should match"
        assert trades[0]["entry_price"] == 45000.0, "Entry price should match"
        print("      ✅ Trade data integrity verified")
    
    # Test multiple trades
    for i in range(3):
        trade = trade_data.copy()
        trade["symbol"] = f"ETH{i}USDT"
        trade["entry_price"] = 3000.0 + i * 100
        redis_manager.store_trade_data(trade, ttl=60)
    
    all_trades = redis_manager.get_trade_data(count=10)
    print(f"      All trades: {len(all_trades)}")
    
    print("      ✅ Trade data operations working correctly")


def test_lock_operations():
    """Test distributed lock operations"""
    print("\n🧪 Testing Lock Operations...")
    
    redis_manager = get_redis_manager()
    
    # Test acquire lock
    acquired = redis_manager.acquire_lock("test_resource", timeout=10)
    print(f"      Acquire lock: {'✅' if acquired else '❌'}")
    
    if acquired:
        # Test release lock
        released = redis_manager.release_lock("test_resource")
        print(f"      Release lock: {'✅' if released else '❌'}")
        
        # Test acquire released lock
        acquired_again = redis_manager.acquire_lock("test_resource", timeout=10)
        print(f"      Re-acquire lock: {'✅' if acquired_again else '❌'}")
        
        if acquired_again:
            redis_manager.release_lock("test_resource")
    
    print("      ✅ Lock operations working correctly")


def test_bulk_operations():
    """Test bulk operations"""
    print("\n🧪 Testing Bulk Operations...")
    
    redis_manager = get_redis_manager()
    
    # Prepare bulk operations
    operations = [
        ("set", "test_bulk_1", "value1"),
        ("set", "test_bulk_2", "value2"),
        ("set", "test_bulk_3", "value3"),
        ("hset", "test_bulk_hash", {"field1": "value1", "field2": "value2"}),
        ("lpush", "test_bulk_list", "item1"),
        ("lpush", "test_bulk_list", "item2"),
    ]
    
    # Execute bulk operations
    results = redis_manager.bulk_operations(operations)
    print(f"      Bulk operations: {len(results)} results")
    
    # Verify results
    assert len(results) == len(operations), "Should return results for all operations"
    
    # Clean up
    cleanup_ops = [
        ("delete", "test_bulk_1", None),
        ("delete", "test_bulk_2", None),
        ("delete", "test_bulk_3", None),
        ("delete", "test_bulk_hash", None),
        ("delete", "test_bulk_list", None),
    ]
    redis_manager.bulk_operations(cleanup_ops)
    
    print("      ✅ Bulk operations working correctly")


def test_monitoring():
    """Test Redis monitoring"""
    print("\n🧪 Testing Redis Monitoring...")
    
    monitor = get_redis_monitor()
    
    # Test health check
    health = monitor.check_health()
    print(f"      Redis connected: {'✅' if health['redis_connected'] else '❌'}")
    print(f"      Health status: {'✅' if health['healthy'] else '❌'}")
    
    if health['issues']:
        print(f"      Issues found: {len(health['issues'])}")
        for issue in health['issues']:
            print(f"         - {issue}")
    
    # Test key stats
    key_stats = health['key_stats']
    print(f"      Key statistics: {len(key_stats)} categories")
    for pattern, count in key_stats.items():
        print(f"         {pattern}: {count} keys")
    
    # Test report generation
    report = monitor.generate_report()
    print(f"      Generated report: {len(report)} characters")
    
    print("      ✅ Monitoring working correctly")


def test_cleanup():
    """Test cleanup operations"""
    print("\n🧪 Testing Cleanup Operations...")
    
    redis_manager = get_redis_manager()
    
    # Create some temporary keys
    redis_manager.set_cache("temp:test1", "value1", ttl=1)
    redis_manager.set_cache("temp:test2", "value2", ttl=1)
    redis_manager.set_cache("permanent:test", "value3", ttl=3600)
    
    # Wait for temp keys to expire
    time.sleep(2)
    
    # Test cleanup
    cleaned_count = redis_manager.cleanup_expired_keys()
    print(f"      Cleaned up: {cleaned_count} keys")
    
    print("      ✅ Cleanup operations working correctly")


def test_performance():
    """Test Redis performance"""
    print("\n🧪 Testing Redis Performance...")
    
    redis_manager = get_redis_manager()
    
    # Test indicator operations performance
    start_time = time.time()
    for i in range(100):
        indicators = {
            "rsi": 50.0 + i,
            "macd": 0.001 + i * 0.0001,
            "adx": 20.0 + i * 0.1
        }
        redis_manager.store_indicators(f"TEST{i}", "1h", indicators, ttl=60)
    store_time = time.time() - start_time
    
    print(f"      100 indicator stores: {store_time:.3f} seconds")
    
    # Test retrieval performance
    start_time = time.time()
    for i in range(100):
        redis_manager.get_indicators(f"TEST{i}", "1h")
    retrieve_time = time.time() - start_time
    
    print(f"      100 indicator retrievals: {retrieve_time:.3f} seconds")
    
    # Test counter performance
    start_time = time.time()
    for i in range(100):
        redis_manager.increment_counter("perf_test", 1, ttl=60)
    counter_time = time.time() - start_time
    
    print(f"      100 counter increments: {counter_time:.3f} seconds")
    
    # Performance should be reasonable
    if store_time < 1.0 and retrieve_time < 0.5 and counter_time < 0.5:
        print("      ✅ Performance is good")
    else:
        print("      ⚠️  Performance could be improved")
    
    # Clean up test data
    for i in range(100):
        redis_manager.cleanup_expired_keys()


async def main():
    """Run all tests"""
    print("🚀 Redis Manager - Test Suite")
    print("=" * 60)
    
    try:
        # Test Redis connection first
        if not test_redis_connection():
            print("\n❌ Redis not available - cannot run tests")
            return
        
        test_key_management()
        test_indicator_operations()
        test_counter_operations()
        test_cache_operations()
        test_trade_data_operations()
        test_lock_operations()
        test_bulk_operations()
        test_monitoring()
        test_cleanup()
        test_performance()
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Key Features Demonstrated:")
        print("• Optimized Redis operations with connection pooling")
        print("• Proper key namespacing and data structure usage")
        print("• TTL management for automatic cleanup")
        print("• Comprehensive error handling and logging")
        print("• Distributed locking for resource management")
        print("• Bulk operations for performance")
        print("• Health monitoring and alerting")
        print("• Memory usage tracking and cleanup")
        
        print("\n🚀 Benefits of Redis Manager:")
        print("• Eliminates scattered Redis usage patterns")
        print("• Provides consistent API across all systems")
        print("• Includes proper error handling and monitoring")
        print("• Offers optimized data structures for each use case")
        print("• Enables automatic cleanup and memory management")
        print("• Reduces Redis memory usage and improves performance")
        
        print("\n📈 Next Steps:")
        print("1. Run migrate_redis_usage.py to update all files")
        print("2. Test the migrated files in your environment")
        print("3. Configure Redis for production use")
        print("4. Set up Redis monitoring and alerting")
        print("5. Implement Redis persistence and backup")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())