#!/usr/bin/env python3
import json
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

# === Updated Dynamic Paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ~/market7
FORK_HISTORY_BASE = PROJECT_ROOT / "output/fork_history"
SCRUBBED_BASE = PROJECT_ROOT / "ml/datasets/fork_pulls"

# === Paths ===
def get_paths(date_str):
    input_path = FORK_HISTORY_BASE / date_str / "fork_scores.jsonl"
    output_dir = SCRUBBED_BASE / date_str
    output_file = output_dir / "scrubbed_fork_scores.jsonl"
    return input_path, output_dir, output_file

# === Helpers ===
def clean_symbol(symbol: str) -> str:
    sym = symbol.strip().upper()
    if not sym.endswith("USDT"):
        sym += "USDT"
    return sym

def to_utc_z(ts) -> str:
    """Convert timestamp (epoch or ISO) into ISO UTC Zulu format."""
    try:
        if isinstance(ts, (int, float)):
            if ts > 1e12:  # Milliseconds
                ts /= 1000.0
            return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ")
        elif isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace("Z", "").replace("+00:00", ""))
            dt = dt.astimezone(timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        pass
    return ts  # fallback

def process_record(record: dict) -> dict:
    if record.get("passed") is False:
        return None

    if "symbol" in record:
        record["symbol"] = clean_symbol(record["symbol"])

    if "timestamp" in record:
        ts = record["timestamp"]
        if isinstance(ts, (int, float)):
            record["ts_iso"] = to_utc_z(ts)
        elif isinstance(ts, str):
            # try to recover ms timestamp from ISO
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "").replace("+00:00", ""))
                epoch_ms = int(dt.timestamp() * 1000)
                record["timestamp"] = epoch_ms
                record["ts_iso"] = to_utc_z(epoch_ms)
            except:
                pass

    if "scored_at" in record:
        record["scored_at"] = to_utc_z(record["scored_at"])

    if "indicators" in record and isinstance(record["indicators"], dict):
        indicators = record["indicators"]
        if "timestamp" in indicators:
            indicators["timestamp_iso"] = to_utc_z(indicators["timestamp"])

    return record

# === Main ===
def main():
    parser = argparse.ArgumentParser(description="Scrub and unify fork scores timestamps and symbols.")
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format. Defaults to yesterday.")
    args = parser.parse_args()

    date_str = args.date or (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    input_file, output_dir, output_file = get_paths(date_str)

    if not input_file.exists():
        print(f"[ERROR] Input file does not exist: {input_file}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned_count = 0
    with open(input_file, "r") as infile, open(output_file, "w") as outfile:
        for line in infile:
            try:
                record = json.loads(line)
                processed = process_record(record)
                if processed is not None:
                    outfile.write(json.dumps(processed) + "\n")
                    cleaned_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to process a record: {e}")
                print(f"[DEBUG] Raw line: {line.strip()}")

    print(f"[DONE] Processed {cleaned_count} records into: {output_file}")

if __name__ == "__main__":
    main()
