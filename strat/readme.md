	•	Uses load_strategy_config() to inject strategy params dynamically.

	•	✅ --strategy support for loading from /live/strat/config
	•	✅ load_strategy_config() integration
	•	✅ Full fallback to main config
	•	✅ Confidence override protection using min_confidence_delta and min_tp1_shift_gain_pct


✅ Strategy backtest CLI created as run_strategy_backtest.py.

It supports:
	•	YAML-based config loading (from /live/strat/config)
	•	Iteration across all fork_scores.jsonl files
	•	Simple strategy evaluation logic (score >= min_score)
	•	Aggregated output written to: /home/signal/market6/backtest/strategy_eval/{strategy_name}_summary.json
python3 run_strategy_backtest.py --strategy confidence_safeguard


✅ Strategy simulation script updated to support:
	•	Filtering trades by TP1 shift, drawdown, and strategy min_score.
	•	Optional --range-start and --range-end date filtering.
	•	Output saved to /home/signal/market6/backtest/strategy_eval/{strategy}_summary.json.

python3 test_strategy_eval.py --strategy confidence_safeguard --range-start 2025-04-10 --range-end 2025-04-22

