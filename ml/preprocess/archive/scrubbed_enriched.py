#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

# === Paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAPER_TRADE_BASE = PROJECT_ROOT / "ml/datasets/scrubbed_paper"
FORK_HISTORY_BASE = PROJECT_ROOT / "output/fork_history"
TV_HISTORY_BASE = PROJECT_ROOT / "output/tv_history"
BTC_SNAPSHOT_BASE = PROJECT_ROOT / "dashboard_backend/btc_logs"
OUTPUT_DIR = PROJECT_ROOT / "ml/datasets/enriched"


# === Helpers ===
def parse_iso(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def time_diff_seconds(dt1: datetime, dt2: datetime) -> float:
    return abs((dt1 - dt2).total_seconds())


def load_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    with open(path, "r") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]


def find_nearest_snapshot(snapshots: list, target_dt: datetime, max_diff: int) -> dict:
    best = None
    best_diff = float("inf")
    for snap in snapshots:
        try:
            snap_dt = datetime.fromisoformat(snap["ts_iso"].replace("Z", "+00:00"))
            diff = time_diff_seconds(target_dt, snap_dt)
            if diff < best_diff and diff <= max_diff:
                best = snap
                best_diff = diff
        except:
            continue
    return best


def find_fork_score(symbol: str, entry_dt: datetime, grace: int = 3600) -> dict:
    date_str = entry_dt.strftime("%Y-%m-%d")
    path = FORK_HISTORY_BASE / date_str / "fork_scores.jsonl"
    records = load_jsonl(path)
    best = None
    best_diff = float("inf")
    for rec in records:
        if rec.get("symbol", "").upper() != symbol.upper():
            continue
        try:
            fork_ts = int(rec["timestamp"]) / 1000
            fork_dt = datetime.fromtimestamp(fork_ts, tz=timezone.utc)
            diff = time_diff_seconds(entry_dt, fork_dt)
            if diff < best_diff and diff <= grace:
                best = rec
                best_diff = diff
        except:
            continue
    return best


def find_tv_score(symbol: str, entry_dt: datetime, grace: int = 3600) -> dict:
    date_str = entry_dt.strftime("%Y-%m-%d")
    path = TV_HISTORY_BASE / date_str / "tv_kicker.jsonl"
    records = load_jsonl(path)
    best = None
    best_diff = float("inf")
    for rec in records:
        if not rec.get("pass"):
            continue
        if rec.get("symbol", "").upper() != symbol.upper():
            continue
        try:
            fork_ts = int(rec["timestamp"]) / 1000
            fork_dt = datetime.fromtimestamp(fork_ts, tz=timezone.utc)
            diff = time_diff_seconds(entry_dt, fork_dt)
            if diff < best_diff and diff <= grace:
                best = rec
                best_diff = diff
        except:
            continue
    return best


# === Main ===
def main():
    parser = argparse.ArgumentParser(
        description="Enrich trades with fork, TV, and BTC context."
    )
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD (UTC)")
    args = parser.parse_args()
    date_str = args.date or (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    paper_trade_file = PAPER_TRADE_BASE / date_str / "scrubbed_trades.jsonl"
    btc_file = BTC_SNAPSHOT_BASE / date_str / "btc_snapshots.jsonl"
    out_folder = OUTPUT_DIR / date_str
    out_file = out_folder / "enriched_data.jsonl"
    out_folder.mkdir(parents=True, exist_ok=True)

    if not paper_trade_file.exists():
        print(f"[ERROR] Missing paper trade file: {paper_trade_file}")
        return
    if not btc_file.exists():
        print(f"[ERROR] Missing BTC snapshots: {btc_file}")
        return

    paper_trades = load_jsonl(paper_trade_file)
    btc_snapshots = load_jsonl(btc_file)

    fork_grace = 3600
    btc_grace = 3600
    enriched_records = []

    for trade in paper_trades:
        merged = trade.copy()
        merged["deal_id"] = trade.get("trade_id")
        symbol = trade.get("symbol")
        try:
            entry_dt = parse_iso(trade["entry_time"])
            exit_dt = parse_iso(trade["exit_time"])
        except Exception as e:
            print(f"[WARN] Skipping trade due to timestamp error: {e}")
            continue

        fork = find_fork_score(symbol, entry_dt, fork_grace)
        if not fork:
            fork = find_tv_score(symbol, entry_dt, fork_grace)
            if fork:
                fork["tv_screener_kick_applied"] = True
        merged["fork_score"] = fork
        merged["btc_entry"] = find_nearest_snapshot(btc_snapshots, entry_dt, btc_grace)
        merged["btc_exit"] = find_nearest_snapshot(btc_snapshots, exit_dt, btc_grace)
        merged["duration_minutes"] = round(time_diff_seconds(exit_dt, entry_dt) / 60, 2)

        enriched_records.append(merged)

    with open(out_file, "w") as f:
        for rec in enriched_records:
            f.write(json.dumps(rec) + "\n")

    print(f"[DONE] Enriched {len(enriched_records)} records into: {out_file}")


if __name__ == "__main__":
    main()
