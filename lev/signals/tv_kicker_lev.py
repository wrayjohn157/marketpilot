from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import json, logging, argparse

import yaml

#!/usr/bin/env python3
from
 pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def load_candidates(path: Path):
    if not path.exists():
        logging.error(f"[tv_kicker] missing candidates: {path}")
        return []
    txt = path.read_text().strip()
    if not txt:
        return []
    try:
        if txt[0] == '[':
            return json.loads(txt)
        # jsonl fallback
        return [json.loads(line) for line in txt.splitlines() if line.strip()]
    except Exception as e:
        logging.error(f"[tv_kicker] parse error {path}: {e}")
        return []

def load_tv(path: Path):
    if not path.exists():
        logging.warning(f"[tv_kicker] tv file not found: {path}")
        return {}
    try:
        data = json.loads(path.read_text())
        # normalize to {SYMBOL: tag_15m}
        out = {}
        for k, v in data.items():
            tag = (v.get("15m") if isinstance(v, dict) else None) or "neutral"
            out[k.upper()] = str(tag).lower()
        return out
    except Exception as e:
        logging.warning(f"[tv_kicker] bad tv json {path}: {e}")
        return {}

def main() -> Any:
    ap = argparse.ArgumentParser("TV kicker for lev (side-aware)")
    ap.add_argument("--side", choices=["long","short"], required=True)
    ap.add_argument("--candidates", required=True,
                    help="e.g. lev/data/fork_backtest_candidates_long.json")
    ap.add_argument("--config", default="lev/signals/config/tv_screener_config.yaml")
    ap.add_argument("--tv-file", default=None, help="override TV screener source file")
    ap.add_argument("--output", default=None,
                    help="e.g. lev/data/fork_tv_adjusted_long.jsonl")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text()).get("tv_screener", {})
    weights_long  = cfg.get("weights_long" , {})
    weights_short = cfg.get("weights_short", {})
    thr_long  = float(cfg.get("score_threshold_long" , 0.45))
    thr_short = float(cfg.get("score_threshold_short", 0.35))
    tv_file = Path(args.tv_file or cfg.get("default_tv_file", ""))

    weights = weights_long if args.side == "long" else weights_short
    min_pass = thr_long if args.side == "long" else thr_short

    cands_path = Path(args.candidates)
    cands = load_candidates(cands_path)
    tv_tags = load_tv(tv_file)

    out_path = Path(args.output or cands_path.with_name(
        cands_path.stem.replace("candidates", "tv_adjusted") + f"_{args.side}.jsonl"
    ))
    out_path.parent.mkdir(parents=True, exist_ok=True)

    today_dir = out_path.parent / datetime.utcnow().strftime("%Y-%m-%d")
    today_dir.mkdir(parents=True, exist_ok=True)
    history_file = today_dir / f"tv_kicker_{args.side}.jsonl"

    passed = 0
    with out_path.open("w") as f_out, history_file.open("a") as f_log:
        for it in cands:
            sym = str(it.get("symbol","")).upper()
            base = float(it.get("score", 0.0))
            tag  = tv_tags.get(sym, "neutral")
            bump = float(weights.get(tag, 0.0))
            adj  = round(base + bump, 4)
            now  = datetime.utcnow()
            row = {
                "symbol": sym, "prev_score": base, "tv_tag": tag,
                "tv_kicker": bump, "adjusted_score": adj,
                "timestamp": int(now.timestamp()*1000), "ts_iso": now.isoformat() + "Z",
                "side": args.side, "pass": adj >= min_pass
            }
            f_log.write(json.dumps(row) + "\n")
            if row["pass"]:
                f_out.write(json.dumps(row) + "\n")
                passed += 1

            icon = "✅" if row["pass"] else ("🟢" if adj > base else "🔻" if adj < base else "➖")
            logging.info(f"{icon} {sym} | {base:.4f} → {adj:.4f} | TV: {tag}")

    logging.info(f"[tv_kicker] saved {passed} to {out_path}")

if __name__ == "__main__":
    main()
