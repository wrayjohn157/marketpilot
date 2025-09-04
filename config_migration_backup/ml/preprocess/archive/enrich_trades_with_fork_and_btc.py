#!/usr/bin/env python3
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

# ── BASE DIRECTORIES ─────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAPER_BASE   = PROJECT_ROOT / "ml/datasets/scrubbed_paper"
FORK_BASE    = PROJECT_ROOT / "output/fork_history"
TV_BASE      = PROJECT_ROOT / "output/tv_history"
BTC_BASE     = PROJECT_ROOT / "dashboard_backend/btc_logs"
OUT_BASE     = PROJECT_ROOT / "ml/datasets/enriched"

# ── TOLERANCES ────────────────────────────────────────────────────────────────
FORK_GRACE_S    = 10     # 30 minutes
BTC_GRACE_S     = 3600     # 1 hour
SCORE_TOLERANCE = 0.001    # TV.prev_score vs fork.score

# ── HELPERS ──────────────────────────────────────────────────────────────────
def parse_iso(z):
    return datetime.strptime(z, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def normalize(sym):
    return sym.upper().strip().replace("USDT", "")

def load_jsonl(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in open(path) if line.strip()]

def find_best_tv(tvs, symbol, entry_dt):
    """Return the TV record with pass=True closest to entry_dt (≤FORK_GRACE_S)."""
    symbol = normalize(symbol)
    best, bd = None, float('inf')
    for t in tvs:
        if not t.get("pass") or normalize(t.get("symbol","")) != symbol:
            continue
        try:
            t_dt = datetime.fromtimestamp(int(t["timestamp"]) / 1000, tz=timezone.utc)
            diff = abs((t_dt - entry_dt).total_seconds())
            if diff <= FORK_GRACE_S and diff < bd:
                best, bd = t, diff
        except:
            continue
    return best

def match_fork_by_tv(forks, tv):
    """Given a TV record, find the fork record whose score≈prev_score and ts≈tv_ts."""
    symbol   = normalize(tv["symbol"])
    tv_score = round(tv.get("prev_score", -999), 4)
    tv_dt    = datetime.fromtimestamp(int(tv["timestamp"]) / 1000, tz=timezone.utc)

    best, bd = None, float('inf')
    for f in forks:
        if normalize(f.get("symbol","")) != symbol:
            continue
        try:
            f_score = round(f.get("score", -999), 4)
            f_dt    = datetime.fromtimestamp(int(f["timestamp"]) / 1000, tz=timezone.utc)
            score_diff = abs(f_score - tv_score)
            time_diff  = abs((f_dt - tv_dt).total_seconds())
            if score_diff <= SCORE_TOLERANCE and time_diff <= FORK_GRACE_S and time_diff < bd:
                best, bd = f, time_diff
        except:
            continue

    if not best:
        return None

    enriched = dict(best)
    enriched.update({
        "tv_kicker_applied": True,
        "tv_tag":           tv.get("tv_tag"),
        "tv_kicker":        tv.get("tv_kicker"),
        "adjusted_score":   tv.get("adjusted_score"),
        "tv_ts":            tv.get("timestamp"),
        "tv_ts_iso":        tv.get("ts_iso"),
    })
    return enriched

def find_closest_fork(forks, symbol, entry_dt):
    """Return the fork record nearest in time to entry_dt (≤FORK_GRACE_S)."""
    symbol = normalize(symbol)
    best, bd = None, float('inf')
    for f in forks:
        if normalize(f.get("symbol","")) != symbol:
            continue
        try:
            f_dt = datetime.fromtimestamp(int(f["timestamp"]) / 1000, tz=timezone.utc)
            diff = abs((f_dt - entry_dt).total_seconds())
            if diff <= FORK_GRACE_S and diff < bd:
                best, bd = f, diff
        except:
            continue
    return best

def find_btc_snap(snaps, ref_dt):
    """Return the BTC snapshot nearest ref_dt (≤BTC_GRACE_S)."""
    best, bd = None, float('inf')
    for s in snaps:
        if "ts_iso" not in s:
            continue
        try:
            s_dt = datetime.fromisoformat(s["ts_iso"].replace("Z", "+00:00"))
            diff = abs((s_dt - ref_dt).total_seconds())
            if diff <= BTC_GRACE_S and diff < bd:
                best, bd = s, diff
        except:
            continue
    return best

# ── MAIN PROCESS ─────────────────────────────────────────────────────────────
def enrich(date_str):
    paper_f = PAPER_BASE / date_str / "scrubbed_trades.jsonl"
    forks_f = FORK_BASE  / date_str / "fork_scores.jsonl"
    tv_f    = TV_BASE    / date_str / "tv_kicker.jsonl"
    btc_f   = BTC_BASE   / date_str / "btc_snapshots.jsonl"
    out_dir = OUT_BASE   / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    trades = load_jsonl(paper_f)
    forks  = load_jsonl(forks_f)
    tvs    = load_jsonl(tv_f)
    btc    = load_jsonl(btc_f)

    enriched, unmatched = [], []

    for t in trades:
        symbol = t["symbol"]
        try:
            entry_dt = parse_iso(t["entry_time"])
            exit_dt  = parse_iso(t["exit_time"])
        except:
            unmatched.append({**t, "reason":"bad_timestamp"})
            continue

        # 1) Try TV‐boosted match
        fork_rec = None
        tv_rec   = find_best_tv(tvs, symbol, entry_dt)
        if tv_rec:
            fork_rec = match_fork_by_tv(forks, tv_rec)

        # 2) Fallback to plain fork match
        if not fork_rec:
            fork_rec = find_closest_fork(forks, symbol, entry_dt)

        if not fork_rec:
            unmatched.append({**t, "reason":"no_fork_found"})
            continue

        enriched.append({
            **t,
            "deal_id":     t["trade_id"],
            "fork_score":  fork_rec,
            "btc_entry":   find_btc_snap(btc, entry_dt),
            "btc_exit":    find_btc_snap(btc, exit_dt),
            "duration_min": round(abs((exit_dt - entry_dt).total_seconds()) / 60, 2),
        })

    # write out
    with open(out_dir / "enriched_data.jsonl","w") as f:
        for r in enriched:
            f.write(json.dumps(r) + "\n")
    with open(out_dir / "unmatched_trades.jsonl","w") as f:
        for r in unmatched:
            f.write(json.dumps(r) + "\n")

    print(f"[✅ DONE] Enriched: {len(enriched)} | Unmatched: {len(unmatched)} → {out_dir}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = p.parse_args()
    enrich(args.date)
