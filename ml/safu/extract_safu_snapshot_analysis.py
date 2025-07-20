import os
import json
import glob
from datetime import datetime
from tqdm import tqdm
from collections import defaultdict

DCA_LOG_BASE = "/home/signal/market7/dca/logs"
SNAPSHOT_BASE = "/home/signal/market7/ml/datasets/recovery_snapshots"
OUTPUT_PATH = "/home/signal/market7/ml/datasets/safu_analysis/merged_safu_dca.jsonl"
SNAPSHOT_TOLERANCE_SEC = 600  # 10 minutes

def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

def load_snapshots_for_date(date_str):
    path = os.path.join(SNAPSHOT_BASE, date_str, "recovery_snapshots.jsonl")
    return load_jsonl(path)

def find_nearest_snapshot(snapshots, target_ts):
    best = None
    best_delta = float("inf")
    for snap in snapshots:
        delta = abs(snap["timestamp"] - target_ts)
        if delta < best_delta and delta <= SNAPSHOT_TOLERANCE_SEC:
            best = snap
            best_delta = delta
    return best

def scan_and_merge():
    merged = []

    date_dirs = sorted([d for d in os.listdir(DCA_LOG_BASE)
                        if d.startswith("2025-") and os.path.isdir(os.path.join(DCA_LOG_BASE, d))])

    for date in tqdm(date_dirs, desc="Processing DCA logs"):
        dca_path = os.path.join(DCA_LOG_BASE, date, "dca_log.jsonl")
        dca_entries = load_jsonl(dca_path)
        if not dca_entries:
            continue

        snapshots = load_snapshots_for_date(date)
        if not snapshots:
            continue

        # Build quick index by deal_id
        snapshots_by_deal = defaultdict(list)
        for snap in snapshots:
            if "deal_id" in snap:
                snapshots_by_deal[str(snap["deal_id"])].append(snap)

        # Sort for faster timestamp search
        for lst in snapshots_by_deal.values():
            lst.sort(key=lambda x: x["timestamp"])

        for dca in dca_entries:
            deal_id = str(dca.get("deal_id"))
            ts = dca.get("timestamp")
            if not deal_id or ts is None:
                continue

            matched_snap = find_nearest_snapshot(snapshots_by_deal.get(deal_id, []), ts)
            out = {
                "deal_id": deal_id,
                "timestamp": ts,
                "symbol": dca.get("symbol"),
                "drawdown_pct": dca.get("drawdown_pct"),
                "safu_score": dca.get("safu_score"),
                "confidence_score": dca.get("confidence_score"),
                "recovery_odds": dca.get("recovery_odds"),
                "zombie_tagged": dca.get("zombie_tagged"),
                "decision": dca.get("decision"),
                "rejection_reason": dca.get("rejection_reason"),
                "volume_sent": dca.get("volume_sent"),
                "tp1_shift": dca.get("tp1_shift"),
            }

            if matched_snap:
                out.update({
                    "snapshot_score_trend": matched_snap.get("snapshot_score_trend"),
                    "snapshot_rsi_trend": matched_snap.get("snapshot_rsi_trend"),
                    "snapshot_min_score": matched_snap.get("snapshot_min_score"),
                    "snapshot_min_rsi": matched_snap.get("snapshot_min_rsi"),
                    "snapshot_max_drawdown": matched_snap.get("snapshot_max_drawdown"),
                    "snapshot_time_to_max_drawdown_min": matched_snap.get("snapshot_time_to_max_drawdown_min"),
                    "snapshot_confidence_score": matched_snap.get("confidence_score"),
                    "snapshot_recovery_odds": matched_snap.get("recovery_odds"),
                })
            else:
                out["snapshot_matched"] = False

            merged.append(out)

    return merged

def save_jsonl(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for row in data:
            f.write(json.dumps(row) + "\n")
    print(f"✅ Saved {len(data)} rows to: {path}")

if __name__ == "__main__":
    results = scan_and_merge()
    save_jsonl(OUTPUT_PATH, results)
