#!/usr/bin/env python3
"""
Parameter optimization script for last 2 weeks
Tests multiple parameter combinations to find best ROI and Profit Factor
"""

import subprocess
import json
import os
from datetime import datetime, timedelta

# Calculate last 2 weeks
end_date = datetime.now()
start_date = end_date - timedelta(days=14)
start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

print(f"Optimizing parameters for period: {start_str} to {end_str}")
print("=" * 80)

# Get API key
api_key = os.environ.get('POLYGON_API_KEY')
if not api_key:
    print("ERROR: POLYGON_API_KEY environment variable not set")
    exit(1)

# Test configurations with different parameter combinations
test_configs = [
    # Config 1: Current settings (baseline)
    {
        "name": "Current Settings (Baseline)",
        "params": {
            "lot_size": 0.03,
            "tp_atr_mult": 3.5,
            "sl_atr_mult": 0.3,
            "enable_counter_trend": True,
            "use_limit_entry": True,
        }
    },
    # Config 2: Tighter TP/SL
    {
        "name": "Tighter TP/SL (2.5x/0.5x)",
        "params": {
            "lot_size": 0.03,
            "tp_atr_mult": 2.5,
            "sl_atr_mult": 0.5,
            "enable_counter_trend": True,
            "use_limit_entry": True,
        }
    },
    # Config 3: Wider TP/SL
    {
        "name": "Wider TP/SL (4.5x/0.2x)",
        "params": {
            "lot_size": 0.03,
            "tp_atr_mult": 4.5,
            "sl_atr_mult": 0.2,
            "enable_counter_trend": True,
            "use_limit_entry": True,
        }
    },
    # Config 4: Trend following (no fade)
    {
        "name": "Trend Following (No Fade)",
        "params": {
            "lot_size": 0.03,
            "tp_atr_mult": 3.5,
            "sl_atr_mult": 0.3,
            "enable_counter_trend": False,
            "use_limit_entry": True,
        }
    },
    # Config 5: Aggressive entry (no limit)
    {
        "name": "Aggressive Entry (No Limit)",
        "params": {
            "lot_size": 0.03,
            "tp_atr_mult": 3.5,
            "sl_atr_mult": 0.3,
            "enable_counter_trend": True,
            "use_limit_entry": False,
        }
    },
    # Config 6: Conservative (tight SL, wide TP)
    {
        "name": "Conservative (3.0x/0.7x)",
        "params": {
            "lot_size": 0.03,
            "tp_atr_mult": 3.0,
            "sl_atr_mult": 0.7,
            "enable_counter_trend": True,
            "use_limit_entry": True,
        }
    },
    # Config 7: Aggressive (wide TP, tight SL)
    {
        "name": "Aggressive (5.0x/0.25x)",
        "params": {
            "lot_size": 0.03,
            "tp_atr_mult": 5.0,
            "sl_atr_mult": 0.25,
            "enable_counter_trend": True,
            "use_limit_entry": True,
        }
    },
    # Config 8: Balanced
    {
        "name": "Balanced (3.0x/0.4x)",
        "params": {
            "lot_size": 0.03,
            "tp_atr_mult": 3.0,
            "sl_atr_mult": 0.4,
            "enable_counter_trend": True,
            "use_limit_entry": True,
        }
    },
    # Config 9: Trend following + no limit
    {
        "name": "Trend Follow + No Limit",
        "params": {
            "lot_size": 0.03,
            "tp_atr_mult": 3.5,
            "sl_atr_mult": 0.3,
            "enable_counter_trend": False,
            "use_limit_entry": False,
        }
    },
    # Config 10: Very tight (scalping style)
    {
        "name": "Scalping Style (2.0x/0.6x)",
        "params": {
            "lot_size": 0.03,
            "tp_atr_mult": 2.0,
            "sl_atr_mult": 0.6,
            "enable_counter_trend": True,
            "use_limit_entry": True,
        }
    },
]

results = []

