from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import os
import sys

# add project root so we can import utils as a package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from
 utils.sim_snapshot_loader import sim_generate_snapshot_series  # fixed import

if len(sys.argv) < 3:
    print("Usage: python3 test_snapshot_series.py SYMBOL ENTRY_TS [TF] [--dump]")
    sys.exit(1)

symbol = sys.argv[1]
entry_ts = int(sys.argv[2])
tf = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "1h"
dump_flag = "--dump" in sys.argv

# Run snapshot series generation
snapshots = sim_generate_snapshot_series(symbol, entry_ts, tf)
print(f"✅ Generated {len(snapshots)} snapshots")

# Print all snapshots to CLI
print(json.dumps(snapshots, indent=2))

# Optional JSONL output
if dump_flag:
    ts_fmt = datetime.utcfromtimestamp(entry_ts / 1000).strftime("%Y%m%d_%H%M")
    outfile = f"/home/signal/market7/sim/sandbox3/debug_log/{symbol}_{tf}_{ts_fmt}_sim_snapshots.jsonl"
    with open(outfile, "w") as f:
        for s in snapshots:
            f.write(json.dumps(s) + "\n")
    print(f"📄 Dumped to: {outfile}")
