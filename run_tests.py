#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from pathlib import Path

"""Test runner script for Market7."""

def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ SUCCESS")
        if result.stdout:
            print("Output:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Run Market7 tests and quality checks")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    parser.add_argument("--lint", action="store_true", help="Run linting only")
    parser.add_argument("--format", action="store_true", help="Run formatting only")
    parser.add_argument(
        "--type-check", action="store_true", help="Run type checking only"
    )
    parser.add_argument("--all", action="store_true", help="Run all checks")
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # If no specific flags, run all
    if not any([args.unit, args.integration, args.lint, args.format, args.type_check]):
        args.all = True

    success = True
    project_root = Path(__file__).parent

    # Change to project root
        os.chdir(project_root)
    # Unit tests
    if args.unit or args.all:
        cmd = ["python", "-m", "pytest", "tests/unit/", "-v"]
        if args.coverage:
            cmd.extend(
                [
                    "--cov=core",
                    "--cov=dca",
                    "--cov=fork",
                    "--cov=lev",
                    "--cov-report=html",
                ]
            )
        if not args.verbose:
            cmd.append("-q")

        if not run_command(cmd, "Unit Tests"):
            success = False

    # Integration tests
    if args.integration or args.all:
        cmd = ["python", "-m", "pytest", "tests/integration/", "-v"]
        if not args.verbose:
            cmd.append("-q")

        if not run_command(cmd, "Integration Tests"):
            success = False

    # Linting
    if args.lint or args.all:
        if not run_command(
            ["python", "-m", "flake8", "core", "dca", "fork", "lev", "utils"],
            "Flake8 Linting",
        ):
            success = False

    # Formatting check
    if args.format or args.all:
        if not run_command(
            ["python", "-m", "black", "--check", "core", "dca", "fork", "lev", "utils"],
            "Black Formatting Check",
        ):
            success = False

        if not run_command(
            [
                "python",
                "-m",
                "isort",
                "--check-only",
                "core",
                "dca",
                "fork",
                "lev",
                "utils",
            ],
            "Import Sorting Check",
        ):
            success = False

    # Type checking
    if args.type_check or args.all:
        if not run_command(
            ["python", "-m", "mypy", "core", "dca", "fork", "lev", "utils"],
            "MyPy Type Checking",
        ):
            success = False

    # Summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 ALL CHECKS PASSED!")
    else:
        print("❌ SOME CHECKS FAILED!")
        sys.exit(1)
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
