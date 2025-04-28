from datetime import datetime
from pathlib import Path
import json

from live.utils.entry_utils import save_daily_entry, load_registry, save_registry

# Constants
REGISTRY_PATH = Path("/home/signal/market6/live/logs/fork_registry.json")

def log_fork_entry(entry: dict):
    """Logs a new fork entry and updates the per-date registry with metadata."""
    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    full_symbol = entry.get("symbol", "UNKNOWN")

    # Load registry
    registry = load_registry()

    # Ensure date section exists
    if date_str not in registry or not isinstance(registry[date_str], dict):
        registry[date_str] = {}

    # Avoid duplicate
    if full_symbol in registry[date_str]:
        print(f"⏩ SKIPPED — {full_symbol} already logged for {date_str}")
        return

    # Add metadata and mark the entry as active
    registry[date_str][full_symbol] = {
        "entry_time": entry.get("entry_time"),
        "entry_ts_iso": entry.get("entry_ts_iso"),
        "entry_price": entry.get("entry_price"),
        "score_hash": entry.get("score_hash"),
        "source": entry.get("source"),
        "status": "active",  # Updated from "pending" to "active"
        "indicators": entry.get("indicators", {})
    }

    save_registry(registry)
    save_daily_entry(entry)

    print(f"✅ LOGGED — {full_symbol:<15} @ {entry.get('entry_price')} → fork_registry.json")

# Optional test call
if __name__ == "__main__":
    sample_entry = {
        "symbol": "DOGEUSDT",
        "entry_time": int(datetime.utcnow().timestamp()),
        "entry_ts_iso": datetime.utcnow().isoformat(),
        "entry_price": 0.175,
        "score_hash": "abc123",
        "source": "fork_score_filter",
        "indicators": {
            "macd_hist": 0.002,
            "rsi": 48.3,
            "adx": 22.1
        }
    }

    log_fork_entry(sample_entry)
