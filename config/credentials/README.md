# Market7 Credential Management

This directory contains centralized credential management for the Market7 trading system.

## Overview

The credential system provides:
- **Centralized Management**: Single source of truth for all credentials
- **Profile Support**: Multiple credential profiles (default, test, prod)
- **Environment Variables**: Support for environment-based credentials
- **Validation**: Automatic credential validation
- **Security**: Secure credential storage and access

## File Structure

```
config/credentials/
├── README.md                           # This file
├── 3commas_default.json.template       # 3Commas API template
├── binance_default.json.template       # Binance API template
├── openai_default.json.template        # OpenAI API template
├── redis_default.json.template         # Redis configuration template
├── backup/                             # Legacy credential backups
└── profiles/                           # Profile-specific credentials
    ├── test/
    ├── prod/
    └── staging/
```

## Supported Credential Types

### 1. 3Commas API
- **Required**: `3commas_api_key`, `3commas_api_secret`, `3commas_bot_id`
- **Optional**: `3commas_bot_id2`, `3commas_email_token`
- **Environment**: `THREECOMMAS_API_KEY`, `THREECOMMAS_API_SECRET`, etc.

### 2. Binance API
- **Required**: `api_key`, `api_secret`
- **Optional**: `testnet`, `sandbox`
- **Environment**: `BINANCE_API_KEY`, `BINANCE_API_SECRET`

### 3. OpenAI API
- **Required**: `OPENAI_API_KEY`
- **Environment**: `OPENAI_API_KEY`

### 4. Redis
- **Required**: `host`, `port`
- **Optional**: `password`, `db`
- **Environment**: `REDIS_HOST`, `REDIS_PORT`, etc.

## Usage

### Basic Usage

```python
from utils.credential_manager import get_3commas_credentials

# Get default credentials
creds = get_3commas_credentials()

# Get specific profile
creds = get_3commas_credentials("prod")
```

### Advanced Usage

```python
from utils.credential_manager import CredentialManager, CredentialType

# Create manager instance
manager = CredentialManager(Path("."))

# Get credentials
creds = manager.get_credentials(CredentialType.THREECOMMAS, "prod")

# Save credentials
manager.save_credentials(CredentialType.BINANCE, {
    "api_key": "your_key",
    "api_secret": "your_secret"
}, "test")
```

### Environment Variables

Set environment variables for automatic credential loading:

```bash
export THREECOMMAS_API_KEY="your_api_key"
export THREECOMMAS_API_SECRET="your_api_secret"
export THREECOMMAS_BOT_ID="your_bot_id"
```

## Migration from Legacy System

### 1. Run Migration Script

```bash
python migrate_credentials.py
```

This will:
- Create credential templates
- Backup legacy files
- Migrate existing credentials
- Set up new structure

### 2. Update Code

Replace hardcoded credential usage:

```python
# Old way
with open("config/paper_cred.json", "r") as f:
    creds = json.load(f)
api_key = creds["3commas_api_key"]

# New way
from utils.credential_manager import get_3commas_credentials
creds = get_3commas_credentials()
api_key = creds["3commas_api_key"]
```

### 3. Update All Files

```bash
python update_credential_usage.py
```

This will automatically update most credential usage patterns.

## Security Best Practices

### 1. File Permissions
```bash
chmod 600 config/credentials/*.json
chmod 700 config/credentials/
```

### 2. Environment Variables
- Use environment variables in production
- Never commit credential files to version control
- Use `.env` files for local development

### 3. Credential Rotation
- Regularly rotate API keys
- Use different profiles for different environments
- Monitor credential usage

## Configuration

### Credential Profiles

Create profile-specific credentials:

```bash
# Create test profile
cp 3commas_default.json.template 3commas_test.json
# Edit 3commas_test.json with test credentials

# Create production profile
cp 3commas_default.json.template 3commas_prod.json
# Edit 3commas_prod.json with production credentials
```

### Environment Configuration

Set up environment-specific configuration:

```bash
# Development
export MARKET7_PROFILE="test"

# Production
export MARKET7_PROFILE="prod"
```

## Troubleshooting

### Common Issues

1. **Missing Credentials**
   ```
   CredentialError: Missing required credentials for 3commas: ['3commas_api_key']
   ```
   - Check if credential file exists
   - Verify required keys are present
   - Check file permissions

2. **Invalid Credentials**
   ```
   CredentialError: Credential validation failed: Invalid API key
   ```
   - Verify API keys are correct
   - Check if keys are active
   - Test credentials manually

3. **File Not Found**
   ```
   FileNotFoundError: [Errno 2] No such file or directory
   ```
   - Run migration script
   - Check file paths
   - Verify directory structure

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Reference

### CredentialManager

Main credential management class.

#### Methods

- `get_credentials(cred_type, profile)`: Get credentials
- `save_credentials(cred_type, credentials, profile)`: Save credentials
- `list_credentials()`: List available credentials
- `clear_cache()`: Clear credential cache

### Convenience Functions

- `get_3commas_credentials(profile)`: Get 3Commas credentials
- `get_binance_credentials(profile)`: Get Binance credentials
- `get_openai_credentials(profile)`: Get OpenAI credentials
- `get_redis_credentials(profile)`: Get Redis credentials

## Examples

### Complete Example

```python
from utils.credential_manager import get_3commas_credentials
import requests
import hmac
import hashlib

def make_3commas_request(path):
    creds = get_3commas_credentials()
    
    signature = hmac.new(
        creds["3commas_api_secret"].encode(),
        path.encode(),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Apikey": creds["3commas_api_key"],
        "Signature": signature
    }
    
    response = requests.get(f"https://api.3commas.io{path}", headers=headers)
    return response.json()

# Usage
trades = make_3commas_request("/public/api/ver1/deals")
```

This system provides a robust, secure, and maintainable way to manage credentials across the entire Market7 trading system.