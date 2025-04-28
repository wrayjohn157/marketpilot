#!/usr/bin/env python3
import json
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

# === Updated Dynamic Paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ~/market7
FORK_SCORES_BASE = PROJECT_ROOT / "output/fork_history/scrubbed"
PAPER_TRADE_BASE = PROJECT_ROOT / "live/paper_trades/scrubbed"
BTC_SNAPSHOT_BASE = PROJECT_ROOT / "live/btc_logs"
OUTPUT_DIR = PROJECT_ROOT / "live/enriched"

# ---- Helper Functions ----

def parse_iso(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def time_diff_seconds(dt1: datetime, dt2: datetime) -> float:
    return abs((dt1 - dt2).total_seconds())

def load_jsonl(file_path: Path) -> list:
    records = []
    if not file_path.exists():
        return records
    with open(file_path, "r") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception as e:
                print(f"[WARN] Skipping a line in {file_path} due to error: {e}")
    return records

def find_nearest_snapshot(snapshots: list, target_dt: datetime, max_diff: int) -> dict:
    best = None
    best_diff = float('inf')
    for snap in snapshots:
        if "ts_iso" not in snap:
            continue
        try:
            snap_dt = parse_iso(snap["ts_iso"])
        except Exception:
            continue
        diff = time_diff_seconds(target_dt, snap_dt)
        if diff < best_diff and diff <= max_diff:
            best_diff = diff
            best = snap
    return best

def find_fork_for_trade(fork_scores: list, trade: dict, grace: int) -> dict:
    trade_symbol = trade.get("symbol", "").strip().upper()
    try:
        trade_entry_dt = parse_iso(trade["entry_time"])
    except Exception as e:
        print(f"[ERROR] Unable to parse trade entry_time: {e}")
        return None
    best = None
    best_diff = float('inf')
    for fork in fork_scores:
        if fork.get("symbol", "").strip().upper() != trade_symbol:
            continue
        try:
            fork_dt = parse_iso(fork["timestamp"])
        except Exception:
            continue
        diff = time_diff_seconds(trade_entry_dt, fork_dt)
        if diff < best_diff and diff <= grace:
            best_diff = diff
            best = fork
    return best

# ---- Main Enrichment Functionality ----

def main():
    parser = argparse.ArgumentParser(
        description="Enrich paper trades by merging with scrubbed fork scores and BTC snapshots."
    )
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format. Defaults to yesterday (UTC).")
    args = parser.parse_args()

    if args.date:
        date_str = args.date
    else:
        date_str = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    fork_file = FORK_SCORES_BASE / date_str / "scrubbed_fork_scores.jsonl"
    paper_trade_file = PAPER_TRADE_BASE / date_str / "scrubbed_trades.jsonl"
    btc_file = BTC_SNAPSHOT_BASE / date_str / "btc_snapshots.jsonl"

    if not paper_trade_file.exists():
        print(f"[ERROR] Paper trade file not found: {paper_trade_file}")
        return
    if not fork_file.exists():
        print(f"[ERROR] Fork scores file not found: {fork_file}")
        return
    if not btc_file.exists():
        print(f"[ERROR] BTC snapshots file not found: {btc_file}")
        return

    paper_trades = load_jsonl(paper_trade_file)
    fork_scores = load_jsonl(fork_file)
    btc_snapshots = load_jsonl(btc_file)

    fork_grace = 1800   # 30 min
    btc_grace = 3600    # 1 hr

    enriched_records = []
    for trade in paper_trades:
        merged = trade.copy()
        merged["deal_id"] = trade.get("trade_id")

        fork_match = find_fork_for_trade(fork_scores, trade, fork_grace)
        merged["fork_score"] = fork_match

        try:
            entry_dt = parse_iso(trade["entry_time"])
            exit_dt = parse_iso(trade["exit_time"])
        except Exception as e:
            print(f"[WARN] Skipping trade due to timestamp parsing error: {e}")
            continue

        btc_entry = find_nearest_snapshot(btc_snapshots, entry_dt, btc_grace)
        btc_exit = find_nearest_snapshot(btc_snapshots, exit_dt, btc_grace)
        merged["btc_entry"] = btc_entry
        merged["btc_exit"] = btc_exit

        duration_sec = time_diff_seconds(exit_dt, entry_dt)
        merged["duration_minutes"] = round(duration_sec / 60, 2)

        enriched_records.append(merged)

    out_folder = OUTPUT_DIR / date_str
    out_folder.mkdir(parents=True, exist_ok=True)
    output_file = out_folder / "enriched_data.jsonl"

    with open(output_file, "w") as f_out:
        for rec in enriched_records:
            f_out.write(json.dumps(rec) + "\n")

    print(f"[DONE] Enriched {len(enriched_records)} records into: {output_file}")

if __name__ == "__main__":
    main()
