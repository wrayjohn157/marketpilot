✅ Strategy hyperopt simulator created! It’s saved as hyperopt_sim_runner.py and supports:
	•	--range-start YYYY-MM-DD
	•	--range-end YYYY-MM-DD
	•	Loops over all YAMLs in /live/strat/config
	•	Simulates backtest via fork_score_filter.py for each date
	•	Reads YYYY-MM-DD_summary.json to extract tp1_hit_rate and avg_drawdown_pct
	•	Logs a comparative table
