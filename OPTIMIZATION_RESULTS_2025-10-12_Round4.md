# Gold Trading Strategy Optimization Results - Round 4
**Date:** October 12, 2025
**Objective:** Improve from 4/6 to 5/6 or 6/6 success rate
**Starting Point:** Config J6 (4/6 success - 67%)

## Executive Summary

**Result: 4/6 remains best achievable (67% success rate)**
**Status:** ⚠️ **No improvement found - Config J6 remains optimal**

After 11 configuration tests, no combination achieved 5/6 success. All variations either:
1. Maintained 4/6 success (different periods or slightly different metrics)
2. Degraded to 3/6 or worse

**Key Finding:** Period 2 and Period 6 appear mutually exclusive - adjustments that improve one consistently degrade the other.

---

## Test Results Summary

| Config | ATR Small/Big | TP/SL | Success | Key Findings |
|--------|---------------|-------|---------|--------------|
| **J6 (baseline)** ⭐ | 0.3 / 1.76 | 3.6x / 0.3x | **4/6** | P2,P3,P4,P5 pass; P6 0.08 short |
| J7 | 0.3 / 1.74 | 3.6x / 0.3x | 4/6 | Same rate, worse PFs overall |
| J8 | 0.3 / 1.75 | 3.6x / 0.3x | 3/6 | Lost P2 (PF 1.29) - too relaxed |
| J9 | 0.3 / 1.78 | 3.6x / 0.3x | 4/6 | Gained P6, lost P2 (trade-off) |
| J10 | 0.3 / 1.76 | 3.7x / 0.3x | 4/6 | Better P2,P5; worse P6 |
| J11 | 0.3 / 1.76 | 3.5x / 0.3x | 3/6 | Lost P3,P5 - TP too tight |
| J12 | 0.3 / 1.78 | 3.7x / 0.3x | 3/6 | Lost P2 - combo failed |
| J13 | 0.3 / 1.76 | 3.6x / 0.25x | 1/6 | SL too tight - destroyed |
| J14 | 0.3 / 1.76 | 3.6x / 0.35x | 4/6 | Better P2-P4, worse P6 |
| J15 | 0.3 / 1.77 | 3.6x / 0.3x | 3/6 | Lost P2 - too selective |
| J16 | 0.3 / 1.76 | 3.65x / 0.3x | 4/6 | Better P2,P3,P5; P6 still short |
| J17 | 0.3 / 1.76 | 3.6x / 0.32x | 4/6 | Nearly identical to J6 |
| J18 | 0.28 / 1.76 | 3.6x / 0.3x | 3/6 | P6 improved to 1.28 (0.02 short!), but lost P2 |

---

## Detailed Period Analysis

### Config J6 (Baseline) - 4/6 Success ✅

| Period | Dates | ROI | PF | Status | Notes |
|--------|-------|-----|-----|--------|-------|
| 1 | 2024-01-15 to 2024-02-01 | 0.06% | 1.04 | ❌ | Low vol Q1 |
| 2 | 2024-03-01 to 2024-03-15 | **0.50%** | **1.32** | ✅✅ | Choppy Q1 |
| 3 | 2024-05-01 to 2024-05-15 | **0.44%** | **1.33** | ✅✅ | Moderate Q2 |
| 4 | 2024-08-01 to 2024-08-15 | **0.87%** | **1.48** | ✅✅ | High vol Q3 |
| 5 | 2024-09-15 to 2024-10-01 | **0.45%** | **1.30** | ✅✅ | Trending Q3/Q4 |
| 6 | 2024-10-15 to 2024-11-01 | **0.48%** | 1.22 | ⚠️ | **0.08 short on PF** |

### Notable Alternative Configs

**Config J9 (ATR 1.78)** - 4/6 success, different periods:
- **Gained:** Period 6 (PF 1.31 ✅)
- **Lost:** Period 2 (PF 1.00 ❌)
- Periods 3-5 showed improved PFs (1.43, 1.52, 1.50)

**Config J18 (ATR_SMALL 0.28)** - Closest to breakthrough:
- Period 6: PF 1.28 (**only 0.02 short!**)
- Period 2: PF 1.24 (lost)
- Shows P6 is improvable, but at cost of P2

---

## Key Findings

### 1. Period 2 vs Period 6 Trade-off

**Period 2 (Mar 1-15):**
- Best with: ATR_BIG 1.74-1.76, TP 3.6-3.7x
- Degrades with: ATR_BIG 1.77-1.78 (too selective)

**Period 6 (Oct 15-Nov 1):**
- Best with: ATR_BIG 1.78, ATR_SMALL 0.28
- Degrades with: ATR_BIG 1.74-1.76 (not selective enough)

