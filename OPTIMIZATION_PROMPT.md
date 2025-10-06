# Strategy Optimization Prompt

## Context

You are analyzing a gold trading strategy repository to find optimal configuration settings. Your goal is to achieve specific performance targets consistently across multiple time periods.

## Objective

Find configuration settings for `ken_gold_candle.py` that achieve:

- **Profit Factor > 1.3**
- **ROI > 0.4%** for 2-week periods
- **Confirmed in at least 4 different 2-week periods** (not necessarily consecutive)
- **try changing the week start and end dates 2 times if necessary**

## Key Information

### API Credentials

```
POLYGON_API_KEY: [obfscuated]
```

### Important Technical Details

1. **Polygon Ticker Format**: Use `C:XAUUSD` (NOT `X:XAUUSD`) for gold forex data
2. **Timeframe**: Use 1-minute data (`--timeframe 1 --timespan minute`)
3. **Account Size**: Use `--initial-cash 10000` for consistency
4. **File to Modify**: Only change configuration variables in `ken_gold_candle.py` (lines 66-177)
5. **DO NOT modify code logic** - only configuration parameters

### Available Tools

- `backtest_runner.py` - Run full backtests with Polygon API data
- `strategy_optimizer.py` - Analyze historical data for optimal parameters
- `test_multiple_periods.sh` - Test configuration across multiple periods
- `optimization_results.json` - Pre-computed optimization results (2024 data)

### Configuration Parameters to Test

Located in `ken_gold_candle.py`:

**Candle Detection (lines 80-82):**

```python
ATR_SMALL_MULTIPLIER = 0.5  # Try: 0.3-0.6
ATR_BIG_MULTIPLIER = 1.5    # Try: 1.3-2.0
```

**TP/SL Ratios (lines 99-100):**

```python
TP_ATR_MULTIPLIER = 2.0  # Try: 2.0-4.0
SL_ATR_MULTIPLIER = 0.5  # Try: 0.3-1.0
```

**Entry Filters (lines 160-164, 173):**

```python
USE_LIMIT_ENTRY = True           # Try: True/False
USE_MOMENTUM_FILTER = True       # Try: True/False
ENABLE_COUNTER_TREND_FADE = True # Try: True/False
```

## Workflow

### Step 1: Read Documentation

```bash
# Review these files to understand the strategy:
- CLAUDE.md (development guide)
- OPTIMIZER_README.md (optimizer usage)
- optimization_results.json (pre-run results)
- OPTIMIZATION_FINDINGS.md (previous optimization attempts)
```

### Step 2: Backup Original Settings

```bash
cp ken_gold_candle.py ken_gold_candle.py.backup
```

### Step 3: Review Existing Optimization Data

Check `optimization_results.json` for best historical TP/SL ratios:

```json
{
  "tp_multiplier": 3.5,
  "sl_multiplier": 0.3,
  "profit_factor": 1.74 // Best from 2024 data
}
```

### Step 4: Define Test Periods

Create 6+ two-week test periods across 2024 (use different market conditions):

```python
periods = [
    "2024-01-01 to 2024-01-15",  # Q1
    "2024-04-01 to 2024-04-15",  # Q2
    "2024-07-01 to 2024-07-15",  # Q3
    "2024-08-01 to 2024-08-15",  # Volatile period
    "2024-09-01 to 2024-09-15",  # Q3 end
    "2024-10-01 to 2024-10-15",  # Q4 (if available)
]
```

### Step 5: Test Baseline Configuration

```bash
export POLYGON_API_KEY="[obfscuated]"
./test_multiple_periods.sh
```

Review output:

```
Period 1: ROI X.XX%, PF X.XX
Period 2: ROI X.XX%, PF X.XX
...
```

### Step 6: Iterate on Configuration

Based on results:

**If Profit Factor is low (<1.3):**

- Increase TP/SL ratio (try 3.0x / 0.4x or 3.5x / 0.3x)
- Make candle detection more selective (increase BIG_MULTIPLIER to 1.7-1.8)
- Disable experimental features (COUNTER_TREND_FADE, LIMIT_ENTRY, MOMENTUM_FILTER)

**If ROI is low (<0.4%):**

- Increase trade frequency (decrease BIG_MULTIPLIER to 1.3-1.4)
- Test different TP targets (2.5x - 3.0x ATR)
- Ensure time filter is active (START_HOUR=4, END_HOUR=13)

**If inconsistent across periods:**

- Find middle ground between aggressive/conservative settings
- Test with simpler configuration (disable all extra filters)
- Consider market-condition filters (volatility threshold)

