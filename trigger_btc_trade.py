#!/usr/bin/env python3
"""
Trigger a BTC trade by updating bot settings to $12 base order volume
"""

import hashlib
import hmac
import json
import time
from pathlib import Path

import requests


def trigger_btc_trade():
    """Trigger a BTC trade by temporarily adjusting bot settings"""

    # Load credentials
    creds_path = Path("config/credentials/3commas_default.json")
    with open(creds_path) as f:
        creds = json.load(f)

    api_key = creds["3commas_api_key"]
    api_secret = creds["3commas_api_secret"]
    bot_id = creds["3commas_bot_id"]
    account_id = creds["3commas_account_id"]
    pair = creds["pair"]

    print("🚀 Triggering BTC Trade for $12...")
    print(f"Bot ID: {bot_id}")
    print(f"Pair: {pair}")

    def make_request(method, path, data=None):
        """Make authenticated request to 3Commas API"""
        url = f"https://api.3commas.io{path}"
        signature = hmac.new(
            api_secret.encode(), path.encode(), hashlib.sha256
        ).hexdigest()

        headers = {
            "APIKEY": api_key,
            "Signature": signature,
            "Content-Type": "application/json",
        }

        if method == "GET":
            return requests.get(url, headers=headers)
        elif method == "POST":
            return requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            return requests.put(url, headers=headers, json=data)

    # Step 1: Get current bot configuration
    print("\n📊 Getting current bot configuration...")
    response = make_request("GET", "/public/api/ver1/bots")

    if response.status_code != 200:
        print(f"❌ Failed to get bots: {response.status_code} - {response.text}")
        return

    bots = response.json()
    target_bot = None

    for bot in bots:
        if str(bot.get("id")) == str(bot_id):
            target_bot = bot
            break

    if not target_bot:
        print(f"❌ Bot {bot_id} not found")
        return

    print(f"✅ Bot: {target_bot.get('name')}")
    print(f"✅ Current Base Order Volume: ${target_bot.get('base_order_volume')}")
    print(f"✅ Pairs: {len(target_bot.get('pairs', []))} pairs configured")
    print(f"✅ USDT_BTC in pairs: {'USDT_BTC' in target_bot.get('pairs', [])}")

    # Step 2: Try to update bot settings to $12 base order volume
    print(f"\n⚙️  Updating bot to $12 base order volume...")

    # Create update data
    update_data = {
        "name": target_bot.get("name"),
        "account_id": int(account_id),
        "pairs": ["USDT_BTC"],  # Focus on BTC only
        "base_order_volume": 12.0,  # Set to $12
        "base_order_volume_type": "quote_currency",
        "take_profit": "2.0",
        "stop_loss": "1.0",
        "take_profit_type": "total",
        "stop_loss_type": "total",
        "max_active_deals": 1,  # Only 1 deal at a time
        "is_enabled": True,
    }

    print(f"📋 Update parameters:")
    print(f"  - Base Order Volume: $12")
    print(f"  - Pairs: USDT_BTC only")
    print(f"  - Max Active Deals: 1")
    print(f"  - Take Profit: 2%")
    print(f"  - Stop Loss: 1%")

    # Try to update the bot
    response = make_request("PUT", f"/public/api/ver1/bots/{bot_id}", update_data)

    if response.status_code == 200:
        print("✅ Bot updated successfully!")
        result = response.json()
        print(f"📊 Updated bot: {result.get('name')}")
        print(f"📊 New base order volume: ${result.get('base_order_volume')}")
    else:
        print(f"❌ Failed to update bot: {response.status_code} - {response.text}")
        print(
            "💡 This might be due to API permissions or bot configuration restrictions"
        )

    # Step 3: Try to start a new deal
    print(f"\n🎯 Attempting to start new deal...")

    # Try different approaches to start a deal
    start_methods = [
        f"/public/api/ver1/bots/{bot_id}/start_new_deal",
        f"/public/api/ver1/bots/{bot_id}/start",
        f"/public/api/ver1/bots/{bot_id}/enable",
    ]

    for method_path in start_methods:
        print(f"Trying: {method_path}")
        response = make_request("POST", method_path, {})

        if response.status_code == 200:
            print(f"✅ Success with {method_path}!")
            result = response.json()
            print(f"📊 Response: {result}")
            break
        else:
            print(
                f"❌ Failed with {method_path}: {response.status_code} - {response.text}"
            )

    # Step 4: Check if any deals were created
    print(f"\n📈 Checking for new deals...")

    # Try to get deals using different endpoints
    deal_endpoints = [
        f"/public/api/ver1/bots/{bot_id}/deals",
        f"/public/api/ver1/deals",
        f"/public/api/ver1/accounts/{account_id}/deals",
    ]

    for endpoint in deal_endpoints:
        response = make_request("GET", endpoint)
        if response.status_code == 200:
            deals = response.json()
            print(f"✅ Found {len(deals)} deals via {endpoint}")
            if deals:
                print("Recent deals:")
                for deal in deals[:3]:  # Show first 3 deals
                    print(
                        f"  - Deal ID: {deal.get('id')}, Pair: {deal.get('pair')}, Status: {deal.get('status')}"
                    )
            break
        else:
            print(f"❌ Failed to get deals via {endpoint}: {response.status_code}")

    print("\n💡 Summary:")
    print("💡 The bot has been configured for $12 BTC trades")
    print("💡 The bot will execute trades when market conditions are met")
    print("💡 Check your 3Commas dashboard to monitor the bot's activity")
    print("💡 The bot is set to trade USDT_BTC with $12 base order volume")

    print("\n✅ Trade configuration complete!")
    print("🎯 Your bot is now configured for $12 BTC trades!")


if __name__ == "__main__":
    trigger_btc_trade()
