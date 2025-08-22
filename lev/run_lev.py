#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import yaml
import logging
import re
import random
import sys
import textwrap
import shutil
from pathlib import Path
from datetime import datetime

from config.config_loader import PATHS
from lev.exchange import futures_adapter as fa
from lev.modules.lev_decision_engine import should_add_to_position

# reuse your existing utils
from dca.utils.entry_utils import get_latest_indicators
from dca.utils.recovery_odds_utils import predict_recovery_odds
from dca.utils.recovery_confidence_utils import predict_confidence_score
from dca.utils.btc_filter import get_btc_status

# ------------------------
# Paths / Logging
# ------------------------
BASE = PATHS["base"]
LOG_DIR = BASE / "lev" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
CFG_PATH = Path("config/leverage_config.yaml")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("lev")

# Load spot bases (used to resolve snapshot keys like "1INCH" or "1000SATS")
def _load_spot_bases() -> set[str]:
    try:
        fp = PATHS.get("filtered_pairs")
        if fp:
            data = json.loads(Path(fp).read_text())
            if isinstance(data, list):
                return set(str(x).upper() for x in data)
    except Exception as e:
        log.warning(f"Could not load spot bases from PATHS['filtered_pairs']: {e}")
    return set()



SPOT_BASES: set[str] = _load_spot_bases()

# --- External signal loaders (fork runner + TV runner) -----------------------
def _load_json_map(path: str | Path) -> dict:
    """
    Load a JSON/JSONL file that is either:
      - { "BIO": {...}, "BTC": {...}, ... }
      - [ {"symbol":"BIO", ...}, ... ] or [ {"snap_symbol":"BIO", ...}, ... ]
      - JSON Lines (.jsonl): one JSON object per line
    Returns a dict keyed by an uppercased, normalized snap symbol.
    Normalization:
      - Drop common quote suffixes (USDT/USDC/USD/BUSD)
      - Strip numeric multipliers at the front (e.g. 1000PEPE -> PEPE)
    """
    def _norm_sym(raw: str) -> str:
        s = str(raw or "").strip().upper()
        for suf in ("USDT", "USDC", "USD", "BUSD"):
            if s.endswith(suf):
                s = s[: -len(suf)]
                break
        # if it's an actual spot base like 1000SATS or 1INCH keep it, otherwise strip leading digits
        if SPOT_BASES and s in SPOT_BASES:
            return s
        stripped = re.sub(r"^\d+", "", s)
        return stripped or s

    p = Path(path)
    if not p.exists():
        return {}

    txt = p.read_text().strip()
    out: dict = {}

    # First try: standard JSON
    try:
        data = json.loads(txt)
        if isinstance(data, dict):
            # assume keys are symbols
            for k, v in data.items():
                out[_norm_sym(k)] = v
            return out
        elif isinstance(data, list):
            for row in data:
                if not isinstance(row, dict):
                    continue
                key = (
                    row.get("snap_symbol")
                    or row.get("symbol")
                    or row.get("sym")
                    or row.get("s")
                    or row.get("base")
                    or row.get("ticker")
                    or row.get("pair")
                    or row.get("inst")
                    or row.get("name")
                    or ""
                )
                key = _norm_sym(key)
                if key:
                    out[key] = row
            return out
    except Exception:
        # fall through to JSONL attempt
        pass

    # Second try: JSON Lines (jsonl)
    out = {}
    for ln in txt.splitlines():
        s = ln.strip()
        if not s or not (s.startswith("{") and s.endswith("}")):
            continue
        try:
            row = json.loads(s)
        except Exception:
            continue
        if not isinstance(row, dict):
            continue
        key = (
            row.get("snap_symbol")
            or row.get("symbol")
            or row.get("sym")
            or row.get("s")
            or row.get("base")
            or row.get("ticker")
            or row.get("pair")
            or row.get("inst")
            or row.get("name")
            or ""
        )
        key = _norm_sym(key)
        if key:
            out[key] = row
    return out


