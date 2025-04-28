#!/usr/bin/env python3
import json
import logging
from pathlib import Path

# === Logging Setup ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Default Paths ===
BASE_DIR = Path(__file__).resolve().parents[2]  # ~/market7/
DEFAULT_INPUT_DIR = BASE_DIR / "ml/datasets/recovery_training"
DEFAULT_OUTPUT_FILE = BASE_DIR / "ml/datasets/recovery_training_merged.jsonl"

# === Merge Helper ===
def merge_jsonl_files(input_dir: Path, output_file: Path) -> int:
    total = 0
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as out_f:
        for file in sorted(input_dir.glob("*.jsonl")):
            if "confscored" in file.name:
                continue  # Skip confidence-labeled datasets
            with open(file, "r") as in_f:
                for line in in_f:
                    if line.strip():
                        out_f.write(line.strip() + "\n")
                        total += 1
    return total

# === Main ===
def main(input_dir: Path, output_file: Path):
    logging.info(f"📂 Merging recovery datasets from: {input_dir}")

    count = merge_jsonl_files(input_dir, output_file)

    if count > 0:
        logging.info(f"✅ Merged {count} entries into {output_file}")
    else:
        logging.warning(f"⚠️ No entries merged. Check input directory!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Merge recovery training datasets.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR, help="Input directory containing daily JSONLs")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE, help="Output merged JSONL file path")
    args = parser.parse_args()

    main(args.input_dir, args.output)
