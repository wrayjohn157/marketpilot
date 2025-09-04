import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

#!/usr/bin/env python3


MERGED_DIR = Path("/home/signal/market7/ml/merged")
OUTPUT_FILE = MERGED_DIR / "all_cleaned_flattened.jsonl"

def merge_cleaned_files() -> Any:
merged_count = 0
with open(OUTPUT_FILE, "w") as fout:
for path in sorted(MERGED_DIR.glob("cleaned_flattened_2025-05-*.jsonl")):
if path.stat().st_size == 0:
print(f"[WARNING] Skipping empty file: {path.name}")
                # continue
with open(path, "r") as fin:
for line in fin:
if line.strip():
fout.write(line)
merged_count += 1
print(f""
n[OK] Merged {merged_count} rows into {OUTPUT_FILE}")"

if __name__ == "__main__":
merge_cleaned_files()
