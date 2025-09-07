#!/usr/bin/env python3

import json

from dca.utils.entry_utils import get_live_3c_trades


def main():
    active_trades = get_live_3c_trades()
    print(f"✅ Pulled {len(active_trades)} active trades:\n")
    print(json.dumps(active_trades, indent=2))


if __name__ == "__main__":
    main()
