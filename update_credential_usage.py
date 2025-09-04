#!/usr/bin/env python3
"""Script to update all credential usage to use centralized system."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


class CredentialUsageUpdater:
    """Updates credential usage throughout the codebase."""

    def __init__(self, project_root: Path):
        """Initialize updater.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.files_updated = 0
        self.patterns_fixed = 0

    def find_credential_usage(self) -> List[Tuple[Path, List[Dict[str, Any]]]]:
        """Find all files with credential usage patterns.

        Returns:
            List of tuples (file_path, patterns_found)
        """
        credential_patterns = [
            {
                "name": "hardcoded_cred_path",
                "pattern": r'CRED_PATH\s*=\s*Path\(["\'][^"\']*paper_cred\.json["\']\)',
                "replacement": "from utils.credential_manager import get_3commas_credentials",
            },
            {
                "name": "hardcoded_cred_path_string",
                "pattern": r'["\'][^"\']*paper_cred\.json["\']',
                "replacement": "get_3commas_credentials()",
            },
            {
                "name": "cred_loading_pattern",
                "pattern": r"with open\([^)]*paper_cred[^)]*\) as f:\s*\n\s*creds = json\.load\(f\)",
                "replacement": "creds = get_3commas_credentials()",
            },
            {
                "name": "pathes_paper_cred",
                "pattern": r'PATHS\[["\']paper_cred["\']\]',
                "replacement": "get_3commas_credentials()",
            },
            {
                "name": "api_key_extraction",
                "pattern": r'creds\[["\']3commas_api_key["\']\]',
                "replacement": 'creds["3commas_api_key"]',
            },
            {
                "name": "api_secret_extraction",
                "pattern": r'creds\[["\']3commas_api_secret["\']\]',
                "replacement": 'creds["3commas_api_secret"]',
            },
        ]

        results = []

        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            patterns_found = []

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                for pattern_info in credential_patterns:
                    matches = re.finditer(
                        pattern_info["pattern"], content, re.MULTILINE
                    )
                    for match in matches:
                        patterns_found.append(
                            {
                                "pattern": pattern_info["name"],
                                "match": match.group(),
                                "start": match.start(),
                                "end": match.end(),
                                "replacement": pattern_info["replacement"],
                            }
                        )

                if patterns_found:
                    results.append((py_file, patterns_found))

            except Exception as e:
                print(f"Error reading {py_file}: {e}")

        return results

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped.

        Args:
            file_path: Path to check

        Returns:
            True if should be skipped
        """
        skip_patterns = [
            "archive/",
            "__pycache__/",
            ".git/",
            "venv/",
            ".pytest_cache/",
            "migrate_credentials.py",
            "update_credential_usage.py",
            "credential_manager.py",
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def update_file(self, file_path: Path, patterns: List[Dict[str, Any]]) -> bool:
        """Update a file with new credential usage.

        Args:
            file_path: File to update
            patterns: Patterns found in the file

        Returns:
            True if file was updated
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content
            updated = False

            # Add import if needed
            if not self._has_credential_import(content):
                content = self._add_credential_import(content)
                updated = True

            # Apply pattern replacements
            for pattern in reversed(patterns):  # Reverse to maintain positions
                start = pattern["start"]
                end = pattern["end"]
                replacement = pattern["replacement"]

                # Adjust positions if content was modified
                if updated:
                    # Recalculate positions after previous replacements
                    continue

                content = content[:start] + replacement + content[end:]
                updated = True
                self.patterns_fixed += 1

            if updated and content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return True

            return False

        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False

    def _has_credential_import(self, content: str) -> bool:
        """Check if file already has credential import.

        Args:
            content: File content

        Returns:
            True if import exists
        """
        import_patterns = [
            "from utils.credential_manager import",
            "import utils.credential_manager",
            "from credential_manager import",
        ]

        return any(pattern in content for pattern in import_patterns)

    def _add_credential_import(self, content: str) -> str:
        """Add credential import to file.

        Args:
            content: File content

        Returns:
            Updated content
        """
        import_line = "from utils.credential_manager import get_3commas_credentials\n"

        # Find the last import statement
        import_pattern = r"^(import|from)\s+.*$"
        lines = content.split("\n")
        last_import_line = -1

        for i, line in enumerate(lines):
            if re.match(import_pattern, line.strip()):
                last_import_line = i

        if last_import_line >= 0:
            # Insert after last import
            lines.insert(last_import_line + 1, import_line)
        else:
            # Insert at the beginning
            lines.insert(0, import_line)

        return "\n".join(lines)

    def update_all_files(self) -> None:
        """Update all files with credential usage."""
        print("🔍 Finding credential usage patterns...")

        usage_files = self.find_credential_usage()

        print(f"Found {len(usage_files)} files with credential usage")

        for file_path, patterns in usage_files:
            print(f"\n📝 Updating {file_path}")
            print(f"   Found {len(patterns)} patterns:")

            for pattern in patterns:
                print(f"   - {pattern['pattern']}: {pattern['match'][:50]}...")

            if self.update_file(file_path, patterns):
                self.files_updated += 1
                print(f"   ✅ Updated successfully")
            else:
                print(f"   ⚠️  No changes made")

    def generate_report(self) -> None:
        """Generate update report."""
        print(f"\n📊 Update Report:")
        print(f"   Files updated: {self.files_updated}")
        print(f"   Patterns fixed: {self.patterns_fixed}")


def main():
    """Main function."""
    project_root = Path(__file__).parent
    updater = CredentialUsageUpdater(project_root)

    print("🔄 Updating credential usage throughout codebase...")
    updater.update_all_files()
    updater.generate_report()

    print("\n✅ Credential usage update complete!")
    print("\n📋 Next steps:")
    print("1. Review the updated files")
    print("2. Test the new credential system")
    print("3. Run the migration script: python migrate_credentials.py")
    print("4. Update any remaining hardcoded paths manually")


if __name__ == "__main__":
    main()
