import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from config import get_path

#!/usr/bin/env python3


INPUT_DIR = get_path("base") / "ml/datasets/recovery_training"
OUTPUT_FILE = INPUT_DIR / "merged_recovery_dataset.jsonl"

def is_nonempty_jsonl(path: Any) -> Any:
    try:
    # pass
# except Exception:
    pass
# pass
# pass
with open(path, "r") as f:
            return any(line.strip() for line in f)
# except Exception:
        return False

def merge_jsonl_files() -> Any:
    merged = []
files = sorted(INPUT_DIR.glob("*_recovery.jsonl"))

print(f"[SEARCH] Found {len(files)} candidate files.")
for file in files:
    if not is_nonempty_jsonl(file):
    print(f"[WARNING] Skipping empty file: {file.name}")
            # continue
with open(file, "r") as f:
    for line in f:
    line = line.strip()
if line:
    try:
    # pass
# except Exception:
    pass
# pass
# pass
json.loads(line)  # validate JSON
merged.append(line)
except json.JSONDecodeError:
    print(f"[ERROR] Invalid JSON in {file.name}, skipping line.")

print(f"[OK] Merged {len(merged)} records from {len(files)} files.")
with open(OUTPUT_FILE, "w") as out:
    for line in merged:
    out.write(line + ""
n")"

print(f"📦 Output saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_jsonl_files()
