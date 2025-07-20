import json
import pandas as pd

INFILE = "/home/signal/market7/ml/datasets/safu_analysis/labeled_safu_dca.jsonl"

def main():
    rows = []
    with open(INFILE) as f:
        for line in f:
            row = json.loads(line)
            rows.append({
                "deal_id": row["deal_id"],
                "symbol": row["symbol"],
                "safu_score": row["safu_score"],
                "drawdown_pct": row["drawdown_pct"],
                "tp1_shift": row.get("tp1_shift"),
                "be_improvement": row.get("be_improvement"),
                "confidence_score": row.get("confidence_score"),
                "recovery_odds": row.get("recovery_odds"),
                "btc_status": row["btc_status"],
                "macd_lift": row.get("macd_lift"),
                "rsi_slope": row.get("rsi_slope"),
                "final_pnl_pct": row.get("final_pnl_pct"),
                "status": row.get("status"),
                "safu_label": row.get("safu_label")
            })

    df = pd.DataFrame(rows)
    print("🔍 Label balance:\n", df["safu_label"].value_counts(), "\n")

    print("📊 SAFU Score (mean):")
    print(df.groupby("safu_label")["safu_score"].mean(), "\n")

    print("📊 Drawdown % (mean):")
    print(df.groupby("safu_label")["drawdown_pct"].mean(), "\n")

    print("📊 Confidence Score (mean):")
    print(df.groupby("safu_label")["confidence_score"].mean(), "\n")

    print("📊 Recovery Odds (mean):")
    print(df.groupby("safu_label")["recovery_odds"].mean(), "\n")

    print("📊 TP1 Shift % (mean):")
    print(df.groupby("safu_label")["tp1_shift"].mean(), "\n")

    print("📊 BE Improvement % (mean):")
    print(df.groupby("safu_label")["be_improvement"].mean(), "\n")

if __name__ == "__main__":
    main()
