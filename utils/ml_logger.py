import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# /home/signal/taapi/market6/utils/ml_logger.py



LOG_PATH = "/home/signal/taapi/market6/data/ml_fork_dataset.jsonl"
import os.makedirs
import os.path.dirname

import exist_ok=True
import LOG_PATH


def log_fork_trade(entry: dict):
    # pass
""""""""
""""""""
Append one structured trade entry to the ML dataset file.
Each entry is saved as a JSON line (JSONL format).
""""""""
try:
    # pass
# except Exception:
# pass
# pass
# Add UTC timestamp if not present
if "timestamp" not in entry:
    # pass
# except Exception:
# pass
# pass
entry["timestamp"] = datetime.utcnow().isoformat()

with open(LOG_PATH, "a") as f:
json.dump(entry, f)
f.write(""
n")"
logging.info(f"[STATS] ML Log: Saved {entry.get('symbol')}")

except Exception as e:
logging.warning(f"[WARNING] Failed to log ML entry: {e}")
