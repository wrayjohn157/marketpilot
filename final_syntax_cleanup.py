#!/usr/bin/env python3
"""
Final syntax cleanup script to fix remaining 41 syntax errors
"""

import os
import re
from pathlib import Path


def fix_specific_syntax_issues(file_path):
    """Fix specific syntax issues in a file"""
    print(f"Fixing {file_path}...")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Fix specific issues based on file patterns

        # 1. Fix empty try blocks
        content = re.sub(r"try:\s*\n\s*except", "try:\n    pass\nexcept", content)

        # 2. Fix empty function definitions
        content = re.sub(
            r'(def\s+\w+\([^)]*\):\s*\n)(\s*"""[^"]*"""\s*\n)?(\s*$)',
            r"\1\2    pass\n",
            content,
            flags=re.MULTILINE,
        )

        # 3. Fix unterminated string literals more aggressively
        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Count quotes and fix if odd
            if line.count('"') % 2 != 0:
                lines[i] = line + '"'
            elif line.count("'") % 2 != 0:
                lines[i] = line + "'"

            # Fix escaped quotes that might be causing issues
            if '\\"' in line:
                lines[i] = lines[i].replace('\\"', '"')
            if "\\'" in line:
                lines[i] = lines[i].replace("\\'", "'")

        content = "\n".join(lines)

        # 4. Fix Unicode characters
        unicode_replacements = {
            "️": "",  # Remove invisible characters
            "🔹": "[INFO]",
            "🚫": "[BLOCKED]",
            "💾": "[SAVE]",
            "🔎": "[SEARCH]",
            "✅": "[OK]",
            "⚙": "[CONFIG]",
            "📁": "[FOLDER]",
            "🔍": "[SEARCH]",
            "⚠️": "[WARNING]",
            "❌": "[ERROR]",
            "🎉": "[SUCCESS]",
            "🔧": "[FIX]",
            "📊": "[STATS]",
            "🎯": "[TARGET]",
            "🚀": "[LAUNCH]",
        }

        for unicode_char, replacement in unicode_replacements.items():
            content = content.replace(unicode_char, replacement)

        # 5. Fix malformed imports
        content = re.sub(r"^import\s*$", "", content, flags=re.MULTILINE)
        content = re.sub(r"^from\s+\w+\s+import\s*$", "", content, flags=re.MULTILINE)

        # 6. Fix unexpected indentation
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            # Fix lines that are unexpectedly indented at module level
            if (
                line.startswith("    ")
                and i > 0
                and (
                    lines[i - 1].strip().startswith("import ")
                    or lines[i - 1].strip().startswith("from ")
                    or lines[i - 1].strip() == ""
                    or lines[i - 1].strip().startswith("#")
                )
                and not line.strip().startswith("def ")
                and not line.strip().startswith("class ")
                and not line.strip().startswith("if ")
                and not line.strip().startswith("for ")
                and not line.strip().startswith("while ")
                and not line.strip().startswith("try:")
                and not line.strip().startswith("except")
                and not line.strip().startswith("finally:")
                and not line.strip().startswith("with ")
                and not line.strip().startswith("@")
                and not line.strip().startswith("return")
                and not line.strip().startswith("yield")
                and not line.strip().startswith("raise")
                and not line.strip().startswith("assert")
                and not line.strip().startswith("pass")
                and not line.strip().startswith("break")
                and not line.strip().startswith("continue")
                and not line.strip().startswith("print")
                and not line.strip().startswith("logger")
                and not line.strip().startswith("log")
            ):
                fixed_lines.append(line.lstrip())
            else:
                fixed_lines.append(line)

        content = "\n".join(fixed_lines)

        # 7. Fix malformed syntax
        content = re.sub(r",\s*\)", ")", content)  # Remove trailing commas
        content = re.sub(r"\(\s*\)", "()", content)  # Fix empty parentheses
        content = re.sub(r"\[\s*\]", "[]", content)  # Fix empty brackets
        content = re.sub(r"{\s*}", "{}", content)  # Fix empty braces

        # 8. Fix specific patterns
        # Fix "def function():" followed by nothing
        content = re.sub(r"(def\s+\w+\([^)]*\):\s*\n)(?!\s)", r"\1    pass\n", content)

        # Fix "try:" followed by nothing
        content = re.sub(r"(try:\s*\n)(?!\s)", r"\1    pass\n", content)

        # 9. Ensure file ends with newline
        if content and not content.endswith("\n"):
            content += "\n"

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✅ Fixed syntax issues")
            return True
        else:
            print(f"  ℹ️  No changes needed")
            return False

    except Exception as e:
        print(f"  ❌ Error fixing {file_path}: {e}")
        return False


def main():
    """Fix remaining syntax errors"""
    print("🔧 Final syntax cleanup - fixing remaining 41 syntax errors...")

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
            if fix_specific_syntax_issues(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")

    print(f"\n🎉 Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
