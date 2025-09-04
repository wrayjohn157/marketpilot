"""Centralized credential management for Market7."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from config.unified_config_manager import get_path, get_config, get_all_paths, get_all_configs


logger = logging.getLogger(__name__)


class CredentialType(Enum):
    """Types of credentials supported."""
    THREECOMMAS = "3commas"
    BINANCE = "binance"
    OPENAI = "openai"
    REDIS = "redis"
    CUSTOM = "custom"


@dataclass
class CredentialConfig:
    """Configuration for a credential type."""
    name: str
    required_keys: List[str]
    optional_keys: List[str] = None
    env_prefix: str = ""
    validation_func: Optional[callable] = None


class CredentialManager:
    """Centralized credential management system."""
    
    # Define credential configurations
    CREDENTIAL_CONFIGS = {
        CredentialType.THREECOMMAS: CredentialConfig(
            name="3commas",
            required_keys=["3commas_api_key", "3commas_api_secret", "3commas_bot_id"],
            optional_keys=["3commas_bot_id2", "3commas_email_token"],
            env_prefix="THREECOMMAS_"
        ),
        CredentialType.BINANCE: CredentialConfig(
            name="binance",
            required_keys=["api_key", "api_secret"],
            optional_keys=["testnet", "sandbox"],
            env_prefix="BINANCE_"
        ),
        CredentialType.OPENAI: CredentialConfig(
            name="openai",
            required_keys=["OPENAI_API_KEY"],
            env_prefix="OPENAI_"
        ),
        CredentialType.REDIS: CredentialConfig(
            name="redis",
            required_keys=["host", "port"],
            optional_keys=["password", "db"],
            env_prefix="REDIS_"
        )
    }
    
    def __init__(self, base_path: Path, use_env: bool = True):
        """Initialize credential manager.
        
        Args:
            base_path: Base path for credential files
            use_env: Whether to check environment variables first
        """
        self.base_path = Path(base_path)
        self.use_env = use_env
        self._credential_cache: Dict[str, Dict[str, Any]] = {}
        
        # Ensure credentials directory exists
        self.credentials_dir = self.base_path / "config" / "credentials"
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
    
    def get_credentials(self, cred_type: CredentialType, profile: str = "default") -> Dict[str, Any]:
        """Get credentials for a specific type and profile.
        
        Args:
            cred_type: Type of credentials to retrieve
            profile: Profile name (e.g., 'default', 'test', 'prod')
            
        Returns:
            Dictionary containing credentials
            
        Raises:
            CredentialError: If credentials cannot be loaded or are invalid
        """
        cache_key = f"{cred_type.value}_{profile}"
        
        # Check cache first
        if cache_key in self._credential_cache:
            return self._credential_cache[cache_key]
        
        # Try to load credentials
        credentials = self._load_credentials(cred_type, profile)
        
        # Validate credentials
        self._validate_credentials(cred_type, credentials)
        
        # Cache and return
        self._credential_cache[cache_key] = credentials
        return credentials
    
    def _load_credentials(self, cred_type: CredentialType, profile: str) -> Dict[str, Any]:
        """Load credentials from file or environment.
        
        Args:
            cred_type: Type of credentials
            profile: Profile name
            
        Returns:
            Loaded credentials dictionary
        """
        config = self.CREDENTIAL_CONFIGS[cred_type]
        credentials = {}
        
        # Try environment variables first if enabled
        if self.use_env:
            credentials.update(self._load_from_env(config))
        
        # Try credential files
        file_credentials = self._load_from_file(cred_type, profile)
        credentials.update(file_credentials)
        
        return credentials
    
    def _load_from_env(self, config: CredentialConfig) -> Dict[str, Any]:
        """Load credentials from environment variables.
        
        Args:
            config: Credential configuration
            
        Returns:
            Environment-based credentials
        """
        credentials = {}
        prefix = config.env_prefix
        
        for key in config.required_keys + (config.optional_keys or []):
            env_key = f"{prefix}{key.upper()}"
            value = os.getenv(env_key)
            if value:
                credentials[key] = value
        
        return credentials
    
    def _load_from_file(self, cred_type: CredentialType, profile: str) -> Dict[str, Any]:
        """Load credentials from file.
        
        Args:
            cred_type: Type of credentials
            profile: Profile name
            
        Returns:
            File-based credentials
        """
        # Try profile-specific file first
        profile_file = self.credentials_dir / f"{cred_type.value}_{profile}.json"
        default_file = self.credentials_dir / f"{cred_type.value}.json"
        legacy_file = self.base_path / "config" / "paper_cred.json"
        
        for file_path in [profile_file, default_file, legacy_file]:
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load credentials from {file_path}: {e}")
                    continue
        
        return {}
    
    def _validate_credentials(self, cred_type: CredentialType, credentials: Dict[str, Any]) -> None:
        """Validate that required credentials are present.
        
        Args:
            cred_type: Type of credentials
            credentials: Credentials to validate
            
        Raises:
            CredentialError: If validation fails
        """
        config = self.CREDENTIAL_CONFIGS[cred_type]
        missing_keys = []
        
        # Check required keys
        for key in config.required_keys:
            if key not in credentials or not credentials[key]:
                missing_keys.append(key)
        
        if missing_keys:
            raise CredentialError(
                f"Missing required credentials for {cred_type.value}: {missing_keys}"
            )
        
        # Run custom validation if provided
        if config.validation_func:
            try:
                config.validation_func(credentials)
            except Exception as e:
                raise CredentialError(f"Credential validation failed: {e}")
    
    def save_credentials(self, cred_type: CredentialType, credentials: Dict[str, Any], 
                        profile: str = "default", overwrite: bool = False) -> None:
        """Save credentials to file.
        
        Args:
            cred_type: Type of credentials
            credentials: Credentials to save
            profile: Profile name
            overwrite: Whether to overwrite existing file
        """
        file_path = self.credentials_dir / f"{cred_type.value}_{profile}.json"
        
        if file_path.exists() and not overwrite:
            raise CredentialError(f"Credentials file {file_path} already exists")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(credentials, f, indent=2)
            logger.info(f"Credentials saved to {file_path}")
        except IOError as e:
            raise CredentialError(f"Failed to save credentials: {e}")
    
    def list_credentials(self) -> Dict[str, List[str]]:
        """List available credential files.
        
        Returns:
            Dictionary mapping credential types to available profiles
        """
        credentials = {}
        
        for file_path in self.credentials_dir.glob("*.json"):
            parts = file_path.stem.split("_", 1)
            cred_type = parts[0]
            profile = parts[1] if len(parts) > 1 else "default"
            
            if cred_type not in credentials:
                credentials[cred_type] = []
            credentials[cred_type].append(profile)
        
        return credentials
    
    def clear_cache(self) -> None:
        """Clear credential cache."""
        self._credential_cache.clear()
        logger.debug("Credential cache cleared")


class CredentialError(Exception):
    """Exception raised for credential-related errors."""
    pass


# Global credential manager instance
def get_credential_manager() -> CredentialManager:
    """Get the global credential manager instance."""
        return CredentialManager(get_path("base"))


# Convenience functions for common credential types
def get_3commas_credentials(profile: str = "default") -> Dict[str, Any]:
    """Get 3Commas API credentials.
    
    Args:
        profile: Credential profile name
        
    Returns:
        3Commas credentials dictionary
    """
    manager = get_credential_manager()
    return manager.get_credentials(CredentialType.THREECOMMAS, profile)


def get_binance_credentials(profile: str = "default") -> Dict[str, Any]:
    """Get Binance API credentials.
    
    Args:
        profile: Credential profile name
        
    Returns:
        Binance credentials dictionary
    """
    manager = get_credential_manager()
    return manager.get_credentials(CredentialType.BINANCE, profile)


def get_openai_credentials(profile: str = "default") -> Dict[str, Any]:
    """Get OpenAI API credentials.
    
    Args:
        profile: Credential profile name
        
    Returns:
        OpenAI credentials dictionary
    """
    manager = get_credential_manager()
    return manager.get_credentials(CredentialType.OPENAI, profile)


def get_redis_credentials(profile: str = "default") -> Dict[str, Any]:
    """Get Redis credentials.
    
    Args:
        profile: Credential profile name
        
    Returns:
        Redis credentials dictionary
    """
    manager = get_credential_manager()
    return manager.get_credentials(CredentialType.REDIS, profile)