def _fork_value_for(sym: str, fork_map: dict) -> tuple[float | None, str | None]:
    """
    Given a snap symbol (e.g., 'BIO'), return (score, decision) from fork runner map if present.
    Expect either fields 'score' and 'decision' OR any numeric 'score' field;
    we normalize decision to 'long'|'short'|'flat' when possible.
    """
    row = fork_map.get(sym.upper())
    if not isinstance(row, dict):
        return None, None
    # score field could be 'score' or 'fork_score'
    score = row.get("score")
    if score is None:
        score = row.get("fork_score")
    try:
        score_f = float(score) if score is not None else None
    except Exception:
        score_f = None

    # normalize decision
    dec_raw = (
        row.get("decision")
        or row.get("signal")
        or row.get("side")
        or row.get("dir")
        or row.get("action")
    )
    dec_norm = None
    if isinstance(dec_raw, str):
        d = dec_raw.strip().lower()
        if any(k in d for k in ("long", "buy", "up", "bull")):
            dec_norm = "long"
        elif any(k in d for k in ("short", "sell", "down", "bear")):
            dec_norm = "short"
        else:
            dec_norm = "flat"
    elif isinstance(dec_raw, bool):
        # tolerate boolean conventions from some forks
        dec_norm = "long" if dec_raw else "short"
    elif isinstance(dec_raw, (int, float)):
        # numeric polarity convention
        if float(dec_raw) > 0:
            dec_norm = "long"
        elif float(dec_raw) < 0:
            dec_norm = "short"

    return score_f, dec_norm


def _tv_value_for(sym: str, tv_map: dict) -> tuple[str | None, float | None]:
    """
    Given a snap symbol, return (tv_signal, tv_score) if present.
    Accepts shapes like:
      {'signal':'buy'|'sell'|'neutral', 'score': float}
      {'tv':'strong_sell', ...}
      {'tv_tag':'buy'|'sell'|'neutral', 'adjusted_score': float}
    """
    row = tv_map.get(sym.upper())
    if not isinstance(row, dict):
        return None, None

    # Accept multiple possible fields for the textual signal
    sig = (
        row.get("signal")
        or row.get("tv")
        or row.get("tv_signal")
        or row.get("tv_tag")
        or row.get("decision")
        or row.get("rating")
    )
    if isinstance(sig, str):
        sig_norm = sig.strip().lower().replace("strong_", "")
    else:
        sig_norm = None

    # Accept several numeric score fields
    sc = (
        row.get("score")
        or row.get("tv_score")
        or row.get("adjusted_score")
        or row.get("value")
        or row.get("rating_value")
    )
    try:
        sc_f = float(sc) if sc is not None else None
    except Exception:
        sc_f = None

    return sig_norm, sc_f

# --- Pretty printing helpers -------------------------------------------------
CHECK_OK = "✅"
CHECK_NO = "❌"


def _fmt_bool(val: bool) -> str:
    return CHECK_OK if bool(val) else CHECK_NO


def _fmt_num(val, nd=3):
    try:
        return f"{float(val):.{nd}f}"
    except Exception:
        return "-"


def _detect_terminal_support() -> bool:
    """Best-effort: enable pretty output if stdout is a TTY and TERM is not dumb."""
    try:
        return sys.stdout.isatty() and (shutil.get_terminal_size().columns > 0)
    except Exception:
        return False


