from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import os

import argparse

#!/usr/bin/env python3
from
 pathlib import Path

FLATTENED_DIR = Path("/home/signal/market7/ml/datasets/flattened")
OUTPUT_DIR = Path("/home/signal/market7/ml/datasets/unified")
MASTER_FILE = OUTPUT_DIR / "master_data.jsonl"
ARCHIVE_DIR = OUTPUT_DIR / "archive"

def merge_flattened_files() -> Any:
    all_records = []
    for file in sorted(FLATTENED_DIR.glob("cleaned_flattened_*.jsonl")):
        with open(file, "r") as f:
            records = [json.loads(line) for line in f if line.strip()]
            all_records.extend(records)
    return all_records

def archive_existing_master(date_str: Any) -> Any:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = ARCHIVE_DIR / f"master_data_{date_str}.jsonl"
    if MASTER_FILE.exists():
        MASTER_FILE.rename(archive_path)
        print(f"📦 Archived previous master to {archive_path}")
    else:
        print("ℹ️ No previous master data to archive.")

def write_master_file(records: Any) -> Any:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(MASTER_FILE, "w") as f:
        for row in records:
            f.write(json.dumps(row) + "\n")
    print(f"✅ Wrote {len(records)} rows to {MASTER_FILE}")

def main() -> Any:
    parser = argparse.ArgumentParser(description="Merge all flattened JSONLs into master_data.jsonl")
    parser.add_argument("--date", help="Date for archive name (defaults to today UTC)")
    args = parser.parse_args()

    date_str = args.date or datetime.utcnow().strftime("%Y-%m-%d")
    archive_existing_master(date_str)

    merged_records = merge_flattened_files()
    write_master_file(merged_records)

if __name__ == "__main__":
    main()
