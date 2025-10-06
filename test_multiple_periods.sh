#!/bin/bash

export POLYGON_API_KEY="[obfscuated]"

periods=(
  "2024-07-01 2024-07-15"
  "2024-07-15 2024-07-30"
  "2024-08-01 2024-08-15"
  "2024-08-15 2024-09-01"
  "2024-09-01 2024-09-15"
)

for period in "${periods[@]}"; do
  start=$(echo $period | cut -d' ' -f1)
  end=$(echo $period | cut -d' ' -f2)
  echo "===== Testing period: $start to $end ====="
  python backtest_runner.py --ticker C:XAUUSD --start-date "$start" --end-date "$end" --timeframe 1 --timespan minute --initial-cash 10000 2>&1 | grep -E "(Return %|Profit Factor)"
  echo ""
done
