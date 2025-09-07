from .unified_config_manager import UnifiedConfigManager

"""
MarketPilot Configuration Module

Unified configuration management for all system components.
"""

# Create singleton instance
config_manager = UnifiedConfigManager()

# Export key functions for backward compatibility
get_config = config_manager.get_config
get_path = config_manager.get_path
get_all_configs = config_manager.get_all_configs
get_all_paths = config_manager.get_all_paths

__all__ = [
    "UnifiedConfigManager",
    "config_manager",
    "get_config",
    "get_path",
    "get_all_configs",
    "get_all_paths",
]
