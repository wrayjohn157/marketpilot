# test_fork_loader.py
import sys
from sim_fork_loader import sim_load_fork_meta  # ✅ LOCAL import (no `utils.` prefix)

symbol = sys.argv[1]
entry_ts = int(sys.argv[2])

fork = sim_load_fork_meta(symbol, entry_ts)
if fork:
    print("✅ Fork found:")
    print(fork)
else:
    print("❌ No fork metadata found.")
