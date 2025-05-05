import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))  # ✅ Fix path to utils

from utils.time_utils import parse_iso, normalize_trade_date
import json
import argparse
from datetime import datetime

RAW_DIR = Path("/home/signal/market7/ml/datasets/raw_paper")
FORK_HISTORY_DIR = Path("/home/signal/market7/output/fork_history")
OUT_DIR = Path("/home/signal/market7/ml/datasets/scrubbed_paper")


def load_fork_logs(date_str: str):
    path = FORK_HISTORY_DIR / date_str / "fork_scores.jsonl"
    if not path.exists():
        print(f"[WARN] No fork log found for {date_str}")
        return []

    with path.open() as f:
        return [json.loads(line) for line in f]


def try_match_fork(symbol, entry_time, fork_logs):
    target_ts = parse_iso(entry_time).timestamp()
    matches = [
        f for f in fork_logs if f.get("symbol") == symbol and abs(f["timestamp"] / 1000 - target_ts) < 900
    ]
    if not matches:
        return None, None

    closest = min(matches, key=lambda f: abs(f["timestamp"] / 1000 - target_ts))
    diff = abs(closest["timestamp"] / 1000 - target_ts)
    return closest, diff


def enrich_trades(date_str: str):
    raw_path = RAW_DIR / date_str / "paper_trades.jsonl"
    if not raw_path.exists():
        print(f"[ERROR] No raw trade file found for {date_str}")
        return []

    fork_logs = load_fork_logs(date_str)
    enriched = []

    with raw_path.open() as f:
        for line in f:
            r = json.loads(line)
            symbol = r.get("symbol") or r["pair"].replace("USDT_", "").replace("_", "")
            entry_time = r.get("entry_time") or r.get("created_at")

            if not symbol or not entry_time:
                print(f"[SKIP] Invalid trade entry: {r}")
                continue

            match, diff = try_match_fork(symbol, entry_time, fork_logs)

            if match:
                r["fork_score"] = round(match.get("score", 0), 4)
                r["fork_timestamp"] = match.get("timestamp")
                r["score_components"] = match.get("score_components", {})
                r["raw_indicators"] = match.get("raw_indicators", {})
                r["score_hash"] = match.get("score_hash", "")
            else:
                print(f"[MISS] No fork match for {symbol} @ {entry_time}")
                r["fork_score"] = None

            enriched.append(r)

    return enriched


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD")
    args = parser.parse_args()

    enriched = enrich_trades(args.date)
    if not enriched:
        print("[WARN] No enriched data written.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{args.date}.jsonl"
    with out_path.open("w") as f:
        for row in enriched:
            f.write(json.dumps(row) + "\n")

    print(f"[DONE] Enriched file written to {out_path}")


if __name__ == "__main__":
    main()
