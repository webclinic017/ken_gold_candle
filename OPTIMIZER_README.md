# Strategy Optimizer - User Guide

This tool analyzes historical 1-minute crypto/forex data to find optimal settings for your two-candle pattern trading strategy.

## ⚠️ IMPORTANT LIMITATIONS

**This optimizer tests a SIMPLIFIED version of your strategy. Results will differ from live trading:**

### What the Optimizer DOES Test ✅

- ✅ Two-candle pattern detection (small setup → big trigger)
- ✅ ATR-based and percentile-based candle sizing
- ✅ Take profit and stop loss execution
- ✅ Trend filter (EMA/SMA based)
- ✅ **Time filter (NEW)** - Use `--start-hour` and `--end-hour` flags

### What the Optimizer DOES NOT Test ❌

- ❌ **Grid trading** - No multi-position tracking or recovery mechanism
- ❌ **Trailing stops** - Individual position trailing not simulated
- ❌ **Equity stops** - No hard drawdown or trailing equity stops
- ❌ **MAX_OPEN_TRADES** - Optimizer doesn't limit concurrent positions
- ❌ **Spread filter** - Not implemented (minor impact)
- ❌ **Slippage** - Assumes perfect fills at exact prices

### Impact on Results

- **Without time filter**: Results will show ~3x more signals than strategy's 5AM-12PM window
- **Without grid**: Actual strategy has recovery mechanism that changes risk/reward profile
- **Without equity stops**: Real strategy has additional risk management not reflected in P&L

### Recommendations

1. **Always use `--start-hour 5 --end-hour 12`** to match your strategy's time filter
2. Use optimizer results as **starting points**, not final values
3. Run full Backtrader backtests to validate with all features enabled
4. Test on demo account before live trading

## 🎯 What's New - Profitability Tracking

**The optimizer now measures actual profitability, not just signal counts!**

✅ **Which candle sizes generate the highest profit** - Tests combinations and ranks by total P&L  
✅ **Optimal TP/SL ratios** - Tests TP/SL as ATR multipliers and finds best risk:reward  
✅ **Win rate & profit factor** - Full performance metrics for every test  
✅ **Drawdown statistics** - Calculates max drawdown and risk-adjusted returns  
✅ **Grid parameter effectiveness** - Tests grid spacing and lot multipliers  
✅ **ATR-based optimization** - NEW! Optimize using ATR multipliers instead of percentiles for candle detection

## Strategy Overview

Your strategy looks for a **two-candle pattern**:

1. **Setup candle** (bar -2): Small, consolidation candle
2. **Trigger candle** (bar -1): Big, breakout candle

The optimizer helps you find the best thresholds to define "small" vs "big" candles using two methods:

### Method 1: Percentile-Based (USE_PERCENTILE_CALCULATION)

- Analyzes last N candles (default: 200)
- Defines thresholds based on percentiles
- **Example**: Small = 20th percentile, Big = 90th percentile
- Updates every N candles to adapt to changing volatility

### Method 2: ATR-Based (USE_ATR_CALCULATION)

- Uses Average True Range (ATR) as baseline volatility measure
- Defines thresholds as ATR multipliers
- **Example**: Small = 0.5x ATR, Big = 1.5x ATR
- Updates every bar automatically

## Installation

1. Install dependencies:

```bash
pip install -r requirements_optimizer.txt
```

2. Get a Polygon.io API key:
   - Sign up at https://polygon.io/
   - Free tier includes 5 API calls per minute
   - Basic plan ($29/month) recommended for extensive optimization

## Time Filter (NEW Feature)

The optimizer now supports time-based filtering to match your strategy's `ENABLE_TIME_FILTER` setting.

### How It Works

- Your strategy only trades during specific hours (default: 5 AM - 12 PM)
- Without time filter, optimizer tests 24/7 trading and shows inflated results
- Use `--start-hour` and `--end-hour` flags to match your strategy's trading hours

### Usage

```bash
# Match strategy's default time window (5 AM - 12 PM)
--start-hour 5 --end-hour 12

# Custom time window (9 AM - 5 PM)
--start-hour 9 --end-hour 17

# No time filter (tests 24/7 - not recommended)
# Omit both flags
```

### Important Notes

