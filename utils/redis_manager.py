#!/usr/bin/env python3

import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import redis
from redis.connection import ConnectionPool
from redis.exceptions import ConnectionError, RedisError, TimeoutError

"""
Redis Manager - Optimized Redis Operations with Proper Data Management
Replaces scattered Redis usage with centralized, efficient operations
"""


class RedisKeyType(Enum):
    """Redis key types for proper data management"""

    INDICATORS = "indicators"
    COUNTERS = "counters"
    LOCKS = "locks"
    QUEUES = "queues"
    CACHE = "cache"
    SESSIONS = "sessions"
    TEMP = "temp"


@dataclass
class RedisConfig:
    """Redis configuration with proper defaults"""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    max_connections: int = 20
    retry_on_timeout: bool = True
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    health_check_interval: int = 30


class RedisKeyManager:
    """Centralized key management with namespacing"""

    @staticmethod
    def indicator(symbol: str, timeframe: str) -> str:
        """Generate indicator key with proper namespace"""
        return f"indicators:{symbol.upper()}:{timeframe}"

    @staticmethod
    def counter(name: str) -> str:
        """Generate counter key with proper namespace"""
        return f"counters:{name}"

    @staticmethod
    def lock(resource: str) -> str:
        """Generate lock key with proper namespace"""
        return f"locks:{resource}"

    @staticmethod
    def queue(name: str) -> str:
        """Generate queue key with proper namespace"""
        return f"queues:{name}"

    @staticmethod
    def cache(key: str) -> str:
        """Generate cache key with proper namespace"""
        return f"cache:{key}"

    @staticmethod
    def session(session_id: str) -> str:
        """Generate session key with proper namespace"""
        return f"sessions:{session_id}"

    @staticmethod
    def temp(key: str) -> str:
        """Generate temporary key with proper namespace"""
        return f"temp:{key}"


