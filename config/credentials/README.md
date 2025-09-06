# Credentials Setup

## Required Files

Create these files in this directory with your actual credentials:

### `3commas_credentials.json`
```json
{
  "api_key": "your_3commas_api_key",
  "api_secret": "your_3commas_api_secret",
  "3commas_bot_id": "your_bot_id"
}
```

### `binance_credentials.json`
```json
{
  "api_key": "your_binance_api_key",
  "api_secret": "your_binance_api_secret"
}
```

## Security Note
- These files are in `.gitignore` and will NOT be committed
- Keep your credentials secure
- Never share these files

## After Adding Credentials
Restart the backend service:
```bash
sudo systemctl restart marketpilot-backend
```
