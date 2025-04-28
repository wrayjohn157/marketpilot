✅ Dry-run simulator script created. It will:
	•	Load historical fork_scores.jsonl data from your fork history path.
	•	Apply filters like min score, RSI, TP1 shift cap, and passed status.
	•	Print a summary table of qualifying trades.
	•	Supports --range-start, --range-end, and optional --config.

You can now run it like:
python3 dry_run_simulator.py --range-start 2025-04-20 --range-end 2025-04-23

Or with a custom config JSON:
python3 dry_run_simulator.py --range-start 2025-04-20 --range-end 2025-04-23 --config custom_config.json

✅ Dry-run simulator script created. You can now run:
python3 dry_run_simulator.py --range-start 2025-04-20 --range-end 2025-04-23

It loads from fork_scores.jsonl, filters based on score, rsi, tp1_shift, and optionally skips failed entries. Results are printed as a table.