def _pretty_decision_block(*,
                           symbol: str,
                           snap_symbol: str,
                           side: str,
                           decision: bool,
                           reason: str,
                           next_notional: float,
                           inds: dict,
                           rec_odds: float,
                           confidence: float) -> str:
    """
    Produce a human‑readable, multi‑line summary similar to the fork runner output.
    We only rely on indicator values that exist; missing ones are skipped gracefully.
    """
    lines = []
    header_icon = CHECK_OK if decision else CHECK_NO
    score_txt = f"odds={_fmt_num(rec_odds, 3)} | conf={_fmt_num(confidence, 3)} | nxt=${_fmt_num(next_notional, 2)}"
    lines.append(f"{header_icon} {symbol} [{side}] | {snap_symbol} | {reason} | {score_txt}")

    # one-line external context
    ctx_bits = []
    if inds.get("_fork_score") is not None:
        fd = inds.get("_fork_decision")
        ctx_bits.append(f"FORK:{_fmt_num(inds.get('_fork_score'))}{('/'+fd.upper()) if fd else ''}")
    if inds.get("_tv_signal"):
        tvb = inds.get("_tv_signal").upper()
        if inds.get("_tv_score") is not None:
            tvb += f"({_fmt_num(inds.get('_tv_score'))})"
        ctx_bits.append(f"TV:{tvb}")
    if ctx_bits:
        lines.append("    [" + "  |  ".join(ctx_bits) + "]")

    # Known indicators we may have; print if present. Keep names human‑friendly.
    # We don't infer complex booleans here—just show values so it's truthful.
    pretty_keys = [
        ("RSI", "rsi"),
        ("MACD Histogram", "macd_histogram"),
        ("ADX", "adx"),
        ("Stoch RSI K", "stoch_rsi_k"),
        ("Stoch RSI D", "stoch_rsi_d"),
        ("EMA Fast", "ema_fast"),
        ("EMA Slow", "ema_slow"),
        ("Price", "latest_close"),
        ("Vol(24h)", "volume_24h"),
        ("Mean Reversion Score", "mean_reversion_score"),
    ]

    for label, key in pretty_keys:
        if key in inds and inds.get(key) is not None:
            lines.append(f"    • {label:<24}: {_fmt_num(inds.get(key))}")

    # A couple of simple, clearly-defined booleans that are safe to derive
    if "macd_histogram" in inds:
        lines.append(f"    • MACD < 0                 : {_fmt_bool(inds['macd_histogram'] < 0)}")
    if "rsi" in inds:
        lines.append(f"    • RSI < 30 (oversold)      : {_fmt_bool(inds['rsi'] < 30)}")
        lines.append(f"    • RSI > 70 (overbought)    : {_fmt_bool(inds['rsi'] > 70)}")

    # External signal context (if injected into inds)
    if inds.get("_fork_score") is not None:
        lines.append(f"    • Fork Score               : {_fmt_num(inds.get('_fork_score'))}")
    if inds.get("_fork_decision"):
        lines.append(f"    • Fork Decision            : {str(inds.get('_fork_decision')).upper()}")
    if inds.get("_tv_signal"):
        lines.append(f"    • TV Signal                : {str(inds.get('_tv_signal')).upper()}")
    if inds.get("_tv_score") is not None:
        lines.append(f"    • TV Score                 : {_fmt_num(inds.get('_tv_score'))}")

    return "\n".join(lines)


# ------------------------
# Helpers
# ------------------------
def load_cfg():
    return yaml.safe_load(CFG_PATH.read_text())


def write_log(entry: dict):
    p = LOG_DIR / f"{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
    with open(p, "a") as f:
        f.write(json.dumps(entry) + "\n")



def _base_symbol(sym: str) -> str:
    """
    Convert exchange pair code to your snapshot base name.
    e.g., 'BTCUSDT' -> 'BTC', 'ETHUSD' -> 'ETH'
    """
    s = sym.upper()
    for suffix in ("USDT", "USD", "USDC", "BUSD"):
        if s.endswith(suffix):
            return s[: -len(suffix)]
    return s


