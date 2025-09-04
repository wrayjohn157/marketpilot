from typing import Dict, List, Optional, Any, Union, Tuple
import json

#!/usr/bin/env python3

 requests

BOT_ID = 16017224
EMAIL_TOKEN = "aa5bba08-4875-41bc-91a0-5e0bb66c72b0"
PAIR = "USDT_BTC"
URL = "https://app.3commas.io/trade_signal/trading_view"

payload = {
"message_type": "bot",
"bot_id": BOT_ID,
"email_token": EMAIL_TOKEN,
"delay_seconds": 0,
"pair": PAIR
}

print(f"[INFO] Sending TV-style test trade for {PAIR}...")

response = requests.post(URL, json=payload)

print(f"[DEBUG] HTTP {response.status_code}")
print(f"[DEBUG] Raw response: {response.text}")

if response.status_code == 200:
print("[OK] Trade signal accepted.")
elif response.status_code == 204:
print("[WARNING] No response content. Check if deal was created on the bot.")
else:
print("[ERROR] Error sending signal.")
