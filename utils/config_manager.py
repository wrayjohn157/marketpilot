from pathlib import Path
from typing import Any, Dict, Optional
import json
import logging

import yaml
from utils.credential_manager import get_3commas_credentials


"""Centralized configuration management for Market7."""

logger = logging.getLogger(__name__)

class ConfigManager:
    """Centralized configuration management."""
    
    def __init__(self, base_path: Path):
        """Initialize configuration manager.
        
        Args:
            base_path: Base path for the project
        """
        self.base_path = Path(base_path)
        self._config_cache: Dict[str, Any] = {}
    
    def get_path(self, key: str) -> Path:
        """Get a configured path.
        
        Args:
            key: Path key
            
        Returns:
            Path object
        """
        paths = {
            "base": self.base_path,
            "config": self.base_path / "config",
            "data": self.base_path / "data",
            "logs": self.base_path / "logs",
            "output": self.base_path / "output",
            "snapshots": self.base_path / "data" / "snapshots",
            "dca_config": self.base_path / "config" / "dca_config.yaml",
            "leverage_config": self.base_path / "config" / "leverage_config.yaml",
            "paper_cred": self.base_path / "config" / "paper_cred.json",
            "btc_logs": self.base_path / "live" / "btc_logs",
            "fork_history": self.base_path / "output" / "fork_history",
        }
        
        if key not in paths:
            logger.warning(f"Unknown path key: {key}")
            return self.base_path
        
        return paths[key]
    
    def load_yaml_config(self, config_path: Path) -> Dict[str, Any]:
        """Load YAML configuration file.
        
        Args:
            config_path: Path to YAML config file
            
        Returns:
            Configuration dictionary
        """
        if str(config_path) in self._config_cache:
            return self._config_cache[str(config_path)]
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self._config_cache[str(config_path)] = config
            return config
        except (yaml.YAMLError, IOError) as e:
            logger.error(f"Failed to load YAML config {config_path}: {e}")
            return {}
    
    def load_json_config(self, config_path: Path) -> Dict[str, Any]:
        """Load JSON configuration file.
        
        Args:
            config_path: Path to JSON config file
            
        Returns:
            Configuration dictionary
        """
        if str(config_path) in self._config_cache:
            return self._config_cache[str(config_path)]
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self._config_cache[str(config_path)] = config
            return config
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load JSON config {config_path}: {e}")
            return {}
    
    def get_credentials(self) -> Dict[str, Any]:
        """Get API credentials.
        
        Returns:
            Credentials dictionary
        """
        cred_path = self.get_path("paper_cred")
        return self.load_json_config(cred_path)
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.get_path("logs"),
            self.get_path("data"),
            self.get_path("output"),
            self.get_path("snapshots"),
            self.get_path("btc_logs"),
            self.get_path("fork_history"),
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

# Global config manager instance
config_manager = ConfigManager(Path(__file__).parent.parent)