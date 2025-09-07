#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

# === Paths ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRUBBED_PATH = PROJECT_ROOT / "ml/datasets/scrubbed_paper"
FORK_PATH = PROJECT_ROOT / "output/fork_history"
TV_PATH = PROJECT_ROOT / "output/tv_history"

# === Tolerances ===
FORK_GRACE_S = 1800
SCORE_TOL = 0.001


def parse_iso(z):
    return datetime.strptime(z, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def normalize(sym):
    return sym.upper().strip().replace("USDT", "")


def load_jsonl(p):
    return [json.loads(line) for line in open(p) if line.strip()] if p.exists() else []


def try_debug_tv_boost(symbol_raw, entry_dt, tvs, forks):
    symbol = normalize(symbol_raw)
    found_tv = False

    for tv in tvs:
        if normalize(tv.get("symbol", "")) != symbol or not tv.get("pass"):
            continue

        try:
            tv_ts = int(tv["timestamp"])
            tv_dt = datetime.fromtimestamp(tv_ts / 1000, tz=timezone.utc)
            tv_score = round(tv.get("prev_score", -999), 4)
            time_to_trade = abs((tv_dt - entry_dt).total_seconds())

            # Print every TV match (even if out of grace window)
            print(
                f"\n🔎 TV match for {symbol_raw} at {tv['ts_iso']} | Δtime to trade: {time_to_trade:.2f}s | TV score: {tv_score}"
            )

            if time_to_trade > FORK_GRACE_S:
                print("⏱️  Skipping — outside grace window")
                continue

            found_tv = True

            for f in forks:
                if normalize(f.get("symbol", "")) != symbol:
                    continue
                try:
                    fork_score = round(f.get("score", -999), 4)
                    fork_dt = datetime.fromtimestamp(
                        f["timestamp"] / 1000, tz=timezone.utc
                    )
                    dt_diff = abs((fork_dt - tv_dt).total_seconds())
                    score_diff = abs(fork_score - tv_score)

                    reason = []
                    if score_diff > SCORE_TOL:
                        reason.append(f"Δscore={score_diff:.5f} (too high)")
                    if dt_diff > FORK_GRACE_S:
                        reason.append(f"Δtime={dt_diff:.2f}s (too far)")
                    if not reason:
                        print(
                            f"✅ MATCH | Fork @ {f['ts_iso']} | Δscore={score_diff:.5f} | Δtime={dt_diff:.2f}s"
                        )
                        return True
                    else:
                        print(
                            f"⚠️  Reject | Fork @ {f['ts_iso']} | Δscore={score_diff:.5f} | Δtime={dt_diff:.2f}s | Reason: {', '.join(reason)}"
                        )
                except Exception as fe:
                    print(f"⚠️  Error inspecting fork: {fe}")
        except Exception as e:
            print(f"❌ Error inspecting TV match: {e}")

    return False


def debug_tv_matches(date_str):
    base = PROJECT_ROOT / "ml/datasets/enriched" / date_str
    forks = load_jsonl(FORK_PATH / date_str / "fork_scores.jsonl")
    tvs = load_jsonl(TV_PATH / date_str / "tv_kicker.jsonl")
    trades = load_jsonl(SCRUBBED_PATH / date_str / "scrubbed_trades.jsonl")

    print(f"\n🔍 Matching trades using TV kicker boost on {date_str}...")

    for t in trades:
        try:
            symbol = t["symbol"]
            entry_dt = parse_iso(t["entry_time"])
            matched = try_debug_tv_boost(symbol, entry_dt, tvs, forks)
            if not matched:
                print(f"❌ No match | {symbol} | Trade at {entry_dt.isoformat()}")
        except Exception as e:
            print(f"❌ Error in trade {t.get('symbol')} | {e}")


# === CLI ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Target date (YYYY-MM-DD)")
    args = parser.parse_args()
    debug_tv_matches(args.date)