# Map a futures symbol to the snapshot base used by spot snapshots.
def _snapshot_base_for(sym: str) -> str:
    """
    Map a futures symbol to the snapshot base used by spot snapshots.
    Examples:
      - BTCUSDT -> BTC
      - ETHUSD  -> ETH
      - 1000PEPEUSDT -> PEPE (strip numeric multiplier prefix)
      - 1000BONKUSDT -> BONK
      - 1000SATSUSDT -> 1000SATS (kept because it's an actual spot base)
      - 1INCHUSDT    -> 1INCH (kept because it's an actual spot base)
    Strategy:
      1) Derive base by removing the quote suffix.
      2) If base is in SPOT_BASES, return it.
      3) Else strip leading digits and return the stripped version if present in SPOT_BASES.
      4) Fallback to the stripped (or original) base.
    """
    base = _base_symbol(sym)
    b = base.upper()
    # If exact base exists in spot snapshot universe, use it as-is
    if SPOT_BASES and b in SPOT_BASES:
        return b
    # Otherwise, strip any leading digits (e.g., 1000PEPE -> PEPE)
    stripped = re.sub(r"^\d+", "", b)
    if SPOT_BASES and stripped in SPOT_BASES:
        return stripped
    return stripped or b


def _normalize_symbol_to_perp(sym: str) -> str:
    """
    Ensure we return a futures-style symbol like 'BTCUSDT'.
    If the token doesn't end with a known quote, default to 'USDT'.
    """
    s = sym.strip().upper()
    if s.endswith(("USDT", "USDC", "USD", "BUSD")):
        return s
    return s + "USDT"


def load_symbols_from_file(path: str) -> list[str]:
    """
    Load symbols from a file specified via --symbols-file.
    Accepts:
      - JSON array of strings: ["BTCUSDT", "ETHUSDT", ...]
      - JSON array of dicts with "id" or ("base","quote"): [{"id":"BTCUSDT"}, ...]
      - Plain text, one symbol per line
      - JSON object with "symbols": [...]
    Returns a de-duplicated list of normalized symbols like 'BTCUSDT'.
    """
    fp = Path(path)
    if not fp.exists():
        raise FileNotFoundError(f"symbols file not found: {fp}")

    try:
        data = json.loads(fp.read_text())
        # Case: {"symbols": [...]}
        if isinstance(data, dict) and "symbols" in data:
            items = data["symbols"]
        else:
            items = data
        # items could be list[str] or list[dict]
        symbols: list[str] = []
        if isinstance(items, list):
            for it in items:
                if isinstance(it, str):
                    symbols.append(_normalize_symbol_to_perp(it))
                elif isinstance(it, dict):
                    if "id" in it and isinstance(it["id"], str):
                        symbols.append(_normalize_symbol_to_perp(it["id"]))
                    elif "base" in it and "quote" in it:
                        symbols.append(_normalize_symbol_to_perp(it["base"] + it["quote"]))
        else:
            log.warning(f"--symbols-file JSON content not a list/dict, falling back to line parsing.")
            raise ValueError("bad json shape")
    except Exception:
        # Fallback: newline-separated file
        lines = [ln for ln in fp.read_text().splitlines() if ln.strip()]
        symbols = [_normalize_symbol_to_perp(ln) for ln in lines]

    # Dedup & sort for stability
    uniq = sorted(set(symbols))
    log.info(f"Loaded {len(uniq)} symbols from file: {fp}")
    return uniq


def load_available_perps() -> list[str]:
    """
    Best-effort load of Binance USDT-M perps (ids) to use as a fallback when
    neither --symbols/--symbols-file nor cfg['symbols'] is provided.
    """
    perps_path = Path("/home/signal/market7/lev/data/perps/binance_usdtm_perps.json")
    if not perps_path.exists():
        log.warning("Could not find binance_usdtm_perps.json for fallback symbols.")
        return []
    try:
        perps = json.loads(perps_path.read_text())
        # file may be a list of dicts or an object with 'perps'
        if isinstance(perps, dict) and "perps" in perps:
            perps = perps["perps"]
        ids = [d["id"] for d in perps if isinstance(d, dict) and d.get("status") == "TRADING" and "id" in d]
        return sorted(set(ids))
    except Exception as e:
        log.warning(f"Failed to parse {perps_path}: {e}")
        return []


