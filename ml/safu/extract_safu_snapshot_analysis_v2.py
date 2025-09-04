from typing import Dict, List, Optional, Any, Union, Tuple
import json
import os

from glob import glob

# extract_safu_snapshot_analysis_v2.py

from
 tqdm import tqdm

DCA_DIR = "/home/signal/market7/dca/logs"
SNAPSHOT_DIR = "/home/signal/market7/ml/datasets/recovery_snapshots"
OUTPUT = "/home/signal/market7/ml/datasets/safu_analysis/merged_safu_dca.jsonl"

merged_rows = []

# Step 1: Build a lookup of snapshots by deal_id
snapshot_lookup = {}

for path in glob(os.path.join(SNAPSHOT_DIR, "*_*.jsonl")):
    basename = os.path.basename(path)
    try:
        symbol, deal_id = basename.replace(".jsonl", "").split("_")
        snapshot_lookup[deal_id] = path
    except Exception:
        continue

print(f"Found {len(snapshot_lookup)} snapshot files.")

# Step 2: Iterate over DCA logs
dca_days = sorted(glob(os.path.join(DCA_DIR, "2025-*")))

for day_folder in tqdm(dca_days, desc="Processing DCA logs"):
    dca_log = os.path.join(day_folder, "dca_log.jsonl")
    if not os.path.exists(dca_log):
        continue

    with open(dca_log) as f:
        for line in f:
            try:
                dca = json.loads(line)
                deal_id = str(dca.get("deal_id"))
                if deal_id and deal_id in snapshot_lookup:
                    with open(snapshot_lookup[deal_id]) as snap_file:
                        snap_lines = [json.loads(s) for s in snap_file if s.strip()]
                        if snap_lines:
                            entry = {
                                "deal_id": deal_id,
                                "symbol": dca.get("symbol"),
                                "drawdown_pct": dca.get("drawdown_pct"),
                                "open_pnl": dca.get("open_pnl"),
                                "safu_score": dca.get("safu_score"),
                                "entry_score": dca.get("entry_score"),
                                "current_score": dca.get("current_score"),
                                "confidence_score": dca.get("confidence_score"),
                                "snapshot_count": len(snap_lines),
                                "snapshots": snap_lines,
                            }
                            merged_rows.append(entry)
            except Exception:
                continue

print(f"✅ Matched {len(merged_rows)} DCA + snapshot combos")

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w") as out:
    for row in merged_rows:
        out.write(json.dumps(row) + "\n")

print(f"💾 Saved to {OUTPUT}")
