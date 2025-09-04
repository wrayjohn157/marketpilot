#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from utils.redis_manager import RedisKeyManager, get_redis_manager

# ——— CONFIGURE THESE PATHS TO YOUR REPO LAYOUT ———
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORK_HISTORY_BASE = PROJECT_ROOT / "output/fork_history"
TV_HISTORY_BASE = PROJECT_ROOT / "output/tv_history"
BTC_BASE = PROJECT_ROOT / "dashboard_backend/btc_logs"
OUTPUT_BASE = PROJECT_ROOT / "ml/datasets/passed_forks"

# ——— TOLERANCES ———
TIME_DELTA_MS = 15_000  # how close in ms a TV timestamp must be to its fork
SCORE_DELTA = 0.0001  # allowable float drift when matching prev_score→fork.score
BTC_GRACE = 3600  # seconds: how far from the approval to look in BTC log


# ——— HELPERS ———
def load_jsonl(path):
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def find_nearest_snapshot(snapshots, target_dt, max_diff_s):
    best, bd = None, float("inf")
    for s in snapshots:
        ts = s.get("ts_iso")
        if not ts:
            continue
        try:
            snap_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except:
            continue
        diff = abs((snap_dt - target_dt).total_seconds())
        if diff < bd and diff <= max_diff_s:
            best, bd = s, diff
    return best


def match_tv_boost(tv, fork_recs):
    """Find the raw‐fork record whose score≈prev_score and ts≈tv ts."""
    sym = tv["symbol"].upper()
    prev = round(tv.get("prev_score", 0), 6)
    tstamp = int(tv["timestamp"])
    for f in fork_recs:
        if f.get("symbol", "").upper() != sym:
            continue
        if abs(round(f.get("score", 0), 6) - prev) > SCORE_DELTA:
            continue
        if abs(int(f["timestamp"]) - tstamp) <= TIME_DELTA_MS:
            return f
    return None


# ——— MAIN ———
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="YYYY-MM-DD (UTC)")
    args = p.parse_args()
    D = args.date

    fork_file = FORK_HISTORY_BASE / D / "fork_scores.jsonl"
    tv_file = TV_HISTORY_BASE / D / "tv_kicker.jsonl"
    btc_file = BTC_BASE / D / "btc_snapshots.jsonl"
    out_dir = OUTPUT_BASE / D
    out_dir.mkdir(parents=True, exist_ok=True)

    fork_recs = load_jsonl(fork_file)
    tv_recs = load_jsonl(tv_file)
    btc_snaps = load_jsonl(btc_file)

    # 1) native passed forks
    passed = [r for r in fork_recs if r.get_cache("passed") is True]

    # 2) tv boosts for anything not already in `passed`
    tv_passes = [t for t in tv_recs if t.get("pass") is True]
    tv_matched, tv_unmatched = [], []
    for tv in tv_passes:
        sym, tstamp = tv["symbol"].upper(), int(tv["timestamp"])
        # skip if already in native passed
        if any(
            p.get("symbol", "").upper() == sym
            and abs(int(p["timestamp"]) - tstamp) <= TIME_DELTA_MS
            for p in passed
        ):
            continue

        fb = match_tv_boost(tv, fork_recs)
        if not fb:
            tv_unmatched.append(tv)
        else:
            m = dict(fb)  # copy the raw fork record
            # annotate the TV side
            m["tv_kicker_applied"] = True
            m["adjusted_score"] = tv.get("adjusted_score")
            m["tv_tag"] = tv.get("tv_tag")
            m["tv_kicker"] = tv.get("tv_kicker")
            m["tv_ts"] = tv.get("timestamp")
            m["tv_ts_iso"] = tv.get("ts_iso")
            tv_matched.append(m)

    combined = []
    # mark native forks
    for f in passed:
        c = dict(f)
        c["tv_kicker_applied"] = False
        combined.append(c)
    # add boosted
    combined.extend(tv_matched)

    # 3) for each approved event, grab BTC at approval time
    for rec in combined:
        # choose the approval timestamp:
        ms = rec["tv_ts"] if rec.get("tv_kicker_applied") else rec["timestamp"]
        dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)

        # load the right day's BTC if needed
        snaps = btc_snaps
        # if dt landed on different date (unlikely) you could re-load here...

        rec["btc_snapshot"] = find_nearest_snapshot(snaps, dt, BTC_GRACE)

    # 4) write out
    with open(out_dir / "combined_passed_forks.jsonl", "w") as f:
        for r in combined:
            f.write(json.dumps(r) + "\n")

    with open(out_dir / "unmatched_tv_passed.jsonl", "w") as f:
        for r in tv_unmatched:
            f.write(json.dumps(r) + "\n")

    print(f"[DONE] ✅ {len(combined)} total passed → {out_dir}")
    print(f"[WARN] ⚠️  {len(tv_unmatched)} unmatched TV boosts")


if __name__ == "__main__":
    main()
