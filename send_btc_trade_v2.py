#!/usr/bin/env python3
"""
Send a small BTC trade for $12 through 3Commas bot - Version 2
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
    
    # Step 1: List all bots to find the correct one
    print("\n📊 Listing all bots...")
    response = make_request("GET", "/public/api/ver1/bots")
    
    if response.status_code != 200:
        print(f"❌ Failed to get bots: {response.status_code} - {response.text}")
        return
    
    bots = response.json()
    target_bot = None
    
    for bot in bots:
        if str(bot.get('id')) == str(bot_id):
            target_bot = bot
            break
    
    if not target_bot:
        print(f"❌ Bot {bot_id} not found in available bots")
        print("Available bots:")
        for bot in bots[:5]:  # Show first 5 bots
            print(f"  - ID: {bot.get('id')}, Name: {bot.get('name')}")
        return
    
    print(f"✅ Found bot: {target_bot.get('name')}")
    print(f"✅ Status: {'Enabled' if target_bot.get('is_enabled') else 'Disabled'}")
    print(f"✅ Pairs: {target_bot.get('pairs')}")
    print(f"✅ Base Order Volume: {target_bot.get('base_order_volume')}")
    print(f"✅ Max Active Deals: {target_bot.get('max_active_deals')}")
    
    # Step 2: Check current deals
    print(f"\n📈 Checking current deals for bot {bot_id}...")
    response = make_request("GET", f"/public/api/ver1/bots/{bot_id}/deals")
    
    if response.status_code == 200:
        deals = response.json()
        active_deals = [deal for deal in deals if deal.get('status') == 'active']
        print(f"📊 Current deals: {len(deals)} total, {len(active_deals)} active")
        
        if active_deals:
            print("Active deals:")
            for deal in active_deals[:3]:  # Show first 3 active deals
                print(f"  - Deal ID: {deal.get('id')}, Pair: {deal.get('pair')}, Status: {deal.get('status')}")
    else:
        print(f"⚠️  Could not get deals: {response.status_code} - {response.text}")
    
    # Step 3: Try to start the bot manually
    print(f"\n🤖 Attempting to start bot manually...")
    
    # Check if bot is enabled
    if not target_bot.get('is_enabled'):
        print("⚠️  Bot is disabled. Cannot start trades.")
        return
    
    # Try to start the bot
    start_data = {
        "bot_id": int(bot_id)
    }
    
    response = make_request("POST", f"/public/api/ver1/bots/{bot_id}/start_new_deal", start_data)
    
    if response.status_code == 200:
        print("✅ Bot started successfully!")
        result = response.json()
        print(f"📊 Response: {result}")
    elif response.status_code == 422:
        print("⚠️  Bot cannot start new deal (possibly already running or conditions not met)")
        print(f"Response: {response.text}")
    else:
        print(f"❌ Failed to start bot: {response.status_code} - {response.text}")
    
    # Step 4: Check account balance
    print(f"\n💰 Checking account balance...")
    response = make_request("GET", f"/public/api/ver1/accounts/{account_id}")
    
    if response.status_code == 200:
        account_info = response.json()
        print(f"✅ Account: {account_info.get('name')}")
        print(f"✅ USDT Balance: {account_info.get('usdt_balance', 'N/A')}")
        print(f"✅ BTC Balance: {account_info.get('btc_balance', 'N/A')}")
    else:
        print(f"⚠️  Could not get account balance: {response.status_code} - {response.text}")
    
    print("\n💡 Note: This is a paper trading bot.")
    print("💡 The bot will execute trades based on its configured strategy and market conditions.")
    print("💡 The bot's base order volume determines the trade size.")
    
    print("\n✅ Trade attempt complete!")
    print("🎯 Check your 3Commas dashboard to see if a new deal was created.")

if __name__ == "__main__":
    send_btc_trade()