### Step 7: Document Changes

For each configuration tested, record:

```
Config X:
- ATR_SMALL_MULTIPLIER: X.X
- ATR_BIG_MULTIPLIER: X.X
- TP_ATR_MULTIPLIER: X.X
- SL_ATR_MULTIPLIER: X.X
- Filters: [LIST]

Results:
- Period 1: ROI X.XX%, PF X.XX ✅/❌
- Period 2: ROI X.XX%, PF X.XX ✅/❌
...
- Success Rate: X/6 periods
```

### Step 8: Validate Best Configuration

Once you find settings that meet criteria in 4+ periods:

```bash
# Test on additional periods not used during optimization
python backtest_runner.py --ticker C:XAUUSD \
  --start-date 2024-11-01 --end-date 2024-11-15 \
  --timeframe 1 --timespan minute --initial-cash 10000
```

### Step 9: Create Summary Report

Document findings in `OPTIMIZATION_RESULTS_[DATE].md`:

- Best configuration found
- Success rate across all periods
- Performance metrics (avg ROI, avg PF, Sharpe, max DD)
- Recommendations for live trading
- Caveats and limitations

### Step 10: Revert Changes

```bash
# Restore original file
cp ken_gold_candle.py.backup ken_gold_candle.py

# Keep these files for future reference:
- test_multiple_periods.sh
- OPTIMIZATION_RESULTS_[DATE].md
- Any modified test periods in the script
```

## Expected Output

### Success Criteria Met

```
✅ OPTIMIZATION SUCCESSFUL

Best Configuration:
- ATR_SMALL_MULTIPLIER: 0.4
- ATR_BIG_MULTIPLIER: 1.6
- TP_ATR_MULTIPLIER: 3.0
- SL_ATR_MULTIPLIER: 0.4

Results Across 6 Periods:
1. Jan 1-15: ROI 0.52%, PF 1.42 ✅✅
2. Apr 1-15: ROI 0.38%, PF 1.31 ❌✅
3. Jul 1-15: ROI 0.61%, PF 1.55 ✅✅
4. Aug 1-15: ROI 1.38%, PF 2.62 ✅✅
5. Sep 1-15: ROI 0.45%, PF 1.38 ✅✅
6. Oct 1-15: ROI 0.33%, PF 1.28 ❌❌

Success Rate: 4/6 periods met both criteria (66.7%)
Average ROI: 0.61%
Average PF: 1.59

✅ CRITERIA MET: 4 periods achieved PF>1.3 AND ROI>0.4%
```

### Success Criteria Not Met

```
❌ OPTIMIZATION INCOMPLETE

After testing 10+ configurations across 6 periods:
- Best single-period: ROI 1.38%, PF 2.62 (Aug 1-15)
- Most consistent config achieved criteria in only 2/6 periods

Root Cause Analysis:
- Strategy is market-condition dependent
- Works well in trending/volatile markets (August)
- Underperforms in choppy/ranging markets (July)

Recommendations:
1. Add volatility filter (only trade when ATR > threshold)
2. Test longer periods (4-week windows)
3. Consider market regime detection
4. Lower target thresholds (PF>1.2, ROI>0.3%)

See OPTIMIZATION_FINDINGS.md for complete analysis.
```

## Tips for Success

1. **Start with optimizer results**: `optimization_results.json` contains pre-computed best TP/SL ratios
2. **Test simple first**: Disable all extra features, use baseline ATR settings (0.5x/1.5x)
3. **Iterate systematically**: Change one category at a time (candles, then TP/SL, then filters)
4. **Watch for overfitting**: If one period performs way better than others, settings may be overfit to that condition
5. **Document everything**: Keep track of all configurations tested to avoid repeating failures
6. **Validate externally**: Test final config on periods not used during optimization

## Common Pitfalls

❌ **Don't:**

- Change code logic (only modify configuration values)
- Test fewer than 4 periods (not enough for validation)
- Use consecutive periods only (test different quarters)
- Ignore consistency (4 successes out of 4 tests in August isn't robust)
- Forget to backup original file

✅ **Do:**

- Use diverse test periods (different quarters, market conditions)
- Document why each change was made
- Test simpler configurations first
- Check Polygon API responses (use `C:XAUUSD` ticker)
- Keep test_multiple_periods.sh for future use

## Follow-Up Tasks

After optimization:

1. Demo test recommended settings for 2-4 weeks
2. Monitor performance vs backtest predictions
3. Adjust for real spreads/slippage
4. Re-optimize quarterly with new data
5. Update CLAUDE.md with new findings
