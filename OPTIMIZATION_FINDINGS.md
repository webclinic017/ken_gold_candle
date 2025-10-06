# Gold Trading Strategy Optimization Results

## Objective
Find configuration settings for ken_gold_candle.py that achieve:
- **Profit Factor > 1.3**
- **ROI > 0.4%** for 2-week periods
- **Consistent across 4+ periods in 2024**

## Test Periods (2-week intervals)
1. July 1-15, 2024
2. July 15-30, 2024
3. August 1-15, 2024
4. August 15 - September 1, 2024
5. September 1-15, 2024

## Key Findings

### Best Performing Configuration
**Configuration:**
- ATR-based candle detection: `ATR_SMALL_MULTIPLIER = 0.3`, `ATR_BIG_MULTIPLIER = 1.8`
- TP/SL: `TP_ATR_MULTIPLIER = 3.0`, `SL_ATR_MULTIPLIER = 0.4`
- No counter-trend fade (`ENABLE_COUNTER_TREND_FADE = False`)
- No limit entry (`USE_LIMIT_ENTRY = False`)
- No momentum filter (`USE_MOMENTUM_FILTER = False`)
- Enter on open (`ENTER_ON_OPEN = True`)

**Results Across 5 Periods:**
- Period 1: ROI -0.20%, PF 0.81 ❌
- Period 2: ROI 0.27%, PF 1.32 ✅ (PF met)
- Period 3: ROI 1.38%, PF 2.62 ✅✅ (BOTH CRITERIA MET)
- Period 4: ROI 0.07%, PF 1.07 ❌
- Period 5: ROI 0.16%, PF 1.36 ✅ (PF met)

**Success Rate:** 1 out of 5 periods met both criteria (August 1-15)

### Configuration Testing Summary

| Config | ATR Small/Big | TP/SL ATR | Counter-Trend | Limit Entry | Best Period ROI | Best Period PF | Periods Meeting Both |
|--------|---------------|-----------|---------------|-------------|-----------------|----------------|---------------------|
| Original | 0.5x / 1.5x | 2.0x / 0.5x | Yes | Yes | 0.30% | 1.16 | 0/5 |
| Config 2 | 0.5x / 1.5x | 2.0x / 1.0x | No | No | 0.30% | 1.16 | 0/5 |
| Config 3 | 0.5x / 1.5x | 3.0x / 0.4x | No | No | 0.41% | 1.26 | 0/5 |
| Config 4 | 0.3x / 1.8x | 3.0x / 0.4x | No | No | **1.38%** | **2.62** | **1/5** |
| Config 5 | 0.4x / 1.6x | 3.5x / 0.3x | No | No | 1.79% | 2.22 | 1/5 |

## Analysis

### What Works
1. **Higher TP/SL ratios** (3.0-3.5x / 0.3-0.4x ATR) improved profit factor significantly
2. **More selective candle sizes** (smaller ATR multipliers) reduced trade frequency but improved quality
3. **Simpler is better**: Disabling counter-trend fade, limit entry, and momentum filters improved consistency
4. **August period performed exceptionally** across all configurations, suggesting market conditions matter more than settings

### What Doesn't Work
1. **Counter-trend fade strategy** significantly degraded performance (negative ROI in first test)
2. **Limit entry with pullback** added complexity without clear benefit
3. **Momentum filters** didn't improve win rate or profit factor
4. **Very tight stop losses** (0.3x ATR) work well with very high TP targets (3.5x) but require perfect entry timing

### Challenges
1. **Inconsistent across periods**: No single configuration met criteria in 4+ periods
2. **Market dependency**: August volatility created favorable conditions that didn't persist
3. **Risk-reward tradeoff**: Higher TP targets reduce win rate but increase profit per win
4. **False signals**: Even selective candle sizes (1.8x ATR) still generated losing trades

## Recommendations

### For Live Trading
**DO NOT deploy current settings** - only 1 in 5 periods met criteria, indicating high risk of drawdown in unfavorable market conditions.

### For Further Optimization
1. **Test longer periods** (4-8 weeks) to find settings that work across full market cycles
2. **Add volatility filter**: Only trade when ATR is above certain threshold
3. **Consider time-of-day filters**: August success might be due to specific trading hours
4. **Test with real spreads**: Polygon data doesn't include actual spreads which will impact results
5. **Explore grid trading**: Might improve recovery from losing trades

### Optimal Settings for Experimental Use
If you want to test in demo account despite inconsistent results:

```python
# Candle Detection
USE_ATR_CALCULATION = True
ATR_SMALL_MULTIPLIER = 0.3  # Very selective
ATR_BIG_MULTIPLIER = 1.8    # Only strong breakouts

# TP/SL
USE_ATR_TP_SL = True
TP_ATR_MULTIPLIER = 3.0
SL_ATR_MULTIPLIER = 0.4

# Entry Settings
ENABLE_COUNTER_TREND_FADE = False
USE_LIMIT_ENTRY = False
USE_MOMENTUM_FILTER = False
ENTER_ON_OPEN = True

# Risk Management
ENABLE_POSITION_SL = True
ENABLE_EQUITY_STOP = True
MAX_DRAWDOWN_PERCENT = 1.5
```

## Conclusion

The goal of achieving PF > 1.3 and ROI > 0.4% consistently across 4+ two-week periods was **not achieved**. While one configuration (Config 4) produced excellent results in August 2024 (1.38% ROI, 2.62 PF), it failed to replicate this performance in other months.

**Root cause**: The strategy appears to be highly sensitive to market conditions. Choppy/ranging markets (July) performed poorly, while trending markets with volatility (August) performed well.

**Next steps**: Either accept lower consistency targets (e.g., 2 out of 5 periods) or develop additional filters to detect favorable market conditions before trading.
