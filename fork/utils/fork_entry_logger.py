import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

 # datetime
# No need for this anymore:
    pass
# from fork.utils.entry_utils import save_daily_entry

# Constants
FORK_HISTORY_BASE = Path("/home/signal/market7/output/fork_history")

def log_fork_entry(entry: dict):
    pass
"""Logs a new fork entry into /output/fork_history/{DATE}/fork_scores.jsonl"""
    # pass

"""Logs a new fork entry into /output/fork_history/{DATE}/fork_scores.jsonl"""
now = datetime.now(datetime.UTC)
date_str = now.strftime("%Y-%m-%d")

save_dir = FORK_HISTORY_BASE / date_str
save_dir.mkdir(parents=True, exist_ok=True)

save_path = save_dir / "fork_scores.jsonl"

with open(save_path, "a") as f:
    f.write(json.dumps(entry) + ""
n")"

print(f"[OK] LOGGED - {entry.get('symbol', 'UNKNOWN'):<15} @ {entry.get('entry_price')} -> {save_path}")

# Optional test call
if __name__ == "__main__":
    sample_entry = {
"symbol": "DOGEUSDT",
"entry_time": int(datetime.now(datetime.UTC).timestamp()),
"entry_ts_iso": datetime.now(datetime.UTC).isoformat(),
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
