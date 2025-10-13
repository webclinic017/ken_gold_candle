#!/bin/bash

export POLYGON_API_KEY="_TOpg2RuyhSYrWHWyyXmzNNXor68u7Qm"

# 12 random 2-week periods throughout 2024
# 6 original periods + 6 new random periods
periods=(
  "2024-01-15 2024-02-01"
  "2024-02-15 2024-03-01"
  "2024-03-01 2024-03-15"
  "2024-04-01 2024-04-15"
  "2024-05-01 2024-05-15"
  "2024-06-01 2024-06-15"
  "2024-07-01 2024-07-15"
  "2024-08-01 2024-08-15"
  "2024-08-20 2024-09-03"
  "2024-09-15 2024-10-01"
  "2024-10-15 2024-11-01"
  "2024-11-15 2024-11-29"
)

echo "========================================"
echo "Testing Config L6 across 12 random periods"
echo "Success target: 60% (8/12 periods)"
echo "Criteria: PF > 1.3 AND ROI > 0.4%"
echo "========================================"
echo ""

pass_count=0
total_count=0

for period in "${periods[@]}"; do
  start=$(echo $period | cut -d' ' -f1)
  end=$(echo $period | cut -d' ' -f2)
  echo "===== Period $((total_count + 1)): $start to $end ====="

  output=$(python backtest_runner.py --ticker C:XAUUSD --start-date "$start" --end-date "$end" --timeframe 1 --timespan minute --initial-cash 10000 2>&1)

  # Extract metrics (accounting for [INFO] prefix)
  roi=$(echo "$output" | grep "Return %:" | awk '{print $5}' | sed 's/%//')
  pf=$(echo "$output" | grep "Profit Factor:" | awk '{print $5}')
  dd=$(echo "$output" | grep "Max Drawdown:" | awk '{print $5}' | sed 's/%//')
  trades=$(echo "$output" | grep "Total Trades:" | awk '{print $5}')

  echo "  ROI: ${roi}% | PF: ${pf} | Max DD: ${dd}% | Trades: ${trades}"

  # Check if period passes (PF > 1.3 AND ROI > 0.4)
  pass=0
  if [ ! -z "$roi" ] && [ ! -z "$pf" ]; then
    if (( $(echo "$pf > 1.3" | bc -l) )) && (( $(echo "$roi > 0.4" | bc -l) )); then
      echo "  ✅ PASS"
      pass_count=$((pass_count + 1))
      pass=1
    else
      echo "  ❌ FAIL"
    fi
  else
    echo "  ⚠️  ERROR - could not parse metrics"
  fi

  total_count=$((total_count + 1))
  echo ""
done

echo "========================================"
echo "FINAL RESULTS"
echo "========================================"
echo "Periods passed: $pass_count / $total_count ($(echo "scale=1; $pass_count * 100 / $total_count" | bc)%)"
echo "Target: 60% (8/12)"

if [ $pass_count -ge 8 ]; then
  echo "✅ TARGET ACHIEVED!"
else
  echo "❌ Target not met (need $((8 - pass_count)) more)"
fi