class RedisDataManager:
    """Optimized Redis data operations with proper error handling"""

    def __init__(self, config: RedisConfig):
        self.config = config
        self.pool = ConnectionPool(
            host=config.host,
            port=config.port,
            db=config.db,
            max_connections=config.max_connections,
            retry_on_timeout=config.retry_on_timeout,
            socket_timeout=config.socket_timeout,
            socket_connect_timeout=config.socket_connect_timeout,
            health_check_interval=config.health_check_interval,
        )
        self.redis = redis.Redis(connection_pool=self.pool)
        self.logger = logging.getLogger(__name__)

    def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            self.redis.ping()
            return True
        except (ConnectionError, TimeoutError) as e:
            self.logger.error(f"Redis health check failed: {e}")
            return False

    def store_indicators(
        self, symbol: str, timeframe: str, indicators: Dict[str, Any], ttl: int = 3600
    ) -> bool:
        """Store indicators using Hash data structure with TTL"""
        try:
            key = RedisKeyManager.indicator(symbol, timeframe)

            # Convert all values to strings for Redis Hash
            hash_data = {k: str(v) for k, v in indicators.items()}

            # Use pipeline for atomic operations
            pipe = self.redis.pipeline()
            pipe.hset(key, mapping=hash_data)
            pipe.expire(key, ttl)
            pipe.execute()

            self.logger.debug(f"Stored indicators for {symbol}_{timeframe}")
            return True
        except RedisError as e:
            self.logger.error(
                f"Failed to store indicators for {symbol}_{timeframe}: {e}"
            )
            return False

    def get_indicators(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get indicators from Hash data structure"""
        try:
            key = RedisKeyManager.indicator(symbol, timeframe)
            data = self.redis.hgetall(key)

            if not data:
                return None

            # Convert string values back to appropriate types
            converted_data = {}
            for k, v in data.items():
                try:
                    # Try to convert to float first
                    converted_data[k] = float(v)
                except ValueError:
                    try:
                        # Try to convert to int
                        converted_data[k] = int(v)
                    except ValueError:
                        # Keep as string
                        converted_data[k] = v

            return converted_data
        except RedisError as e:
            self.logger.error(f"Failed to get indicators for {symbol}_{timeframe}: {e}")
            return None

    def store_trade_data(self, trade_data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Store trade data in queue with TTL"""
        try:
            key = RedisKeyManager.queue("trades")
            trade_json = json.dumps(trade_data)

            pipe = self.redis.pipeline()
            pipe.lpush(key, trade_json)
            pipe.expire(key, ttl)
            pipe.execute()

            self.logger.debug(
                f"Stored trade data: {trade_data.get('symbol', 'unknown')}"
            )
            return True
        except RedisError as e:
            self.logger.error(f"Failed to store trade data: {e}")
            return False

    def get_trade_data(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get trade data from queue"""
        try:
            key = RedisKeyManager.queue("trades")
            data = self.redis.lrange(key, 0, count - 1)

            trades = []
            for item in data:
                try:
                    trades.append(json.loads(item))
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse trade data: {e}")
                    continue

            return trades
        except RedisError as e:
            self.logger.error(f"Failed to get trade data: {e}")
            return []

    def set_counter(self, name: str, value: int, ttl: int = 3600) -> bool:
        """Set counter value with TTL"""
        try:
            key = RedisKeyManager.counter(name)
            pipe = self.redis.pipeline()
            pipe.set(key, value)
            pipe.expire(key, ttl)
            pipe.execute()

            self.logger.debug(f"Set counter {name} to {value}")
            return True
        except RedisError as e:
            self.logger.error(f"Failed to set counter {name}: {e}")
            return False

    def get_counter(self, name: str) -> Optional[int]:
        """Get counter value"""
        try:
            key = RedisKeyManager.counter(name)
            value = self.redis.get(key)
            return int(value) if value else None
        except (RedisError, ValueError) as e:
            self.logger.error(f"Failed to get counter {name}: {e}")
            return None

    def increment_counter(
        self, name: str, amount: int = 1, ttl: int = 3600
    ) -> Optional[int]:
        """Increment counter value with TTL"""
        try:
            key = RedisKeyManager.counter(name)
            pipe = self.redis.pipeline()
            pipe.incrby(key, amount)
            pipe.expire(key, ttl)
            result = pipe.execute()

            self.logger.debug(f"Incremented counter {name} by {amount}")
            return result[0]
        except RedisError as e:
            self.logger.error(f"Failed to increment counter {name}: {e}")
            return None

    def set_cache(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set cache value with TTL"""
        try:
            cache_key = RedisKeyManager.cache(key)
            value_json = json.dumps(value) if not isinstance(value, str) else value

            pipe = self.redis.pipeline()
            pipe.set(cache_key, value_json)
            pipe.expire(cache_key, ttl)
            pipe.execute()

            self.logger.debug(f"Set cache {key} with TTL {ttl}")
            return True
        except RedisError as e:
            self.logger.error(f"Failed to set cache {key}: {e}")
            return False

    def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value"""
        try:
            cache_key = RedisKeyManager.cache(key)
            value = self.redis.get(cache_key)

            if value is None:
                return None

            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except RedisError as e:
            self.logger.error(f"Failed to get cache {key}: {e}")
            return None

    def acquire_lock(self, resource: str, timeout: int = 10) -> bool:
        """Acquire distributed lock"""
        try:
            key = RedisKeyManager.lock(resource)
            lock_value = f"{time.time()}:{id(self)}"

            # Try to acquire lock with timeout
            acquired = self.redis.set(key, lock_value, nx=True, ex=timeout)
            return bool(acquired)
        except RedisError as e:
            self.logger.error(f"Failed to acquire lock for {resource}: {e}")
            return False

    def release_lock(self, resource: str) -> bool:
        """Release distributed lock"""
        try:
            key = RedisKeyManager.lock(resource)
            self.redis.delete(key)
            self.logger.debug(f"Released lock for {resource}")
            return True
        except RedisError as e:
            self.logger.error(f"Failed to release lock for {resource}: {e}")
            return False

    def cleanup_expired_keys(self) -> int:
        """Clean up expired keys and return count of cleaned keys"""
        try:
            # Get all keys with no expiration
            all_keys = self.redis.keys("*")
            cleaned_count = 0

            for key in all_keys:
                ttl = self.redis.ttl(key)
                if ttl == -1:  # No expiration set
                    # Check if it's a temporary key
                    if key.startswith("temp:") or key.startswith("cache:"):
                        self.redis.delete(key)
                        cleaned_count += 1
                        self.logger.debug(f"Cleaned up expired key: {key}")

            self.logger.info(f"Cleaned up {cleaned_count} expired keys")
            return cleaned_count
        except RedisError as e:
            self.logger.error(f"Failed to cleanup expired keys: {e}")
            return 0

    def get_memory_info(self) -> Dict[str, Any]:
        """Get Redis memory usage information"""
        try:
            info = self.redis.info("memory")
            return {
                "used_memory": info.get("used_memory_human", "0B"),
                "used_memory_peak": info.get("used_memory_peak_human", "0B"),
                "max_memory": info.get("maxmemory_human", "0B"),
                "memory_fragmentation_ratio": info.get("mem_fragmentation_ratio", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except RedisError as e:
            self.logger.error(f"Failed to get memory info: {e}")
            return {}

    def get_key_stats(self) -> Dict[str, int]:
        """Get statistics about key usage"""
        try:
            stats = {}
            key_patterns = [
                "indicators:*",
                "counters:*",
                "locks:*",
                "queues:*",
                "cache:*",
                "sessions:*",
                "temp:*",
            ]

            for pattern in key_patterns:
                keys = self.redis.keys(pattern)
                stats[pattern] = len(keys)

            return stats
        except RedisError as e:
            self.logger.error(f"Failed to get key stats: {e}")
            return {}

    def bulk_operations(self, operations: List[Tuple[str, str, Any]]) -> List[Any]:
        """Execute bulk operations using pipeline"""
        try:
            pipe = self.redis.pipeline()

            for op_type, key, value in operations:
                if op_type == "set":
                    pipe.set(key, value)
                elif op_type == "hset":
                    pipe.hset(key, mapping=value)
                elif op_type == "lpush":
                    pipe.lpush(key, value)
                elif op_type == "sadd":
                    pipe.sadd(key, value)
                elif op_type == "delete":
                    pipe.delete(key)

            return pipe.execute()
        except RedisError as e:
            self.logger.error(f"Failed to execute bulk operations: {e}")
            return []


class RedisMonitor:
    """Redis monitoring and alerting"""

    def __init__(self, redis_manager: RedisDataManager):
        self.redis_manager = redis_manager
        self.logger = logging.getLogger(__name__)

    def check_health(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_status = {
            "redis_connected": self.redis_manager.health_check(),
            "memory_info": self.redis_manager.get_memory_info(),
            "key_stats": self.redis_manager.get_key_stats(),
            "timestamp": time.time(),
        }

        # Check for potential issues
        issues = []

        if not health_status["redis_connected"]:
            issues.append("Redis connection failed")

        memory_info = health_status["memory_info"]
        if memory_info:
            frag_ratio = memory_info.get("memory_fragmentation_ratio", 0)
            if frag_ratio > 1.5:
                issues.append(f"High memory fragmentation: {frag_ratio}")

        key_stats = health_status["key_stats"]
        temp_keys = key_stats.get("temp:*", 0)
        if temp_keys > 1000:
            issues.append(f"Too many temporary keys: {temp_keys}")

        health_status["issues"] = issues
        health_status["healthy"] = len(issues) == 0

        return health_status

    def generate_report(self) -> str:
        """Generate monitoring report"""
        health = self.check_health()

        report = f"""
Redis Health Report - {time.strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

Connection Status: {'✅ Healthy' if health['redis_connected'] else '❌ Failed'}

Memory Usage:
  Used Memory: {health['memory_info'].get('used_memory', 'Unknown')}
  Peak Memory: {health['memory_info'].get('used_memory_peak', 'Unknown')}
  Max Memory: {health['memory_info'].get('max_memory', 'Unknown')}
  Fragmentation: {health['memory_info'].get('memory_fragmentation_ratio', 'Unknown')}

Key Statistics:
"""

        for pattern, count in health["key_stats"].items():
            report += f"  {pattern}: {count} keys\n"

        if health["issues"]:
            report += "\nIssues Found:\n"
            for issue in health["issues"]:
                report += f"  ⚠️  {issue}\n"
        else:
            report += "\n✅ No issues found\n"

        return report


# Global Redis manager instance
_redis_manager = None


def get_redis_manager() -> RedisDataManager:
    """Get global Redis manager instance"""
    global _redis_manager
    if _redis_manager is None:
        config = RedisConfig()
        _redis_manager = RedisDataManager(config)
    return _redis_manager


def get_redis_monitor() -> RedisMonitor:
    """Get Redis monitor instance"""
    return RedisMonitor(get_redis_manager())


# Example usage
if __name__ == "__main__":
    # Initialize Redis manager
    config = RedisConfig()
    redis_manager = RedisDataManager(config)

    # Test operations
    print("Testing Redis operations...")

    # Store indicators
    indicators = {"rsi": 65.5, "macd": 0.001, "adx": 25.3, "ema50": 45000.0}

    success = redis_manager.store_indicators("BTC", "1h", indicators)
    print(f"Store indicators: {'✅' if success else '❌'}")

    # Get indicators
    retrieved = redis_manager.get_indicators("BTC", "1h")
    print(f"Retrieved indicators: {retrieved}")

    # Set counter
    redis_manager.set_counter("scan_count", 100)
    count = redis_manager.get_counter("scan_count")
    print(f"Counter value: {count}")

    # Increment counter
    new_count = redis_manager.increment_counter("scan_count", 5)
    print(f"Incremented counter: {new_count}")

    # Set cache
    redis_manager.set_cache("cache:btc_condition", "bullish", ttl=300)
    condition = redis_manager.get_cache("cache:btc_condition")
    print(f"BTC condition: {condition}")

    # Generate health report
    monitor = RedisMonitor(redis_manager)
    report = monitor.generate_report()
    print(report)
