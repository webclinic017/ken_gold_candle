#!/usr/bin/env python3
"""
Test multiple parameter combinations across 4 different 2-week periods
Find settings with PF > 1.7 and ROI > 1.5% consistently across all periods
"""

import subprocess
import json
import os
from datetime import datetime, timedelta

api_key = "[obfscuated]"

# Define 4 different 2-week periods in 2024
test_periods = [
    ("2024-03-01", "2024-03-15", "Period 1: Early March"),
    ("2024-05-15", "2024-05-29", "Period 2: Mid May"),
    ("2024-07-01", "2024-07-15", "Period 3: Early July"),
    ("2024-09-10", "2024-09-24", "Period 4: Mid September"),
]

# Test different TP/SL configurations
# Focus on tighter ranges that might achieve higher profit factors
tp_sl_configs = [
    {"tp": 1.5, "sl": 0.3, "name": "Tight TP, Very Tight SL"},
    {"tp": 1.5, "sl": 0.5, "name": "Tight TP, Tight SL"},
    {"tp": 2.0, "sl": 0.3, "name": "Medium TP, Very Tight SL"},
    {"tp": 2.0, "sl": 0.5, "name": "Medium TP, Tight SL"},
    {"tp": 2.5, "sl": 0.3, "name": "Wide TP, Very Tight SL"},
    {"tp": 2.5, "sl": 0.5, "name": "Wide TP, Tight SL"},
    {"tp": 3.0, "sl": 0.3, "name": "Very Wide TP, Very Tight SL"},
]

print("=" * 80)
print("MULTI-PERIOD OPTIMIZATION TEST")
print("=" * 80)
print(f"Target: Profit Factor > 1.7 AND ROI > 1.5%")
print(f"Testing {len(tp_sl_configs)} configurations across {len(test_periods)} periods")
print("=" * 80)

all_results = {}

# Test each configuration
for config_idx, config in enumerate(tp_sl_configs, 1):
    config_name = config['name']
    tp = config['tp']
    sl = config['sl']

    print(f"\n[{config_idx}/{len(tp_sl_configs)}] Testing Config: {config_name} (TP={tp}x, SL={sl}x)")
    print("-" * 80)

    period_results = []

    # Test across all periods
    for period_idx, (start, end, period_name) in enumerate(test_periods, 1):
        print(f"  Period {period_idx}/4: {period_name} ({start} to {end})...", end=" ")

        # Run optimizer
        cmd = [
            "uv", "run", "strategy_optimizer.py",
            "--api-key", api_key,
            "--symbol", "XAUUSD",
            "--asset-class", "forex",
            "--start", start,
            "--end", end,
            "--start-hour", "4",
            "--end-hour", "13",
            "--use-atr-method",
            "--atr-small-mult", "0.5",
            "--atr-big-mult", "1.5",
            "--optimize-tp-sl",
            "--tp-range-min", str(tp),
            "--tp-range-max", str(tp),
            "--sl-range-min", str(sl),
            "--sl-range-max", str(sl),
            "--tp-sl-step", "0.1",
            "--output", f"temp_test_{config_idx}_{period_idx}.json"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # Parse output to get results
            output = result.stdout

            # Extract metrics from output
            pnl = None
            pf = None
            win_rate = None
            trades = None

            for line in output.split('\n'):
                if 'Total P&L:' in line:
                    try:
                        pnl = float(line.split('$')[1].strip())
                    except:
                        pass
                elif 'Profit Factor:' in line:
                    try:
                        pf = float(line.split(':')[1].strip())
                    except:
                        pass
                elif 'Win Rate:' in line:
                    try:
                        win_rate = float(line.split(':')[1].strip().replace('%', ''))
                    except:
                        pass

            # Calculate ROI (assuming $10k account)
            roi = (pnl / 10000 * 100) if pnl else 0

            if pnl is not None and pf is not None:
                period_results.append({
                    'period': period_name,
                    'start': start,
                    'end': end,
                    'pnl': pnl,
                    'roi': roi,
                    'profit_factor': pf,
                    'win_rate': win_rate,
                    'meets_target': pf > 1.7 and roi > 1.5
                })

                status = "✓" if (pf > 1.7 and roi > 1.5) else "✗"
                print(f"{status} P&L=${pnl:.2f} ROI={roi:.2f}% PF={pf:.2f}")
            else:
                print("✗ Failed to parse results")

            # Cleanup
            temp_file = f"temp_test_{config_idx}_{period_idx}.json"
            if os.path.exists(temp_file):
                os.remove(temp_file)

        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
            continue

    # Store results for this configuration
    if period_results:
        all_results[config_name] = {
            'tp': tp,
            'sl': sl,
            'periods': period_results,
            'success_count': sum(1 for r in period_results if r['meets_target']),
            'avg_pf': sum(r['profit_factor'] for r in period_results) / len(period_results),
            'avg_roi': sum(r['roi'] for r in period_results) / len(period_results),
            'min_pf': min(r['profit_factor'] for r in period_results),
            'min_roi': min(r['roi'] for r in period_results),
        }

print("\n" + "=" * 80)
print("FINAL RESULTS - CONFIGURATIONS MEETING TARGET IN ALL 4 PERIODS")
print("=" * 80)

# Find configs that meet target in all periods
winning_configs = []
for config_name, data in all_results.items():
    if data['success_count'] == 4:
        winning_configs.append((config_name, data))

if winning_configs:
    print(f"\n🎉 Found {len(winning_configs)} configuration(s) meeting target in ALL 4 periods!\n")

    for config_name, data in winning_configs:
        print(f"🏆 {config_name}")
        print(f"   TP: {data['tp']}x ATR, SL: {data['sl']}x ATR")
        print(f"   Average Profit Factor: {data['avg_pf']:.2f}")
        print(f"   Average ROI: {data['avg_roi']:.2f}%")
        print(f"   Min Profit Factor: {data['min_pf']:.2f}")
        print(f"   Min ROI: {data['min_roi']:.2f}%")
        print(f"\n   Period Results:")
        for period in data['periods']:
            print(f"     {period['period']}: PF={period['profit_factor']:.2f}, ROI={period['roi']:.2f}%")
        print()
else:
    print("\n❌ No configuration met the target (PF > 1.7 AND ROI > 1.5%) in ALL 4 periods")
    print("\nBest Performing Configs:")

    # Sort by success count, then by avg PF
    sorted_configs = sorted(
        all_results.items(),
        key=lambda x: (x[1]['success_count'], x[1]['avg_pf']),
        reverse=True
    )

    for config_name, data in sorted_configs[:5]:
        print(f"\n{config_name} (TP={data['tp']}x, SL={data['sl']}x)")
        print(f"  Success: {data['success_count']}/4 periods")
        print(f"  Avg PF: {data['avg_pf']:.2f}, Avg ROI: {data['avg_roi']:.2f}%")
        print(f"  Min PF: {data['min_pf']:.2f}, Min ROI: {data['min_roi']:.2f}%")

# Save full results
with open('multi_period_test_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)

print(f"\n✅ Full results saved to: multi_period_test_results.json")
print("=" * 80)
