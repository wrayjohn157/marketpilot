#!/usr/bin/env python3
import json, argparse
from datetime import datetime, timezone
from pathlib import Path

# ─── PATHS ──────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parents[2]
PAPER_BASE  = ROOT / "ml/datasets/scrubbed_paper"
FORK_BASE   = ROOT / "output/fork_history"
OUT_BASE    = ROOT / "ml/datasets/enriched"

# ─── PARAMS ─────────────────────────────────────────────────────────
FORK_GRACE_S = 1800  # seconds

def parse_iso(z):
    return datetime.strptime(z, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def normalize(sym):
    return sym.upper().rstrip("USDT")

def load_jsonl(p: Path):
    if not p.exists(): return []
    return [json.loads(l) for l in p.open() if l.strip()]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = p.parse_args()

    trades = load_jsonl(PAPER_BASE/args.date/"scrubbed_trades.jsonl")
    forks  = load_jsonl(FORK_BASE/args.date/"fork_scores.jsonl")
    outdir = OUT_BASE/args.date
    outdir.mkdir(exist_ok=True, parents=True)

    matched, unmatched = [], []
    for t in trades:
        sym, entry = normalize(t["symbol"]), parse_iso(t["entry_time"])
        best, bd = None, float("inf")
        for f in forks:
            if not f.get("passed", False): continue
            if normalize(f["symbol"]) != sym: continue
            fdt = datetime.fromtimestamp(f["timestamp"]/1000, tz=timezone.utc)
            d = abs((fdt-entry).total_seconds())
            if d <= FORK_GRACE_S and d < bd:
                best, bd = f, d
        if best:
            matched.append({"trade": t, "fork": best})
        else:
            unmatched.append(t)

    with open(outdir/"fork_matched.jsonl","w") as f:
        for r in matched: f.write(json.dumps(r)+"\n")
    with open(outdir/"remaining.jsonl","w") as f:
        for r in unmatched: f.write(json.dumps(r)+"\n")

    print(f"[✅ DONE] {len(matched)} matched, {len(unmatched)} to TV")
    
if __name__=="__main__":
    main()
