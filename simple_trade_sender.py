#!/usr/bin/env python3
"""
Simple trade sender that monitors Redis for trade signals and sends them to 3Commas
"""

import json
import time
import redis
import requests
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class SimpleTradeSender:
    def __init__(self):
        # Load credentials
        creds_path = Path("config/credentials/3commas_default.json")
        with open(creds_path) as f:
            self.creds = json.load(f)
        
        # Redis connection
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # 3Commas settings
        self.bot_id = self.creds["3commas_bot_id"]
        self.email_token = self.creds["3commas_email_token"]
        self.signal_url = "https://app.3commas.io/trade_signal/trading_view"
        
        # Track sent trades
        self.sent_trades_key = "SENT_TRADES"
        
    def should_send_trade(self, symbol, current_price):
        """Check if we should send this trade (avoid duplicates)"""
        last_data = self.redis_client.hget(self.sent_trades_key, symbol)
        if last_data is None:
            return True
        
        try:
            last_price = json.loads(last_data)["entry_price"]
            price_change = abs(current_price - last_price) / last_price
            return price_change >= 0.02  # 2% price change threshold
        except Exception:
            return True
    
    def send_trade_signal(self, symbol, current_price):
        """Send trade signal to 3Commas using correct format"""
        pair = f"USDT_{symbol.replace('USDT', '')}"
        
        payload = {
            "message_type": "bot",
            "bot_id": self.bot_id,
            "email_token": self.email_token,
            "delay_seconds": 0,
            "pair": pair
        }
        
        try:
            response = requests.post(self.signal_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"✅ Sent {pair} signal to 3Commas")
            
            # Track sent trade
            self.redis_client.hset(
                self.sent_trades_key, 
                symbol, 
                json.dumps({"entry_price": current_price, "timestamp": time.time()})
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send {pair} signal: {e}")
            return False
    
    def monitor_trades(self):
        """Monitor Redis for trade signals"""
        logger.info("🔍 Monitoring for trade signals...")
        
        while True:
            try:
                # Check for trade signals in Redis
                # This is a simplified version - in production you'd have more sophisticated signal detection
                
                # Example: Check if there are any new trade opportunities
                # In a real system, this would monitor indicators, ML predictions, etc.
                
                # For now, let's just log that we're monitoring
                logger.info("📊 Monitoring trade signals...")
                
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("🛑 Trade sender stopped")
                break
            except Exception as e:
                logger.error(f"❌ Error in trade monitoring: {e}")
                time.sleep(5)

def main():
    sender = SimpleTradeSender()
    sender.monitor_trades()

if __name__ == "__main__":
    main()
