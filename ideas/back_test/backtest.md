✅ Script patched and enhanced.

You can now run it like this to evaluate strategy results:
python3 simulate_strategy_on_history.py --strategy confidence_safeguard --range-start 2025-04-20 --range-end 2025-04-23

It will:
	•	Load fork_scores.jsonl per day from /output/fork_history/
	•	Apply strategy thresholds (score, RSI, TP1 shift)
	•	Print summary metrics and sample failed entries
