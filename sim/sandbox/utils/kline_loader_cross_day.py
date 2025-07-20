from pathlib import Path
SNAPSHOT_BASE = Path("/home/signal/market7/data/snapshots")
def load_forward_klines_cross_days(symbol, tf, start_time, max_days=30):
    from datetime import datetime
    import pandas as pd

    all_klines = []
    start_ms = int(start_time)
    symbol = symbol.upper()

    if not SNAPSHOT_BASE.exists():
        print(f"[WARN] Snapshot folder {SNAPSHOT_BASE} missing")
        return []

    start_date = datetime.utcfromtimestamp(start_time / 1000).date()

    for folder in sorted(SNAPSHOT_BASE.iterdir()):
        if not folder.is_dir():
            continue
        try:
            folder_date = datetime.strptime(folder.name, "%Y-%m-%d").date()
        except ValueError:
            continue

        file_path = folder / f"{symbol}_{tf}_klines.json"
        if not file_path.exists():
            continue
        try:
            df = pd.read_json(file_path, orient="values")
            df.columns = [
                "timestamp", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "num_trades",
                "taker_buy_base", "taker_buy_quote", "ignore"
            ]
            df = df[df["timestamp"] >= start_ms]
            if not df.empty:
                all_klines.append(df)
        except Exception as e:
            print(f"[WARN] Failed to load {file_path}: {e}")
            continue

    if all_klines:
        combined_df = pd.concat(all_klines, ignore_index=True)
        combined_df = combined_df[combined_df["timestamp"] >= start_ms]
        return combined_df.to_dict(orient="records")
    else:
        return []
