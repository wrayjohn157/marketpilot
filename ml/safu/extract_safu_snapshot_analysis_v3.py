from typing import Dict, List, Optional, Any, Union, Tuple
import json
import os

from tqdm import tqdm

#!/usr/bin/env python3
from
 pathlib import Path

# Paths
BASE = Path("/home/signal/market7")
SNAPSHOT_DIR = BASE / "ml/datasets/recovery_snapshots"
OUTPUT_PATH = BASE / "ml/datasets/safu_analysis/merged_safu_dca.jsonl"

def load_jsonl(path: Any) -> Any:
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

def main() -> Any:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with open(OUTPUT_PATH, "w") as out_f:
        for file in tqdm(list(SNAPSHOT_DIR.glob("*_*.jsonl")), desc="🔍 Scanning SAFU snapshots"):
            try:
                data = load_jsonl(file)
                for row in data:
                    if row.get("safu_score") is not None:
                        row["snapshot_file"] = file.name
                        out_f.write(json.dumps(row) + "\n")
                        count += 1
            except Exception as e:
                print(f"❌ Failed to read {file.name}: {e}")
                continue

    print(f"\n✅ Extracted {count} rows with safu_score into: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
