from typing import Dict, List, Optional, Any, Union, Tuple
import json

import argparse

#!/usr/bin/env python3
from
 pathlib import Path

# Defaults
SPOT_LIST_DEFAULT = Path("/home/signal/market7/data/filtered_pairs.json")
PERPS_FILE_DEFAULT = Path("/home/signal/market7/lev/data/perps/filtered_perps.json")
OUT_FILE_DEFAULT = Path("/home/signal/market7/lev/data/perps/spot_perp_intersection.json")

# Recognized perp quote suffixes (when deriving base from id if 'base' missing)
QUOTE_SUFFIXES = ("USDT", "USDC", "USD", "FDUSD", "BUSD", "TUSD")

def load_spot_bases(path: Path) -> set[str]:
    with open(path, "r") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Spot list should be a JSON array of bases, got: {type(data)}")
    # Ensure strings and upper-case
    bases = {str(x).upper() for x in data}
    # Remove obvious non-bases just in case
    bases.discard("USDT")
    bases.discard("USDC")
    bases.discard("USD")
    return bases

def load_perps_symbols(path: Path) -> list[dict]:
    """
    Accepts:
      - a list of symbol dicts
      - or an object with 'symbols': [ ... ] (as in filtered_perps.json)
    Returns the list of dicts. Each dict should have 'id' and 'base' ideally.
    """
    with open(path, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        symbols = data
    elif isinstance(data, dict) and "symbols" in data and isinstance(data["symbols"], list):
        symbols = data["symbols"]
        print(f"Using perps file: {path}")
        print(f"Perp file is an object. Top-level keys: {list(data.keys())}")
    else:
        raise ValueError("Perps file must be a list of objects or an object with 'symbols' list.")

    # Normalize minimal required fields and try to derive base if missing.
    norm = []
    for d in symbols:
        if not isinstance(d, dict):
            continue
        obj = dict(d)  # shallow copy
        if "id" not in obj:
            continue
        if "base" not in obj or not obj["base"]:
            obj["base"] = derive_base_from_id(obj["id"])
        obj["base"] = str(obj["base"]).upper()
        norm.append(obj)
    return norm

def derive_base_from_id(sym_id: str) -> str:
    s = str(sym_id).upper()
    for suf in QUOTE_SUFFIXES:
        if s.endswith(suf):
            return s[: -len(suf)]
    return s

def normalized_for_match(base: str) -> str:
    """
    Normalize perps base for matching to spot bases:
    - Treat '1000PEPE' as 'PEPE', '1000SHIB' as 'SHIB'
    - Keep tokens like '1INCH' as-is (avoid over-stripping)
    Only strip exact leading '1000' or '1000000' if what's after is all letters.
    """
    b = base.upper()
    for pref in ("1000000", "1000"):
        if b.startswith(pref):
            tail = b[len(pref):]
            if tail.isalpha() and len(tail) >= 2:
                return tail
    # One-off special where Binance uses "1MBABYDOGE"
    if b.startswith("1MBABYDOGE"):
        return "BABYDOGE"
    return b

def main() -> Any:
    ap = argparse.ArgumentParser(description="Build spot∩perp list while preserving perp metadata.")
    ap.add_argument("--spot", type=Path, default=SPOT_LIST_DEFAULT,
                    help=f"Path to spot filtered bases (default: {SPOT_LIST_DEFAULT})")
    ap.add_argument("--perps", type=Path, default=PERPS_FILE_DEFAULT,
                    help=f"Path to perps file (default: {PERPS_FILE_DEFAULT})")
    ap.add_argument("--out", type=Path, default=OUT_FILE_DEFAULT,
                    help=f"Where to write intersection (default: {OUT_FILE_DEFAULT})")
    args = ap.parse_args()

    # Load spot bases
    spot_bases = load_spot_bases(args.spot)
    print(f"Loaded spot bases: {len(spot_bases)}")

    # Load perps symbols
    perps = load_perps_symbols(args.perps)
    print(f"Loaded perps    : {len(perps)}", end=" ")

    # Build set of uniquely matched “preferred bases” for stats
    unique_pref = set()
    for p in perps:
        b = p.get("base") or derive_base_from_id(p.get("id", ""))
        unique_pref.add(normalized_for_match(str(b)))
    print(f"(unique preferred bases: {len(unique_pref)})")

    # Compute intersection: keep full perp objects where normalized base ∈ spot_bases
    intersection = []
    overlap_bases = set()
    for obj in perps:
        raw_base = obj.get("base") or derive_base_from_id(obj.get("id", ""))
        nb = normalized_for_match(str(raw_base))
        if nb in spot_bases:
            intersection.append(obj)
            overlap_bases.add(nb)

    print(f"Overlap bases   : {len(overlap_bases)}")

    # Write full objects list (preserving metadata)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(intersection, f, indent=2)
    print(f"✅ Wrote {len(intersection)} symbols -> {args.out}")

if __name__ == "__main__":
    main()
