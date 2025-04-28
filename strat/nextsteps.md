# === Next Step: Enhance Simulation Engine ===
# We will evolve hyperopt_sim_runner.py to actually re-score trades using the YAML config
# Here's the plan:

# ✅ CURRENT:
# - Loops over strategy YAMLs
# - Loads daily summary results (from existing backtest output)
# - Logs comparative table of TP1 hit rate, drawdown

# 🛠 NEXT:
# 1. Simulate fork_score_filter.py logic using each strategy config
#    - Inject the config into the scoring logic dynamically
#    - Re-score each entry using the weight rules
#    - Output updated `final_fork_rrr_trades.json`

# 2. Trigger downstream backtest from these rescored trades (e.g., run_fork_backtest.py)
#    - Feed in the updated output and wait for summary file

# 3. Collect actual metrics after the simulated filter + backtest pass
#    - TP1 hit %, drawdown, average win/loss, etc.

# 4. Log results per strategy with clear performance markers
#    - Output CSV or table: [strategy, date, tp1%, avg_drawdown, trades_passed, median_score]

# 🔁 Bonus:
# - Add --top-n mode to only print best strategies
# - Add support for multiple timeframes or BTC filters per strategy

# 👷 Ready to start building fork_score_filter.py as a module for scoring trades by config? Let me know and I’ll start!
