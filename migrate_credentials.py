#!/usr/bin/env python3
"""Credential migration script for Market7."""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from utils.credential_manager import CredentialManager, CredentialType


def migrate_legacy_credentials(
    legacy_file: Path, cred_type: CredentialType, profile: str = "default"
) -> bool:
    """Migrate credentials from legacy file to new system.

    Args:
        legacy_file: Path to legacy credential file
        cred_type: Type of credentials
        profile: Profile name for new credentials

    Returns:
        True if migration successful, False otherwise
    """
    if not legacy_file.exists():
        print(f"Legacy file {legacy_file} not found")
        return False

    try:
        # Load legacy credentials
        with open(legacy_file, "r") as f:
            legacy_creds = json.load(f)

        # Create credential manager
        manager = CredentialManager(Path("."))

        # Map legacy credentials to new format
        if cred_type == CredentialType.THREECOMMAS:
            new_creds = {
                "3commas_api_key": legacy_creds.get("3commas_api_key"),
                "3commas_api_secret": legacy_creds.get("3commas_api_secret"),
                "3commas_bot_id": legacy_creds.get("3commas_bot_id"),
                "3commas_bot_id2": legacy_creds.get("3commas_bot_id2"),
                "3commas_email_token": legacy_creds.get("3commas_email_token"),
            }
        elif cred_type == CredentialType.BINANCE:
            new_creds = {
                "api_key": legacy_creds.get("api_key"),
                "api_secret": legacy_creds.get("api_secret"),
                "testnet": legacy_creds.get("testnet", False),
                "sandbox": legacy_creds.get("sandbox", False),
            }
        elif cred_type == CredentialType.OPENAI:
            new_creds = {"OPENAI_API_KEY": legacy_creds.get("OPENAI_API_KEY")}
        else:
            print(f"Unsupported credential type: {cred_type}")
            return False

        # Save new credentials
        manager.save_credentials(cred_type, new_creds, profile, overwrite=True)
        print(f"✅ Migrated {cred_type.value} credentials to profile '{profile}'")
        return True

    except Exception as e:
        print(f"❌ Failed to migrate {cred_type.value} credentials: {e}")
        return False


def create_credential_templates() -> None:
    """Create credential template files."""
    templates_dir = Path("config/credentials")
    templates_dir.mkdir(parents=True, exist_ok=True)

    templates = {
        "3commas_default.json.template": {
            "3commas_api_key": "your_3commas_api_key_here",
            "3commas_api_secret": "your_3commas_api_secret_here",
            "3commas_bot_id": "your_3commas_bot_id_here",
            "3commas_bot_id2": "your_second_bot_id_here",
            "3commas_email_token": "your_3commas_email_token_here",
        },
        "binance_default.json.template": {
            "api_key": "your_binance_api_key_here",
            "api_secret": "your_binance_api_secret_here",
            "testnet": True,
            "sandbox": False,
        },
        "openai_default.json.template": {"OPENAI_API_KEY": "your_openai_api_key_here"},
        "redis_default.json.template": {
            "host": "localhost",
            "port": 6379,
            "password": "",
            "db": 0,
        },
    }

    for filename, content in templates.items():
        template_path = templates_dir / filename
        if not template_path.exists():
            with open(template_path, "w") as f:
                json.dump(content, f, indent=2)
            print(f"✅ Created template: {template_path}")


def backup_legacy_credentials() -> None:
    """Backup legacy credential files."""
    backup_dir = Path("config/credentials/backup")
    backup_dir.mkdir(parents=True, exist_ok=True)

    legacy_files = [
        Path("config/paper_cred.json"),
        Path("config/binance_futures_testnet.json"),
    ]

    for legacy_file in legacy_files:
        if legacy_file.exists():
            backup_path = backup_dir / legacy_file.name
            shutil.copy2(legacy_file, backup_path)
            print(f"✅ Backed up: {legacy_file} -> {backup_path}")


def main():
    """Main migration function."""
    print("🔄 Starting Market7 credential migration...")

    # Create templates
    print("\n📝 Creating credential templates...")
    create_credential_templates()

    # Backup legacy files
    print("\n💾 Backing up legacy credentials...")
    backup_legacy_credentials()

    # Try to migrate 3commas credentials
    print("\n🔄 Migrating 3Commas credentials...")
    legacy_3commas = Path("config/paper_cred.json")
    if legacy_3commas.exists():
        migrate_legacy_credentials(legacy_3commas, CredentialType.THREECOMMAS)
    else:
        print("⚠️  No legacy 3Commas credentials found")

    # Try to migrate binance credentials
    print("\n🔄 Migrating Binance credentials...")
    legacy_binance = Path("config/binance_futures_testnet.json")
    if legacy_binance.exists():
        migrate_legacy_credentials(legacy_binance, CredentialType.BINANCE)
    else:
        print("⚠️  No legacy Binance credentials found")

    print("\n✅ Migration complete!")
    print("\n📋 Next steps:")
    print("1. Review the migrated credentials in config/credentials/")
    print("2. Update any hardcoded credential paths in your code")
    print("3. Test the new credential system")
    print("4. Remove legacy credential files when ready")


if __name__ == "__main__":
    main()
