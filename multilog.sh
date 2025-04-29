#!/bin/bash
trap '' SIGTERM

multitail \
  -n 50 -l "sudo journalctl -u fork_safu_monitor.service -f" \
  -n 50 -l "sudo journalctl -u generate_tv_screener_ratings.service -f" \
  -n 50 -l "sudo journalctl -u fork_runner.service -f" \
  -n 50 -l "sudo journalctl -u market7.service -f" \
  -n 50 -l "sudo journalctl -u rolling_indicators_market7.service -f" \
  -n 50 -l "sudo journalctl -u rolling_klines_market7.service -f" \
  -n 50 -l "sudo journalctl -u tv_kicker_market7.service -f"
