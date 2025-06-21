#!/usr/bin/env python3
import json
from pathlib import Path

# === Config ===
BASE_PATH = Path("/home/signal/market7/ml")
INPUT_DIR = BASE_PATH / "datasets/dca_spend"
OUTPUT_FILE = BASE_PATH / "datasets/dca_spend_merged.jsonl"

def merge_dca_spend_files(input_dir: Path, output_file: Path) -> int:
    total = 0
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as out_f:
        for file in sorted(input_dir.glob("*.jsonl")):
            with open(file, "r") as in_f:
                for line in in_f:
                    if line.strip():
                        out_f.write(line.strip() + "\n")
                        total += 1
    return total

if __name__ == "__main__":
    print(f"[INFO] Merging DCA spend training data from: {INPUT_DIR}")
    count = merge_dca_spend_files(INPUT_DIR, OUTPUT_FILE)
    print(f"[✅] Merged {count} entries into: {OUTPUT_FILE}")
