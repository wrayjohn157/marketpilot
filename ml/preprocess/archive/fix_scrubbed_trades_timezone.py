#!/usr/bin/env python3
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

INPUT_PATH = Path("/home/signal/market7/ml/datasets/scrubbed_paper/2025-05-12/scrubbed_trades.jsonl")
OUTPUT_PATH = Path("/home/signal/market7/ml/datasets/enriched/2025-05-12/scrubbed_trades_fixed.jsonl")
TIME_SHIFT = timedelta(hours=-2)

def shift_iso_time(iso_str):
    dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
    shifted = dt + TIME_SHIFT
    return shifted.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def main():
    if not INPUT_PATH.exists():
        print(f"❌ File not found: {INPUT_PATH}")
        return

    with open(INPUT_PATH) as f_in, open(OUTPUT_PATH, "w") as f_out:
        count = 0
        for line in f_in:
            if not line.strip():
                continue
            data = json.loads(line)
            try:
                data["entry_time"] = shift_iso_time(data["entry_time"])
                data["exit_time"] = shift_iso_time(data["exit_time"])
                f_out.write(json.dumps(data) + "\n")
                count += 1
            except Exception as e:
                print(f"⚠️ Skipping bad line: {e}")
                continue

    print(f"[✅ DONE] Fixed {count} records → {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
