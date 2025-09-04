from typing import Dict, List, Optional, Any, Union, Tuple
import json
import os

from
 pathlib import Path

# CONFIGURE THESE PATHS
input_path = "/home/signal/market7/ml/datasets/safu_merged/2025-05-21/enriched_with_safu.jsonl"
output_path = "/home/signal/market7/ml/datasets/safu_labeled/2025-05-21/labeled_safu_data.jsonl"

# CREATE OUTPUT DIR
Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)

# LABELING RULES
DRAWDOWN_THRESHOLD = -10.0
RECOVERY_PNL_THRESHOLD = 1.0
HIGH_RECOVERY_PNL = 3.0

labeled_records = []

with open(input_path, "r") as infile:
    for line in infile:
        record = json.loads(line)
        drawdown = record.get("drawdown_pct")
        pnl = record["trade"].get("pnl_pct", 0)

        if drawdown is None:
            tag = "not_applicable"
            reason = "missing_drawdown"
        elif drawdown < DRAWDOWN_THRESHOLD and pnl < RECOVERY_PNL_THRESHOLD:
            tag = True
            reason = "deep_drawdown_no_recovery"
        elif drawdown < DRAWDOWN_THRESHOLD and pnl >= HIGH_RECOVERY_PNL:
            tag = False
            reason = "recovered_from_drawdown"
        else:
            tag = "not_applicable"
            reason = "low_drawdown_or_unclear"

        record["should_have_closed"] = tag
        record["label_reason"] = reason
        labeled_records.append(record)

with open(output_path, "w") as outfile:
    for r in labeled_records:
        outfile.write(json.dumps(r) + "\n")

print(f"✅ Saved {len(labeled_records)} labeled records to: {output_path}")
