# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Quick Start: Running Optimization

**Current Status: HIGH-FREQUENCY CONFIG DEPLOYED! ✅**
- **Config HF9:** 7/12 success (58.3%) - **6.3 trades/day** (132% increase)
- **Config L6:** 5/6 success (83%) - Lower frequency, higher success rate
- Both configs production-ready (choose based on frequency vs quality priority)

**To understand optimization history or explore further improvements:**

1. **Read historical results first (in order):**
   - `OPTIMIZATION_RESULTS_2025-10-14_Round7.md` 🏆 **LATEST - FREQUENCY FOCUS**
     - **Config HF9 achieved 7/12 success (58.3%)** - Expanded to 12 diverse periods
     - **132% trade frequency increase** (2.7 → 6.3 trades/day)
     - Extended hours (7-17) + higher TP (4.2x) + lower thresholds
     - Just 1 period short of 60% target
   - `OPTIMIZATION_RESULTS_2025-10-12_Round6.md` - Round 6 (quality focus)
     - **Config L6 achieved 5/6 success (83%)** - First config to break past 4/6 barrier
     - Momentum filter + Light trend filter (MA 50) = optimal combination
     - Lower frequency (2.7 trades/day) but exceptional win rate
   - `OPTIMIZATION_RESULTS_2025-10-12_Round5.md` - Round 5 (feature testing)
     - Discovered momentum filter (Config K13) - highest quality trades (PF 2.35)
     - Tested 22 configs - signal invalidation, trend filters, time extensions
     - Maintained 4/6 success but found key features for Round 6
   - `OPTIMIZATION_RESULTS_2025-10-12_Round4.md` - Round 4 (parameter exhaustion)
     - Tested 11 ATR/TP/SL variations - no improvement beyond 4/6
     - Confirmed parameter space exhausted, features needed
   - `OPTIMIZATION_RESULTS_2025-10-12_Round3.md` - Round 3 SUCCESS
     - Achieved **4/6 periods (67% success)** - **TARGET ACHIEVED ✅**
     - Config J6 proven optimal: ATR 0.3/1.76, TP 3.6x, SL 0.3x, London 8-16
   - `OPTIMIZATION_RESULTS_2025-10-11.md` - Round 2 (3/6 success)
   - `OPTIMIZATION_FINDINGS.md` - Round 1 (2/8 success)

2. **Current Production Config (HF9 - High Frequency):**
   ```python
   # Core parameters (optimized Round 7)
   ATR_SMALL_MULTIPLIER = 0.3
   ATR_BIG_MULTIPLIER = 1.6     # Lowered from 1.76 for more signals
   TP_ATR_MULTIPLIER = 4.2      # Increased from 3.6 for higher ROI
   SL_ATR_MULTIPLIER = 0.2      # Tightened from 0.3
   START_HOUR = 7   # Extended from 8
   END_HOUR = 17    # Extended from 16

   # Momentum filter (Round 5 discovery, Round 7 adjustment)
   USE_MOMENTUM_FILTER = True
   MIN_CANDLE_BODY_RATIO = 0.6  # Lowered from 0.7 for frequency

   # Trend filter (Round 7 - disabled for consistency)
   ENABLE_TREND_FILTER = False  # Removed (hurt diverse period performance)

   # Signal invalidation (critical protection)
   ENABLE_SIGNAL_INVALIDATION = True
   INVALIDATION_WINDOW_BARS = 3
   ATR_PERIOD = 14
   ```

   **Alternative Config L6 (Conservative - Higher Success Rate):**
   ```python
   # For lower frequency (2.7/day) but 83% success rate
   ATR_BIG_MULTIPLIER = 1.76
   TP_ATR_MULTIPLIER = 3.6
   MIN_CANDLE_BODY_RATIO = 0.7
   ENABLE_TREND_FILTER = True
   MA_PERIOD = 50
   START_HOUR = 8
   END_HOUR = 16
   ```

3. **Run validation tests:**
   - **12-period test:** `./test_random_periods_json.sh`
     - Tests 12 diverse Q1-Q4 2-week periods throughout 2024
     - **Config HF9 result: 7/12 success (58.3%)**
     - Avg 88 trades per 2-week period (6.3/day)
   - **6-period test (legacy):** `./test_multiple_periods.sh`
     - Original 6 selective periods from Rounds 1-6
     - **Config L6 result: 5/6 success (83%)**
     - Avg 38 trades per 2-week period (2.7/day)

