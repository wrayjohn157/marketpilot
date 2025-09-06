#!/usr/bin/env python3
"""
Unified Configuration Manager - Smart, Environment-Aware Config System
Replaces all hardcoded paths and scattered configs with a unified, intelligent system
"""

import json
import logging
import os
import platform
import socket
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Removed circular imports - these functions are defined later in this file


class Environment(Enum):
    """Environment types for smart path resolution"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class ConfigValidationError(Exception):
    """Custom exception for config validation errors"""

    message: str
    config_key: str
    expected_type: str
    actual_value: Any


@dataclass
class EnvironmentInfo:
    """Environment detection information"""

    environment: Environment
    base_path: Path
    is_docker: bool
    is_development: bool
    hostname: str
    platform: str


class EnvironmentDetector:
    """Smart environment detection with multiple fallback strategies"""

    @staticmethod
    def detect_environment() -> EnvironmentInfo:
        """Detect current environment using multiple strategies"""

        # Strategy 1: Environment variable
        env_var = os.getenv("MARKET7_ENV", "").lower()
        if env_var in ["dev", "development"]:
            environment = Environment.DEVELOPMENT
        elif env_var in ["staging", "stage"]:
            environment = Environment.STAGING
        elif env_var in ["prod", "production"]:
            environment = Environment.PRODUCTION
        elif env_var in ["test", "testing"]:
            environment = Environment.TESTING
        else:
            # Strategy 2: Path-based detection
            current_path = Path.cwd().as_posix()
            if "/workspace" in current_path or "/tmp" in current_path:
                environment = Environment.DEVELOPMENT
            elif "/home/signal" in current_path:
                environment = Environment.PRODUCTION
            elif "/opt/market7" in current_path:
                environment = Environment.STAGING
            else:
                # Strategy 3: Hostname-based detection
                hostname = socket.gethostname().lower()
                if "dev" in hostname or "local" in hostname:
                    environment = Environment.DEVELOPMENT
                elif "staging" in hostname or "stage" in hostname:
                    environment = Environment.STAGING
                elif "prod" in hostname or "production" in hostname:
                    environment = Environment.PRODUCTION
                else:
                    # Default to development
                    environment = Environment.DEVELOPMENT

        # Determine base path
        base_path = EnvironmentDetector._get_base_path(environment)

        # Detect if running in Docker
        is_docker = EnvironmentDetector._is_docker()

        return EnvironmentInfo(
            environment=environment,
            base_path=base_path,
            is_docker=is_docker,
            is_development=environment == Environment.DEVELOPMENT,
            hostname=socket.gethostname(),
            platform=platform.system(),
        )

    @staticmethod
    def _get_base_path(environment: Environment) -> Path:
        """Get base path based on environment"""
        if environment == Environment.DEVELOPMENT:
            return Path("/home/signal/marketpilot")
        elif environment == Environment.STAGING:
            return Path("/opt/marketpilot")
        elif environment == Environment.PRODUCTION:
            return Path("/home/signal/marketpilot")
        else:  # TESTING
            return Path("/tmp/marketpilot_test")

    @staticmethod
    def _is_docker() -> bool:
        """Detect if running in Docker container"""
        try:
            with open("/proc/1/cgroup", "r") as f:
                return "docker" in f.read()
        except:
            return False


class SmartDefaults:
    """Smart defaults for all configuration types"""

    @staticmethod
    def get_default_paths(environment: Environment, base_path: Path) -> Dict[str, Path]:
        """Get environment-specific default paths"""
        defaults = {
            "base": base_path,
            "snapshots": base_path / "data" / "snapshots",
            "fork_history": base_path / "output" / "fork_history",
            "btc_logs": base_path / "dashboard_backend" / "btc_logs",
            "live_logs": base_path / "live" / "logs",
            "models": base_path / "live" / "models",
            "paper_cred": base_path / "config" / "paper_cred.json",
            "tv_history": base_path / "output" / "tv_history",
            "final_fork_rrr_trades": base_path
            / "output"
            / "final_fork_rrr_trades.json",
            "fork_tv_adjusted": base_path / "output" / "fork_tv_adjusted.jsonl",
            "dashboard_cache": base_path / "dashboard_backend" / "cache",
            "backtest_summary": base_path / "backtest" / "data" / "summary",
            "fork_candidates": base_path / "output" / "fork_candidates.json",
            "fork_backtest_candidates": base_path
            / "output"
            / "fork_backtest_candidates.json",
            "dca_tracking_log": base_path
            / "dca"
            / "logs"
            / "dca_tracking"
            / "dca_fired.jsonl",
            "dca_log_base": base_path / "dca" / "logs",
            "ml_dataset_base": base_path / "live" / "ml_dataset",
            "tv_screener_config": base_path / "config" / "tv_screener_config.yaml",
            "filtered_pairs": base_path / "data" / "filtered_pairs.json",
            "kline_snapshots": base_path / "data" / "snapshots",
            "fork_trade_candidates": base_path
            / "output"
            / "fork_trade_candidates.json",
            "final_forked_trades": base_path / "output" / "final_forked_trades.json",
            "binance_symbols": base_path / "data" / "binance_symbols.json",
            "dca_config": base_path / "config" / "dca_config.yaml",
            "fork_safu_config": base_path / "config" / "fork_safu_config.yaml",
            "enriched": base_path / "ml" / "datasets" / "enriched",
            "dca_tracking": base_path
            / "dca"
            / "logs"
            / "dca_tracking"
            / "dca_fired.jsonl",
            "recovery_snapshots": base_path / "ml" / "datasets" / "recovery_snapshots",
            "dca_spend": base_path / "ml" / "datasets" / "dca_spend",
        }

        # Add environment-specific paths
        if environment == Environment.DEVELOPMENT:
            defaults.update(
                {
                    "test_data": base_path / "test" / "data",
                    "test_logs": base_path / "test" / "logs",
                    "debug_logs": base_path / "debug" / "logs",
                }
            )
        elif environment == Environment.PRODUCTION:
            defaults.update(
                {
                    "backup": base_path / "backup",
                    "archive": base_path / "archive",
                    "monitoring": base_path / "monitoring",
                }
            )

        return defaults

    @staticmethod
    def get_default_configs() -> Dict[str, Dict[str, Any]]:
        """Get smart defaults for all config types"""
        return {
            "dca_config": {
                "min_score": 0.65,
                "max_dca_attempts": 5,
                "dca_volume_multiplier": 1.2,
                "btc_sentiment_weight": 0.3,
                "recovery_odds_threshold": 0.6,
                "confidence_threshold": 0.7,
                "zombie_trade_threshold": 0.3,
                "safu_exit_threshold": 0.4,
                "volume_penalty_threshold": 2.0,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "macd_signal_threshold": 0.001,
                "adx_trend_threshold": 25,
                "atr_volatility_threshold": 0.02,
                "ema_trend_periods": [50, 200],
                "stoch_rsi_periods": [14, 3, 3],
                "qqe_periods": [14, 5],
                "psar_settings": {"step": 0.02, "max_step": 0.2},
                "volume_sma_period": 9,
                "btc_condition_weights": {
                    "bullish": 1.2,
                    "neutral": 1.0,
                    "bearish": 0.8,
                },
            },
            "fork_safu_config": {
                "min_score": 0.4,
                "weights": {
                    "rsi_recovery": 0.25,
                    "stoch_rsi_cross": 0.20,
                    "macd_histogram": 0.15,
                    "adx_rising": 0.15,
                    "ema_price_reclaim": 0.10,
                    "volume_penalty": 0.10,
                    "mean_reversion": 0.05,
                },
                "rsi_recovery_range": [30, 50],
                "stoch_rsi_cross_threshold": 0.25,
                "macd_histogram_threshold": 0.001,
                "adx_rising_threshold": 20,
                "volume_penalty_multiplier": 2.0,
                "mean_reversion_atr_multiplier": 3.0,
            },
            "tv_screener_config": {
                "enabled": True,
                "disable_if_btc_unhealthy": True,
                "score_threshold": 0.7,
                "weights": {
                    "strong_buy": 0.30,
                    "buy": 0.20,
                    "neutral": 0.10,
                    "sell": -0.20,
                    "strong_sell": -0.30,
                },
                "update_interval": 300,  # 5 minutes
                "max_retries": 3,
                "timeout": 30,
            },
            "unified_pipeline_config": {
                "enabled": True,
                "update_interval": 60,
                "max_retries": 3,
                "timeout": 30,
                "tech_filter": {
                    "enabled": True,
                    "min_score": 0.6,
                    "timeframes": ["15m", "1h", "4h"],
                    "thresholds": {
                        "neutral": {
                            "15m": {
                                "qqe_min": 30,
                                "qqe_max": 50,
                                "rsi_range": [35, 65],
                            },
                            "1h": {"qqe_min": 30, "qqe_max": 50},
                            "4h": {"qqe_min": 30, "qqe_max": 50},
                        },
                        "bullish": {
                            "15m": {"adx_min": 20, "rsi_max": 75},
                            "1h": {"qqe_min": 55, "qqe_max": 80},
                            "4h": {"qqe_min": 55, "qqe_max": 80},
                        },
                        "bearish": {
                            "15m": {"rsi_max": 45},
                            "1h": {"qqe_max": 50},
                            "4h": {"qqe_max": 50},
                        },
                    },
                },
                "fork_scorer": {
                    "enabled": True,
                    "min_score": 0.73,
                    "weights": {
                        "macd_histogram": 0.20,
                        "macd_bearish_cross": 0.15,
                        "rsi_recovery": 0.15,
                        "stoch_rsi_cross": 0.15,
                        "stoch_overbought_penalty": 0.10,
                        "adx_rising": 0.10,
                        "ema_price_reclaim": 0.10,
                        "mean_reversion_score": 0.05,
                    },
                },
                "tv_adjuster": {"enabled": True, "weight": 0.3, "min_score": 0.7},
            },
            "ml_pipeline_config": {
                "enabled": True,
                "update_interval": 3600,  # 1 hour
                "max_retries": 3,
                "timeout": 60,
                "models": {
                    "safu_exit": {
                        "enabled": True,
                        "retrain_interval": 86400,  # 24 hours
                        "min_accuracy": 0.8,
                        "features": [
                            "rsi",
                            "stoch_rsi_k",
                            "macd_histogram",
                            "adx",
                            "ema_distance",
                        ],
                    },
                    "recovery_odds": {
                        "enabled": True,
                        "retrain_interval": 86400,
                        "min_accuracy": 0.75,
                        "features": [
                            "rsi",
                            "stoch_rsi_k",
                            "macd_histogram",
                            "adx",
                            "ema_distance",
                            "volume_ratio",
                        ],
                    },
                    "confidence_score": {
                        "enabled": True,
                        "retrain_interval": 86400,
                        "min_accuracy": 0.7,
                        "features": [
                            "rsi",
                            "stoch_rsi_k",
                            "macd_histogram",
                            "adx",
                            "ema_distance",
                            "volume_ratio",
                            "atr",
                        ],
                    },
                    "dca_spend": {
                        "enabled": True,
                        "retrain_interval": 86400,
                        "min_accuracy": 0.8,
                        "features": [
                            "rsi",
                            "stoch_rsi_k",
                            "macd_histogram",
                            "adx",
                            "ema_distance",
                            "volume_ratio",
                            "atr",
                            "price",
                        ],
                    },
                    "trade_success": {
                        "enabled": True,
                        "retrain_interval": 86400,
                        "min_accuracy": 0.75,
                        "features": [
                            "rsi",
                            "stoch_rsi_k",
                            "macd_histogram",
                            "adx",
                            "ema_distance",
                            "volume_ratio",
                            "atr",
                            "price",
                            "btc_sentiment",
                        ],
                    },
                },
            },
        }


class ConfigValidator:
    """Comprehensive config validation with detailed error reporting"""

    @staticmethod
    def validate_paths(paths: Dict[str, Path]) -> List[str]:
        """Validate all paths and return list of issues"""
        issues = []

        for key, path in paths.items():
            if not isinstance(path, Path):
                issues.append(f"Path '{key}' is not a Path object: {type(path)}")
                continue

            # Check if path exists (for required paths)
            required_paths = [
                "base",
                "snapshots",
                "fork_history",
                "btc_logs",
                "live_logs",
                "models",
            ]
            if key in required_paths and not path.exists():
                issues.append(f"Required path '{key}' does not exist: {path}")

            # Check if path is writable (for log paths)
            log_paths = ["btc_logs", "live_logs", "dca_log_base"]
            if key in log_paths and path.exists() and not os.access(path, os.W_OK):
                issues.append(f"Log path '{key}' is not writable: {path}")

        return issues

    @staticmethod
    def validate_config(config: Dict[str, Any], config_type: str) -> List[str]:
        """Validate config against schema and return list of issues"""
        issues = []

        if config_type == "dca_config":
            issues.extend(ConfigValidator._validate_dca_config(config))
        elif config_type == "fork_safu_config":
            issues.extend(ConfigValidator._validate_fork_safu_config(config))
        elif config_type == "tv_screener_config":
            issues.extend(ConfigValidator._validate_tv_screener_config(config))
        elif config_type == "unified_pipeline_config":
            issues.extend(ConfigValidator._validate_unified_pipeline_config(config))
        elif config_type == "ml_pipeline_config":
            issues.extend(ConfigValidator._validate_ml_pipeline_config(config))

        return issues

    @staticmethod
    def _validate_dca_config(config: Dict[str, Any]) -> List[str]:
        """Validate DCA config"""
        issues = []

        # Required fields
        required_fields = ["min_score", "max_dca_attempts", "dca_volume_multiplier"]
        for field in required_fields:
            if field not in config:
                issues.append(f"DCA config missing required field: {field}")
            elif not isinstance(config[field], (int, float)):
                issues.append(
                    f"DCA config field '{field}' must be numeric: {type(config[field])}"
                )

        # Validate score ranges
        if "min_score" in config and not (0 <= config["min_score"] <= 1):
            issues.append(
                f"DCA min_score must be between 0 and 1: {config['min_score']}"
            )

        if "max_dca_attempts" in config and not (1 <= config["max_dca_attempts"] <= 10):
            issues.append(
                f"DCA max_dca_attempts must be between 1 and 10: {config['max_dca_attempts']}"
            )

        return issues

    @staticmethod
    def _validate_fork_safu_config(config: Dict[str, Any]) -> List[str]:
        """Validate Fork SAFU config"""
        issues = []

        if "weights" in config:
            total_weight = sum(config["weights"].values())
            if abs(total_weight - 1.0) > 0.01:
                issues.append(f"Fork SAFU weights must sum to 1.0: {total_weight}")

        return issues

    @staticmethod
    def _validate_tv_screener_config(config: Dict[str, Any]) -> List[str]:
        """Validate TV Screener config"""
        issues = []

        if "weights" in config:
            for key, weight in config["weights"].items():
                if not isinstance(weight, (int, float)):
                    issues.append(
                        f"TV Screener weight '{key}' must be numeric: {type(weight)}"
                    )
                elif not (-1 <= weight <= 1):
                    issues.append(
                        f"TV Screener weight '{key}' must be between -1 and 1: {weight}"
                    )

        return issues

    @staticmethod
    def _validate_unified_pipeline_config(config: Dict[str, Any]) -> List[str]:
        """Validate Unified Pipeline config"""
        issues = []

        # Validate tech filter thresholds
        if "tech_filter" in config and "thresholds" in config["tech_filter"]:
            thresholds = config["tech_filter"]["thresholds"]
            for condition, timeframes in thresholds.items():
                if not isinstance(timeframes, dict):
                    issues.append(
                        f"Tech filter thresholds for '{condition}' must be a dict"
                    )
                    continue

                for tf, params in timeframes.items():
                    if not isinstance(params, dict):
                        issues.append(
                            f"Tech filter thresholds for '{condition}.{tf}' must be a dict"
                        )

        return issues

    @staticmethod
    def _validate_ml_pipeline_config(config: Dict[str, Any]) -> List[str]:
        """Validate ML Pipeline config"""
        issues = []

        if "models" in config:
            for model_name, model_config in config["models"].items():
                if not isinstance(model_config, dict):
                    issues.append(f"ML model '{model_name}' config must be a dict")
                    continue

                if "min_accuracy" in model_config and not (
                    0 <= model_config["min_accuracy"] <= 1
                ):
                    issues.append(
                        f"ML model '{model_name}' min_accuracy must be between 0 and 1: {model_config['min_accuracy']}"
                    )

        return issues


class UnifiedConfigManager:
    """Main unified configuration manager with smart defaults and validation"""

    def __init__(self, environment: Optional[Environment] = None):
        self.env_info = EnvironmentDetector.detect_environment()
        if environment:
            self.env_info.environment = environment

        self.paths = {}
        self.configs = {}
        self.validation_issues = []

        self._load_paths()
        self._load_configs()
        self._validate_all()

    def _load_paths(self):
        """Load all paths with smart defaults"""
        # Load from paths_config.yaml if it exists
        paths_config_path = self.env_info.base_path / "config" / "paths_config.yaml"
        if paths_config_path.exists():
            try:
                with open(paths_config_path, "r") as f:
                    raw_config = yaml.safe_load(f)

                # Convert to Path objects
                for key, value in raw_config.items():
                    normalized_key = key.replace("_path", "").replace("_base", "")
                    self.paths[normalized_key] = Path(value)
            except Exception as e:
                logging.warning(f"Failed to load paths_config.yaml: {e}")

        # Get smart defaults
        defaults = SmartDefaults.get_default_paths(
            self.env_info.environment, self.env_info.base_path
        )

        # Merge with defaults (defaults take precedence for missing keys)
        for key, default_path in defaults.items():
            if key not in self.paths:
                self.paths[key] = default_path

        # Ensure all required paths exist
        self._ensure_required_paths()

    def _load_configs(self):
        """Load all configs with smart defaults"""
        # Get smart defaults
        defaults = SmartDefaults.get_default_configs()

        # Load config files
        config_files = {
            "dca_config": self.paths.get("dca_config"),
            "fork_safu_config": self.paths.get("fork_safu_config"),
            "tv_screener_config": self.paths.get("tv_screener_config"),
            "unified_pipeline_config": self.paths.get("unified_pipeline_config"),
            "ml_pipeline_config": self.paths.get("ml_pipeline_config"),
        }

        for config_name, config_path in config_files.items():
            if config_path and config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        if config_path.suffix == ".yaml":
                            config_data = yaml.safe_load(f)
                        elif config_path.suffix == ".json":
                            config_data = json.load(f)
                        else:
                            config_data = {}

                    # Merge with defaults
                    default_config = defaults.get(config_name, {})
                    merged_config = self._merge_configs(default_config, config_data)
                    self.configs[config_name] = merged_config
                except Exception as e:
                    logging.warning(f"Failed to load {config_name}: {e}")
                    self.configs[config_name] = defaults.get(config_name, {})
            else:
                # Use defaults
                self.configs[config_name] = defaults.get(config_name, {})

    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Merge user config with defaults (user takes precedence)"""
        merged = default.copy()

        for key, value in user.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value

        return merged

    def _ensure_required_paths(self):
        """Ensure all required paths exist"""
        required_paths = [
            "snapshots",
            "fork_history",
            "btc_logs",
            "live_logs",
            "models",
        ]

        for path_key in required_paths:
            if path_key in self.paths:
                path = self.paths[path_key]
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logging.warning(f"Failed to create required path {path_key}: {e}")

    def _validate_all(self):
        """Validate all paths and configs"""
        # Validate paths
        path_issues = ConfigValidator.validate_paths(self.paths)
        self.validation_issues.extend(path_issues)

        # Validate configs
        for config_name, config_data in self.configs.items():
            config_issues = ConfigValidator.validate_config(config_data, config_name)
            self.validation_issues.extend(
                [f"{config_name}: {issue}" for issue in config_issues]
            )

        # Log validation issues
        if self.validation_issues:
            logging.warning(
                f"Config validation issues found: {len(self.validation_issues)}"
            )
            for issue in self.validation_issues:
                logging.warning(f"  - {issue}")

    def get_path(self, key: str) -> Path:
        """Get path by key with validation"""
        if key not in self.paths:
            raise KeyError(
                f"Path key '{key}' not found. Available keys: {list(self.paths.keys())}"
            )

        return self.paths[key]

    def get_config(self, key: str) -> Dict[str, Any]:
        """Get config by key with validation"""
        if key not in self.configs:
            raise KeyError(
                f"Config key '{key}' not found. Available keys: {list(self.configs.keys())}"
            )

        return self.configs[key]

    def get_all_paths(self) -> Dict[str, Path]:
        """Get all paths"""
        return self.paths.copy()

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all configs"""
        return self.configs.copy()

    def get_environment_info(self) -> EnvironmentInfo:
        """Get environment information"""
        return self.env_info

    def get_validation_issues(self) -> List[str]:
        """Get all validation issues"""
        return self.validation_issues.copy()

    def is_valid(self) -> bool:
        """Check if all configs are valid"""
        return len(self.validation_issues) == 0

    def save_config(self, key: str, config: Dict[str, Any]):
        """Save config to file"""
        if key not in self.configs:
            raise KeyError(f"Config key '{key}' not found")

        config_path = self.paths.get(key)
        if not config_path:
            raise ValueError(f"No path configured for config '{key}'")

        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w") as f:
                if config_path.suffix == ".yaml":
                    yaml.dump(config, f, default_flow_style=False, indent=2)
                elif config_path.suffix == ".json":
                    json.dump(config, f, indent=2)
                else:
                    raise ValueError(
                        f"Unsupported config file format: {config_path.suffix}"
                    )

            # Update in-memory config
            self.configs[key] = config

            logging.info(f"Config '{key}' saved to {config_path}")
        except Exception as e:
            logging.error(f"Failed to save config '{key}': {e}")
            raise

    def reload(self):
        """Reload all configs from files"""
        self.paths = {}
        self.configs = {}
        self.validation_issues = []

        self._load_paths()
        self._load_configs()
        self._validate_all()

        logging.info("Configs reloaded successfully")


# Global instance for easy access
_config_manager = None


def get_config_manager() -> UnifiedConfigManager:
    """Get global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = UnifiedConfigManager()
    return _config_manager