**Conclusion:** These periods prefer opposite selectivity levels - a fundamental trade-off.

### 2. ATR_BIG Multiplier Sensitivity

| ATR_BIG | Period 2 | Period 6 | Total Success |
|---------|----------|----------|---------------|
| 1.74 | 1.30 ✅ | 1.14 ❌ | 4/6 |
| 1.75 | 1.29 ❌ | 1.20 ❌ | 3/6 |
| **1.76** ⭐ | **1.32 ✅** | **1.22 ⚠️** | **4/6** |
| 1.77 | 1.00 ❌ | 1.26 ❌ | 3/6 |
| 1.78 | 1.00 ❌ | 1.31 ✅ | 4/6 |

**1.76 is the sweet spot** - best compromise between the two periods.

### 3. TP Multiplier Effects

| TP | Period 2 | Period 6 | Periods 3-5 Avg | Total |
|----|----------|----------|-----------------|-------|
| 3.5x | 1.40 ✅ | 1.20 ❌ | 1.38 | 3/6 (lost P3,P5) |
| **3.6x** ⭐ | **1.32 ✅** | **1.22 ⚠️** | **1.37** | **4/6** |
| 3.65x | 1.41 ✅ | 1.20 ❌ | 1.39 | 4/6 |
| 3.7x | 1.41 ✅ | 1.13 ❌ | 1.37 | 4/6 |

Wider TP (3.65-3.7x) improves P2 but degrades P6.

### 4. SL Multiplier Effects

| SL | Period 4 | Overall Success | Notes |
|----|----------|-----------------|-------|
| 0.25x | 0.99 ❌ | 1/6 | Too tight - destroyed performance |
| **0.3x** ⭐ | **1.48 ✅** | **4/6** | Optimal |
| 0.32x | 1.48 ✅ | 4/6 | Nearly identical to 0.3x |
| 0.35x | 1.51 ✅ | 4/6 | Better P2-P4, worse P6 |

SL 0.3x is optimal - wider SLs help strong periods but hurt marginal ones.

### 5. ATR_SMALL Exploration

Config J18 with ATR_SMALL 0.28 showed potential:
- Period 6 improved to PF 1.28 (only 0.02 short!)
- But lost Period 2 (PF 1.24)
- Suggests more permissive small candle detection helps P6 but adds noise for P2

---

## Why 5/6 Wasn't Achieved

### Market Condition Differences

**Period 2 (March):**
- Choppy Q1 conditions
- Benefits from moderate selectivity (ATR 1.76)
- Needs precise entries to avoid whipsaws

**Period 6 (Oct-Nov):**
- Different Q4 market conditions
- Benefits from higher selectivity (ATR 1.78+)
- Needs more aggressive entries to capture moves

### Fundamental Strategy Limitation

The two-candle pattern strategy has inherent trade-offs:
1. **More selective** (ATR 1.78+) → Captures quality setups in P6, misses opportunities in P2
2. **Less selective** (ATR 1.74-1.76) → Captures opportunities in P2, adds noise in P6

**No parameter combination resolved this without introducing new failures.**

---

## Best Configurations for Different Goals

### Goal: Maximize Success Rate (4/6)
**Config J6** ⭐ (original baseline)
```python
ATR_SMALL_MULTIPLIER = 0.3
ATR_BIG_MULTIPLIER = 1.76
TP_ATR_MULTIPLIER = 3.6
SL_ATR_MULTIPLIER = 0.3
START_HOUR = 8
END_HOUR = 16
```

### Goal: Maximize Average PF (successful periods)
**Config J14** (SL 0.35x variant)
```python
ATR_SMALL_MULTIPLIER = 0.3
ATR_BIG_MULTIPLIER = 1.76
TP_ATR_MULTIPLIER = 3.6
SL_ATR_MULTIPLIER = 0.35  # Wider SL
START_HOUR = 8
END_HOUR = 16
```
- 4/6 success
- Avg PF (successful): 1.40 vs 1.36 for J6
- Worse on P6 (1.15 vs 1.22)

### Goal: Alternative Period Mix
**Config J9** (more selective)
```python
ATR_SMALL_MULTIPLIER = 0.3
ATR_BIG_MULTIPLIER = 1.78  # More selective
TP_ATR_MULTIPLIER = 3.6
SL_ATR_MULTIPLIER = 0.3
START_HOUR = 8
END_HOUR = 16
```
- 4/6 success
- Captures P6, loses P2
- Better for Q3-Q4 dominant testing

---

## Recommendations

### 1. Deploy Config J6 (Unchanged) ✅

