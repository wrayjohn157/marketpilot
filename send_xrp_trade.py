#!/usr/bin/env python3

import json
from pathlib import Path

import requests

"""
Send XRP trade using 3Commas TradingView signal format
"""


def send_xrp_trade():
    """Send XRP trade using 3Commas TradingView signal format"""

    # Load credentials
    creds_path = Path("config/credentials/3commas_default.json")
    with open(creds_path) as f:
        creds = json.load(f)

    bot_id = creds["3commas_bot_id"]
    email_token = creds["3commas_email_token"]

    print("🚀 Sending XRP Trade Signal...")
    print(f"Bot ID: {bot_id}")
    print(f"Pair: USDT_XRP")

    # Create the signal payload using the correct format from entry_utils.py
    payload = {
        "action": "add_funds_in_quote",
        "message_type": "bot",
        "bot_id": bot_id,
        "email_token": email_token,
        "delay_seconds": 0,
        "pair": "USDT_XRP",
        "volume": 12,  # $12 trade
    }

    print(f"📋 Signal payload:")
    print(json.dumps(payload, indent=2))

    # Send the signal to 3Commas TradingView endpoint
    url = "https://app.3commas.io/trade_signal/trading_view"

    try:
        print(f"\n📤 Sending signal to: {url}")
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        print(f"✅ Signal sent successfully!")
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response: {response.text}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send signal: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = send_xrp_trade()
    if success:
        print("\n🎉 XRP trade signal sent successfully!")
        print("💡 Check your 3Commas dashboard to see the trade execution")
    else:
        print("\n❌ Failed to send XRP trade signal")
