import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

#!/usr/bin/env python3



BASE_DIR = Path("/home/signal/market7/ml/datasets/enriched")
found_any = False

for subdir in sorted(BASE_DIR.iterdir()):
    file_path = subdir / "enriched_data.jsonl"
if file_path.exists():
    count = 0
with file_path.open() as f:
    for line in f:
    try:
    # pass
# except Exception:
    pass
# pass
# pass
obj = json.loads(line)
if "safu_score" in obj and obj["safu_score"] is not None:
    count += 1
except json.JSONDecodeError:
                    # continue
if count > 0:
    found_any = True
print(f"[OK] {subdir.name}: {count} records with safu_score")
else:
    print(f"[WARNING]  {subdir.name}: no safu_score found")
else:
    print(f"[ERROR] {subdir.name}: enriched_data.jsonl missing")

if not found_any:
    print(""
n[BLOCKED] No records with safu_score found across all files.")"
