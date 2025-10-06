POLYGON_API_KEY: [obfscuated]

Read OPTIMIZATION_PROMPT.md and find configuration settings for ken_gold_candle.py that
achieve Profit Factor > 1.3 and ROI > 0.4% confirmed in at least 4 different 2-week periods
in 2024.

Key requirements:

- Use C:XAUUSD ticker (not X:XAUUSD)
- Test with 1-minute data
- Only modify config variables in ken_gold_candle.py (lines 66-177)
- Use ./test_multiple_periods.sh for validation
- Document all results
- Revert file when done
