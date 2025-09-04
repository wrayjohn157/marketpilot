#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

# === CONFIG PATHS ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORK_HISTORY_BASE = PROJECT_ROOT / "output/fork_history"
TV_HISTORY_BASE = PROJECT_ROOT / "output/tv_history"
OUTPUT_BASE = PROJECT_ROOT / "ml/datasets/passed_forks"

# === SETTINGS ===
TIME_DELTA_MS = 15_000  # 15 seconds
SCORE_DELTA = 0.0001  # Allowable float drift


def load_jsonl(path):
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def save_jsonl(path, records):
    with open(path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


def match_tv_boosted(tv_entry, fork_records):
    target_symbol = tv_entry["symbol"].strip().upper()
    prev_score = round(tv_entry.get("prev_score", 0), 6)
    ts_tv = int(tv_entry.get("timestamp", 0))

    for fork in fork_records:
        if fork.get("symbol", "").strip().upper() != target_symbol:
            continue

        score = round(fork.get("score", 0), 6)
        if abs(score - prev_score) > SCORE_DELTA:
            continue

        ts_fork = int(fork.get("timestamp", 0))
        if abs(ts_fork - ts_tv) <= TIME_DELTA_MS:
            return fork

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Merge fork history with TV-kicker boosts."
    )
    parser.add_argument("--date", required=True, help="Target date in YYYY-MM-DD (UTC)")
    args = parser.parse_args()
    date_str = args.date

    # === Load files ===
    fork_path = FORK_HISTORY_BASE / date_str / "fork_scores.jsonl"
    tv_path = TV_HISTORY_BASE / date_str / "tv_kicker.jsonl"
    out_dir = OUTPUT_BASE / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    combined_path = out_dir / "combined_passed_forks.jsonl"
    unmatched_path = out_dir / "unmatched_tv_passed.jsonl"

    forks = load_jsonl(fork_path)
    tv_entries = load_jsonl(tv_path)

    passed_forks = [f for f in forks if f.get("passed") is True]
    tv_passes = [tv for tv in tv_entries if tv.get("pass") is True]

    matched_tv = []
    unmatched_tv = []

    for tv in tv_passes:
        matched = match_tv_boosted(tv, forks)
        if matched:
            enriched = dict(matched)
            enriched.update(
                {
                    "tv_kicker_applied": True,
                    "adjusted_score": tv.get("adjusted_score"),
                    "tv_tag": tv.get("tv_tag"),
                    "tv_kicker": tv.get("tv_kicker"),
                    "tv_ts": tv.get("timestamp"),
                    "tv_ts_iso": tv.get("ts_iso"),
                }
            )
            matched_tv.append(enriched)
        else:
            unmatched_tv.append(tv)

    final = passed_forks + matched_tv

    save_jsonl(combined_path, final)
    save_jsonl(unmatched_path, unmatched_tv)

    print(f"[DONE] ✅ {len(final)} passed forks saved to: {combined_path}")
    print(f"[WARN] ⚠️  {len(unmatched_tv)} unmatched TV passes → {unmatched_path}")


if __name__ == "__main__":
    main()
