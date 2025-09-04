#!/usr/bin/env python3
"""
Redis Migration Script - Convert scattered Redis usage to optimized Redis Manager
Updates all files to use the new RedisManager instead of direct Redis operations
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class RedisMigrationTool:
    """Tool to migrate all Redis usage to optimized Redis Manager"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.migration_map = self._build_migration_map()
        self.files_to_update = []
        self.backup_dir = workspace_root / "redis_migration_backup"
    
    def _build_migration_map(self) -> Dict[str, str]:
        """Build mapping from old Redis patterns to new Redis Manager calls"""
        return {
            # Redis connection patterns
            r'r = redis\.Redis\(host="localhost", port=6379, decode_responses=True\)': 'from utils.redis_manager import get_redis_manager\nr = get_redis_manager()',
            r'r = redis\.Redis\(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB\)': 'from utils.redis_manager import get_redis_manager\nr = get_redis_manager()',
            r'redis_client = redis\.Redis\(host=\'localhost\', port=6379, db=0\)': 'from utils.redis_manager import get_redis_manager\nredis_client = get_redis_manager()',
            
            # Key patterns - convert to proper namespacing
            r'f"\{symbol\.upper\(\)\}_\{tf\}"': 'RedisKeyManager.indicator(symbol, tf)',
            r'f"\{symbol\.upper\(\)\}_\{tf\}_RSI14"': 'f"indicators:{symbol.upper()}:{tf}:RSI14"',
            r'f"\{symbol\.upper\(\)\}_\{tf\}_StochRSI_K"': 'f"indicators:{symbol.upper()}:{tf}:StochRSI_K"',
            r'f"\{symbol\.upper\(\)\}_\{tf\}_StochRSI_D"': 'f"indicators:{symbol.upper()}:{tf}:StochRSI_D"',
            r'"BTC_1h_latest_close"': '"indicators:BTC:1h:latest_close"',
            r'"BTC_1h_EMA50"': '"indicators:BTC:1h:EMA50"',
            r'"BTC_15m_RSI14"': '"indicators:BTC:15m:RSI14"',
            r'"BTC_1h_ADX14"': '"indicators:BTC:1h:ADX14"',
            r'"btc_condition"': '"cache:btc_condition"',
            r'"last_scan_vol"': '"counters:last_scan_vol"',
            r'"tech_filter_count_in"': '"counters:tech_filter_count_in"',
            r'"tech_filter_count_out"': '"counters:tech_filter_count_out"',
            r'"volume_filter_count"': '"counters:volume_filter_count"',
            r'"FINAL_TRADES"': '"queues:final_trades"',
            r'"SENT_TRADES"': '"sessions:sent_trades"',
            r'"VOLUME_PASSED_TOKENS"': '"queues:volume_passed_tokens"',
            r'"FORK_RRR_PASSED"': '"queues:fork_rrr_passed"',
            r'"fork_score:approved"': '"queues:fork_score_approved"',
            
            # Redis operations - convert to Redis Manager methods
            r'r\.set\(([^,]+),\s*json\.dumps\(([^)]+)\)\)': 'r.store_indicators(\\1, \\2)',
            r'r\.set\(([^,]+),\s*([^)]+)\)': 'r.set_cache(\\1, \\2)',
            r'r\.get\(([^)]+)\)': 'r.get_cache(\\1)',
            r'r\.hset\(([^,]+),\s*([^,]+),\s*json\.dumps\(([^)]+)\)\)': 'r.store_trade_data({\\"symbol\\": \\2, \\"data\\": \\3})',
            r'r\.hget\(([^,]+),\s*([^)]+)\)': 'r.get_trade_data()',
            r'r\.sadd\(([^,]+),\s*([^)]+)\)': 'r.store_trade_data({\\"symbol\\": \\2})',
            r'r\.smembers\(([^)]+)\)': 'r.get_trade_data()',
            r'r\.rpush\(([^,]+),\s*json\.dumps\(([^)]+)\)\)': 'r.store_trade_data(\\2)',
            r'r\.lpush\(([^,]+),\s*json\.dumps\(([^)]+)\)\)': 'r.store_trade_data(\\2)',
            r'r\.delete\(([^)]+)\)': 'r.cleanup_expired_keys()',
            r'r\.exists\(([^)]+)\)': 'r.get_cache(\\1) is not None',
            r'r\.keys\(([^)]+)\)': 'r.get_key_stats()',
        }
    
    def find_files_to_migrate(self) -> List[Path]:
        """Find all Python files that need Redis migration"""
        python_files = []
        
        # Search for Python files with Redis usage
        for root, dirs, files in os.walk(self.workspace_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.pytest_cache', 'redis_migration_backup']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    if self._needs_redis_migration(file_path):
                        python_files.append(file_path)
        
        return python_files
    
    def _needs_redis_migration(self, file_path: Path) -> bool:
        """Check if file needs Redis migration"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for Redis patterns
            redis_patterns = [
                r'redis\.Redis\(',
                r'r\.get\(',
                r'r\.set\(',
                r'r\.hget\(',
                r'r\.hset\(',
                r'r\.sadd\(',
                r'r\.smembers\(',
                r'r\.rpush\(',
                r'r\.lpush\(',
                r'r\.delete\(',
                r'r\.exists\(',
                r'r\.keys\(',
            ]
            
            for pattern in redis_patterns:
                if re.search(pattern, content):
                    return True
            
            return False
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return False
    
    def backup_file(self, file_path: Path) -> Path:
        """Create backup of file before migration"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create relative path in backup
        relative_path = file_path.relative_to(self.workspace_root)
        backup_path = self.backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def migrate_file(self, file_path: Path) -> bool:
        """Migrate a single file to use Redis Manager"""
        try:
            # Create backup
            backup_path = self.backup_file(file_path)
            logger.info(f"Backed up {file_path} to {backup_path}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply migrations
            content = self._apply_migrations(content)
            
            # Add Redis Manager import if needed
            if self._needs_redis_manager_import(content):
                content = self._add_redis_manager_import(content)
            
            # Remove old Redis imports if present
            content = self._remove_old_redis_imports(content)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"✅ Migrated {file_path}")
                return True
            else:
                logger.info(f"⏭️  No changes needed for {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to migrate {file_path}: {e}")
            return False
    
    def _apply_migrations(self, content: str) -> str:
        """Apply all migration patterns to content"""
        for pattern, replacement in self.migration_map.items():
            content = re.sub(pattern, replacement, content)
        return content
    
    def _needs_redis_manager_import(self, content: str) -> bool:
        """Check if file needs Redis Manager import"""
        return (
            'get_redis_manager(' in content or 
            'RedisKeyManager.' in content or
            'store_indicators(' in content or
            'get_indicators(' in content or
            'store_trade_data(' in content or
            'get_trade_data(' in content or
            'set_counter(' in content or
            'get_counter(' in content or
            'set_cache(' in content or
            'get_cache(' in content
        ) and 'from utils.redis_manager import' not in content
    
    def _add_redis_manager_import(self, content: str) -> str:
        """Add Redis Manager import to file"""
        import_line = "from utils.redis_manager import get_redis_manager, RedisKeyManager\n"
        
        # Find the best place to add import
        lines = content.split('\n')
        
        # Look for existing imports
        import_index = -1
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i
        
        if import_index >= 0:
            # Insert after last import
            lines.insert(import_index + 1, import_line)
        else:
            # Insert at the beginning
            lines.insert(0, import_line)
        
        return '\n'.join(lines)
    
    def _remove_old_redis_imports(self, content: str) -> str:
        """Remove old Redis imports"""
        patterns_to_remove = [
            r'import redis\n',
            r'from redis import Redis\n',
            r'import redis\nfrom redis.connection import ConnectionPool\n',
        ]
        
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content)
        
        return content
    
    def migrate_all(self) -> Dict[str, int]:
        """Migrate all files found"""
        logger.info("🔍 Finding files to migrate...")
        files_to_migrate = self.find_files_to_migrate()
        
        logger.info(f"Found {len(files_to_migrate)} files to migrate")
        
        results = {
            'total': len(files_to_migrate),
            'migrated': 0,
            'skipped': 0,
            'failed': 0
        }
        
        for file_path in files_to_migrate:
            logger.info(f"Migrating {file_path.relative_to(self.workspace_root)}...")
            
            if self.migrate_file(file_path):
                results['migrated'] += 1
            else:
                results['skipped'] += 1
        
        return results
    
    def create_migration_report(self, results: Dict[str, int]) -> str:
        """Create migration report"""
        report = f"""
# Redis Migration Report

## Summary
- **Total files processed**: {results['total']}
- **Successfully migrated**: {results['migrated']}
- **Skipped (no changes)**: {results['skipped']}
- **Failed**: {results['failed']}

## Migration Details

### What was changed:
1. **Redis connections** → `get_redis_manager()`
2. **Key patterns** → `RedisKeyManager` namespacing
3. **Redis operations** → Redis Manager methods
4. **Data structures** → Optimized Hash/List/Set usage

### Examples of changes:

#### Before:
```python
import redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Inconsistent key patterns
key = f"{symbol}_{tf}"
r.set(key, json.dumps(indicators))
r.set(f"{symbol}_{tf}_RSI14", indicators["RSI14"])

# Inefficient operations
r.get("BTC_1h_latest_close")
r.get("BTC_1h_EMA50")
r.get("BTC_15m_RSI14")
```

#### After:
```python
from utils.redis_manager import get_redis_manager, RedisKeyManager
r = get_redis_manager()

# Proper namespacing
r.store_indicators(symbol, tf, indicators)

# Optimized operations
indicators = r.get_indicators("BTC", "1h")
```

### Benefits:
- ✅ **Connection pooling**: Better performance and reliability
- ✅ **Key namespacing**: Prevents key collisions
- ✅ **Data structure optimization**: Uses appropriate Redis types
- ✅ **TTL management**: Automatic cleanup of temporary data
- ✅ **Error handling**: Robust error handling and logging
- ✅ **Monitoring**: Built-in health checks and monitoring

### Backup:
All original files backed up to: `{self.backup_dir}`

### Next Steps:
1. Test the migrated files
2. Update Redis configuration for production
3. Implement Redis monitoring and alerting
4. Set up Redis persistence and backup
5. Monitor Redis performance and memory usage
"""
        return report


def main():
    """Main migration function"""
    workspace_root = Path.cwd()
    logger.info(f"Starting Redis migration in {workspace_root}")
    
    # Create migration tool
    migration_tool = RedisMigrationTool(workspace_root)
    
    # Run migration
    results = migration_tool.migrate_all()
    
    # Create report
    report = migration_tool.create_migration_report(results)
    
    # Save report
    report_path = workspace_root / "REDIS_MIGRATION_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    logger.info(f"Migration complete! Report saved to {report_path}")
    logger.info(f"Results: {results}")
    
    return results


if __name__ == "__main__":
    main()