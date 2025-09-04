#!/usr/bin/env python3
"""
Fix remaining syntax errors in Python files
"""

import os
import re
from pathlib import Path

def fix_file_syntax(file_path):
    """Fix syntax errors in a specific file"""
    print(f"Fixing {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix common syntax issues
        
        # 1. Fix malformed function parameters (extra colons)
        content = re.sub(r',\s*:\s*Any\)', ')', content)
        
        # 2. Fix unterminated string literals
        # Look for lines that might have unterminated strings
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.count('"') % 2 != 0 or line.count("'") % 2 != 0:
                # Try to fix by adding closing quote
                if line.count('"') % 2 != 0:
                    lines[i] = line + '"'
                elif line.count("'") % 2 != 0:
                    lines[i] = line + "'"
        content = '\n'.join(lines)
        
        # 3. Fix unexpected indentation at module level
        lines = content.split('\n')
        fixed_lines = []
        for i, line in enumerate(lines):
            # If line starts with spaces but previous line was import/from
            if i > 0 and line.startswith('    ') and not line.strip().startswith('def ') and not line.strip().startswith('class '):
                prev_line = lines[i-1].strip()
                if prev_line.startswith('import ') or prev_line.startswith('from ') or prev_line == '':
                    # This should be at module level
                    fixed_lines.append(line.lstrip())
                    continue
            fixed_lines.append(line)
        content = '\n'.join(fixed_lines)
        
        # 4. Fix empty import statements
        content = re.sub(r'^import\s*$', '', content, flags=re.MULTILINE)
        
        # 5. Fix malformed imports
        content = re.sub(r'^import\s+$', '', content, flags=re.MULTILINE)
        
        # 6. Fix duplicate imports more aggressively
        lines = content.split('\n')
        seen_imports = set()
        filtered_lines = []
        
        for line in lines:
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                if line.strip() not in seen_imports:
                    seen_imports.add(line.strip())
                    filtered_lines.append(line)
                else:
                    print(f"  Removing duplicate import: {line.strip()}")
            else:
                filtered_lines.append(line)
        
        content = '\n'.join(filtered_lines)
        
        # 7. Fix common indentation issues
        lines = content.split('\n')
        fixed_lines = []
        for i, line in enumerate(lines):
            # Fix lines that are indented but should be at module level
            if (line.startswith('    ') and 
                i > 0 and 
                (lines[i-1].strip().startswith('import ') or 
                 lines[i-1].strip().startswith('from ') or
                 lines[i-1].strip() == '' or
                 lines[i-1].strip().startswith('#')) and
                not line.strip().startswith('def ') and
                not line.strip().startswith('class ') and
                not line.strip().startswith('if ') and
                not line.strip().startswith('for ') and
                not line.strip().startswith('while ') and
                not line.strip().startswith('try:') and
                not line.strip().startswith('except') and
                not line.strip().startswith('finally:') and
                not line.strip().startswith('with ') and
                not line.strip().startswith('@')):
                fixed_lines.append(line.lstrip())
            else:
                fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # 8. Remove empty lines at the beginning
        lines = content.split('\n')
        while lines and not lines[0].strip():
            lines.pop(0)
        content = '\n'.join(lines)
        
        # 9. Ensure file ends with newline
        if content and not content.endswith('\n'):
            content += '\n'
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Fixed syntax errors")
            return True
        else:
            print(f"  ℹ️  No changes needed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix remaining syntax errors"""
    print("🔧 Fixing remaining syntax errors...")
    
    # Files with remaining syntax errors
    problem_files = [
        "dashboard_backend/eval_routes/gpt_eval_api.py",
        "dashboard_backend/anal/capital_routes.py",
        "dca/modules/dca_decision_engine.py",
        "dca/utils/recovery_confidence_utils.py",
        "dca/utils/trade_health_evaluator.py",
        "dca/utils/safu_reentry_utils.py",
        "dca/utils/btc_filter.py",
        "dca/utils/recovery_odds_utils.py",
        "dca/utils/tv_utils.py",
        "ml/confidence/merge_confidence_training.py",
        "ml/safu/check_enriched_safu.py",
        "ml/safu/label_safu_trades.py",
        "ml/recovery/build_recovery_dataset.py",
        "ml/recovery/merge_recovery_datasets.py",
        "ml/preprocess/paper_scrubber.py",
        "ml/preprocess/extract_ml_dataset.py",
        "ml/preprocess/build_enriched_dataset.py",
        "ml/preprocess/hail_mary.py",
        "ml/preprocess/merge_cleaned_flattened.py",
        "ml/preprocess/archive/extract_passed_forks copy.py",
        "ml/utils/time_utils.py",
        "fork/modules/fork_safu_monitor.py",
        "fork/utils/fork_entry_utils.py",
        "fork/utils/fork_entry_logger.py",
        "fork/utils/entry_utils.py",
        "indicators/rrr_filter.py",
        "indicators/send_test_trade.py",
        "indicators/store_indicators.py",
        "indicators/tv_kicker.py",
        "indicators/rrr_filter/tv_puller.py",
        "indicators/rrr_filter/evaluate.py",
        "indicators/rrr_filter/run_rrr_filter.py",
        "indicators/rrr_filter/tv_screener_score.py",
        "indicators/rrr_filter/time_to_profit.py",
        "core/redis_utils.py",
        "data/volume_filter.py",
        "data/update_binance_symbols.py",
        "data/rolling_klines.py",
        "data/backfill_indicators.py",
        "utils/error_handling.py",
        "utils/sim_indicators.py",
        "utils/ml_logger.py",
        "utils/log_reader.py",
    ]
    
    fixed_count = 0
    
    for file_path in problem_files:
        if os.path.exists(file_path):
            if fix_file_syntax(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n🎉 Fixed {fixed_count} files")

if __name__ == "__main__":
    main()