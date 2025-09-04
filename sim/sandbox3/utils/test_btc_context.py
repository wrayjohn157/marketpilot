from typing import Dict, List, Optional, Any, Union, Tuple
import json
import os
import sys

from sim_btc_context import get_btc_context_for_sim, load_btc_snapshot_for_time

#!/usr/bin/env python3
from
 datetime import datetime

# ensure this folder is on PYTHONPATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def fmt_ts(ts_ms: int) -> str:
    return datetime.utcfromtimestamp(ts_ms // 1000).isoformat()

def usage() -> Any:
    print(f"Usage: {sys.argv[0]} <ts1_ms> [<ts2_ms> ...]")
    print("Example:")
    print(f"  {sys.argv[0]} 1752191745000 1752260400000")
    sys.exit(1)

if len(sys.argv) < 2:
    usage()

for arg in sys.argv[1:]:
    try:
        ts = int(arg)
    except ValueError:
        print(f"✖ invalid timestamp: {arg}")
        continue

    print(f"\n=== Entry time: {fmt_ts(ts)} ({ts} ms) ===")
    full = get_btc_context_for_sim(ts)
    print("get_btc_context_for_sim →")
    print(json.dumps(full, indent=2))

    slim = load_btc_snapshot_for_time(ts)
    print("load_btc_snapshot_for_time →")
    print(json.dumps(slim, indent=2))

print()
