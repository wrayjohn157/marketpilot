#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

# === Path Config ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAPER_TRADE_BASE = PROJECT_ROOT / "ml/datasets/scrubbed_paper"
FORK_SCORES_BASE = PROJECT_ROOT / "ml/datasets/fork_pulls"
FORK_HISTORY_BASE = PROJECT_ROOT / "output/fork_history"
TV_KICKER_BASE = PROJECT_ROOT / "output/tv_history"
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
        if "ts_iso" not in snap:
            continue
        try:
            snap_dt = datetime.fromisoformat(snap["ts_iso"].replace("Z", "+00:00"))
        except Exception:
            continue
        diff = time_diff_seconds(target_dt, snap_dt)
        if diff < best_diff and diff <= max_diff:
            best = snap
            best_diff = diff
    return best


def find_fork_score(symbol: str, entry_dt: datetime, fork_grace=3600) -> dict:
    date_str = entry_dt.strftime("%Y-%m-%d")
    fork_file = FORK_SCORES_BASE / date_str / "scrubbed_fork_scores.jsonl"
    scores = load_jsonl(fork_file)

    best = None
    best_diff = float("inf")
    for record in scores:
        if record.get("symbol", "").upper() != symbol.upper():
            continue
        try:
            fork_ts = int(record["timestamp"]) / 1000
            fork_dt = datetime.fromtimestamp(fork_ts, tz=timezone.utc)
        except:
            continue
        diff = time_diff_seconds(entry_dt, fork_dt)
        if diff < best_diff and diff <= fork_grace:
            best = record
            best_diff = diff
    return best


def find_tv_boosted_fork(symbol: str, entry_dt: datetime, fork_grace=3600) -> dict:
    date_str = entry_dt.strftime("%Y-%m-%d")
    tv_file = TV_KICKER_BASE / date_str / "tv_kicker.jsonl"
    tv_scores = load_jsonl(tv_file)
    best = None
    best_diff = float("inf")
    for record in tv_scores:
        if not record.get("pass"):
            continue
        if record.get("symbol", "").upper() != symbol.upper():
            continue
        try:
            ts = int(record["timestamp"]) / 1000
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        except:
            continue
        diff = time_diff_seconds(entry_dt, dt)
        if diff < best_diff and diff <= fork_grace:
            best = record
            best_diff = diff
    if best:
        # Try to pull full fork score from fork_history
        fallback_path = FORK_HISTORY_BASE / date_str / "fork_scores.jsonl"
        all_forks = load_jsonl(fallback_path)
        for record in all_forks:
            if record.get("symbol", "").upper() == symbol.upper():
                try:
                    ts = int(record["timestamp"]) / 1000
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    if time_diff_seconds(entry_dt, dt) <= fork_grace:
                        return record
                except:
                    continue
    return None


# === Main ===


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD (UTC)")
    args = parser.parse_args()

    date_str = args.date or (datetime.now(datetime.UTC) - timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )

    paper_file = PAPER_TRADE_BASE / date_str / "scrubbed_trades.jsonl"
    btc_file = BTC_SNAPSHOT_BASE / date_str / "btc_snapshots.jsonl"

    paper_trades = load_jsonl(paper_file)
    btc_snaps = load_jsonl(btc_file)

    btc_grace = 10800  # 3 hours
    enriched, unmatched = [], []

    for trade in paper_trades:
        symbol = trade.get("symbol", "").strip().upper()
        entry_time = trade.get("entry_time")
        exit_time = trade.get("exit_time")
        if not (entry_time and exit_time):
            continue
        try:
            entry_dt = parse_iso(entry_time)
            exit_dt = parse_iso(exit_time)
        except:
            continue

        fork_score = find_fork_score(symbol, entry_dt)
        if not fork_score:
            fork_score = find_tv_boosted_fork(symbol, entry_dt)

        enriched_entry = trade.copy()
        enriched_entry["deal_id"] = trade.get("trade_id")
        enriched_entry["fork_score"] = fork_score
        enriched_entry["btc_entry"] = find_nearest_snapshot(
            btc_snaps, entry_dt, btc_grace
        )
        enriched_entry["btc_exit"] = find_nearest_snapshot(
            btc_snaps, exit_dt, btc_grace
        )
        enriched_entry["duration_minutes"] = round(
            time_diff_seconds(exit_dt, entry_dt) / 60, 2
        )

        if fork_score:
            enriched.append(enriched_entry)
        else:
            unmatched.append(enriched_entry)

    out_folder = OUTPUT_DIR / date_str
    out_folder.mkdir(parents=True, exist_ok=True)

    with open(out_folder / "enriched_data.jsonl", "w") as f:
        for rec in enriched:
            f.write(json.dumps(rec) + "\n")

    with open(out_folder / "unmatched_trades.jsonl", "w") as f:
        for rec in unmatched:
            f.write(json.dumps(rec) + "\n")

    print(
        f"[DONE] Enriched {len(enriched)} trades, {len(unmatched)} unmatched → {out_folder}"
    )


if __name__ == "__main__":
    main()