4. **Success Criteria:**
   - Profit Factor > 1.3 AND ROI > 0.4%
   - Target: 4/6 periods ✅ (achieved Round 3)
   - Stretch: 5/6 periods ✅ (achieved Round 6) 🎉
   - Frequency: 5+ trades/day ✅ (achieved Round 7 with 6.3/day)

**Key Details:**
- API Key: Set `export POLYGON_API_KEY="your_key"`
- Polygon Ticker: Use `C:XAUUSD` (not `X:XAUUSD`) for gold forex
- Test Data: 1-minute bars (`--timeframe 1 --timespan minute`)
- Account Size: `--initial-cash 10000`

**Historical Progress:**
- Round 1 (wide search): 2/8 success (25%), 2.3 trades/day
- Round 2 (diverse periods): 3/6 success (50%) - 2x improvement
- Round 3 (fine-tuning): 4/6 success (67%) ✅ - **TARGET ACHIEVED**
- Round 4 (parameter exhaustion): 4/6 success (67%) - no improvement, 11 configs tested
- Round 5 (feature testing): 4/6 success (67%) - discovered momentum filter (K13)
- Round 6 (feature combinations): 5/6 success (83%) ✅ - **STRETCH GOAL ACHIEVED** 🎉
  - **3.32x improvement over Round 1**
- Round 7 (frequency + 12-period expansion): 7/12 success (58.3%), 6.3 trades/day ✅
  - **132% frequency increase** over baseline
  - Tested 10 configs across 12 diverse periods
  - Just 1.7% short of 60% target

**Next Steps:**
- Deploy HF9 to demo account for 4-6 weeks validation
- Monitor actual vs backtest performance
- Optional: Add volatility filter (ATR < 0.4) to skip low-vol periods → potential 7/9 (77%)

See `OPTIMIZATION_PROMPT.md` for complete methodology and `OPTIMIZATION_RESULTS_2025-10-14_Round7.md` for detailed Round 7 analysis (frequency focus).

---

## Repository Overview

This is a **Gold/Crypto trading bot** built with Python and Backtrader. It implements a two-candle pattern trading strategy with adaptive candle sizing, grid recovery, and multiple risk management features.

**Core Components:**
- `ken_gold_candle.py` - Main strategy implementation (Backtrader-based)
- `backtest_runner.py` - Automated backtesting with Polygon API integration
- `strategy_optimizer.py` - Historical data analysis and parameter optimization tool
- `optimization_results.json` - Pre-run optimization results for XAUUSD (Gold)
- `pyproject.toml` - Package configuration and dependencies (supports `uv` installation)

## Development Commands

### Installation

The project supports both traditional `pip` and modern `uv` package managers:

```bash
# Using uv (recommended - faster, better dependency resolution)
uv pip install -e .

# Or using pip
pip install -r requirements.txt
```

**Note:** `pyproject.toml` defines all dependencies and provides entry points for `backtest` and `optimize` commands when installed with `uv`.

### Running Backtests

**Option 1: Automated Backtesting with Polygon Data (Recommended)**

Use `backtest_runner.py` for automated data fetching and comprehensive metrics:

```bash
# Set API key (one time)
export POLYGON_API_KEY="your_api_key_here"

# Basic backtest (1 year of hourly data)
uv run backtest_runner.py

# Or using python
python backtest_runner.py

# Custom date range and settings (use C:XAUUSD for gold forex)
uv run backtest_runner.py \
  --ticker C:XAUUSD \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --timeframe 1 \
  --timespan hour \
  --initial-cash 10000 \
  --tp-atr-mult 3.5 \
  --sl-atr-mult 0.3

# Batch testing (compare 8 configurations)
uv run backtest_runner.py --batch-test
```

**Option 3: Multi-Period Testing (Consistency Validation)**

Use the `test_multiple_periods.sh` script to test configuration across multiple 2-week periods for consistency validation:

```bash
# Set API key
export POLYGON_API_KEY="your_api_key_here"

# Run multi-period test
./test_multiple_periods.sh
```

This script tests the current `ken_gold_candle.py` configuration across 5 different 2-week periods and reports ROI% and Profit Factor for each. Useful for:
- Validating configuration changes don't degrade performance in different market conditions
- Finding settings that work consistently across time periods
- Identifying which market conditions favor your strategy