for i, config in enumerate(test_configs, 1):
    print(f"\n[{i}/{len(test_configs)}] Testing: {config['name']}")
    print("-" * 80)

    # Build command
    cmd = [
        "python", "backtest_runner.py",
        "--api-key", api_key,
        "--ticker", "X:XAUUSD",
        "--start-date", start_str,
        "--end-date", end_str,
        "--timeframe", "1",
        "--timespan", "hour",
        "--initial-cash", "10000",
        "--run-name", config['name'],
        "--output", f"optimization_test_{i}.json"
    ]

    # Add parameters
    params = config['params']
    cmd.extend(["--lot-size", str(params['lot_size'])])
    cmd.extend(["--tp-atr-mult", str(params['tp_atr_mult'])])
    cmd.extend(["--sl-atr-mult", str(params['sl_atr_mult'])])

    if params['enable_counter_trend']:
        cmd.append("--enable-counter-trend")

    if not params['use_limit_entry']:
        cmd.append("--no-limit-entry")

    # Run backtest
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Load result
        with open(f"optimization_test_{i}.json", 'r') as f:
            result_data = json.load(f)
            if result_data:
                result_data = result_data[0]  # Get first result
                results.append({
                    'config': config['name'],
                    'params': params,
                    'return_pct': result_data['portfolio']['return_pct'],
                    'profit_factor': result_data['trade_stats']['profit_factor'],
                    'sharpe': result_data['performance']['sharpe_ratio'],
                    'max_drawdown_pct': result_data['performance']['max_drawdown_pct'],
                    'total_trades': result_data['trade_stats']['total_trades'],
                    'win_rate': result_data['trade_stats']['win_rate']
                })

                print(f"✓ Return: {result_data['portfolio']['return_pct']:.2f}%")
                print(f"✓ Profit Factor: {result_data['trade_stats']['profit_factor']:.2f}")
                print(f"✓ Sharpe: {result_data['performance']['sharpe_ratio']:.2f}")
                print(f"✓ Trades: {result_data['trade_stats']['total_trades']}")

        # Cleanup temp file
        os.remove(f"optimization_test_{i}.json")

    except Exception as e:
        print(f"✗ Error: {e}")
        continue

print("\n" + "=" * 80)
print("OPTIMIZATION RESULTS SUMMARY")
print("=" * 80)

# Sort by profit factor
results_by_pf = sorted(results, key=lambda x: x['profit_factor'], reverse=True)
print("\n🏆 TOP 3 BY PROFIT FACTOR:")
for i, r in enumerate(results_by_pf[:3], 1):
    print(f"\n{i}. {r['config']}")
    print(f"   Profit Factor: {r['profit_factor']:.2f}")
    print(f"   Return: {r['return_pct']:.2f}%")
    print(f"   Sharpe: {r['sharpe']:.2f}")
    print(f"   Trades: {r['total_trades']}")
    print(f"   Parameters: TP={r['params']['tp_atr_mult']}x, SL={r['params']['sl_atr_mult']}x, Counter-Trend={r['params']['enable_counter_trend']}, Limit={r['params']['use_limit_entry']}")

# Sort by ROI
results_by_roi = sorted(results, key=lambda x: x['return_pct'], reverse=True)
print("\n\n💰 TOP 3 BY ROI:")
for i, r in enumerate(results_by_roi[:3], 1):
    print(f"\n{i}. {r['config']}")
    print(f"   Return: {r['return_pct']:.2f}%")
    print(f"   Profit Factor: {r['profit_factor']:.2f}")
    print(f"   Sharpe: {r['sharpe']:.2f}")
    print(f"   Trades: {r['total_trades']}")
    print(f"   Parameters: TP={r['params']['tp_atr_mult']}x, SL={r['params']['sl_atr_mult']}x, Counter-Trend={r['params']['enable_counter_trend']}, Limit={r['params']['use_limit_entry']}")

# Find best overall (highest combined score)
for r in results:
    # Normalized score: 50% profit factor, 50% ROI (normalized)
    max_pf = max([x['profit_factor'] for x in results]) if results else 1
    max_roi = max([x['return_pct'] for x in results]) if results else 1
    r['combined_score'] = (r['profit_factor'] / max_pf * 50) + (r['return_pct'] / max_roi * 50)

results_by_combined = sorted(results, key=lambda x: x['combined_score'], reverse=True)

print("\n\n⭐ BEST OVERALL (Combined Score):")
best = results_by_combined[0]
print(f"\n{best['config']}")
print(f"   Return: {best['return_pct']:.2f}%")
print(f"   Profit Factor: {best['profit_factor']:.2f}")
print(f"   Sharpe: {best['sharpe']:.2f}")
print(f"   Max Drawdown: {best['max_drawdown_pct']:.2f}%")
print(f"   Win Rate: {best['win_rate']:.2f}%")
print(f"   Total Trades: {best['total_trades']}")
print(f"\n   OPTIMAL PARAMETERS:")
print(f"   TP_ATR_MULTIPLIER = {best['params']['tp_atr_mult']}")
print(f"   SL_ATR_MULTIPLIER = {best['params']['sl_atr_mult']}")
print(f"   ENABLE_COUNTER_TREND_FADE = {best['params']['enable_counter_trend']}")
print(f"   USE_LIMIT_ENTRY = {best['params']['use_limit_entry']}")

# Save full results
with open('optimization_results_2weeks.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n✓ Full results saved to: optimization_results_2weeks.json")
print("=" * 80)
