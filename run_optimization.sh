#!/bin/bash
# Parameter optimization for last 2 weeks
# Finds best settings by ROI and Profit Factor

# Check for API key
if [ -z "$POLYGON_API_KEY" ]; then
    echo "Please set your Polygon.io API key:"
    read -p "Enter API key: " api_key
    export POLYGON_API_KEY="$api_key"
fi

# Calculate dates (last 2 weeks)
END_DATE=$(date +%Y-%m-%d)
START_DATE=$(date -v-14d +%Y-%m-%d 2>/dev/null || date -d "14 days ago" +%Y-%m-%d)

echo "Optimizing for period: $START_DATE to $END_DATE"
echo "=========================================="

# Run the optimization
python optimize_parameters.py
