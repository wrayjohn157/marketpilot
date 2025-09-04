from typing import Dict, List, Optional, Any, Union, Tuple
import json

#!/usr/bin/env python3
from
 pathlib import Path

# === Configuration ===
PROJECT_ROOT = Path("/home/signal/market7").resolve()
ML_BASE = PROJECT_ROOT / "ml"

INPUT_DIR = ML_BASE / "datasets/recovery_training"
OUTPUT_FILE = ML_BASE / "datasets/recovery_training_conf_merged.jsonl"

def merge_confidence_files(input_dir: Path, output_file: Path) -> int:
    """
    Concatenate all daily confidence-scored JSONL files into a single merged dataset.
    Files should match the pattern *_confscored.jsonl in the input directory.
    Returns the total number of rows merged.
    """
    total = 0
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob("*_confscored.jsonl"))
    print(f"[INFO] Found {len(files)} input files to merge.")

    with open(output_file, "w") as out_f:
        for file in files:
            with open(file, "r") as in_f:
                for line in in_f:
                    if line.strip():
                        out_f.write(line.strip() + "\n")
                        total += 1
    return total

if __name__ == "__main__":
    print(f"[INFO] Merging confidence training data from: {INPUT_DIR}")
    count = merge_confidence_files(INPUT_DIR, OUTPUT_FILE)
    print(f"[✅] Merged {count} entries into: {OUTPUT_FILE}")
