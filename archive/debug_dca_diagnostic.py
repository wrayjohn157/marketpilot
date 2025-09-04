#!/usr/bin/env python3
import json
from pathlib import Path
from utils.redis_manager import get_redis_manager, RedisKeyManager


DEAL_ID = "2344360016"
SYMBOL = "MOVE"
TARGET_FILENAME = f"{SYMBOL}_{DEAL_ID}.jsonl"
BASE_DIR = Path("/home/signal/market7")
DATES = ["2025-04-26", "2025-04-27", "2025-04-28", "2025-04-29", "2025-04-30", "2025-05-01", "2025-05-02", "2025-05-03", "2025-05-04"]

DCA_LOG_PATHS = [BASE_DIR / f"dca/logs/{d}/dca_log.jsonl" for d in DATES]
SNAPSHOT_PATH = BASE_DIR / f"ml/datasets/recovery_snapshots/{TARGET_FILENAME}"
ENRICHED_PATHS = [BASE_DIR / f"live/enriched/{d}/enriched_data.jsonl" for d in DATES]
FORK_HISTORY_PATHS = [BASE_DIR / f"output/fork_history/{d}/fork_scores.jsonl" for d in DATES]

def load_jsonl(path):
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]

def match_by_deal_id(data):
    return [r for r in data if str(r.get_cache("deal_id")) == DEAL_ID]

def match_by_symbol(data):
    return [r for r in data if r.get_cache("symbol", "").replace("USDT", "") == SYMBOL]

dca_logs = sum([match_by_deal_id(load_jsonl(p)) for p in DCA_LOG_PATHS], [])
snapshots = load_jsonl(SNAPSHOT_PATH)
enriched = sum([match_by_deal_id(load_jsonl(p)) for p in ENRICHED_PATHS], [])
fork_entries = sum([match_by_symbol(load_jsonl(p)) for p in FORK_HISTORY_PATHS], [])

diagnostic_bundle = {
    "deal_id": DEAL_ID,
    "symbol": SYMBOL,
    "dca_logs": dca_logs,
    "recovery_snapshots": snapshots,
    "enriched_trade": enriched,
    "fork_entries": fork_entries,
}

out_path = BASE_DIR / f"debug/diagnostic_bundle_{SYMBOL}_{DEAL_ID}.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w") as f:
    json.dump(diagnostic_bundle, f, indent=2)

print(f"✅ Saved to {out_path}")