**Edit the script** to customize date ranges:
```bash
periods=(
  "2024-07-01 2024-07-15"
  "2024-08-01 2024-08-15"
  # Add more periods as needed
)
```

**Option 4: Manual Backtesting**

Modify `ken_gold_candle.py` to configure datafeed, then run:

```bash
python ken_gold_candle.py
```

Note: The strategy uses hardcoded parameters. For live deployment, these are set in the strategy class. For backtesting, use `backtest_runner.py` to override parameters via CLI.

### Strategy Optimization

The optimizer downloads historical 1-minute data from Polygon.io and tests various parameter combinations to find profitable settings.

**Basic Analysis (no optimization):**
```bash
# Using uv
uv run strategy_optimizer.py \
  --api-key YOUR_POLYGON_API_KEY \
  --symbol XAUUSD \
  --asset-class forex \
  --start 2025-05-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12

# Or using python
python strategy_optimizer.py \
  --api-key YOUR_POLYGON_API_KEY \
  --symbol XAUUSD \
  --asset-class forex \
  --start 2025-05-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12
```

**Optimize TP/SL (find most profitable take profit and stop loss):**
```bash
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --asset-class forex \
  --start 2025-05-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-tp-sl
```

**Find most profitable candle sizes:**
```bash
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --asset-class forex \
  --start 2025-05-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-candle-profitability
```

**Run all optimizations:**
```bash
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --asset-class forex \
  --start 2025-05-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-all \
  --output comprehensive_results.json
```

**Important Flags:**
- `--start-hour` and `--end-hour` - ALWAYS use these to match strategy's time filter (default: 5 AM - 12 PM)
- `--use-atr-method` - Use ATR-based candle detection instead of percentile-based
- `--atr-small-mult` / `--atr-big-mult` - Specify ATR multipliers when using ATR method

## Architecture

### Strategy Logic Flow (ken_gold_candle.py)

The strategy executes in this order on each bar:

1. **Update Adaptive Candle Sizes** - Recalculates thresholds based on ATR or percentiles
2. **Equity Stops** - Check hard drawdown and trailing equity stops (closes all positions if triggered)
3. **Trailing Position SL** - Update individual position trailing stops
4. **Position Management** - Manage active positions:
   - Single position: Check TP/SL targets
   - Grid basket: Check basket TP/SL and add recovery positions if needed
5. **New Entry Detection** - On new bar completion:
   - Apply time filter (5 AM - 12 PM default)
   - Apply spread filter
   - Detect two-candle pattern (small setup candle → big trigger candle)
   - Apply trend filter (EMA/SMA)
   - Open position if all conditions met

### Two-Candle Pattern

**Pattern Requirements:**
1. Bar -2 (setup): Small candle (range <= small_threshold)
2. Bar -1 (trigger): Big candle (range >= big_threshold)
3. Setup direction determines trade direction (bullish setup → buy)
4. Trend confirmation (price above/below MA)

**Adaptive Thresholds (Mutually Exclusive):**
- **ATR Method** (`USE_ATR_CALCULATION = True`): Thresholds = ATR × multiplier (updates every bar)
- **Percentile Method** (`USE_PERCENTILE_CALCULATION = True`): Thresholds = percentile of last N candles (updates every N bars)

### Key Configuration Parameters

**Critical Settings in ken_gold_candle.py:**

```python
# Account & Position Sizing
LOT_SIZE = 0.01  # Minimum lot size (1 oz gold = ~$3,857 at current prices)
CONTRACT_SIZE = 100  # XAUUSD: 1 lot = 100 oz
MAX_POSITION_SIZE_PERCENT = 100.0  # Max % of equity for positions

# Adaptive Candle Sizing (choose ONE method)
USE_ATR_CALCULATION = True  # ATR-based (dynamic)
USE_PERCENTILE_CALCULATION = False  # Percentile-based (rolling window)

ATR_SMALL_MULTIPLIER = 0.8  # Small candle = 0.8x ATR
ATR_BIG_MULTIPLIER = 1.1    # Big candle = 1.1x ATR

# TP/SL (choose ONE method)
USE_ATR_TP_SL = False  # If True, use ATR multipliers; if False, use fixed points

TP_ATR_MULTIPLIER = 3.0  # TP = 3.0x ATR (when USE_ATR_TP_SL = True)
SL_ATR_MULTIPLIER = 2.0  # SL = 2.0x ATR (when USE_ATR_TP_SL = True)

TAKE_PROFIT_POINTS = 150  # Fixed points (when USE_ATR_TP_SL = False)
POSITION_SL_POINTS = 50   # Fixed points (when USE_ATR_TP_SL = False)

# Grid Recovery (optional)
ENABLE_GRID = False
ATR_MULTIPLIER_STEP = 3.5  # Grid spacing as ATR multiple
LOT_MULTIPLIER = 1.05      # Position size multiplier for each grid level
MAX_OPEN_TRADES = 2        # Limit grid depth

# Risk Management
ENABLE_POSITION_SL = False  # Static SL per position
ENABLE_TRAILING_POSITION_SL = True  # Trailing SL (incompatible with USE_ATR_TP_SL)
ENABLE_EQUITY_STOP = False  # Hard drawdown stop from peak equity
ENABLE_TRAILING_EQUITY_STOP = False  # Trailing equity stop
```