- Both flags must be used together (can't set only one)
- Hours must be 0-23 (24-hour format)
- End hour is exclusive: `--start-hour 5 --end-hour 12` means 5:00 AM to 11:59 AM
- Optimizer will warn you if time filter is disabled

## ATR-Based Optimization (NEW Feature)

The optimizer now supports **ATR-based candle detection** for profitability optimizations.

### What's the Difference?

**Percentile Method (Default):**

- Uses rolling percentiles (e.g., 30th/80th) to define small/big candles
- Adapts to recent volatility over lookback period
- Tests different percentile thresholds to find most profitable

**ATR Method (NEW):**

- Uses ATR multipliers (e.g., 0.5x/1.5x) to define small/big candles
- Adapts continuously with ATR updates
- Tests different ATR multipliers to find most profitable

### When to Use ATR Method

Use `--use-atr-method` if:

- Your strategy uses `USE_ATR_CALCULATION = True` (not percentile-based)
- You want results that match your ATR-based strategy settings
- You prefer dynamic volatility adaptation over percentile-based thresholds

### Usage

```bash
# Basic: Use ATR-based optimization with defaults (0.5x / 1.5x)
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --use-atr-method

# Advanced: Specify custom ATR multipliers
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --use-atr-method \
  --atr-small-mult 0.6 \
  --atr-big-mult 1.8

# Optimize TP/SL with ATR-based candle detection
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --use-atr-method \
  --optimize-tp-sl

# Find most profitable ATR multipliers (candle sizes)
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --use-atr-method \
  --optimize-candle-profitability
```

### Important: Match Your Strategy

**If your strategy uses:**

```python
USE_ATR_CALCULATION = True
```

**Then you MUST use:**

```bash
--use-atr-method
```

Otherwise, the optimizer will test percentile-based detection while your strategy uses ATR-based, leading to mismatched results.

## Usage Examples

### Basic Analysis (No Optimization)

Analyzes data and tests current default settings:

```bash
python strategy_optimizer.py \
  --api-key YOUR_POLYGON_API_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12
```

**⚠️ Note:** Always include `--start-hour 5 --end-hour 12` to match your strategy's time filter!

This will:

- Download 1-minute BTCUSD data
- Calculate candle size distributions
- Test default percentile settings (20th/90th)
- Test default ATR settings (0.5x/1.5x)
- Analyze volatility for TP/SL suggestions
- Generate recommendations

### Optimize Percentile Thresholds

Test multiple combinations to find best percentile settings:

```bash
python strategy_optimizer.py \
  --api-key YOUR_POLYGON_API_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-percentile
```

This tests all combinations of:

- Small candle: 10%, 15%, 20%, 25%, 30%, 35%, 40%
- Big candle: 70%, 75%, 80%, 85%, 90%, 95%

Shows which combination generates the most valid signals.

### Optimize ATR Multipliers

Test multiple combinations to find best ATR multipliers:

```bash
python strategy_optimizer.py \
  --api-key YOUR_POLYGON_API_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-atr
```

This tests all combinations of:

- Small multiplier: 0.3x, 0.4x, 0.5x, 0.6x, 0.7x, 0.8x, 0.9x, 1.0x
- Big multiplier: 1.0x, 1.1x, 1.2x, ..., 2.5x

### Optimize TP/SL Ratios (NEW)

Find the most profitable Take Profit and Stop Loss levels:

```bash
python strategy_optimizer.py \
  --api-key YOUR_POLYGON_API_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-tp-sl
```

**Output:**

```
🏆 BEST TP/SL CONFIG:
   TP: 2.5x ATR
   SL: 1.0x ATR
   Risk:Reward: 2.5
   Total P&L: $12,450.00
   Win Rate: 58.3%
   Profit Factor: 2.14
```

### Find Most Profitable Candle Sizes (NEW)

Answers: "Which candle sizes actually make money?"

```bash
python strategy_optimizer.py \
  --api-key YOUR_POLYGON_API_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-candle-profitability
```

**Output:**

```
🏆 MOST PROFITABLE CANDLE SIZES:
   Small: 30%
   Big: 80%
   Total P&L: $8,234.50
   Trades: 47
   Win Rate: 61.7%
   Profit Factor: 2.41
```

### Optimize Grid Parameters (NEW - Experimental)

**⚠️ Note:** This is a simplified baseline analysis. Full grid backtesting with multi-position tracking is not yet implemented.

```bash
python strategy_optimizer.py \
  --api-key YOUR_POLYGON_API_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --optimize-grid
```

Provides recommended starting points for grid spacing and lot multipliers based on baseline strategy performance.

### Complete Optimization Run

Run ALL optimization methods in one command:

```bash
python strategy_optimizer.py \
  --api-key YOUR_POLYGON_API_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-all \
  --output comprehensive_results.json
```

This runs:

- Signal count analysis (percentile & ATR)
- TP/SL optimization
- Candle profitability analysis
- Grid parameter recommendations

### Different Crypto Symbols

Test with Ethereum or Gold:

```bash
# Ethereum
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol ETHUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-percentile

# Gold (if available on your Polygon plan)
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-atr
```

## Output

The script generates a JSON file with comprehensive results:

```json
{
  "symbol": "BTCUSD",
  "start_date": "2025-09-01",
  "end_date": "2025-09-30",
  "recommendations": {
    "percentile_method": {
      "recommended": {
        "small": 20,
        "big": 90,
        "lookback": 200,
        "update_frequency": 200
      }
    },
    "atr_method": {
      "recommended": {
        "small_multiplier": 0.5,
        "big_multiplier": 1.5,
        "atr_period": 14
      }
    },
    "risk_management": {
      "mean_atr": 45.23,
      "suggested_tp": 35.67,
      "suggested_sl": 67.85
    }
  },
  "percentile_optimization": [...],
  "atr_optimization": [...]
}
```

## Understanding Results

### Performance Metrics (NEW)

The optimizer now tracks actual profitability with comprehensive metrics:

#### Total P&L

- Total profit/loss from all simulated trades
- **What you want:** Positive and as high as possible
- **Caveat:** Must be balanced with drawdown

#### Win Rate

- Formula: (Winning trades / Total trades) × 100
- **Typical range:** 40-60% for 2:1 R:R strategies
- **Note:** High win rate ≠ profitable if losses are too large

#### Profit Factor

- Formula: Gross profit / Gross loss
- **Interpretation:**
  - `< 1.0` = Losing strategy
  - `1.0 - 1.5` = Marginally profitable
  - `1.5 - 2.5` = Good strategy
  - `> 2.5` = Excellent (or possibly over-optimized)

#### Maximum Drawdown

- Largest peak-to-trough decline in equity
- **Why it matters:** Risk of ruin, position sizing
- **Rule of thumb:** Drawdown should be < 30% of total P&L

#### Sharpe Ratio

- Risk-adjusted returns (not annualized)
- **Interpretation:**
  - `< 0.5` = Poor risk-adjusted returns
  - `0.5 - 1.5` = Acceptable
  - `> 1.5` = Good
- **Note:** Use for comparing strategies, not as absolute metric

#### Expectancy

- Average P&L per trade
- **Use for:** Position sizing (Kelly Criterion)
- **What you want:** Positive and consistent

### Signal Count (Legacy)

- **Higher signal count** = More trading opportunities
- **Lower signal count** = More selective (potentially higher quality)
- **Note:** Signal count alone doesn't tell profitability - use new metrics above

### Candle Size Distribution

The analysis shows percentiles of candle ranges:

- **20th percentile** = 80% of candles are bigger (good for "small" threshold)
- **90th percentile** = 90% of candles are smaller (good for "big" threshold)

### Volatility Analysis

Suggests TP/SL levels based on:

- **ATR values**: Natural volatility measure
- **Price movement percentiles**: Historical move distances
- **Recommendations**: Balance profit capture vs stop-out risk

## Applying Results to Your Strategy

After running the optimizer, update your strategy file (`ken_gold_candle.py`):

### For Percentile Method

**Run optimizer WITHOUT `--use-atr-method` flag:**

```bash
python strategy_optimizer.py ... --optimize-candle-profitability
```

**Apply results:**

```python
USE_PERCENTILE_CALCULATION = True
SMALL_CANDLE_PERCENTILE = 25  # From optimization results
BIG_CANDLE_PERCENTILE = 85    # From optimization results
PERCENTILE_LOOKBACK = 200
PERCENTILE_UPDATE_FREQ = 200
```

### For ATR Method

**Run optimizer WITH `--use-atr-method` flag:**

```bash
python strategy_optimizer.py ... --use-atr-method --optimize-candle-profitability
```

**Apply results:**

```python
USE_ATR_CALCULATION = True
ATR_SMALL_MULTIPLIER = 0.6   # From optimization results (small_atr_multiplier)
ATR_BIG_MULTIPLIER = 1.8     # From optimization results (big_atr_multiplier)
ATR_PERIOD = 14
```

### Risk Management (Using Optimized TP/SL)

**Option 1: ATR-Based TP/SL (RECOMMENDED - Dynamic)**

Use optimizer results directly with ATR multipliers:

```python
# Enable ATR-based TP/SL (automatically adapts to volatility)
USE_ATR_TP_SL = True
TP_ATR_MULTIPLIER = 2.0      # From optimizer: --optimize-tp-sl
SL_ATR_MULTIPLIER = 1.0      # From optimizer: --optimize-tp-sl
ENABLE_POSITION_SL = True    # Enable SL if using SL multiplier
```

**Option 2: Fixed Points (Classic - Static)**

Convert ATR multipliers to fixed points:

```python
# Fixed point-based (does not adapt to volatility)
USE_ATR_TP_SL = False
TAKE_PROFIT_POINTS = 100     # Example: 2.0 x 50 ATR = 100 points
POSITION_SL_POINTS = 50      # Example: 1.0 x 50 ATR = 50 points
ENABLE_POSITION_SL = True
```

**Why ATR-Based is Better:**

- ✅ Automatically adjusts to changing market volatility
- ✅ Uses optimizer results directly (no manual conversion)
- ✅ More robust across different market conditions
- ✅ Same TP/SL works on volatile and calm days

### Grid Parameters (If Using Grid Trading)

```python
# From grid optimization results
ATR_MULTIPLIER_STEP = 3.0    # Grid spacing (conservative: 2.5-3.5x ATR)
LOT_MULTIPLIER = 1.05         # Position sizing multiplier (conservative: 1.0-1.1x)
MAX_OPEN_TRADES = 2           # Limit grid depth based on account size
```

## Best Practices

### 1. Test Multiple Time Periods

Don't optimize on a single month. Test multiple periods:

```bash
# Test Q3 2025
python strategy_optimizer.py --start 2025-07-01 --end 2025-09-30 ...

# Test Q4 2025
python strategy_optimizer.py --start 2025-10-01 --end 2025-12-31 ...
```

### 2. Consider Market Conditions

- **High volatility periods**: May need wider thresholds (higher big percentile)
- **Low volatility periods**: May need tighter thresholds (lower big percentile)
- **Trending markets**: Percentile method may work better
- **Ranging markets**: ATR method may be more stable

### 3. Avoid Over-Optimization

- Don't chase the absolute highest P&L on a single period
- Look for **consistent** performance across different periods
- Balance profitability with robustness

**Example: Choose Robust Over Peak Performance**

| Config | Sep P&L | Oct P&L | Nov P&L | Average | Std Dev |
| ------ | ------- | ------- | ------- | ------- | ------- |
| A      | $8,000  | $7,500  | $7,200  | $7,567  | $327    |
| B      | $12,000 | $2,000  | $1,500  | $5,167  | $4,815  |

**Choose Config A:** Lower peak but more consistent

### 4. Walk-Forward Analysis

1. Optimize on training period (e.g., Sep 2025)
2. Test settings on validation period (e.g., Oct 2025)
3. If results are similar, settings are robust
4. If results diverge significantly, settings may be over-fit

### 5. Combine with Other Filters

The optimizer tests the **pattern alone**. Your strategy includes:

- Trend filter (EMA/SMA)
- Time filter (trading hours)
- Spread filter
- Risk management

These additional filters will **reduce** signal count but **improve** quality.

## Example Workflow

### Recommended Approach for ATR-Based Strategy (Profitability-First)

**For strategies using `USE_ATR_CALCULATION = True`:**

```bash
# Step 1: Initial analysis - understand your data
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12

# Step 2: Find most profitable ATR multipliers (candle sizes)
# Don't pass --atr-small-mult or --atr-big-mult - we're finding them!
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --use-atr-method \
  --optimize-candle-profitability \
  --output sep_candles.json

# Review results, note best ATR multipliers (e.g., 0.6x / 1.8x ATR)

# Step 3: Find best TP/SL using optimal ATR multipliers from Step 2
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --use-atr-method \
  --atr-small-mult 0.6 \
  --atr-big-mult 1.8 \
  --optimize-tp-sl \
  --output sep_tpsl.json

# Review results, note best TP/SL (e.g., 2.5x ATR / 1.0x ATR)

# Step 4: Validate on different period (CRITICAL - avoid over-fitting)
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --start 2025-10-01 \
  --end 2025-10-31 \
  --start-hour 5 \
  --end-hour 12 \
  --use-atr-method \
  --optimize-candle-profitability \
  --output oct_candles_validation.json

# Step 5: Compare September vs October
# If results are similar → Settings are robust
# If results differ significantly → Settings may be over-fit, use more conservative values
```

### Recommended Approach for Percentile-Based Strategy

**For strategies using `USE_PERCENTILE_CALCULATION = True`:**

```bash
# Step 1: Find most profitable percentiles (candle sizes)
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-candle-profitability \
  --output sep_candles.json

# Review results, note best percentiles (e.g., 30% / 80%)

# Step 2: Find best TP/SL (no arguments needed - uses default percentiles)
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-tp-sl \
  --output sep_tpsl.json

# Review results, note best TP/SL (e.g., 2.5x ATR / 1.0x ATR)
```

### Quick Complete Analysis

```bash
# Run everything at once (takes ~10-15 minutes)
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol BTCUSD \
  --start 2025-09-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --optimize-all \
  --output comprehensive_sep.json
```

## Troubleshooting

### Error: "No data found"

- Check date format (YYYY-MM-DD)
- Ensure dates are not in the future
- Verify symbol format (BTCUSD, not BTC/USD)
- Check Polygon.io subscription level (crypto data availability)

### Error: "API Error: 429"

- You've hit rate limits (5 calls/min on free tier)
- Wait 1 minute and retry
- Consider upgrading Polygon.io plan
- Use smaller date ranges

### Error: "API Error: 401"

- Invalid API key
- Check you're using the correct key from Polygon.io dashboard

### Very Few Signals / No Trades

- Try more lenient thresholds (lower big percentile)
- Check if data period had unusual volatility
- Verify trend filter isn't too restrictive
- TP/SL might be too tight - increase TP multiplier

### Too Many Signals

- Use stricter thresholds (higher big percentile, lower small percentile)
- This is often good - additional filters in strategy will reduce them
- Focus on signal quality over quantity

### Negative P&L for All Configs

- Market conditions might not suit this strategy during test period
- Try different time period (different volatility regime)
- Consider if pattern needs refinement
- Check if TP/SL ratios are realistic

### Results Vary Wildly Between Periods

- Strategy might not be robust to changing market conditions
- Over-optimization risk - use more conservative settings
- Consider adaptive parameters or wider optimization ranges

## Advanced Customization

The optimizer is now highly extensible. You can:

### Custom TP/SL Ranges

Edit the optimizer call to test specific ranges:

```python
# In strategy_optimizer.py
tp_sl_results = analyzer.optimize_tp_sl_ratios(
    tp_range=(1.5, 4.0),    # Test higher TPs
    sl_range=(0.5, 1.5),    # Tighter SLs
    step=0.25               # Finer granularity
)
```

### Custom Candle Size Testing

```python
candle_profit_results = analyzer.optimize_candle_sizes_with_profitability(
    tp_atr_mult=2.5,        # Use your optimal TP
    sl_atr_mult=1.0,        # Use your optimal SL
    small_range=(20, 40),   # Narrow the search
    big_range=(70, 90),
    step=5                  # Finer steps
)
```

### Test Different ATR Periods

Modify the `_calculate_indicators()` method to test ATR(10), ATR(20), etc.

See the code comments for guidance on extending functionality.

## Support

For issues or questions:

1. Check this README first
2. Verify your Polygon.io API key and subscription
3. Review the error messages carefully
4. Test with a small date range first (1 week)

## Quick Reference

### Basic Analysis

```bash
python strategy_optimizer.py --api-key KEY --symbol BTCUSD --start DATE --end DATE --start-hour 5 --end-hour 12
```

### TP/SL Optimization (Percentile-Based)

```bash
python strategy_optimizer.py --api-key KEY --symbol BTCUSD --start DATE --end DATE --start-hour 5 --end-hour 12 --optimize-tp-sl
```

### TP/SL Optimization (ATR-Based)

```bash
python strategy_optimizer.py --api-key KEY --symbol BTCUSD --start DATE --end DATE --start-hour 5 --end-hour 12 --use-atr-method --optimize-tp-sl
```

### Candle Profitability (Percentile-Based)

```bash
python strategy_optimizer.py --api-key KEY --symbol BTCUSD --start DATE --end DATE --start-hour 5 --end-hour 12 --optimize-candle-profitability
```

### Candle Profitability (ATR-Based)

```bash
python strategy_optimizer.py --api-key KEY --symbol BTCUSD --start DATE --end DATE --start-hour 5 --end-hour 12 --use-atr-method --optimize-candle-profitability
```

### Complete Analysis (Percentile-Based)

```bash
python strategy_optimizer.py --api-key KEY --symbol BTCUSD --start DATE --end DATE --start-hour 5 --end-hour 12 --optimize-all
```

### Complete Analysis (ATR-Based)

```bash
python strategy_optimizer.py --api-key KEY --symbol BTCUSD --start DATE --end DATE --start-hour 5 --end-hour 12 --use-atr-method --optimize-all
```

### Gold (XAUUSD) with ATR-Based

```bash
python strategy_optimizer.py --api-key KEY --symbol XAUUSD --asset-class forex --start DATE --end DATE --start-hour 5 --end-hour 12 --use-atr-method --optimize-all
```

### Without Time Filter (24/7 Testing - Not Recommended)

```bash
# Omit --start-hour and --end-hour flags (will show warning)
python strategy_optimizer.py --api-key KEY --symbol BTCUSD --start DATE --end DATE --optimize-all
```

## Next Steps

After finding optimal settings:

1. ✅ Review profitability metrics (P&L, profit factor, drawdown)
2. ✅ Validate on multiple time periods (avoid over-fitting)
3. ✅ Update your `ken_gold_candle.py` strategy with optimized parameters:

   ```python
   # Example: Apply optimizer results
   USE_ATR_TP_SL = True           # Enable ATR-based TP/SL
   TP_ATR_MULTIPLIER = 2.5        # From optimizer output
   SL_ATR_MULTIPLIER = 1.0        # From optimizer output
   ENABLE_POSITION_SL = True      # Enable SL

   SMALL_CANDLE_PERCENTILE = 30   # From candle profitability
   BIG_CANDLE_PERCENTILE = 80     # From candle profitability
   ```

4. ✅ Run Backtrader backtest with new settings
5. ✅ Forward test on demo account
6. ✅ Monitor live performance vs optimization results
7. ✅ Re-optimize quarterly as market conditions change

## ✅ Verification: What We Can Now Test

The optimizer now supports **full profitability optimization with both methods**:

### ✅ What Works Now (After Fix)

| Feature                  | Percentile Method          | ATR Method                                            | Status       |
| ------------------------ | -------------------------- | ----------------------------------------------------- | ------------ |
| **Signal Counting**      | ✅ `--optimize-percentile` | ✅ `--optimize-atr`                                   | Working      |
| **TP/SL Profitability**  | ✅ Default mode            | ✅ `--use-atr-method --optimize-tp-sl`                | **FIXED** ✅ |
| **Candle Profitability** | ✅ Default mode            | ✅ `--use-atr-method --optimize-candle-profitability` | **FIXED** ✅ |
| **Grid Optimization**    | ✅ Default mode            | ✅ `--use-atr-method --optimize-grid`                 | **FIXED** ✅ |
| **Complete Analysis**    | ✅ `--optimize-all`        | ✅ `--use-atr-method --optimize-all`                  | **FIXED** ✅ |

### 🔴 What Was Broken (Before Fix)

**Problem:** Profitability optimizations (`--optimize-tp-sl`, `--optimize-candle-profitability`) always used **percentile-based** candle detection, even when testing ATR strategies.

**Impact:** If your strategy used `USE_ATR_CALCULATION = True`, optimizer results didn't match your strategy's actual behavior.

### 🎯 Core Functionality Review

**✅ Nothing Was Removed:**

- All original percentile-based optimization preserved (default behavior)
- Signal counting methods unchanged
- All performance metrics still calculated

**✅ What Was Added:**

- ATR-based profitability testing (new `use_atr` parameter throughout)
- Proper parameter flow from CLI → main() → optimizers → backtest
- Clear console output showing which method is active
- Automatic output formatting based on method used

**✅ Backward Compatibility:**

- Default behavior unchanged (percentile-based)
- Existing commands work identically
- Only new flag `--use-atr-method` enables ATR mode

### 📊 Testing Both Methods

**Yes, you can now test for USE_ATR + PNL!**

**The workflow depends on what you're optimizing:**

#### Step 1: Find Optimal ATR Multipliers (Candle Sizes)

```bash
# Find which ATR multipliers are most profitable
# Don't pass --atr-small-mult or --atr-big-mult - we're finding them!
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --start 2025-05-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --use-atr-method \
  --optimize-candle-profitability
```

**Output will show:**

```
🏆 MOST PROFITABLE CANDLE SIZES:
   Small: 0.6x ATR
   Big: 1.8x ATR
   Total P&L: $8,234.50
   Trades: 47
   Win Rate: 61.7%
```

**This tests combinations like:**

- 0.3x/1.0x, 0.3x/1.1x, 0.3x/1.2x... → P&L for each
- 0.4x/1.0x, 0.4x/1.1x, 0.4x/1.2x... → P&L for each
- Returns: **Best ATR multipliers by profitability**

#### Step 2: Find Optimal TP/SL Using Those ATR Multipliers

```bash
# Now use the optimal ATR multipliers from Step 1
python strategy_optimizer.py \
  --api-key YOUR_KEY \
  --symbol XAUUSD \
  --start 2025-05-01 \
  --end 2025-09-30 \
  --start-hour 5 \
  --end-hour 12 \
  --use-atr-method \
  --atr-small-mult 0.6 \
  --atr-big-mult 1.8 \
  --optimize-tp-sl
```

**Output will show:**

```
🏆 BEST TP/SL CONFIG:
   TP: 2.5x ATR
   SL: 1.0x ATR
   Total P&L: $12,450.00
   Win Rate: 58.3%
```

**This tests:**

- TP=1.0x/SL=0.5x, TP=1.5x/SL=0.5x, TP=2.0x/SL=0.5x...
- While holding candle sizes constant at 0.6x/1.8x
- Returns: **Best TP/SL ratios by profitability**

#### Why Two Steps?

| What You're Optimizing             | What Stays Fixed                 | Arguments Needed                                                    |
| ---------------------------------- | -------------------------------- | ------------------------------------------------------------------- |
| **Candle sizes** (ATR multipliers) | TP/SL ratios (default 2.0x/1.0x) | ❌ **Don't pass** `--atr-small-mult` or `--atr-big-mult`            |
| **TP/SL ratios**                   | Candle sizes (ATR multipliers)   | ✅ **Pass** `--atr-small-mult 0.6 --atr-big-mult 1.8` (from Step 1) |

**Key Insight:**

- `--optimize-candle-profitability` **finds** the ATR multipliers → don't pass them as arguments
- `--optimize-tp-sl` **uses** fixed ATR multipliers → pass them as arguments (from previous optimization)

### 🔧 Technical Implementation Flow

**How the fix works (ATR method):**

```
Command Line
    ↓
--use-atr-method flag set
    ↓
main() receives args.use_atr_method = True
    ↓
Calls: optimize_tp_sl_ratios(use_atr=True, small_atr_mult=0.5, big_atr_mult=1.4)
    ↓
For each TP/SL combination:
    Calls: backtest_strategy(use_atr=True, small_atr_mult=0.5, big_atr_mult=1.4)
        ↓
        Pattern detection uses: threshold = atr_mult × ATR value
        Not: threshold = percentile of recent ranges
        ↓
        Tracks: P&L, win rate, profit factor, drawdown
    ↓
Returns: DataFrame sorted by total_pnl
```

**What was broken before:**

```
❌ backtest_strategy(use_atr=False)  # Always False!
   ↓
   Always used: threshold = percentile × recent ranges
   Never used: threshold = atr_mult × ATR value
```

**What's fixed now:**

```
✅ backtest_strategy(use_atr=args.use_atr_method)  # Passed correctly!
   ↓
   if use_atr:
       threshold = atr_mult × ATR value  # ✅ ATR method
   else:
       threshold = percentile × recent ranges  # ✅ Percentile method
```

## Key Improvements Over Original

**Before:** Only counted signals, no profitability tracking  
**Now:** Full backtesting with P&L, win rate, profit factor, and drawdown

**Before:** Guessed at TP/SL values  
**Now:** Optimizes TP/SL ratios to find most profitable settings

**Before:** Didn't know which candle sizes make money  
**Now:** Tests and ranks candle sizes by actual profitability

**Before:** Profitability tests forced percentile method  
**Now:** Can optimize profitability with ATR OR percentile method (**FIXED**)

**Before:** ATR strategy users got mismatched results  
**Now:** ATR strategy users get accurate, applicable results (**FIXED**)

Good luck with your optimization! 🚀
