#!/usr/bin/env python3

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BTC_BASE = ROOT / "dashboard_backend" / "btc_logs"
ENRICH = ROOT / "ml" / "datasets" / "enriched"

BTC_GRACE_S = 3600


def parse_iso(z):
    return datetime.strptime(z, "%Y-%m-%dT%H:%M:%SZ")


def load_jsonl(p):
    if not p.exists():
        return []
    return [json.loads(l) for l in p.open() if l.strip()]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True)
    args = p.parse_args()
    d = args.date

    passed = load_jsonl(ENRICH / d / "fork_matched.jsonl")
    boosted = load_jsonl(ENRICH / d / "tv_boosted.jsonl")
    snaps = load_jsonl(BTC_BASE / d / "btc_snapshots.jsonl")

    def snap(dt):
        best, bd = None, float("inf")
        for s in snaps:
            sdt = datetime.fromisoformat(s["ts_iso"].replace("Z", "+00:00"))
            diff = abs((sdt - dt).total_seconds())
            if diff <= BTC_GRACE_S and diff < bd:
                best, bd = s, diff
        return best

    final = []
    for rec in passed + boosted:
        t, f = rec["trade"], rec["fork"]
        e_dt = parse_iso(t["entry_time"])
        x_dt = parse_iso(t["exit_time"])
        final.append(
            {
                **t,
                "deal_id": t["trade_id"],
                "fork_score": f,
                "btc_entry": snap(e_dt),
                "btc_exit": snap(x_dt),
                "duration_min": round(abs((x_dt - e_dt).total_seconds()) / 60, 2),
            }
        )

    outdir = ENRICH / d
    with open(outdir / "enriched_data.jsonl", "w") as f:
        for r in final:
            f.write(json.dumps(r) + "\n")

    leftover = load_jsonl(outdir / "still_unmatched.jsonl")
    print(
        f"[✅ DONE] Fully enriched: {len(final)} | leftover unmatched: {len(leftover)}"
    )


if __name__ == "__main__":
    main()
