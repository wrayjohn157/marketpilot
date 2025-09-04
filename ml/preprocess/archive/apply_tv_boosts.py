#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TV_BASE = ROOT / "output" / "tv_history"
FORK_BASE = ROOT / "output" / "fork_history"
ENRICH = ROOT / "ml" / "datasets" / "enriched"

TV_GRACE_S = 1800
FORK_GRACE_S = 1800
SCORE_TOLERANCE = Decimal("0.001")


def normalize(s):
    return s.upper().rstrip("USDT")


def load_jsonl(p):
    return [json.loads(l) for l in p.open() if l.strip()] if p.exists() else []


def dtms(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True)
    args = p.parse_args()
    d = args.date

    rem = load_jsonl(ENRICH / d / "remaining.jsonl")
    forks = load_jsonl(FORK_BASE / d / "fork_scores.jsonl")
    tvs = load_jsonl(TV_BASE / d / "tv_kicker.jsonl")
    boosted, still = [], []

    for t in rem:
        sym, e_dt = normalize(t["symbol"]), datetime.strptime(
            t["entry_time"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=timezone.utc)
        best_tv, tb = None, float("inf")

        for tv in tvs:
            if not tv.get("pass"):
                continue
            if normalize(tv.get("symbol", "")) != sym:
                continue
            try:
                tvdt = dtms(tv["timestamp"])
                diff = abs((tvdt - e_dt).total_seconds())
                if diff <= TV_GRACE_S and diff < tb:
                    best_tv, tb = tv, diff
            except:
                continue

        if not best_tv:
            still.append(t)
            continue

        tv_score = Decimal(str(round(best_tv["prev_score"], 4)))
        tvdt = dtms(best_tv["timestamp"])

        match_found = False
        for f in forks:
            if normalize(f.get("symbol", "")) != sym:
                continue
            try:
                f_score = Decimal(str(round(f["score"], 4)))
                fdt = dtms(f["timestamp"])
                if (
                    abs(f_score - tv_score) <= SCORE_TOLERANCE
                    and abs((fdt - tvdt).total_seconds()) <= FORK_GRACE_S
                ):
                    f2 = dict(f)
                    f2.update(
                        {
                            "tv_kicker_applied": True,
                            "tv_tag": best_tv["tv_tag"],
                            "tv_kicker": best_tv["tv_kicker"],
                            "adjusted_score": best_tv["adjusted_score"],
                            "tv_ts": best_tv["timestamp"],
                            "tv_ts_iso": best_tv["ts_iso"],
                        }
                    )
                    boosted.append({"trade": t, "fork": f2})
                    match_found = True
                    break
            except Exception as e:
                continue

        if not match_found:
            # === DEBUG LOGGING ===
            print(
                f"[❌ NO FORK MATCH] {sym} | trade @ {e_dt.isoformat()} | TV score {tv_score} @ {tvdt.isoformat()}"
            )
            still.append(t)

    with open(ENRICH / d / "tv_boosted.jsonl", "w") as f:
        for r in boosted:
            f.write(json.dumps(r) + "\n")
    with open(ENRICH / d / "still_unmatched.jsonl", "w") as f:
        for r in still:
            f.write(json.dumps(r) + "\n")

    print(f"[✅ DONE] TV-boosted: {len(boosted)} | still unmatched: {len(still)}")


if __name__ == "__main__":
    main()
