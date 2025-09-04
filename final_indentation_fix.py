#!/usr/bin/env python3
"""
Final indentation fix for remaining syntax issues
"""

import os
import re

def fix_indentation_issues(file_path):
    """Fix indentation issues in a file"""
    print(f"Fixing {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix common indentation patterns
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Fix lines that should be indented but aren't
            if (stripped and 
                not stripped.startswith('#') and
                not stripped.startswith('from ') and
                not stripped.startswith('import ') and
                not stripped.startswith('def ') and
                not stripped.startswith('class ') and
                not stripped.startswith('"""') and
                not stripped.startswith("'''") and
                not stripped.startswith('if __name__') and
                i > 0 and
                lines[i-1].strip().endswith(':')):
                # This line should be indented
                if not line.startswith('    '):
                    fixed_lines.append('    ' + line)
                    continue
            
            # Fix malformed import statements
            if stripped.startswith('from ') and 'import' in stripped and ',' in stripped:
                # Fix malformed import statements
                fixed_lines.append('    ' + stripped)
                continue
            
            # Fix docstring issues
            if stripped == '"""Docstring placeholder."""' or stripped == '""""""':
                fixed_lines.append('    """Docstring placeholder."""')
                continue
            
            # Fix specific problematic patterns
            if 'import exist_ok=True' in stripped:
                fixed_lines.append('    # import exist_ok=True')
                continue
            
            if '→' in stripped:
                fixed_lines.append(line.replace('→', '->'))
                continue
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Fixed indentation issues")
            return True
        else:
            print(f"  ℹ️  No changes needed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix remaining indentation issues"""
    print("🔧 Final indentation fix...")
    
    problem_files = [
        "dashboard_backend/eval_routes/gpt_eval_api.py",
        "dashboard_backend/anal/capital_routes.py",
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
            if fix_indentation_issues(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n🎉 Fixed {fixed_count} files")

if __name__ == "__main__":
    main()