#!/usr/bin/env python3
"""
Dependency Installer - Install missing packages for refactored systems
"""

import os
import subprocess
import sys


def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False


def main():
    """Install all required dependencies"""
    print("🚀 Installing dependencies for refactored systems...")

    # Core dependencies
    packages = [
        "redis",  # For Redis Manager
        "pandas",  # For ML pipeline
        "scikit-learn",  # For ML models
        "xgboost",  # For ML models
        "ta",  # For technical indicators
        "influxdb-client",  # For time-series data (optional)
        "psycopg2-binary",  # For PostgreSQL (optional)
    ]

    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1

    print(f"\n📊 Installation Summary:")
    print(f"✅ Successfully installed: {success_count}/{len(packages)} packages")

    if success_count == len(packages):
        print("🎉 All dependencies installed successfully!")
    else:
        print("⚠️  Some packages failed to install. Check the errors above.")

    print("\n📋 Next Steps:")
    print("1. Test the refactored systems")
    print("2. Run the main workflows")
    print("3. Verify all integrations are working")


if __name__ == "__main__":
    main()
