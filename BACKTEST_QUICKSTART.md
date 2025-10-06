# 🧪 Backtest Runner - Quick Start Guide

This guide will help you get started with the automated backtesting tool in under 5 minutes.

---

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **Polygon.io API key** ([Get free key](https://polygon.io/))
3. **uv installed** (recommended):

   ```bash
   # Mac/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

4. **Dependencies installed**:

   ```bash
   # Using uv (recommended - much faster)
   uv pip install -e .

   # Or using pip
   pip install -r requirements.txt
   ```

---

## 🚀 Quick Start

### Step 1: Set Your API Key

```bash
# On Mac/Linux
export POLYGON_API_KEY="your_api_key_here"

# On Windows (PowerShell)
$env:POLYGON_API_KEY="your_api_key_here"
```

### Step 2: Run Your First Backtest

```bash
# Using uv (recommended)
uv run backtest_runner.py

# Or using python directly
python backtest_runner.py
```

That's it! This will:

- Download 1 year of hourly XAUUSD data from Polygon
- Run a backtest with default strategy settings
- Display comprehensive performance metrics
- Save results to `backtest_results.json`

---

## 📊 Understanding the Output

After the backtest completes, you'll see:

```
================================================================================
BACKTEST RESULTS: Backtest Run
================================================================================

📊 PORTFOLIO PERFORMANCE
  Starting Value:    $10,000.00
  Ending Value:      $10,523.45
  Total Return:      $523.45
  Return %:          5.23%

📈 PERFORMANCE METRICS
  Sharpe Ratio:      1.45        ← Higher is better (>1.0 is good)
  Max Drawdown:      8.50%       ← Lower is better (<15% is acceptable)
  Avg Daily Return:  0.0023      ← Positive is profitable
  SQN:               1.89        ← >1.6 is good, >2.5 is excellent
  VWR:               85.3%       ← Higher is better (volatility-weighted)

🎯 TRADE STATISTICS
  Total Trades:      156
  Won:               68 (43.59%) ← Win rate
  Lost:              88
  Win Streak:        7           ← Longest consecutive wins
  Loss Streak:       5           ← Longest consecutive losses
  Avg Duration:      12.3 bars   ← Average trade length

💰 PROFIT & LOSS
  Net P&L:           $523.45     ← Total profit
  Avg Trade:         $3.35       ← Average profit per trade
  Profit Factor:     1.32        ← Gross profit ÷ Gross loss (>1.5 is good)
  Avg Win:           $15.67
  Avg Loss:          -$8.45
  Largest Win:       $89.23
  Largest Loss:      -$45.12
```

### Key Metrics to Watch

| Metric            | Good Value | What It Means                                       |
| ----------------- | ---------- | --------------------------------------------------- |
| **Return %**      | Positive   | Overall profitability                               |
| **Sharpe Ratio**  | > 1.0      | Risk-adjusted returns (higher = better risk/reward) |
| **Max Drawdown**  | < 15%      | Worst equity decline (lower = safer)                |
| **Profit Factor** | > 1.5      | Total wins ÷ Total losses                           |
| **Win Rate**      | 40-60%     | % of winning trades                                 |
| **SQN**           | > 1.6      | System Quality Number (>2.5 = excellent)            |

---

## 🧪 Testing Different Configurations

### Test Counter-Trend Strategy

```bash
uv run backtest_runner.py \
  --enable-counter-trend \
  --run-name "Counter-Trend Test"
```

### Test Different TP/SL Settings

```bash
uv run backtest_runner.py \
  --tp-atr-mult 4.0 \
  --sl-atr-mult 0.5 \
  --run-name "Aggressive TP/SL"
```

### Test with Grid Trading

```bash
uv run backtest_runner.py \
  --enable-grid \
  --lot-size 0.03 \
  --run-name "Grid Strategy"
```

### Test on Different Date Range

```bash
uv run backtest_runner.py \
  --start-date 2024-01-01 \
  --end-date 2024-06-30 \
  --run-name "Q1-Q2 2024"
```

### Test Different Timeframes

```bash
# 4-hour bars
uv run backtest_runner.py \
  --timeframe 4 \
  --timespan hour \
  --run-name "4H Timeframe"

# Daily bars
uv run backtest_runner.py \
  --timeframe 1 \
  --timespan day \
  --run-name "Daily Timeframe"
```

---

## 🔄 Batch Testing (Compare Multiple Configs)

Run 8 different configurations automatically:

```bash
uv run backtest_runner.py --batch-test
```

This will test:

1. Default strategy
2. Grid trading enabled
3. Counter-trend fade
4. Aggressive TP (4x ATR)
5. Conservative TP (2x ATR)
6. Tight SL (0.5x ATR)
7. Wide SL (2x ATR)
8. Higher lot size (0.05)

After all tests complete, you'll see a comparison table:

```
================================================================================
BACKTEST COMPARISON
================================================================================

Run Name                       Return %     Sharpe     DD %      Win %     PF
--------------------------------------------------------------------------------
Default Strategy                    5.23%    1.45      -8.50%    42.50%   1.32
Grid Enabled                        8.91%    1.67      -12.30%   38.20%   1.45
Counter-Trend Fade                  3.12%    0.98      -6.20%    48.10%   1.18
Aggressive TP (4x ATR)              7.45%    1.52      -9.80%    35.30%   1.41
Conservative TP (2x ATR)            4.23%    1.21      -7.10%    48.90%   1.15
Tight SL (0.5x ATR)                -2.34%    0.45      -15.20%   28.10%   0.85
Wide SL (2x ATR)                    6.78%    1.38      -11.50%   41.20%   1.28
Higher Lot Size (0.05)              8.72%    1.55      -14.20%   42.50%   1.32
```

---

## 💾 Viewing Saved Results

All results are saved to `backtest_results.json`. You can:

```python
import json

# Load results
with open('backtest_results.json', 'r') as f:
    results = json.load(f)

# Print summary
for result in results:
    print(f"{result['run_name']}: {result['portfolio']['return_pct']:.2f}%")
```

---

## 🎯 Next Steps

### 1. Find Optimal Parameters

Use the optimizer to find the best TP/SL settings:

```bash
uv run strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --asset-class forex \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --optimize-tp-sl
```

### 2. Apply Best Settings

Edit `ken_gold_candle.py` with the best parameters from your tests:

```python
# From backtest/optimizer results
TP_ATR_MULTIPLIER = 3.5  # Best from testing
SL_ATR_MULTIPLIER = 0.3  # Best from testing
```

### 3. Validate on Different Period

Always test on a different time period (walk-forward validation):

```bash
# Train period
uv run backtest_runner.py \
  --start-date 2024-01-01 \
  --end-date 2024-06-30 \
  --run-name "Training Period"

# Test period (unseen data)
uv run backtest_runner.py \
  --start-date 2024-07-01 \
  --end-date 2024-12-31 \
  --run-name "Test Period"
```

### 4. Demo Test Before Live

Never skip demo testing! Run your strategy on a demo account with real-time data before risking real money.

---

## 🔧 Troubleshooting

### Error: "Polygon API key required"

Set your API key:

```bash
export POLYGON_API_KEY="your_key"
```

Or pass it directly:

```bash
uv run backtest_runner.py --api-key "your_key"
```

### Error: "Failed to fetch data"

Common causes:

- Invalid ticker format (use `X:XAUUSD` for Gold, not `XAUUSD`)
- Date range too old (free tier has limited history)
- API rate limit (wait 1 minute)

### No Trades Executed

Try:

- Longer date range (`--start-date 2024-01-01`)
- Different timeframe (`--timespan day`)
- Check strategy filters in `ken_gold_candle.py`

---

## 📚 Advanced Usage

### Custom Strategy Parameters

You can override ANY strategy parameter:

```bash
uv run backtest_runner.py \
  --run-name "Custom Config" \
  --lot-size 0.05 \
  --tp-atr-mult 3.5 \
  --sl-atr-mult 0.3 \
  --max-drawdown 2.0 \
  --enable-grid \
  --enable-counter-trend
```

### Save to Custom File

```bash
uv run backtest_runner.py \
  --output my_backtest_results.json
```

### Test Multiple Symbols

```bash
# Bitcoin
uv run backtest_runner.py \
  --ticker X:BTCUSD \
  --run-name "Bitcoin Test"

# Ethereum
uv run backtest_runner.py \
  --ticker X:ETHUSD \
  --run-name "Ethereum Test"

# Stocks
uv run backtest_runner.py \
  --ticker AAPL \
  --run-name "Apple Stock"
```

---

## ⚠️ Important Notes

1. **Past performance ≠ Future results** - Backtesting shows what WOULD have happened, not what WILL happen
2. **Avoid over-optimization** - Don't chase the highest return on one period
3. **Always validate** - Test on multiple time periods
4. **Demo test first** - Never go live without demo testing
5. **Monitor drawdown** - High profit with high drawdown = high risk

---

## 🎓 Learning Resources

- [Backtrader Documentation](https://www.backtrader.com/)
- [Polygon API Docs](https://polygon.io/docs)
- [Strategy Optimization Guide](OPTIMIZER_README.md)
- [Main README](README.md)

---

**Happy Testing! 🚀**