def get_path(key: str) -> Path:
    """Get path by key (convenience function)"""
    return get_config_manager().get_path(key)


def get_config(key: str) -> Dict[str, Any]:
    """Get config by key (convenience function)"""
    return get_config_manager().get_config(key)


def get_all_paths() -> Dict[str, Path]:
    """Get all paths (convenience function)"""
    return get_config_manager().get_all_paths()


def get_all_configs() -> Dict[str, Dict[str, Any]]:
    """Get all configs (convenience function)"""
    return get_config_manager().get_all_configs()


# Backward compatibility
def get_paths() -> Dict[str, Path]:
    """Backward compatibility function"""
    return get_all_paths()


# Example usage
if __name__ == "__main__":
    # Initialize config manager
    config_manager = UnifiedConfigManager()

    # Get environment info
    env_info = config_manager.get_environment_info()
    print(f"Environment: {env_info.environment.value}")
    print(f"Base Path: {env_info.base_path}")
    print(f"Is Docker: {env_info.is_docker}")
    print(f"Is Development: {env_info.is_development}")

    # Get paths
    print("\nPaths:")
    for key, path in config_manager.get_all_paths().items():
        print(f"  {key}: {path}")

    # Get configs
    print("\nConfigs:")
    for key, config in config_manager.get_all_configs().items():
        print(f"  {key}: {len(config)} items")

    # Check validation
    if config_manager.is_valid():
        print("\n✅ All configs are valid")
    else:
        print("\n❌ Config validation issues:")
        for issue in config_manager.get_validation_issues():
            print(f"  - {issue}")