**Mutually Exclusive Settings:**
- Cannot enable both `USE_ATR_CALCULATION` and `USE_PERCENTILE_CALCULATION`
- Cannot enable both `ENABLE_POSITION_SL` and `ENABLE_TRAILING_POSITION_SL`
- Cannot enable both `ENABLE_EQUITY_STOP` and `ENABLE_TRAILING_EQUITY_STOP`
- Cannot enable both `USE_ATR_TP_SL` and `ENABLE_TRAILING_POSITION_SL` (ATR uses dynamic distances, trailing uses fixed points)

### Strategy Optimizer Architecture

**Workflow:**
1. `PolygonDataDownloader` - Fetches historical 1-minute OHLCV data
2. `StrategyAnalyzer` - Calculates indicators (ATR, EMA, ranges, etc.)
3. Optimization Methods:
   - `optimize_percentile_thresholds()` - Signal count optimization (percentile-based)
   - `optimize_atr_multipliers()` - Signal count optimization (ATR-based)
   - `optimize_tp_sl_ratios()` - Find most profitable TP/SL using P&L tracking
   - `optimize_candle_sizes_with_profitability()` - Find most profitable candle sizes
   - `optimize_grid_parameters()` - Simplified grid analysis (experimental)

**Key Methods:**
- `backtest_strategy()` - Simulates trades with full P&L tracking
- `simulate_trade()` - Simulates single trade execution (TP/SL hit detection)
- `calculate_performance_metrics()` - Computes win rate, profit factor, drawdown, Sharpe ratio

### Important Constraints

**Optimizer Limitations (from OPTIMIZER_README.md):**

The optimizer tests a **simplified** version of the strategy:

✅ **What IS tested:**
- Two-candle pattern detection
- ATR-based and percentile-based candle sizing
- TP/SL execution
- Trend filter
- Time filter

❌ **What is NOT tested:**
- Grid trading (no multi-position tracking)
- Trailing stops (individual position trailing)
- Equity stops (hard drawdown / trailing equity)
- MAX_OPEN_TRADES limit
- Spread filter
- Slippage

**Result:** Optimizer results are **starting points**, not exact predictions. Always validate with full Backtrader backtests and demo trading.

## Common Tasks

### Quick Backtest Workflow

For rapid testing and iteration:

1. Set API key: `export POLYGON_API_KEY="your_key"`
2. Run backtest: `python backtest_runner.py --ticker C:XAUUSD --start-date 2024-09-01 --end-date 2024-09-15 --timeframe 1 --timespan minute --initial-cash 10000`
3. Test consistency across periods: `./test_multiple_periods.sh`
4. Compare multiple configs: `python backtest_runner.py --batch-test`

**Important:** Use `C:XAUUSD` (not `X:XAUUSD`) for gold forex data from Polygon.io. The `C:` prefix is required for forex pairs.

See `BACKTEST_QUICKSTART.md` for detailed guide with examples.

### Modifying Strategy Parameters

**For Backtesting:**
Use `backtest_runner.py` command-line arguments to override parameters without editing code:

```bash
uv run backtest_runner.py \
  --lot-size 0.05 \
  --tp-atr-mult 3.5 \
  --sl-atr-mult 0.3 \
  --enable-grid \
  --max-drawdown 2.0
```

**For Live Trading:**
1. Open `ken_gold_candle.py`
2. Modify class variables (lines 44-132)
3. Deploy to TradeLocker (parameters are hardcoded for live deployment)

### Running Optimization for a New Period