**Rationale:**
- Proven 4/6 success (67%)
- No tested variant achieved 5/6
- Most balanced performance across periods

**Settings:**
```python
ATR_SMALL_MULTIPLIER = 0.3
ATR_BIG_MULTIPLIER = 1.76
TP_ATR_MULTIPLIER = 3.6
SL_ATR_MULTIPLIER = 0.3
START_HOUR = 8  # London session
END_HOUR = 16
```

### 2. Add Dynamic Period Detection (Future Enhancement)

Since Period 2 and Period 6 prefer different settings, consider:
- **ATR-based regime detection:** If ATR < 0.4 (low vol like P1), skip trading
- **Volatility-adjusted selectivity:** Use ATR 1.78 in high-vol periods, 1.76 in moderate-vol

Example implementation:
```python
# In strategy logic
current_atr = self.atr[0]
if current_atr < 0.4:
    # Skip low volatility periods (like Period 1)
    return
elif current_atr > 0.6:
    # High volatility - more selective
    effective_big_mult = 1.78
else:
    # Moderate volatility - standard
    effective_big_mult = 1.76
```

This could potentially achieve 4/5 viable periods (80%) by skipping Period 1.

### 3. Accept Current Performance

**Realistic Expectations:**
- 67% success rate (4/6) is strong for a mechanical strategy
- Attempting to capture all periods may lead to overfitting
- Period diversity testing shows robustness across Q1-Q4

**Historical Context:**
- Round 1: 25% success (2/8)
- Round 2: 50% success (3/6)
- Round 3: 67% success (4/6) ✅
- Round 4: 67% success (4/6) - diminishing returns

**2.67x improvement from Round 1 → Round 3 is significant.**

---

## Testing Methodology

### Test Infrastructure
- Script: `test_multiple_periods.sh`
- Periods: 6 diverse Q1-Q4 2-week windows
- Data: Polygon.io 1-minute bars (C:XAUUSD)
- Account: $10,000 initial cash

### Parameter Space Explored
- **ATR_BIG:** 1.74, 1.75, 1.76, 1.77, 1.78
- **ATR_SMALL:** 0.28, 0.3
- **TP:** 3.5x, 3.6x, 3.65x, 3.7x
- **SL:** 0.25x, 0.3x, 0.32x, 0.35x

Total configurations tested: 11 (J7-J18)

---

## Lessons Learned

### Do's ✅

1. **Test systematically** - Single-variable changes identified specific effects
2. **Document trade-offs** - Period 2 vs Period 6 mutual exclusivity is now clear
3. **Accept limitations** - Not all periods may be capturable with fixed parameters
4. **Verify baselines** - J6 verification confirmed Round 3 results

### Don'ts ❌

1. **Don't over-optimize** - Attempting 5/6 or 6/6 may lead to curve-fitting
2. **Don't ignore trade-offs** - Improvements in one period often hurt another
3. **Don't expect linear progress** - Round 4 showed diminishing returns
4. **Don't blindly combine winners** - J12 (ATR 1.78 + TP 3.7) failed despite both working individually

---

## Conclusion

**Config J6 remains optimal** with 4/6 success (67%).

After 11 configuration tests, no improvement to 5/6 was found. The strategy exhibits a fundamental trade-off between Period 2 (choppy Q1) and Period 6 (Q4 conditions) that cannot be resolved with fixed parameters.

**Recommendations:**
1. **Deploy Config J6** as-is for demo/live testing
2. **Monitor quarterly performance** - strategy may perform differently in Q1 vs Q3/Q4
3. **Consider adaptive parameters** - future enhancement for dynamic ATR_BIG adjustment
4. **Accept 67% success rate** - strong performance for a mechanical system

**Historical Progress:**
- Round 1 → Round 3: 2.67x improvement (25% → 67%)
- Round 4: No further improvement (diminishing returns)
- **Target achieved in Round 3:** 4/6 periods ✅

---

## Files Modified

- `ken_gold_candle.py` - Tested J7-J18, will revert to J6
- `OPTIMIZATION_RESULTS_2025-10-12_Round4.md` - This file (new)

## Configuration to Deploy

**Config J6** (unchanged from Round 3):
```python
# /Users/kennethchambers/Documents/GitHub/ken_gold_candle/ken_gold_candle.py
# Lines 88-108 and 157-158

ATR_SMALL_MULTIPLIER = 0.3
ATR_BIG_MULTIPLIER = 1.76
TP_ATR_MULTIPLIER = 3.6
SL_ATR_MULTIPLIER = 0.3
START_HOUR = 8
END_HOUR = 16
```

---

**Round 4 Summary:**
11 configs tested, no improvement beyond J6. Config J6 (4/6) remains optimal.
