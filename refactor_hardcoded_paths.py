#!/usr/bin/env python3

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

"""
Script to systematically fix hardcoded paths in MarketPilot codebase.

This script will:
1. Find all hardcoded get_path("base") /  paths
2. Replace them with proper config-based paths
3. Remove sys.path manipulation hacks
4. Add proper imports
"""

# Project root
PROJECT_ROOT = Path(__file__).parent

# Common hardcoded path patterns to fix
HARDCODED_PATTERNS = {
    r'get_path("base") / ': 'get_path("base") / ',
    r'get_path("base") / ': 'get_path("base") / ',
    r'Path\(get_path("base") / "([^"]+)"\)': r'get_path("base") / "\1"',
    r'Path\(get_path("base") / "([^"]+)"\)': r'get_path("base") / "\1"',
}

# sys.path patterns to remove
SYSPATH_PATTERNS = [
    r"sys\.path\.append\([^)]+\)\s*#.*",
    r"sys\.path\.insert\([^)]+\)\s*#.*",
]


def find_files_with_hardcoded_paths() -> List[Path]:
    """Find all Python files with hardcoded paths."""
    files_with_issues = []

    for py_file in PROJECT_ROOT.rglob("*.py"):
        # Skip backup directories
        if "deployment_backups" in str(py_file):
            continue
        if "venv" in str(py_file):
            continue
        if "__pycache__" in str(py_file):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")

            # Check for hardcoded paths
            if "/home/signal/market" in content:
                files_with_issues.append(py_file)
                continue

            # Check for sys.path manipulation
            if "sys.path." in content and "append" in content:
                files_with_issues.append(py_file)

        except Exception as e:
            print(f"⚠️  Error reading {py_file}: {e}")

    return files_with_issues


def fix_file_paths(file_path: Path, dry_run: bool = True) -> Tuple[bool, List[str]]:
    """Fix hardcoded paths in a single file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content
        changes = []

        # Fix hardcoded paths
        for pattern, replacement in HARDCODED_PATTERNS.items():
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                matches = re.findall(pattern, content)
                changes.append(f"Fixed hardcoded paths: {matches}")
                content = new_content

        # Remove sys.path manipulation
        for pattern in SYSPATH_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, "", content)
                changes.append(f"Removed sys.path manipulation: {matches}")

        # Add proper imports if config is used
        if "get_path(" in content and "from config" not in content:
            # Add import at the top after existing imports
            lines = content.split("\n")
            import_index = 0

            # Find where to insert the import
            for i, line in enumerate(lines):
                if line.strip().startswith("import ") or line.strip().startswith(
                    "from "
                ):
                    import_index = i + 1
                elif line.strip() and not line.strip().startswith("#"):
                    break

            # Insert the import
            lines.insert(import_index, "from config import get_path")
            content = "\n".join(lines)
            changes.append("Added config import")

        # Write changes if not dry run
        if content != original_content:
            if not dry_run:
                file_path.write_text(content, encoding="utf-8")
            return True, changes
        else:
            return False, []

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False, [f"Error: {e}"]


def main():
    """Main refactoring function."""
    print("🔍 MarketPilot Hardcoded Path Refactor")
    print("=" * 50)

    # Find files with issues
    print("Finding files with hardcoded paths...")
    problem_files = find_files_with_hardcoded_paths()

    if not problem_files:
        print("✅ No hardcoded paths found!")
        return

    print(f"📁 Found {len(problem_files)} files with hardcoded paths:")
    for file_path in problem_files[:10]:  # Show first 10
        rel_path = file_path.relative_to(PROJECT_ROOT)
        print(f"   • {rel_path}")

    if len(problem_files) > 10:
        print(f"   ... and {len(problem_files) - 10} more")

    # Ask for confirmation
    print("\n🚀 Ready to fix these files?")
    print("1. Dry run (show changes)")
    print("2. Apply fixes")
    print("3. Cancel")

    choice = input("Choose (1/2/3): ").strip()

    if choice == "3":
        print("❌ Cancelled")
        return

    dry_run = choice == "1"
    mode = "DRY RUN" if dry_run else "APPLYING FIXES"

    print(f"\n🔧 {mode}")
    print("-" * 30)

    fixed_count = 0
    for file_path in problem_files:
        rel_path = file_path.relative_to(PROJECT_ROOT)
        changed, changes = fix_file_paths(file_path, dry_run)

        if changed:
            fixed_count += 1
            print(f"\n📝 {rel_path}")
            for change in changes:
                print(f"   ✓ {change}")

    print(f"\n📊 Summary:")
    print(f"   • Files processed: {len(problem_files)}")
    print(f"   • Files changed: {fixed_count}")

    if dry_run and fixed_count > 0:
        print(f"\n💡 Run again with option 2 to apply these changes")


if __name__ == "__main__":
    main()
