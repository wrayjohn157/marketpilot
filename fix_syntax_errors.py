#!/usr/bin/env python3
"""
Fix syntax errors in Python files
"""

import os
import re
from pathlib import Path

def fix_duplicate_imports(file_path):
    """Fix duplicate import statements"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match duplicate imports
    pattern = r'from\s+([^\s]+)\s+import\s+([^\n]+)\nfrom\s+\1\s+import\s+([^\n]+)'
    
    def replace_duplicate(match):
        module = match.group(1)
        imports1 = match.group(2).strip()
        imports2 = match.group(3).strip()
        
        # Combine imports
        all_imports = f"{imports1}, {imports2}"
        return f"from {module} import {all_imports}"
    
    new_content = re.sub(pattern, replace_duplicate, content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def fix_indentation_errors(file_path):
    """Fix common indentation errors"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed = False
    new_lines = []
    
    for i, line in enumerate(lines):
        # Fix lines that start with spaces but should be at module level
        if line.strip() and not line.startswith(' ') and i > 0:
            # Check if previous line was an import and this line is indented
            if i > 0 and ('import' in lines[i-1] or 'from' in lines[i-1]):
                if line.startswith('    '):
                    # This should be at module level
                    new_lines.append(line.lstrip())
                    fixed = True
                    continue
        
        new_lines.append(line)
    
    if fixed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(''.join(new_lines))
        return True
    return False

def fix_missing_imports(file_path):
    """Add missing common imports"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file uses Any but doesn't import it
    if 'Any' in content and 'from typing import' not in content:
        # Add typing import
        lines = content.split('\n')
        import_line = 'from typing import Any'
        
        # Find the right place to insert
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_index = i + 1
        
        lines.insert(insert_index, import_line)
        new_content = '\n'.join(lines)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    
    return False

def fix_invalid_characters(file_path):
    """Fix invalid characters in files"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace common invalid characters
    replacements = {
        '─': '-',  # Unicode box drawing character
        '–': '-',  # En dash
        '—': '-',  # Em dash
        ''': "'",  # Left single quotation mark
        ''': "'",  # Right single quotation mark
        '"': '"',  # Left double quotation mark
        '"': '"',  # Right double quotation mark
    }
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def fix_line_continuation_errors(file_path):
    """Fix line continuation character errors"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix malformed line continuations
    # Pattern: \ followed by invalid character
    pattern = r'\\([^\\\n])'
    new_content = re.sub(pattern, r'\\\n\1', content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def fix_empty_imports(file_path):
    """Fix empty import statements"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix "import " without module name
    pattern = r'^import\s*$'
    new_content = re.sub(pattern, '', content, flags=re.MULTILINE)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def fix_file(file_path):
    """Fix all issues in a single file"""
    print(f"Fixing {file_path}...")
    
    fixes_applied = []
    
    if fix_duplicate_imports(file_path):
        fixes_applied.append("duplicate imports")
    
    if fix_indentation_errors(file_path):
        fixes_applied.append("indentation")
    
    if fix_missing_imports(file_path):
        fixes_applied.append("missing imports")
    
    if fix_invalid_characters(file_path):
        fixes_applied.append("invalid characters")
    
    if fix_line_continuation_errors(file_path):
        fixes_applied.append("line continuation")
    
    if fix_empty_imports(file_path):
        fixes_applied.append("empty imports")
    
    if fixes_applied:
        print(f"  ✅ Fixed: {', '.join(fixes_applied)}")
        return True
    else:
        print(f"  ℹ️  No fixes needed")
        return False

def main():
    """Fix syntax errors in all Python files"""
    print("🔧 Fixing syntax errors...")
    
    # Files with known syntax errors
    problem_files = [
        "test_redis_manager.py",
        "test_unified_config.py", 
        "dashboard_backend/eval_routes/gpt_eval_api.py",
        "dashboard_backend/anal/capital_routes.py",
        "dca/modules/dca_decision_engine.py",
        "dca/utils/zombie_utils.py",
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
        "indicators/fork_score_filter.py",
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
            if fix_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n🎉 Fixed {fixed_count} files")

if __name__ == "__main__":
    main()