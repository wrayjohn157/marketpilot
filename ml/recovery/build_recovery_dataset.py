# build_recovery_dataset.py
import json
import argparse
from pathlib import Path
from datetime import datetime
from dateutil import parser as dtparser

# === Input directories ===
ENRICHED_DIR = Path("/home/signal/market7/ml/datasets/enriched")
SNAPSHOT_DIR = Path("/home/signal/market7/ml/datasets/recovery_snapshots")
DCA_LOG_DIR = Path("/home/signal/market7/dca/logs")

# === Output directory ===
OUTPUT_DIR = Path("/home/signal/market7/ml/datasets/recovery_training")

REQUIRED_MODEL_FEATURES = [
    "step", "entry_score", "current_score", "drawdown_pct", "safu_score",
    "macd_lift", "rsi", "rsi_slope", "adx", "confidence_score", "tp1_shift",
    "snapshot_score_trend", "snapshot_rsi_trend", "snapshot_max_drawdown",
    "snapshot_min_score", "snapshot_min_rsi", "snapshot_time_to_max_drawdown_min",
    "recovery_label"
]

def load_jsonl(path):
    if not path.exists():
        return []
    with open(path, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

def extract_trends(snapshots):
    times, dd_vals, score_vals, rsi_vals = [], [], [], []
    for snap in snapshots:
        try:
            dt = dtparser.parse(snap.get("timestamp"))
            dd = snap.get("drawdown_pct")
            score = snap.get("current_score")
            rsi = snap.get("rsi")
            if dd is None or score is None or rsi is None:
                continue
            times.append(dt)
            dd_vals.append(dd)
            score_vals.append(score)
            rsi_vals.append(rsi)
        except:
            continue

    if not times:
        return {k: 0.0 for k in REQUIRED_MODEL_FEATURES if k.startswith("snapshot_")}

    try:
        return {
            "snapshot_score_trend": score_vals[-1] - score_vals[0],
            "snapshot_rsi_trend": rsi_vals[-1] - rsi_vals[0],
            "snapshot_max_drawdown": max(dd_vals),
            "snapshot_min_score": min(score_vals),
            "snapshot_min_rsi": min(rsi_vals),
            "snapshot_time_to_max_drawdown_min": (times[dd_vals.index(max(dd_vals))] - times[0]).total_seconds() / 60.0
        }
    except:
        return {k: 0.0 for k in REQUIRED_MODEL_FEATURES if k.startswith("snapshot_")}

def build_daily_dataset(date_str):
    enriched_path = ENRICHED_DIR / date_str / "enriched_data.jsonl"
    dca_path = DCA_LOG_DIR / date_str / "dca_log.jsonl"
    out_path = OUTPUT_DIR / f"{date_str}_recovery.jsonl"

    enriched = load_jsonl(enriched_path)
    dca_logs = { (e["symbol"], e["deal_id"]): e for e in load_jsonl(dca_path) }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w") as fout:
        for row in enriched:
            trade = row.get("trade", {})
            full_symbol = trade.get("symbol", "")
            symbol = full_symbol.replace("USDT", "")
            deal_id = trade.get("trade_id")
            pnl = trade.get("pnl_pct")
            status = trade.get("status")
            exit_time = trade.get("exit_time")

            print(f"\n🔍 Evaluating {full_symbol} {deal_id}")
            snapshot_file = SNAPSHOT_DIR / f"{symbol}_{deal_id}.jsonl"
            snapshots = load_jsonl(snapshot_file)
            if not snapshots:
                print("⚠️ No snapshots found.")
                continue

            latest = snapshots[-1]
            dca = dca_logs.get((full_symbol, deal_id), {})

            try:
                safu_score = dca.get("safu_score", 0)
                health_status = dca.get("health_status")
                is_zombie = (safu_score is not None and safu_score >= 0.5 and health_status == "Zombie")
            except:
                is_zombie = False

            step = dca.get("step", 0)
            recovery_label = int(
                status in ("completed", "closed") and pnl is not None and pnl > 0.3
            )

            record = {
                "symbol": symbol,
                "deal_id": deal_id,
                "step": step,
                "entry_score": latest.get("entry_score"),
                "current_score": latest.get("current_score"),
                "drawdown_pct": latest.get("drawdown_pct"),
                "safu_score": latest.get("safu_score"),
                "macd_lift": latest.get("macd_lift"),
                "rsi": latest.get("rsi"),
                "rsi_slope": latest.get("rsi_slope"),
                "adx": latest.get("adx"),
                "confidence_score": latest.get("confidence_score"),
                "tp1_shift": latest.get("tp1_shift"),
                "safu_good_but_zombie": int(is_zombie),
                "recovery_label": recovery_label,
                "status": status,
                "exit_time": exit_time,
                "pnl_pct": pnl
            }

            record.update(extract_trends(snapshots))
            missing = [k for k in REQUIRED_MODEL_FEATURES if k not in record or record[k] is None]
            if missing:
                print(f"⚠️ Missing fields: {missing} → Skipped.")
                continue

            fout.write(json.dumps(record) + "\n")

    print(f"\n✅ Saved recovery training data for {date_str} → {out_path.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="Date in YYYY-MM-DD format")
    args = parser.parse_args()
    build_daily_dataset(args.date)
