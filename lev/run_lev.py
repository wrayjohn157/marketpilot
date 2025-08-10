#!/usr/bin/env python3
import json, logging, yaml
from pathlib import Path
from datetime import datetime

from config.config_loader import PATHS  # reuse existing loader for base paths
from lev.exchange.futures_adapter import (
    init_exchange, get_positions, set_symbol_leverage, place_order, get_liquidation_price,
    account_notional_exposure
)
from lev.modules.lev_decision_engine import should_add_to_position
from dca.utils.entry_utils import get_latest_indicators  # reuse your indicator fetch
from dca.utils.recovery_odds_utils import predict_recovery_odds
from dca.utils.recovery_confidence_utils import predict_confidence_score
from dca.utils.btc_filter import get_btc_status

BASE = PATHS["base"]
LOG_DIR = BASE / "lev" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = Path("config/leverage_config.yaml")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("lev")

def load_cfg():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def write_log(entry: dict):
    p = LOG_DIR / f"{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
    with open(p, "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    cfg = load_cfg()
    if not cfg.get("enabled", False):
        log.info("Leverage pipeline disabled.")
        return

    ex = init_exchange(cfg)  # e.g., ccxt or your adapter wiring

    # Example loop: iterate symbols from your existing universe (reuse however you source these)
    symbols = ["BTCUSDT", "ETHUSDT"]  # TODO: replace with your real source
    btc_status = get_btc_status({})   # reuse your BTC market filter if desired

    acct_notional = account_notional_exposure(ex)
    if acct_notional > cfg["max_account_notional"]:
        log.warning(f"Account notional {acct_notional} exceeds cap; skipping.")
        return

    for sym in symbols:
        set_symbol_leverage(ex, sym, cfg.get("default_symbol_leverage", cfg["max_leverage"]))

        inds = get_latest_indicators(sym) or {}
        rec_odds = predict_recovery_odds(sym, inds) or 0.0
        conf = predict_confidence_score(sym, inds) or 0.0

        pos = get_positions(ex, sym)
        liq = get_liquidation_price(ex, sym, pos)

        decision, reason, next_notional = should_add_to_position(
            cfg=cfg,
            symbol=sym,
            position=pos,
            indicators=inds,
            btc_status=btc_status,
            recovery_odds=rec_odds,
            confidence=conf,
            liquidation_price=liq,
        )

        write_log({
            "t": datetime.utcnow().isoformat(),
            "symbol": sym,
            "decision": decision,
            "reason": reason,
            "next_notional": next_notional,
            "inds": inds,
            "rec_odds": rec_odds,
            "confidence": conf,
            "liq": liq,
            "acct_notional": acct_notional
        })

        if decision:
            place_order(ex, symbol=sym, target_notional=next_notional)

if __name__ == "__main__":
    main()
