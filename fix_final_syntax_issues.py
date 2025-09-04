#!/usr/bin/env python3
"""
Fix final syntax issues including Unicode characters and structural problems
"""

import os
import re
from pathlib import Path

def fix_unicode_and_syntax(file_path):
    """Fix Unicode characters and syntax issues in a file"""
    print(f"Fixing Unicode and syntax in {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix Unicode characters that cause syntax errors
        unicode_replacements = {
            '🚫': '[BLOCKED]',
            '💾': '[SAVE]',
            '🔎': '[SEARCH]',
            '✅': '[OK]',
            '⚙': '[CONFIG]',
            '📁': '[FOLDER]',
            '🔍': '[SEARCH]',
            '⚠️': '[WARNING]',
            '❌': '[ERROR]',
            '🎉': '[SUCCESS]',
            '🔧': '[FIX]',
            '📊': '[STATS]',
            '🎯': '[TARGET]',
            '🚀': '[LAUNCH]',
            '💡': '[IDEA]',
            '🔒': '[LOCK]',
            '🔓': '[UNLOCK]',
            '⭐': '[STAR]',
            '🔥': '[FIRE]',
            '💯': '[100]',
            '📈': '[UP]',
            '📉': '[DOWN]',
            '💰': '[MONEY]',
            '🏆': '[TROPHY]',
            '🎪': '[CIRCUS]',
            '🎨': '[ART]',
            '🎵': '[MUSIC]',
            '🎬': '[MOVIE]',
            '🎮': '[GAME]',
            '🎯': '[TARGET]',
            '🎲': '[DICE]',
            '🎳': '[BOWLING]',
            '🎸': '[GUITAR]',
            '🎺': '[TRUMPET]',
            '🎻': '[VIOLIN]',
            '🎼': '[MUSIC]',
            '🎽': '[RUNNING]',
            '🎾': '[TENNIS]',
            '🎿': '[SKIING]',
            '🏀': '[BASKETBALL]',
            '🏁': '[FINISH]',
            '🏂': '[SNOWBOARD]',
            '🏃': '[RUNNING]',
            '🏄': '[SURFING]',
            '🏅': '[MEDAL]',
            '🏆': '[TROPHY]',
            '🏇': '[HORSE]',
            '🏈': '[FOOTBALL]',
            '🏉': '[RUGBY]',
            '🏊': '[SWIMMING]',
            '🏋': '[WEIGHTLIFTING]',
            '🏌': '[GOLF]',
            '🏍': '[MOTORCYCLE]',
            '🏎': '[RACING]',
            '🏏': '[CRICKET]',
            '🏐': '[VOLLEYBALL]',
            '🏑': '[HOCKEY]',
            '🏒': '[HOCKEY]',
            '🏓': '[PINGPONG]',
            '🏔': '[MOUNTAIN]',
            '🏕': '[CAMPING]',
            '🏖': '[BEACH]',
            '🏗': '[CONSTRUCTION]',
            '🏘': '[HOUSES]',
            '🏙': '[CITY]',
            '🏚': '[HOUSE]',
            '🏛': '[BUILDING]',
            '🏜': '[DESERT]',
            '🏝': '[ISLAND]',
            '🏞': '[PARK]',
            '🏟': '[STADIUM]',
            '🏠': '[HOUSE]',
            '🏡': '[HOUSE]',
            '🏢': '[OFFICE]',
            '🏣': '[POST]',
            '🏤': '[POST]',
            '🏥': '[HOSPITAL]',
            '🏦': '[BANK]',
            '🏧': '[ATM]',
            '🏨': '[HOTEL]',
            '🏩': '[LOVE]',
            '🏪': '[STORE]',
            '🏫': '[SCHOOL]',
            '🏬': '[STORE]',
            '🏭': '[FACTORY]',
            '🏮': '[LANTERN]',
            '🏯': '[CASTLE]',
            '🏰': '[CASTLE]',
            '🏳': '[FLAG]',
            '🏴': '[FLAG]',
            '🏵': '[ROSETTE]',
            '🏶': '[LABEL]',
            '🏷': '[TAG]',
            '🏸': '[BADMINTON]',
            '🏹': '[ARCHERY]',
            '🏺': '[POT]',
            '🏻': '[LIGHT]',
            '🏼': '[MEDIUM]',
            '🏽': '[MEDIUM]',
            '🏾': '[DARK]',
            '🏿': '[DARK]',
        }
        
        for unicode_char, replacement in unicode_replacements.items():
            content = content.replace(unicode_char, replacement)
        
        # Fix unterminated string literals more aggressively
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Check for unterminated strings and fix them
            if line.count('"') % 2 != 0:
                # Add closing quote
                lines[i] = line + '"'
                print(f"  Fixed unterminated double quote on line {i+1}")
            elif line.count("'") % 2 != 0:
                # Add closing quote
                lines[i] = line + "'"
                print(f"  Fixed unterminated single quote on line {i+1}")
            
            # Fix escaped quotes
            if '\\"' in line:
                lines[i] = lines[i].replace('\\"', '"')
                print(f"  Fixed escaped double quote on line {i+1}")
            if "\\'" in line:
                lines[i] = lines[i].replace("\\'", "'")
                print(f"  Fixed escaped single quote on line {i+1}")
        
        content = '\n'.join(lines)
        
        # Fix structural issues
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Fix empty try blocks
            if line.strip() == 'try:' and i + 1 < len(lines) and lines[i + 1].strip() == '':
                # Add pass statement
                fixed_lines.append(line)
                fixed_lines.append('    pass')
                print(f"  Added pass to empty try block on line {i+1}")
                continue
            
            # Fix empty function definitions
            if (line.strip().startswith('def ') and 
                i + 1 < len(lines) and 
                (lines[i + 1].strip() == '' or lines[i + 1].strip().startswith('"""'))):
                # Add pass statement
                fixed_lines.append(line)
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('"""'):
                    # Skip docstring
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().endswith('"""'):
                        j += 1
                    if j < len(lines):
                        j += 1
                    # Add pass after docstring
                    fixed_lines.append('    pass')
                    # Skip the docstring lines
                    for k in range(i + 1, j):
                        if k < len(lines):
                            fixed_lines.append(lines[k])
                    continue
            
            # Fix malformed function parameters
            if 'def ' in line and ', :' in line:
                lines[i] = re.sub(r',\s*:', '', line)
                print(f"  Fixed malformed function parameter on line {i+1}")
            
            # Fix malformed imports
            if line.strip() == 'import ':
                lines[i] = ''
                print(f"  Removed empty import on line {i+1}")
            
            # Fix unexpected indentation
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
                not line.strip().startswith('continue') and
                not line.strip().startswith('print') and
                not line.strip().startswith('logger') and
                not line.strip().startswith('log')):
                fixed_lines.append(line.lstrip())
                print(f"  Fixed unexpected indentation on line {i+1}")
            else:
                fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Fix malformed syntax
        content = re.sub(r',\s*\)', ')', content)  # Remove trailing commas
        content = re.sub(r'\(\s*\)', '()', content)  # Fix empty parentheses
        content = re.sub(r'\[\s*\]', '[]', content)  # Fix empty brackets
        content = re.sub(r'{\s*}', '{}', content)  # Fix empty braces
        
        # Ensure file ends with newline
        if content and not content.endswith('\n'):
            content += '\n'
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Fixed Unicode and syntax issues")
            return True
        else:
            print(f"  ℹ️  No changes needed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix Unicode and syntax issues in problematic files"""
    print("🔧 Fixing Unicode characters and final syntax issues...")
    
    # Files with remaining issues
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
            if fix_unicode_and_syntax(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n🎉 Fixed {fixed_count} files")

if __name__ == "__main__":
    main()