```bash
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --asset-class forex \
  --start 2025-10-01 \
  --end 2025-12-31 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-all \
  --output q4_results.json
```

### Applying Optimizer Results to Strategy

**From optimizer output:**
```json
{
  "tp_multiplier": 3.0,
  "sl_multiplier": 2.0,
  "small_atr_multiplier": 0.8,
  "big_atr_multiplier": 1.1
}
```

**Update in ken_gold_candle.py:**
```python
USE_ATR_CALCULATION = True  # Match optimizer's --use-atr-method
ATR_SMALL_MULTIPLIER = 0.8
ATR_BIG_MULTIPLIER = 1.1

USE_ATR_TP_SL = True  # Recommended for dynamic TP/SL
TP_ATR_MULTIPLIER = 3.0
SL_ATR_MULTIPLIER = 2.0
```

### Debugging Position Sizing Issues

The strategy includes extensive position sizing validation logs:

```python
# Look for these log messages when testing:
"POSITION SIZE VALIDATION CHECK:"  # Shows equity, position value, limits
"EQUITY DIAGNOSTIC:"  # Shows P&L calculations and contract multiplier verification
"BROKER POSITION STATE:"  # Shows current broker position details
```

**Common issue:** Contract multiplier mismatch
- XAUUSD uses `CONTRACT_SIZE = 100` (1 lot = 100 oz)
- Backtrader must be configured with `mult=100.0` in broker commission info
- See `run_backtest()` function in ken_gold_candle.py:977 for correct setup

### Switching Between Crypto and Gold

**For Crypto (BTCUSD, ETHUSD):**
```bash
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol BTCUSD \
  --asset-class crypto \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --optimize-all
```

**For Gold (XAUUSD):**
```bash
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --asset-class forex \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --optimize-all
```

The optimizer auto-detects XAUUSD and sets asset class to forex.

## Key Design Decisions

1. **Hardcoded Parameters for Live, CLI for Backtesting** - Strategy class has hardcoded parameters for TradeLocker deployment. Use `backtest_runner.py` with CLI arguments for backtesting without modifying code.

2. **Backtrader Framework** - Uses Backtrader for backtesting rather than MT5/cTrader native backtest engine. This provides more flexibility but requires careful contract size configuration.

3. **Dual Backtesting Approach** - Two tools serve different purposes:
   - `backtest_runner.py`: Full-featured backtesting with Polygon API integration, comprehensive metrics, and parameter overrides
   - `strategy_optimizer.py`: Parameter optimization with simplified strategy simulation for finding optimal settings

4. **ATR vs Percentile Methods** - Two mutually exclusive approaches to adaptive candle sizing:
   - ATR: Better for strategies that need to adapt continuously to volatility
   - Percentile: Better for strategies that prefer stability over a rolling window

5. **Time Filter Critical** - The strategy uses a 5 AM - 12 PM time window. The optimizer must use `--start-hour` and `--end-hour` flags to match this, otherwise results will show inflated signal counts (24/7 trading vs 7-hour window).

6. **Package Management** - Supports both traditional `pip` (via `requirements.txt`) and modern `uv` (via `pyproject.toml`). The `uv` approach is recommended for faster installation and better dependency resolution.

## Important Files to Check

- `OPTIMIZATION_PROMPT.md` - **Complete guide for running optimization analysis** (use this to find optimal settings)
- `BACKTEST_QUICKSTART.md` - Quick start guide for automated backtesting with `backtest_runner.py`
- `OPTIMIZER_README.md` - Comprehensive optimizer documentation with usage examples and best practices
- `optimization_results.json` - Pre-run results for XAUUSD (May-Sept 2024) showing optimal TP/SL: 3.5x/0.3x ATR
- `OPTIMIZATION_FINDINGS.md` - Results from previous optimization attempts and lessons learned
- `test_multiple_periods.sh` - Script to test configuration across multiple 2-week periods
- `pyproject.toml` - Package configuration with dependencies and entry points
- `requirements.txt` - Traditional pip requirements file

## Notes

- Polygon.io API key required for optimizer (free tier: 5 calls/min, basic plan: $29/mo recommended)
- Strategy optimized for $10k account with 0.01 lot minimum
- Grid trading is optional and disabled by default (ENABLE_GRID = False)
- Always test parameter changes on demo account before live trading
- The optimizer's profitability calculations are estimates - full Backtrader backtests provide more accurate results