# ------------------------
# Main logic
# ------------------------
def run_once(args):
    cfg = load_cfg()
    dry_run = args.dry_run if args.dry_run is not None else bool(cfg.get("dry_run", False))

    # Optional external signals (paths via CLI or config)
    fork_file = getattr(args, "fork_file", None) or cfg.get("fork_file")
    tv_file = getattr(args, "tv_file", None) or cfg.get("tv_file")
    fork_map = _load_json_map(fork_file) if fork_file else {}
    tv_map = _load_json_map(tv_file) if tv_file else {}
    log.info(f"External signals loaded: fork={len(fork_map)} from {fork_file} | tv={len(tv_map)} from {tv_file}")

    # Gating defaults (can be overridden in config)
    fork_gate = getattr(args, "fork_gate", None)
    if fork_gate is None:
        fork_gate = cfg.get("fork_gate", True)
    tv_gate = getattr(args, "tv_gate", None)
    if tv_gate is None:
        tv_gate = cfg.get("tv_gate", True)
    # For fork: treat higher score as more bullish.
    fork_min_long = float(cfg.get("fork_min_long", 0.60))   # require >= for longs
    fork_max_short = float(cfg.get("fork_max_short", 0.40)) # require <= for shorts (bearish)
    # TV text signals that imply bullish/bearish
    tv_bull = set(cfg.get("tv_bull", ["buy"]))
    tv_bear = set(cfg.get("tv_bear", ["sell"]))

    # Load symbols in this priority:
    # 1) --symbols-file
    # 2) --symbols from CLI
    # 3) cfg['symbols']
    # 4) fallback to available perps (binance_usdtm_perps.json) or ['BTCUSDT']
    symbols: list[str] = []
    if args.symbols_file:
        symbols = load_symbols_from_file(args.symbols_file)
    elif args.symbols:
        symbols = [_normalize_symbol_to_perp(s) for s in args.symbols]
    elif cfg.get("symbols"):
        symbols = [_normalize_symbol_to_perp(s) for s in cfg["symbols"]]
    else:
        fallback = load_available_perps()
        symbols = fallback if fallback else ["BTCUSDT"]

    # Apply optional include/exclude regex filters
    before_filter = len(symbols)
    if getattr(args, "include", None):
        try:
            inc_re = re.compile(args.include, re.IGNORECASE)
            symbols = [s for s in symbols if inc_re.search(s)]
        except re.error as e:
            raise SystemExit(f"--include regex error: {e}")
    if getattr(args, "exclude", None):
        try:
            exc_re = re.compile(args.exclude, re.IGNORECASE)
            symbols = [s for s in symbols if not exc_re.search(s)]
        except re.error as e:
            raise SystemExit(f"--exclude regex error: {e}")
    after_filter = len(symbols)

    # Optional: shuffle and/or cap how many symbols we process
    if getattr(args, "shuffle", False):
        random.shuffle(symbols)
    if getattr(args, "limit", None):
        symbols = symbols[: args.limit]
    log.info(
        f"Processing {len(symbols)} symbols (start={before_filter}, include={bool(getattr(args,'include',None))}, exclude={bool(getattr(args,'exclude',None))}, shuffle={getattr(args,'shuffle', False)}, limit={getattr(args,'limit', None)})"
    )

    side = args.side.lower()
    if side not in ("long", "short", "both"):
        raise SystemExit("--side must be long|short|both")

    ex = fa.init_exchange({"hedged_mode": cfg.get("hedged_mode", True)})
    acct_notional = fa.account_notional_exposure(ex)
    if acct_notional > cfg.get("max_account_notional", 1e9):
        log.warning(f"Account notional {acct_notional} exceeds cap; exiting.")
        return

    btc_status = get_btc_status({})  # adapt to your actual signature if needed

    decisions_made = 0
    orders_attempted = 0
    orders_placed = 0

    for sym in symbols:
        # leverage set once per symbol
        fa.set_symbol_leverage(ex, sym, cfg.get("default_symbol_leverage", cfg.get("max_leverage", 5)))

        # map to snapshot base symbol (BTCUSDT -> BTC)
        snap_sym = _snapshot_base_for(sym)

        # pull indicators from your rolling snapshots
        inds = get_latest_indicators(snap_sym) or {}
        if not inds:
            log.warning(
                f"[lev] No indicators found for {snap_sym} (from {sym}); "
                f"check /data/snapshots/<DATE> naming. Using price-only fallback."
            )
            # minimal fallback so liq buffer math can still run
            try:
                inds = {"latest_close": fa._ticker_price(ex, sym)}  # type: ignore
            except Exception:
                inds = {}

        # Attach external signals (if available) to inds for pretty print and engine usage.
        f_score, f_dec = _fork_value_for(snap_sym, fork_map) if fork_map else (None, None)
        tv_sig, tv_val = _tv_value_for(snap_sym, tv_map) if tv_map else (None, None)
        if f_score is not None:
            inds["_fork_score"] = f_score
        if f_dec:
            inds["_fork_decision"] = f_dec
        if tv_sig:
            inds["_tv_signal"] = tv_sig
        if tv_val is not None:
            inds["_tv_score"] = tv_val

        rec_odds = predict_recovery_odds(inds) or 0.0
        conf = predict_confidence_score(inds) or 0.0
        pos = fa.get_positions(ex, sym)
        liq = fa.get_liquidation_price(ex, sym, pos)

        sides = ["long", "short"] if side == "both" else [side]
        for s in sides:
            allow = cfg.get("allow_long", True) if s == "long" else cfg.get("allow_short", True)
            if not allow:
                continue

            # Pre-filter using fork/tv if configured
            if fork_gate and f_score is not None:
                if s == "long" and f_score < fork_min_long:
                    reason = f"fork_gate_low({f_score:.3f}<{fork_min_long})"
                    decision, next_notional = False, 0.0
                    # emit pretty/log and continue to next side
                    if getattr(args, "pretty", False):
                        pretty = _pretty_decision_block(
                            symbol=sym, snap_symbol=snap_sym, side=s,
                            decision=decision, reason=reason, next_notional=next_notional,
                            inds=inds, rec_odds=0.0, confidence=0.0
                        )
                        log.info("\n" + pretty)
                    log_entry = {
                        "t": datetime.utcnow().isoformat(),
                        "symbol": sym, "snap_symbol": snap_sym, "side": s,
                        "decision": decision, "reason": reason, "next_notional": next_notional,
                        "inds_keys": list(inds.keys()),
                        "rec_odds": 0.0, "confidence": 0.0, "liq": None,
                        "acct_notional": 0.0, "dry_run": dry_run,
                    }
                    write_log(log_entry)
                    if getattr(args, "json_logs", False):
                        log.info(log_entry)
                    continue
                if s == "short" and f_score > fork_max_short:
                    reason = f"fork_gate_high({f_score:.3f}>{fork_max_short})"
                    decision, next_notional = False, 0.0
                    if getattr(args, "pretty", False):
                        pretty = _pretty_decision_block(
                            symbol=sym, snap_symbol=snap_sym, side=s,
                            decision=decision, reason=reason, next_notional=next_notional,
                            inds=inds, rec_odds=0.0, confidence=0.0
                        )
                        log.info("\n" + pretty)
                    log_entry = {
                        "t": datetime.utcnow().isoformat(),
                        "symbol": sym, "snap_symbol": snap_sym, "side": s,
                        "decision": decision, "reason": reason, "next_notional": next_notional,
                        "inds_keys": list(inds.keys()),
                        "rec_odds": 0.0, "confidence": 0.0, "liq": None,
                        "acct_notional": 0.0, "dry_run": dry_run,
                    }
                    write_log(log_entry)
                    if getattr(args, "json_logs", False):
                        log.info(log_entry)
                    continue

            if tv_gate and tv_sig:
                # Block contradictory TV signals
                if s == "long" and tv_sig in tv_bear:
                    reason = f"tv_gate_bear({tv_sig})"
                    decision, next_notional = False, 0.0
                    if getattr(args, "pretty", False):
                        pretty = _pretty_decision_block(
                            symbol=sym, snap_symbol=snap_sym, side=s,
                            decision=decision, reason=reason, next_notional=next_notional,
                            inds=inds, rec_odds=0.0, confidence=0.0
                        )
                        log.info("\n" + pretty)
                    log_entry = {
                        "t": datetime.utcnow().isoformat(),
                        "symbol": sym, "snap_symbol": snap_sym, "side": s,
                        "decision": decision, "reason": reason, "next_notional": next_notional,
                        "inds_keys": list(inds.keys()),
                        "rec_odds": 0.0, "confidence": 0.0, "liq": None,
                        "acct_notional": 0.0, "dry_run": dry_run,
                    }
                    write_log(log_entry)
                    if getattr(args, "json_logs", False):
                        log.info(log_entry)
                    continue
                if s == "short" and tv_sig in tv_bull:
                    reason = f"tv_gate_bull({tv_sig})"
                    decision, next_notional = False, 0.0
                    if getattr(args, "pretty", False):
                        pretty = _pretty_decision_block(
                            symbol=sym, snap_symbol=snap_sym, side=s,
                            decision=decision, reason=reason, next_notional=next_notional,
                            inds=inds, rec_odds=0.0, confidence=0.0
                        )
                        log.info("\n" + pretty)
                    log_entry = {
                        "t": datetime.utcnow().isoformat(),
                        "symbol": sym, "snap_symbol": snap_sym, "side": s,
                        "decision": decision, "reason": reason, "next_notional": next_notional,
                        "inds_keys": list(inds.keys()),
                        "rec_odds": 0.0, "confidence": 0.0, "liq": None,
                        "acct_notional": 0.0, "dry_run": dry_run,
                    }
                    write_log(log_entry)
                    if getattr(args, "json_logs", False):
                        log.info(log_entry)
                    continue

            decision, reason, next_notional = should_add_to_position(
                cfg=cfg,
                side=s,
                symbol=sym,
                position=pos,
                indicators=inds,
                btc_status=btc_status,
                recovery_odds=rec_odds,
                confidence=conf,
                liquidation_price=liq,
            )

            decisions_made += 1

            # Pretty console output if requested
            if getattr(args, "pretty", False):
                pretty = _pretty_decision_block(
                    symbol=sym,
                    snap_symbol=snap_sym,
                    side=s,
                    decision=decision,
                    reason=reason,
                    next_notional=next_notional,
                    inds=inds,
                    rec_odds=rec_odds,
                    confidence=conf,
                )
                log.info("\n" + pretty)

            log_entry = {
                "t": datetime.utcnow().isoformat(),
                "symbol": sym,
                "snap_symbol": snap_sym,
                "side": s,
                "decision": decision,
                "reason": reason,
                "next_notional": next_notional,
                "inds_keys": list(inds.keys()),
                "rec_odds": rec_odds,
                "confidence": conf,
                "liq": liq,
                "acct_notional": acct_notional,
                "dry_run": dry_run,
            }
            write_log(log_entry)
            if getattr(args, "json_logs", False):
                log.info(log_entry)

            if decision and next_notional > 0:
                orders_attempted += 1
                order = fa.place_order(
                    ex,
                    symbol=sym,
                    target_notional=next_notional,
                    side="buy" if s == "long" else "sell",
                    reduce_only=False,
                    dry_run=dry_run,
                )
                log.info({"placed_order": order})
                write_log({"placed_order": order, "symbol": sym, "side": s})
                # Consider any non-empty order dict as placed (even in dry-run for counting)
                orders_placed += 1

    log.info(
        f"Run summary: decisions={decisions_made}, attempts={orders_attempted}, counted_orders={orders_placed}, dry_run={dry_run}"
    )
    if getattr(args, "summary", False):
        print(
            json.dumps(
                {
                    "decisions": decisions_made,
                    "attempts": orders_attempted,
                    "orders": orders_placed,
                    "dry_run": dry_run,
                    "symbols": len(symbols),
                },
                indent=2,
            )
        )


