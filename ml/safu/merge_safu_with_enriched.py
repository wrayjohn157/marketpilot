import os
import json
from tqdm import tqdm

SAFU_INPUT = "/home/signal/market7/ml/datasets/safu_analysis/merged_safu_dca.jsonl"
ENRICHED_ROOT = "/home/signal/market7/ml/datasets/enriched"
OUTPUT_PATH = "/home/signal/market7/ml/datasets/safu_analysis/labeled_safu_dca.jsonl"

def load_enriched_trades():
    enriched_by_id = {}
    for root, _, files in os.walk(ENRICHED_ROOT):
        for fname in files:
            if not fname.endswith(".jsonl"):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath) as f:
                for line in f:
                    try:
                        j = json.loads(line)
                        deal_id = j.get("deal_id") or j.get("trade", {}).get("trade_id")
                        if deal_id:
                            enriched_by_id[deal_id] = {
                                "final_pnl_pct": j.get("pnl_pct") or j.get("trade", {}).get("pnl_pct"),
                                "status": j.get("status") or j.get("trade", {}).get("status")
                            }
                    except:
                        continue
    return enriched_by_id

def main():
    print("📥 Loading enriched trade data...")
    enriched = load_enriched_trades()
    print(f"✅ Loaded {len(enriched)} enriched trade outcomes")

    labeled = []
    with open(SAFU_INPUT) as f:
        for line in tqdm(f, desc="🔗 Merging SAFU with outcomes"):
            row = json.loads(line)
            deal_id = row["deal_id"]
            outcome = enriched.get(deal_id)
            if not outcome:
                continue

            row.update(outcome)
            row["safu_label"] = "recovered" if (outcome["final_pnl_pct"] or 0) > 0 else "not_recovered"
            labeled.append(row)

    print(f"✅ Writing {len(labeled)} labeled snapshots to: {OUTPUT_PATH}")
    with open(OUTPUT_PATH, "w") as out:
        for row in labeled:
            out.write(json.dumps(row) + "\n")

if __name__ == "__main__":
    main()
