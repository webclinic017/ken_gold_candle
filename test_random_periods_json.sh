#!/bin/bash

export POLYGON_API_KEY="_TOpg2RuyhSYrWHWyyXmzNNXor68u7Qm"

# 12 random 2-week periods throughout 2024
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
results_file="/tmp/backtest_summary_$$.txt"

> "$results_file"  # Clear file

for period in "${periods[@]}"; do
  start=$(echo $period | cut -d' ' -f1)
  end=$(echo $period | cut -d' ' -f2)

  total_count=$((total_count + 1))
  echo "===== Period $total_count: $start to $end ====="

  # Run backtest and save to backtest_results.json
  python backtest_runner.py --ticker C:XAUUSD --start-date "$start" --end-date "$end" --timeframe 1 --timespan minute --initial-cash 10000 > /dev/null 2>&1

  # Parse JSON results using Python
  result=$(python3 << 'EOF'
import json
try:
    with open('backtest_results.json', 'r') as f:
        data = json.load(f)
        if data and len(data) > 0:
            result = data[0]
            roi = result['portfolio']['return_pct']
            pf = result['pnl']['profit_factor']
            dd = result['performance']['max_drawdown_pct']
            trades = result['trades']['total']
            print(f"{roi:.2f}|{pf:.2f}|{dd:.2f}|{trades}")
        else:
            print("N/A|N/A|N/A|N/A")
except Exception as e:
    print(f"ERROR|ERROR|ERROR|ERROR")
EOF
)

  # Parse the result
  IFS='|' read -r roi pf dd trades <<< "$result"

  echo "  ROI: ${roi}% | PF: ${pf} | Max DD: ${dd}% | Trades: ${trades}"

  # Check if period passes (PF > 1.3 AND ROI > 0.4)
  pass_status="FAIL"
  if [ "$roi" != "N/A" ] && [ "$pf" != "N/A" ]; then
    # Use bc for floating point comparison
    if (( $(echo "$pf > 1.3" | bc -l) )) && (( $(echo "$roi > 0.4" | bc -l) )); then
      echo "  ✅ PASS"
      pass_count=$((pass_count + 1))
      pass_status="PASS"
    else
      echo "  ❌ FAIL"
    fi
  else
    echo "  ⚠️  ERROR"
  fi

  # Save to results file
  echo "$total_count|$start|$end|$roi|$pf|$dd|$trades|$pass_status" >> "$results_file"
  echo ""
done

echo "========================================"
echo "FINAL RESULTS"
echo "========================================"
echo ""

# Print summary table
echo "Period | Dates              | ROI%   | PF   | DD%   | Trades | Status"
echo "-------|--------------------| -------| -----| ------|--------|-------"
while IFS='|' read -r num start end roi pf dd trades status; do
  printf "%-6s | %s - %s | %6s | %5s | %5s | %6s | %s\n" "$num" "$start" "$end" "$roi" "$pf" "$dd" "$trades" "$status"
done < "$results_file"

echo ""
echo "Periods passed: $pass_count / $total_count ($(echo "scale=1; $pass_count * 100 / $total_count" | bc)%)"
echo "Target: 60% (8/12)"
echo ""

if [ $pass_count -ge 8 ]; then
  echo "✅ TARGET ACHIEVED!"
else
  echo "❌ Target not met (need $((8 - pass_count)) more passing periods)"
fi

rm "$results_file"