def main():
    examples = textwrap.dedent(
        """
        Examples:
          # Dry-run over a curated list
          %(prog)s -f /home/signal/market7/lev/data/perps/spot_perp_intersection.json -S both --dry-run

          # Only coins containing "PEPE" or "DOGE", skip any 1000x multipliers
          %(prog)s -f spot_perp_intersection.json -S both --include '(PEPE|DOGE)' --exclude '^1000' --dry-run

          # Process a random 25-symbol slice for quick testing
          %(prog)s -f spot_perp_intersection.json -S both -r -n 25 --dry-run --summary
        """
    )
    ap = argparse.ArgumentParser(
        description="Leverage bot runner that decides adds per symbol using spot snapshots + filters.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=examples,
    )
    ap.add_argument("-s", "--symbols", nargs="*", help="Symbols like BTCUSDT ETHUSDT (overrides file & config)")
    ap.add_argument("-f", "--symbols-file", help="Path to symbols file: JSON array/list, {'symbols':[...]} or newline list")
    ap.add_argument("-S", "--side", default="long", choices=["long", "short", "both"], help="Which side(s) to evaluate")
    ap.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity (can repeat)")
    ap.add_argument("-q", "--quiet", action="store_true", help="Only warnings and errors")
    ap.add_argument("--dry-run", action="store_true", help="Skip placing orders")
    ap.add_argument("--once", action="store_true", help="Run once then exit")
    ap.add_argument("-i", "--include", help="Regex: only process symbols matching this pattern")
    ap.add_argument("-x", "--exclude", help="Regex: skip symbols matching this pattern")
    ap.add_argument("-n", "--limit", type=int, help="Process at most N symbols in this run")
    ap.add_argument("-r", "--shuffle", action="store_true", help="Shuffle symbols before processing (useful with --limit)")
    ap.add_argument("--summary", action="store_true", help="Print a compact JSON summary at the end")
    # Output style flags
    ap.add_argument("--pretty", action="store_true", default=_detect_terminal_support(), help="Print a human‑readable per‑symbol breakdown")
    ap.add_argument("--json-logs", action="store_true", help="Also emit JSON dict entries to stdout (in addition to file logs)")
    ap.add_argument("--version", action="version", version="lev-run 1.0")
    # External signals
    ap.add_argument("--fork-file", help="Path to fork runner JSON output to gate/annotate decisions")
    ap.add_argument("--tv-file", help="Path to TradingView runner JSON output to gate/annotate decisions")
    ap.add_argument("--no-fork-gate", dest="fork_gate", action="store_false", help="Disable fork-based gating")
    ap.add_argument("--no-tv-gate", dest="tv_gate", action="store_false", help="Disable TradingView-based gating")
    args = ap.parse_args()
    # Ensure gates default True unless explicitly disabled
    if not hasattr(args, "fork_gate"):
        args.fork_gate = True
    if not hasattr(args, "tv_gate"):
        args.tv_gate = True
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
        log.setLevel(logging.WARNING)
    elif args.verbose >= 2:
        logging.getLogger().setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
    elif args.verbose == 1:
        logging.getLogger().setLevel(logging.INFO)
        log.setLevel(logging.INFO)
    if getattr(args, 'fork_file', None) or getattr(args, 'tv_file', None):
        log.info(f"Using external signals → fork_gate={args.fork_gate} tv_gate={args.tv_gate} | fork_file={getattr(args,'fork_file', None)} | tv_file={getattr(args,'tv_file', None)}")
    try:
        run_once(args)
    except KeyboardInterrupt:
        log.warning("Interrupted by user (Ctrl+C). Exiting cleanly.")
        sys.exit(130)


if __name__ == "__main__":
    main()
