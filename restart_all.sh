#!/bin/bash
echo "🔄 Restarting Market7 Services..."

services=(
  fork_score_filter
  generate_tv_screener_ratings
  market7
  ml_confidence_cache_market7
  btc_logger
  fork_metrics
  fork_safu_monitor
  rolling_indicators_market7
  rolling_klines_market7
  smart_dca_market7
  tv_kicker_market7
  fork_runner
)

for service in "${services[@]}"; do
  echo "🚀 Restarting $service..."
  sudo service "$service" restart
done

echo "✅ All services restarted."
