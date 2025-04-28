#!/usr/bin/env python3
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

# === Logging Setup ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Default Paths ===
BASE_DIR = Path(__file__).resolve().parents[2]  # ~/market7/
ENRICHED_DIR = BASE_DIR / "live/enriched"
DCA_LOG_DIR = BASE_DIR / "dca/logs"
DEFAULT_OUTPUT_DIR = BASE_DIR / "ml/datasets/recovery_training"

# === Helpers ===
def load_jsonl(path: Path) -> list:
    if not path.exists():
        logging.warning(f"[WARN] File not found: {path}")
        return []
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

def save_jsonl(path: Path, records: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

def build_recovery_dataset(enriched: list, dca_log: list, include_snapshots: bool) -> list:
    enriched_map = {e["deal_id"]: e for e in enriched if "deal_id" in e}
    rows = []

    for entry in dca_log:
        deal_id = entry.get("deal_id")
        enriched_entry = enriched_map.get(deal_id)
        if not enriched_entry:
            continue

        row = {
            "deal_id": deal_id,
            "symbol": entry.get("symbol"),
            "step": entry.get("step"),
            "entry_score": entry.get("entry_score"),
            "current_score": entry.get("current_score"),
            "drawdown_pct": entry.get("indicators", {}).get("drawdown_pct"),
            "safu_score": entry.get("safu_score"),
            "macd_lift": entry.get("indicators", {}).get("macd_lift"),
            "rsi": entry.get("indicators", {}).get("rsi"),
            "rsi_slope": entry.get("indicators", {}).get("rsi_slope"),
            "adx": entry.get("indicators", {}).get("adx"),
            "confidence_score": entry.get("confidence_score"),
            "tp1_shift": entry.get("tp1_shift"),
            "recovery_label": 1 if enriched_entry.get("status") == "passed" else 0,
            "safu_good_but_zombie": enriched_entry.get("safu_good_but_zombie", False),
            "zombie_reason": enriched_entry.get("zombie_reason", [])
        }

        if include_snapshots:
            meta = enriched_entry.get("snapshot_meta", {})
            for k, v in meta.items():
                row[f"snapshot_{k}"] = v

        rows.append(row)

    return rows

# === Main Pipeline ===
def main(date_str: str, include_snapshots: bool, output_dir: Path):
    enriched_file = ENRICHED_DIR / date_str / "enriched_data.jsonl"
    dca_log_file = DCA_LOG_DIR / date_str / "dca_log.jsonl"
    output_file = output_dir / f"{date_str}.jsonl"

    if not enriched_file.exists() or not dca_log_file.exists():
        logging.error(f"❌ Missing input files for {date_str}")
        exit(1)

    logging.info(f"📚 Loading enriched and DCA logs for {date_str}...")
    enriched = load_jsonl(enriched_file)
    dca_log = load_jsonl(dca_log_file)

    logging.info(f"🔧 Building recovery dataset (snapshots included: {include_snapshots})...")
    rows = build_recovery_dataset(enriched, dca_log, include_snapshots)

    if rows:
        save_jsonl(output_file, rows)
        logging.info(f"✅ Saved {len(rows)} rows to {output_file}")
    else:
        logging.warning(f"⚠️ No valid rows generated for {date_str}")
        exit(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build per-day recovery dataset for ML training.")
    parser.add_argument("--date", required=True, help="Target date (YYYY-MM-DD)")
    parser.add_argument("--include-snapshots", action="store_true", help="Include snapshot_meta fields (flattened)")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory path")
    args = parser.parse_args()

    main(args.date, args.include_snapshots, Path(args.output_dir))
