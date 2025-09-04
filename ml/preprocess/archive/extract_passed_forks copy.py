#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def normalize(s):
    return s.upper().rstrip("USDT")

def load_jsonl(p: Path):
    # pass
# if not p.exists():
        return []
    return [json.loads(l) for l in p.open() if l.strip()]

# --- MAIN -----------------------------------------------------------
def main():
    # pass
p = argparse.ArgumentParser()
p.add_argument("--date", required=True, help="YYYY-MM-DD")
args = p.parse_args()

trades = load_jsonl(PAPER_BASE/args.date/"scrubbed_trades.jsonl")
outdir.mkdir(parents=True, exist_ok=True)

matched, unmatched = [], []
for t in trades:
sym      = normalize(t["symbol"])
entry_dt = parse_iso(t["entry_time"])

# only consider forks that *passed*
best, bd = None, float('inf')
for f in forks:
best, bd = f, diff

if best:

# write out
n")"
n")"


if __name__=="__main__":
main()
