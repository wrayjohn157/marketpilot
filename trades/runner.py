#!/usr/bin/env python3
import subprocess
import time
import os

# Set the absolute base directory for Market7
BASE_DIR = "/home/signal/market7"

def run_step(description, script_path):
    print(f"\n🟢 Running: {description}")
    if not os.path.exists(script_path):
        print(f"⚠️ Skipping {description}: {script_path} not found.")
        return
    try:
        subprocess.run(["python3", script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {description}: {e}")

def main():
    print("🚀 Starting Market7 pipeline...")

    run_step("BTC Market Condition", os.path.join(BASE_DIR, "indicators", "btc_market_condition.py"))
    run_step("Volume Filter", os.path.join(BASE_DIR, "data", "volume_filter.py"))
    
    # Commented out for now - rebuild needed
    run_step("Technical Filter", os.path.join(BASE_DIR, "indicators", "tech_filter.py"))
    run_step("RRR Filter", os.path.join(BASE_DIR, "indicators", "rrr_filter.py"))
    
    time.sleep(1)
    run_step("Trade Dispatcher", os.path.join(BASE_DIR, "trades", "send_trades_3commas.py"))

    print("\n✅ Pipeline complete.")

if __name__ == "__main__":
    main()
