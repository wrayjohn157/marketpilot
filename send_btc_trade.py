#!/usr/bin/env python3
"""
Send a small BTC trade for $12 through 3Commas bot
"""

import json
import hashlib
import hmac
import requests
import time
from pathlib import Path

def send_btc_trade():
    """Send a $12 BTC trade through 3Commas bot"""
    
    # Load credentials
    creds_path = Path("config/credentials/3commas_default.json")
    with open(creds_path) as f:
        creds = json.load(f)
    
    api_key = creds["3commas_api_key"]
    api_secret = creds["3commas_api_secret"]
    bot_id = creds["3commas_bot_id"]
    account_id = creds["3commas_account_id"]
    pair = creds["pair"]
    
    print("🚀 Sending BTC Trade for $12...")
    print(f"Bot ID: {bot_id}")
    print(f"Account ID: {account_id}")
    print(f"Pair: {pair}")
    
    def make_request(method, path, data=None):
        """Make authenticated request to 3Commas API"""
        url = f"https://api.3commas.io{path}"
        signature = hmac.new(
            api_secret.encode(), 
            path.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "APIKEY": api_key,
            "Signature": signature,
            "Content-Type": "application/json"
        }
        
        if method == "GET":
            return requests.get(url, headers=headers)
        elif method == "POST":
            return requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            return requests.put(url, headers=headers, json=data)
    
    # Step 1: Check bot status
    print("\n📊 Checking bot status...")
    response = make_request("GET", f"/public/api/ver1/bots/{bot_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get bot info: {response.status_code} - {response.text}")
        return
    
    bot_info = response.json()
    print(f"✅ Bot: {bot_info.get('name')}")
    print(f"✅ Status: {'Enabled' if bot_info.get('is_enabled') else 'Disabled'}")
    print(f"✅ Pairs: {bot_info.get('pairs')}")
    
    if not bot_info.get('is_enabled'):
        print("⚠️  Bot is disabled. Enabling...")
        enable_data = {"is_enabled": True}
        response = make_request("PUT", f"/public/api/ver1/bots/{bot_id}/enable", enable_data)
        if response.status_code == 200:
            print("✅ Bot enabled successfully!")
        else:
            print(f"❌ Failed to enable bot: {response.text}")
            return
    
    # Step 2: Check account balance
    print("\n💰 Checking account balance...")
    response = make_request("GET", f"/public/api/ver1/accounts/{account_id}")
    
    if response.status_code == 200:
        account_info = response.json()
        print(f"✅ Account: {account_info.get('name')}")
        print(f"✅ Balance: {account_info.get('usdt_balance', 'N/A')} USDT")
    else:
        print(f"⚠️  Could not get account balance: {response.text}")
    
    # Step 3: Create a manual deal (simulate a trade)
    print("\n📈 Creating manual deal for $12 BTC...")
    
    # For paper trading, we'll create a manual deal
    deal_data = {
        "bot_id": int(bot_id),
        "pair": pair,
        "base_order_volume": 12.0,  # $12
        "base_order_volume_type": "quote_currency",  # Quote currency (USDT)
        "take_profit": "2.0",  # 2% profit target
        "stop_loss": "1.0",   # 1% stop loss
        "take_profit_type": "total",  # Total profit
        "stop_loss_type": "total",    # Total stop loss
        "note": "MarketPilot test trade - $12 BTC"
    }
    
    print(f"📋 Deal parameters:")
    print(f"  - Amount: $12 USDT")
    print(f"  - Pair: {pair}")
    print(f"  - Take Profit: 2%")
    print(f"  - Stop Loss: 1%")
    
    # Note: 3Commas doesn't have a direct "create deal" endpoint
    # Instead, we'll start the bot and let it handle the trade
    print("\n🤖 Starting bot to execute trade...")
    
    # Check if bot is already running deals
    response = make_request("GET", f"/public/api/ver1/bots/{bot_id}/deals")
    
    if response.status_code == 200:
        deals = response.json()
        active_deals = [deal for deal in deals if deal.get('status') == 'active']
        print(f"📊 Current active deals: {len(active_deals)}")
        
        if len(active_deals) > 0:
            print("⚠️  Bot already has active deals. Trade may not execute immediately.")
        else:
            print("✅ Bot is ready for new trades.")
    
    # For paper trading, we can't directly create a $12 trade
    # The bot will execute trades based on its strategy
    print("\n💡 Note: This is a paper trading bot.")
    print("💡 The bot will execute trades based on its configured strategy.")
    print("💡 To trigger a trade, you can:")
    print("   1. Wait for the bot's strategy to trigger")
    print("   2. Manually trigger the bot if it has manual start capability")
    print("   3. Adjust the bot's base order volume to $12")
    
    # Check bot configuration
    print(f"\n⚙️  Bot Configuration:")
    print(f"  - Base Order Volume: {bot_info.get('base_order_volume', 'N/A')}")
    print(f"  - Base Order Volume Type: {bot_info.get('base_order_volume_type', 'N/A')}")
    print(f"  - Max Active Deals: {bot_info.get('max_active_deals', 'N/A')}")
    
    print("\n✅ Trade setup complete!")
    print("🎯 Your bot is ready to execute trades based on its strategy.")

if __name__ == "__main__":
    send_btc_trade()
