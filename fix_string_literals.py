#!/usr/bin/env python3
"""
Fix unterminated string literals and other syntax issues
"""

import os
import re
from pathlib import Path

def fix_string_literals(file_path):
    """Fix unterminated string literals in a file"""
    print(f"Fixing string literals in {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix unterminated string literals
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Check for unterminated strings
            if line.count('"') % 2 != 0:
                # Add closing quote
                lines[i] = line + '"'
                print(f"  Fixed unterminated double quote on line {i+1}")
            elif line.count("'") % 2 != 0:
                # Add closing quote
                lines[i] = line + "'"
                print(f"  Fixed unterminated single quote on line {i+1}")
            
            # Fix escaped quotes that might be causing issues
            if '\\"' in line or "\\'" in line:
                # Replace escaped quotes with regular quotes
                lines[i] = lines[i].replace('\\"', '"').replace("\\'", "'")
                print(f"  Fixed escaped quotes on line {i+1}")
        
        content = '\n'.join(lines)
        
        # Fix other common syntax issues
        # Fix malformed function calls with extra commas
        content = re.sub(r',\s*\)', ')', content)
        
        # Fix malformed imports
        content = re.sub(r'^import\s*$', '', content, flags=re.MULTILINE)
        
        # Fix unexpected indentation
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Fix lines that are unexpectedly indented at module level
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
                not line.strip().startswith('@') and
                not line.strip().startswith('return') and
                not line.strip().startswith('yield') and
                not line.strip().startswith('raise') and
                not line.strip().startswith('assert') and
                not line.strip().startswith('pass') and
                not line.strip().startswith('break') and
                not line.strip().startswith('continue')):
                fixed_lines.append(line.lstrip())
                print(f"  Fixed unexpected indentation on line {i+1}")
            else:
                fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Fix unindent issues
        lines = content.split('\n')
        fixed_lines = []
        indent_level = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                fixed_lines.append(line)
                continue
                
            # Calculate expected indentation
            if stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'with ', 'except', 'finally:', 'else:', 'elif ')):
                indent_level = 0
            elif stripped.startswith(('return', 'yield', 'raise', 'assert', 'pass', 'break', 'continue')):
                indent_level = 4
            elif stripped.startswith(('import ', 'from ')):
                indent_level = 0
            
            # Fix unindent issues
            if line.startswith('    ') and indent_level == 0:
                fixed_lines.append(line.lstrip())
            elif not line.startswith(' ') and indent_level > 0:
                fixed_lines.append('    ' * (indent_level // 4) + line)
            else:
                fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Fixed string literals and syntax issues")
            return True
        else:
            print(f"  ℹ️  No changes needed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix string literals in problematic files"""
    print("🔧 Fixing string literals and syntax issues...")
    
    # Files with string literal issues
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
            if fix_string_literals(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n🎉 Fixed {fixed_count} files")

if __name__ == "__main__":
    main()