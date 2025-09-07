#!/usr/bin/env python3
"""
Environment configuration for MarketPilot
Overrides the config system to use the correct paths
"""

import os
import sys
from pathlib import Path

# Set environment variables before any config imports
os.environ["MARKET7_ENV"] = "production"
os.environ["MARKET7_BASE_PATH"] = str(Path(__file__).parent)


# Monkey patch the config manager to use our paths
def patch_config_manager():
    """Patch the config manager to use correct paths"""
    import config.unified_config_manager as config_module

    # Override the _get_base_path method
    def patched_get_base_path(environment):
        """Always return the current directory as base path"""
        return Path(__file__).parent

    config_module.EnvironmentInfo._get_base_path = staticmethod(patched_get_base_path)

    # Override the environment detection
    def patched_detect_environment():
        """Force production environment"""
        from config.unified_config_manager import Environment

        return Environment.PRODUCTION

    config_module.EnvironmentInfo.detect_environment = staticmethod(
        patched_detect_environment
    )


# Apply the patch
patch_config_manager()

print(f"✅ Config environment patched. Base path: {Path(__file__).parent}")
