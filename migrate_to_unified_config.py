#!/usr/bin/env python3
"""
Migration Script - Convert all hardcoded paths to unified config system
Updates all files to use the new UnifiedConfigManager instead of hardcoded paths
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


class ConfigMigrationTool:
    """Tool to migrate all hardcoded paths to unified config system"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.migration_map = self._build_migration_map()
        self.files_to_update = []
        self.backup_dir = workspace_root / "config_migration_backup"
    
    def _build_migration_map(self) -> Dict[str, str]:
        """Build mapping from hardcoded patterns to unified config calls"""
        return {
            # Hardcoded absolute paths
            r'Path\("/home/signal/market7/config/tv_screener_config\.yaml"\)': 'get_path("tv_screener_config")',
            r'Path\("/home/signal/market7/dashboard_backend/cache/fork_metrics\.json"\)': 'get_path("dashboard_cache") / "fork_metrics.json"',
            r'Path\("/home/signal/market7/config/fork_safu_config\.yaml"\)': 'get_path("fork_safu_config")',
            r'Path\("/home/signal/market7/config/dca_config\.yaml"\)': 'get_path("dca_config")',
            
            # Relative path calculations
            r'BASE_DIR = Path\(__file__\)\.resolve\(\)\.parent\.parent\.parent': 'BASE_DIR = get_path("base")',
            r'BASE_DIR = Path\(__file__\)\.resolve\(\)\.parent\.parent': 'BASE_DIR = get_path("base")',
            r'PROJECT_ROOT = CURRENT_FILE\.parents\[1\]': 'PROJECT_ROOT = get_path("base")',
            r'CURRENT_FILE = Path\(__file__\)\.resolve\(\)\nPROJECT_ROOT = CURRENT_FILE\.parents\[1\]': 'PROJECT_ROOT = get_path("base")',
            
            # Config path constructions
            r'BASE_DIR / "config" / "fork_safu_config\.yaml"': 'get_path("fork_safu_config")',
            r'BASE_DIR / "config" / "tv_screener_config\.yaml"': 'get_path("tv_screener_config")',
            r'BASE_DIR / "config" / "dca_config\.yaml"': 'get_path("dca_config")',
            r'get_path("snapshots")': 'get_path("snapshots")',
            r'get_path("fork_history")': 'get_path("fork_history")',
            r'get_path("btc_logs")': 'get_path("btc_logs")',
            r'get_path("live_logs")': 'get_path("live_logs")',
            r'get_path("models")': 'get_path("models")',
            r'BASE_DIR / "ml" / "models" / "safu_exit_model\.pkl"': 'get_path("models") / "safu_exit_model.pkl"',
            
            # PATHS usage patterns (already good, but ensure consistency)
            r'PATHS\["paper_cred"\]': 'get_path("paper_cred")',
            r'PATHS\["snapshots"\]': 'get_path("snapshots")',
            r'PATHS\["fork_history"\]': 'get_path("fork_history")',
            r'PATHS\["btc_logs"\]': 'get_path("btc_logs")',
            r'PATHS\["live_logs"\]': 'get_path("live_logs")',
            r'PATHS\["models"\]': 'get_path("models")',
            r'PATHS\["dca_config"\]': 'get_path("dca_config")',
            r'PATHS\["tv_screener_config"\]': 'get_path("tv_screener_config")',
            r'PATHS\["fork_safu_config"\]': 'get_path("fork_safu_config")',
            r'PATHS\["final_fork_rrr_trades"\]': 'get_path("final_fork_rrr_trades")',
            r'PATHS\["fork_tv_adjusted"\]': 'get_path("fork_tv_adjusted")',
            r'PATHS\["fork_backtest_candidates"\]': 'get_path("fork_backtest_candidates")',
            r'PATHS\["tv_history"\]': 'get_path("tv_history")',
            r'PATHS\["filtered_pairs"\]': 'get_path("filtered_pairs")',
            r'PATHS\["base"\]': 'get_path("base")',
        }
    
    def find_files_to_migrate(self) -> List[Path]:
        """Find all Python files that need migration"""
        python_files = []
        
        # Search for Python files with hardcoded paths
        for root, dirs, files in os.walk(self.workspace_root):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.pytest_cache']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    if self._needs_migration(file_path):
                        python_files.append(file_path)
        
        return python_files
    
    def _needs_migration(self, file_path: Path) -> bool:
        """Check if file needs migration"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for hardcoded patterns
            hardcoded_patterns = [
                r'/home/signal/market7',
                r'Path\(__file__\)\.resolve\(\)\.parent',
                r'BASE_DIR = Path\(__file__\)',
                r'PROJECT_ROOT = CURRENT_FILE\.parents',
                r'CONFIG_PATH = Path\(',
                r'from config\.config_loader import PATHS',
            ]
            
            for pattern in hardcoded_patterns:
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
        """Migrate a single file to use unified config"""
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
            
            # Add import if needed
            if self._needs_unified_config_import(content):
                content = self._add_unified_config_import(content)
            
            # Remove old imports if present
            content = self._remove_old_imports(content)
            
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
    
    def _needs_unified_config_import(self, content: str) -> bool:
        """Check if file needs unified config import"""
        return (
            'get_path(' in content or 
            'get_config(' in content or
            'get_all_paths(' in content or
            'get_all_configs(' in content
        ) and 'from config.unified_config_manager import' not in content
    
    def _add_unified_config_import(self, content: str) -> str:
        """Add unified config import to file"""
        import_line = "from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs\n"
        
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
    
    def _remove_old_imports(self, content: str) -> str:
        """Remove old config loader imports"""
        patterns_to_remove = [
            r'from config\.config_loader import PATHS\n',
            r'from config\.config_loader import PATHS, CONFIG_PATH\n',
            r'import sys\nfrom pathlib import Path\n# === Patch sys\.path to reach /market7 ===\nCURRENT_FILE = Path\(__file__\)\.resolve\(\)\nPROJECT_ROOT = CURRENT_FILE\.parents\[1\]\nsys\.path\.append\(str\(PROJECT_ROOT\)\)\n',
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
# Configuration Migration Report

## Summary
- **Total files processed**: {results['total']}
- **Successfully migrated**: {results['migrated']}
- **Skipped (no changes)**: {results['skipped']}
- **Failed**: {results['failed']}

## Migration Details

### What was changed:
1. **Hardcoded absolute paths** → `get_path("key")`
2. **Relative path calculations** → `get_path("base")`
3. **PATHS dictionary usage** → `get_path("key")`
4. **Config file paths** → `get_path("config_key")`

### Examples of changes:

#### Before:
```python
CONFIG_PATH = get_path("tv_screener_config")
BASE_DIR = get_path("base")
SAFU_CONFIG_PATH = get_path("fork_safu_config")
```

#### After:
```python
from config.unified_config_manager import get_path, get_config
from config.unified_config_manager import get_config
CONFIG_PATH = get_path("tv_screener_config")
BASE_DIR = get_path("base")
SAFU_CONFIG_PATH = get_path("fork_safu_config")
```

### Benefits:
- ✅ **Environment-aware**: Automatically detects dev/staging/prod
- ✅ **Smart defaults**: Fallback values for missing configs
- ✅ **Validation**: Comprehensive config validation
- ✅ **Consistent API**: Same interface across all systems
- ✅ **Easy maintenance**: Centralized configuration management

### Backup:
All original files backed up to: `{self.backup_dir}`

### Next Steps:
1. Test the migrated files
2. Update any remaining hardcoded paths manually
3. Add environment-specific configurations
4. Implement config validation in your deployment pipeline
"""
        return report


def main():
    """Main migration function"""
    workspace_root = Path.cwd()
    logger.info(f"Starting migration in {workspace_root}")
    
    # Create migration tool
    migration_tool = ConfigMigrationTool(workspace_root)
    
    # Run migration
    results = migration_tool.migrate_all()
    
    # Create report
    report = migration_tool.create_migration_report(results)
    
    # Save report
    report_path = workspace_root / "CONFIG_MIGRATION_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    logger.info(f"Migration complete! Report saved to {report_path}")
    logger.info(f"Results: {results}")
    
    return results


if __name__ == "__main__":
    main()