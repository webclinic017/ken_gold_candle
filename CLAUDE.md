# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **Gold/Crypto trading bot** built with Python and Backtrader. It implements a two-candle pattern trading strategy with adaptive candle sizing, grid recovery, and multiple risk management features.

**Core Components:**
- `ken_gold_candle.py` - Main strategy implementation (Backtrader-based)
- `strategy_optimizer.py` - Historical data analysis and parameter optimization tool
- `optimization_results.json` - Pre-run optimization results for XAUUSD (Gold)

## Development Commands

### Running the Strategy

```bash
# Basic backtest (modify ken_gold_candle.py to configure datafeed first)
python ken_gold_candle.py
```

Note: The strategy uses hardcoded parameters. No CLI arguments are supported as this is designed for TradeLocker deployment.

### Strategy Optimization

The optimizer downloads historical 1-minute data from Polygon.io and tests various parameter combinations to find profitable settings.

**Requirements:**
```bash
pip install -r requirements_optimizer.txt  # If this file exists
# Otherwise: pip install requests pandas numpy
```

**Basic Analysis (no optimization):**
```bash
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

### Modifying Strategy Parameters

1. Open `ken_gold_candle.py`
2. Modify class variables (lines 44-132)
3. Run backtest to verify changes

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

1. **Hardcoded Parameters** - Strategy is designed for TradeLocker deployment where parameters are typically hardcoded rather than user-adjustable.

2. **Backtrader Framework** - Uses Backtrader for backtesting rather than MT5/cTrader native backtest engine. This provides more flexibility but requires careful contract size configuration.

3. **Separate Optimizer** - Optimization is a standalone tool rather than integrated into the strategy. This allows running historical analysis without modifying the live trading code.

4. **ATR vs Percentile Methods** - Two mutually exclusive approaches to adaptive candle sizing:
   - ATR: Better for strategies that need to adapt continuously to volatility
   - Percentile: Better for strategies that prefer stability over a rolling window

5. **Time Filter Critical** - The strategy uses a 5 AM - 12 PM time window. The optimizer must use `--start-hour` and `--end-hour` flags to match this, otherwise results will show inflated signal counts (24/7 trading vs 7-hour window).

## Important Files to Check

- `OPTIMIZER_README.md` - Comprehensive optimizer documentation with usage examples and best practices
- `optimization_results.json` - Pre-run results for XAUUSD (May-Sept 2025) showing optimal TP/SL: 3.0x/2.0x ATR
- Deleted files in git status: `BUGFIX_VALIDATION.md`, `comprehensive_results.json`, `comprehensive_results_fixed.json` - These appear to be debugging artifacts that have been removed

## Notes

- Polygon.io API key required for optimizer (free tier: 5 calls/min, basic plan: $29/mo recommended)
- Strategy optimized for $10k account with 0.01 lot minimum
- Grid trading is optional and disabled by default (ENABLE_GRID = False)
- Always test parameter changes on demo account before live trading
- The optimizer's profitability calculations are estimates - full Backtrader backtests provide more accurate results
