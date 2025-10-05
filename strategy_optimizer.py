"""
Strategy Optimizer for Gold Candle Trading Bot

This script downloads historical 1-minute crypto data from Polygon.io and analyzes
it to find optimal settings for the two-candle pattern strategy.

The strategy looks for:
1. Small setup candle (consolidation)
2. Big trigger candle (breakout)

Optimizes:
- Percentile-based thresholds (what percentile defines "small" vs "big" candles)
- ATR-based multipliers (how many ATRs define "small" vs "big" candles)
- Other strategy parameters like take profit, stop loss, etc.

Usage:
    python strategy_optimizer.py --api-key YOUR_KEY --symbol BTCUSD --start 2025-09-01 --end 2025-09-30
"""

import argparse
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, List
import json


class PolygonDataDownloader:
    """Handles downloading historical data from Polygon.io"""
    
    BASE_URL = "https://api.polygon.io/v2/aggs/ticker"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def download_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        asset_class: str = 'crypto',
        interval: int = 1
    ) -> pd.DataFrame:
        """
        Download historical data at specified interval for a given asset class.
        
        Args:
            symbol: Ticker symbol (e.g., 'BTCUSD', 'XAUUSD')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            asset_class: Type of asset ('crypto', 'forex', 'stocks', 'indices')
            interval: Candle interval in minutes (default: 1)
        
        Returns:
            DataFrame with OHLCV data and timestamp index
        """
        # Determine API prefix based on asset class
        prefix_map = {
            'crypto': 'X',
            'forex': 'C',
            'stocks': 'T', # This is usually just the ticker, but we'll use T for clarity if needed
            'indices': 'I',
        }
        
        prefix = prefix_map.get(asset_class.lower(), '')
        
        # Format ticker for API call
        api_ticker = f"{prefix}:{symbol.upper()}" if prefix else symbol.upper()
        
        url = (
            f"{self.BASE_URL}/{api_ticker}/range/{interval}/minute/"
            f"{start_date}/{end_date}?adjusted=true&sort=asc&limit=50000&apiKey={self.api_key}"
        )
        
        print(f"Downloading {api_ticker} data from {start_date} to {end_date}...")
        response = requests.get(url)
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        data = response.json()
        
        if 'results' not in data or not data['results']:
            raise Exception(f"No data found for {api_ticker} between {start_date} and {end_date}")
        
        # Convert to DataFrame
        df = pd.DataFrame(data['results'])
        df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # Rename columns to standard OHLCV format
        df = df.rename(columns={
            'o': 'open',
            'h': 'high',
            'l': 'low',
            'c': 'close',
            'v': 'volume'
        })
        
        print(f"✅ Downloaded {len(df)} candles")
        return df[['open', 'high', 'low', 'close', 'volume']]


class StrategyAnalyzer:
    """Analyzes historical data to find optimal strategy parameters"""
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize analyzer with historical data.
        
        Args:
            data: DataFrame with OHLCV data
        """
        self.data = data.copy()
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        """Calculate all necessary indicators"""
        # Candle range (high - low)
        self.data['range'] = self.data['high'] - self.data['low']
        
        # Candle body size
        self.data['body'] = abs(self.data['close'] - self.data['open'])
        
        # Candle direction
        self.data['bullish'] = self.data['close'] > self.data['open']
        
        # ATR calculation (14-period default)
        self.data['tr'] = self._calculate_true_range()
        self.data['atr_14'] = self.data['tr'].rolling(window=14).mean()
        
        # Moving averages for trend filter
        self.data['ema_100'] = self.data['close'].ewm(span=100, adjust=False).mean()
        self.data['sma_100'] = self.data['close'].rolling(window=100).mean()
        
        # Price changes for volatility analysis
        self.data['price_change'] = self.data['close'].diff()
        self.data['price_change_pct'] = self.data['close'].pct_change() * 100
        
        print(f"✅ Calculated indicators for {len(self.data)} candles")
    
    def _calculate_true_range(self) -> pd.Series:
        """Calculate True Range for ATR"""
        high_low = self.data['high'] - self.data['low']
        high_close = abs(self.data['high'] - self.data['close'].shift())
        low_close = abs(self.data['low'] - self.data['close'].shift())
        return pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    def analyze_candle_distribution(self) -> Dict:
        """Analyze the distribution of candle sizes"""
        print("\n" + "="*70)
        print("CANDLE SIZE DISTRIBUTION ANALYSIS")
        print("="*70)
        
        # Calculate percentiles for candle ranges
        percentiles = [10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 95]
        range_percentiles = {
            p: self.data['range'].quantile(p/100) 
            for p in percentiles
        }
        
        print("\nCandle Range Percentiles:")
        for p, value in range_percentiles.items():
            print(f"  {p}th percentile: ${value:.2f}")
        
        # Statistics
        stats = {
            'mean_range': self.data['range'].mean(),
            'median_range': self.data['range'].median(),
            'std_range': self.data['range'].std(),
            'mean_atr': self.data['atr_14'].mean(),
            'median_atr': self.data['atr_14'].median(),
            'percentiles': range_percentiles
        }
        
        print(f"\nRange Statistics:")
        print(f"  Mean: ${stats['mean_range']:.2f}")
        print(f"  Median: ${stats['median_range']:.2f}")
        print(f"  Std Dev: ${stats['std_range']:.2f}")
        print(f"  Mean ATR(14): ${stats['mean_atr']:.2f}")
        
        return stats
    
    def test_two_candle_pattern(
        self,
        small_percentile: int,
        big_percentile: int,
        lookback_period: int = 200
    ) -> Dict:
        """
        Test the two-candle pattern strategy with given percentile thresholds.
        
        Args:
            small_percentile: Percentile threshold for small candle (e.g., 20)
            big_percentile: Percentile threshold for big candle (e.g., 90)
            lookback_period: Number of candles to use for percentile calculation
        
        Returns:
            Dictionary with performance metrics
        """
        signals = []
        
        for i in range(lookback_period + 1, len(self.data)):
            # Calculate rolling percentile thresholds
            recent_ranges = self.data['range'].iloc[i-lookback_period:i]
            small_threshold = recent_ranges.quantile(small_percentile / 100)
            big_threshold = recent_ranges.quantile(big_percentile / 100)
            
            # Check pattern: small candle [-2], big candle [-1]
            setup_range = self.data['range'].iloc[i-2]
            trigger_range = self.data['range'].iloc[i-1]
            
            if setup_range <= small_threshold and trigger_range >= big_threshold:
                setup_bullish = self.data['bullish'].iloc[i-2]
                trigger_bullish = self.data['bullish'].iloc[i-1]
                
                # Check trend filter (price above EMA100)
                current_price = self.data['close'].iloc[i-1]
                trend_up = current_price > self.data['ema_100'].iloc[i-1]
                
                signals.append({
                    'timestamp': self.data.index[i],
                    'direction': 'buy' if setup_bullish and trend_up else 'sell' if not setup_bullish and not trend_up else 'filtered',
                    'entry_price': self.data['close'].iloc[i-1],
                    'setup_range': setup_range,
                    'trigger_range': trigger_range,
                    'small_threshold': small_threshold,
                    'big_threshold': big_threshold
                })
        
        return {
            'total_signals': len(signals),
            'buy_signals': sum(1 for s in signals if s['direction'] == 'buy'),
            'sell_signals': sum(1 for s in signals if s['direction'] == 'sell'),
            'filtered_signals': sum(1 for s in signals if s['direction'] == 'filtered'),
            'signals': signals
        }
    
    def test_atr_pattern(
        self,
        small_multiplier: float,
        big_multiplier: float,
        atr_period: int = 14
    ) -> Dict:
        """
        Test the two-candle pattern strategy with ATR-based thresholds.
        
        Args:
            small_multiplier: ATR multiplier for small candle (e.g., 0.5)
            big_multiplier: ATR multiplier for big candle (e.g., 1.5)
            atr_period: ATR calculation period
        
        Returns:
            Dictionary with performance metrics
        """
        signals = []
        
        for i in range(atr_period + 1, len(self.data)):
            # Get ATR value
            atr_value = self.data['atr_14'].iloc[i]
            if pd.isna(atr_value) or atr_value <= 0:
                continue
            
            small_threshold = small_multiplier * atr_value
            big_threshold = big_multiplier * atr_value
            
            # Check pattern
            setup_range = self.data['range'].iloc[i-2]
            trigger_range = self.data['range'].iloc[i-1]
            
            if setup_range <= small_threshold and trigger_range >= big_threshold:
                setup_bullish = self.data['bullish'].iloc[i-2]
                trigger_bullish = self.data['bullish'].iloc[i-1]
                
                # Trend filter
                current_price = self.data['close'].iloc[i-1]
                trend_up = current_price > self.data['ema_100'].iloc[i-1]
                
                signals.append({
                    'timestamp': self.data.index[i],
                    'direction': 'buy' if setup_bullish and trend_up else 'sell' if not setup_bullish and not trend_up else 'filtered',
                    'entry_price': self.data['close'].iloc[i-1],
                    'setup_range': setup_range,
                    'trigger_range': trigger_range,
                    'atr_value': atr_value,
                    'small_threshold': small_threshold,
                    'big_threshold': big_threshold
                })
        
        return {
            'total_signals': len(signals),
            'buy_signals': sum(1 for s in signals if s['direction'] == 'buy'),
            'sell_signals': sum(1 for s in signals if s['direction'] == 'sell'),
            'filtered_signals': sum(1 for s in signals if s['direction'] == 'filtered'),
            'signals': signals
        }
    
    def optimize_percentile_thresholds(
        self,
        small_range: Tuple[int, int] = (10, 40),
        big_range: Tuple[int, int] = (70, 95),
        step: int = 5,
        tp_atr_mult: float = 2.0,
        sl_atr_mult: float = 1.0,
        start_hour: int = None,
        end_hour: int = None
    ) -> pd.DataFrame:
        """
        Test multiple combinations of percentile thresholds.
        
        Args:
            small_range: Range of small candle percentiles to test
            big_range: Range of big candle percentiles to test
            step: Step size for iteration
            tp_atr_mult: Take profit multiplier (default: 2.0x ATR)
            sl_atr_mult: Stop loss multiplier (default: 1.0x ATR)
            start_hour: Start hour for time filter (0-23), None to disable
            end_hour: End hour for time filter (0-23), None to disable
        
        Returns:
            DataFrame with results for each combination, ranked by profitability
        """
        print("\n" + "="*70)
        print("OPTIMIZING PERCENTILE THRESHOLDS")
        print("="*70)
        print(f"Using TP/SL: {tp_atr_mult}x / {sl_atr_mult}x ATR")
        if start_hour is not None and end_hour is not None:
            print(f"Time Filter: {start_hour}:00 - {end_hour}:00")
        else:
            print("Time Filter: Disabled (24/7 trading)")
        
        results = []
        small_percentiles = range(small_range[0], small_range[1] + 1, step)
        big_percentiles = range(big_range[0], big_range[1] + 1, step)
        
        total_tests = len(list(small_percentiles)) * len(list(big_percentiles))
        test_count = 0
        
        for small_p in range(small_range[0], small_range[1] + 1, step):
            for big_p in range(big_range[0], big_range[1] + 1, step):
                test_count += 1
                print(f"Testing {test_count}/{total_tests}: Small={small_p}%, Big={big_p}%", end='\r')
                
                # Run backtest to get profitability metrics
                backtest = self.backtest_strategy(
                    small_percentile=small_p,
                    big_percentile=big_p,
                    tp_atr_mult=tp_atr_mult,
                    sl_atr_mult=sl_atr_mult,
                    use_atr=False,
                    start_hour=start_hour,
                    end_hour=end_hour
                )
                
                results.append({
                    'small_percentile': small_p,
                    'big_percentile': big_p,
                    'total_trades': backtest['total_trades'],
                    'total_pnl': round(backtest['total_pnl'], 2),
                    'win_rate': round(backtest['win_rate'], 2),
                    'profit_factor': round(backtest['profit_factor'], 2),
                    'max_drawdown': round(backtest['max_drawdown'], 2),
                    'expectancy': round(backtest['expectancy'], 2)
                })
        
        print()  # New line after progress
        df = pd.DataFrame(results)
        df = df.sort_values('total_pnl', ascending=False)
        
        print(f"\n✅ Tested {len(df)} combinations")
        print("\nTop 10 Configurations by Profitability:")
        print(df.head(10).to_string(index=False))
        
        return df
    
    def optimize_atr_multipliers(
        self,
        small_range: Tuple[float, float] = (0.3, 1.0),
        big_range: Tuple[float, float] = (1.0, 2.5),
        step: float = 0.1,
        tp_atr_mult: float = 2.0,
        sl_atr_mult: float = 1.0,
        start_hour: int = None,
        end_hour: int = None
    ) -> pd.DataFrame:
        """
        Test multiple combinations of ATR multipliers.
        
        Args:
            small_range: Range of small candle multipliers to test
            big_range: Range of big candle multipliers to test
            step: Step size for iteration
            tp_atr_mult: Take profit multiplier (default: 2.0x ATR)
            sl_atr_mult: Stop loss multiplier (default: 1.0x ATR)
            start_hour: Start hour for time filter (0-23), None to disable
            end_hour: End hour for time filter (0-23), None to disable
        
        Returns:
            DataFrame with results for each combination, ranked by profitability
        """
        print("\n" + "="*70)
        print("OPTIMIZING ATR MULTIPLIERS")
        print("="*70)
        print(f"Using TP/SL: {tp_atr_mult}x / {sl_atr_mult}x ATR")
        if start_hour is not None and end_hour is not None:
            print(f"Time Filter: {start_hour}:00 - {end_hour}:00")
        else:
            print("Time Filter: Disabled (24/7 trading)")
        
        results = []
        
        # Generate ranges
        small_multipliers = np.arange(small_range[0], small_range[1] + step, step)
        big_multipliers = np.arange(big_range[0], big_range[1] + step, step)
        
        total_tests = len(small_multipliers) * len(big_multipliers)
        test_count = 0
        
        for small_m in small_multipliers:
            for big_m in big_multipliers:
                test_count += 1
                print(f"Testing {test_count}/{total_tests}: Small={small_m:.1f}x, Big={big_m:.1f}x", end='\r')
                
                # Run backtest to get profitability metrics
                backtest = self.backtest_strategy(
                    small_percentile=30,  # Not used when use_atr=True
                    big_percentile=80,    # Not used when use_atr=True
                    tp_atr_mult=tp_atr_mult,
                    sl_atr_mult=sl_atr_mult,
                    use_atr=True,
                    small_atr_mult=small_m,
                    big_atr_mult=big_m,
                    start_hour=start_hour,
                    end_hour=end_hour
                )
                
                results.append({
                    'small_multiplier': round(small_m, 2),
                    'big_multiplier': round(big_m, 2),
                    'total_trades': backtest['total_trades'],
                    'total_pnl': round(backtest['total_pnl'], 2),
                    'win_rate': round(backtest['win_rate'], 2),
                    'profit_factor': round(backtest['profit_factor'], 2),
                    'max_drawdown': round(backtest['max_drawdown'], 2),
                    'expectancy': round(backtest['expectancy'], 2)
                })
        
        print()  # New line after progress
        df = pd.DataFrame(results)
        df = df.sort_values('total_pnl', ascending=False)
        
        print(f"\n✅ Tested {len(df)} combinations")
        print("\nTop 10 Configurations by Profitability:")
        print(df.head(10).to_string(index=False))
        
        return df
    
    def simulate_trade(
        self,
        entry_idx: int,
        direction: str,
        tp_distance: float,
        sl_distance: float,
        max_bars: int = 1000
    ) -> Dict:
        """
        Simulate a single trade and return outcome.
        
        Args:
            entry_idx: Bar index where trade enters
            direction: 'buy' or 'sell'
            tp_distance: Take profit distance in price units
            sl_distance: Stop loss distance in price units
            max_bars: Maximum bars to hold trade before timeout
        
        Returns:
            Dictionary with trade outcome details
        """
        if entry_idx >= len(self.data) - 1:
            return None
        
        entry_price = self.data['close'].iloc[entry_idx]
        
        # Set TP and SL levels
        if direction == 'buy':
            tp_level = entry_price + tp_distance
            sl_level = entry_price - sl_distance
        else:  # sell
            tp_level = entry_price - tp_distance
            sl_level = entry_price + sl_distance
        
        # Scan forward bars to find which hits first
        for i in range(entry_idx + 1, min(entry_idx + max_bars, len(self.data))):
            high = self.data['high'].iloc[i]
            low = self.data['low'].iloc[i]
            open_price = self.data['open'].iloc[i]
            
            if direction == 'buy':
                tp_hit = high >= tp_level
                sl_hit = low <= sl_level
                
                # If both hit in same bar, check which is closer to open
                if tp_hit and sl_hit:
                    tp_distance_from_open = abs(tp_level - open_price)
                    sl_distance_from_open = abs(sl_level - open_price)
                    
                    # Assume the closer level was hit first
                    if sl_distance_from_open <= tp_distance_from_open:
                        return {
                            'outcome': 'loss',
                            'pnl': -sl_distance,
                            'bars_held': i - entry_idx,
                            'exit_price': sl_level
                        }
                    else:
                        return {
                            'outcome': 'win',
                            'pnl': tp_distance,
                            'bars_held': i - entry_idx,
                            'exit_price': tp_level
                        }
                # Only TP hit
                elif tp_hit:
                    return {
                        'outcome': 'win',
                        'pnl': tp_distance,
                        'bars_held': i - entry_idx,
                        'exit_price': tp_level
                    }
                # Only SL hit
                elif sl_hit:
                    return {
                        'outcome': 'loss',
                        'pnl': -sl_distance,
                        'bars_held': i - entry_idx,
                        'exit_price': sl_level
                    }
            else:  # sell
                tp_hit = low <= tp_level
                sl_hit = high >= sl_level
                
                # If both hit in same bar, check which is closer to open
                if tp_hit and sl_hit:
                    tp_distance_from_open = abs(tp_level - open_price)
                    sl_distance_from_open = abs(sl_level - open_price)
                    
                    # Assume the closer level was hit first
                    if sl_distance_from_open <= tp_distance_from_open:
                        return {
                            'outcome': 'loss',
                            'pnl': -sl_distance,
                            'bars_held': i - entry_idx,
                            'exit_price': sl_level
                        }
                    else:
                        return {
                            'outcome': 'win',
                            'pnl': tp_distance,
                            'bars_held': i - entry_idx,
                            'exit_price': tp_level
                        }
                # Only TP hit
                elif tp_hit:
                    return {
                        'outcome': 'win',
                        'pnl': tp_distance,
                        'bars_held': i - entry_idx,
                        'exit_price': tp_level
                    }
                # Only SL hit
                elif sl_hit:
                    return {
                        'outcome': 'loss',
                        'pnl': -sl_distance,
                        'bars_held': i - entry_idx,
                        'exit_price': sl_level
                    }
        
        # Trade timed out
        exit_price = self.data['close'].iloc[min(entry_idx + max_bars - 1, len(self.data) - 1)]
        pnl = (exit_price - entry_price) if direction == 'buy' else (entry_price - exit_price)
        
        return {
            'outcome': 'timeout',
            'pnl': pnl,
            'bars_held': max_bars,
            'exit_price': exit_price
        }
    
    def calculate_performance_metrics(self, trades: List[Dict]) -> Dict:
        """
        Calculate comprehensive performance metrics from trade list.
        
        Args:
            trades: List of trade outcome dictionaries
        
        Returns:
            Dictionary with performance statistics
        """
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_pnl': 0,
                'max_drawdown': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'sharpe_ratio': 0
            }
        
        wins = [t for t in trades if t['outcome'] == 'win']
        losses = [t for t in trades if t['outcome'] == 'loss']
        
        total_wins = sum(t['pnl'] for t in wins)
        total_losses = abs(sum(t['pnl'] for t in losses))
        
        # Calculate equity curve for drawdown
        equity_curve = [0]
        for trade in trades:
            equity_curve.append(equity_curve[-1] + trade['pnl'])
        
        # Calculate maximum drawdown
        peak = equity_curve[0]
        max_dd = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd
        
        # Calculate metrics
        win_rate = (len(wins) / len(trades) * 100) if trades else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else float('inf')
        avg_win = (total_wins / len(wins)) if wins else 0
        avg_loss = (total_losses / len(losses)) if losses else 0
        
        # Sharpe ratio (returns / std dev)
        # Note: Not annualized since trade frequency varies - use raw ratio
        pnls = [t['pnl'] for t in trades]
        sharpe = (np.mean(pnls) / np.std(pnls)) if np.std(pnls) > 0 else 0
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pnl': sum(pnls),
            'max_drawdown': max_dd,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_bars_held': np.mean([t['bars_held'] for t in trades]),
            'sharpe_ratio': sharpe,
            'expectancy': np.mean(pnls)  # Average P&L per trade
        }
    
    def backtest_strategy(
        self,
        small_percentile: int,
        big_percentile: int,
        tp_atr_mult: float,
        sl_atr_mult: float,
        lookback_period: int = 200,
        use_atr: bool = False,
        small_atr_mult: float = 0.5,
        big_atr_mult: float = 1.5,
        start_hour: int = None,
        end_hour: int = None
    ) -> Dict:
        """
        Full backtest with P&L tracking for strategy parameters.
        
        Args:
            small_percentile: Percentile for small candle threshold
            big_percentile: Percentile for big candle threshold
            tp_atr_mult: Take profit as multiple of ATR
            sl_atr_mult: Stop loss as multiple of ATR
            lookback_period: Lookback for percentile calculation
            use_atr: If True, use ATR multipliers instead of percentiles
            small_atr_mult: Small candle ATR multiplier (if use_atr=True)
            big_atr_mult: Big candle ATR multiplier (if use_atr=True)
            start_hour: Start hour for time filter (0-23), None to disable
            end_hour: End hour for time filter (0-23), None to disable
        
        Returns:
            Dictionary with backtest results and performance metrics
        """
        trades = []
        signals = []
        
        start_idx = max(lookback_period, 14) + 2  # Need ATR and lookback data
        
        for i in range(start_idx, len(self.data) - 1):
            # Time filter (mimics strategy's ENABLE_TIME_FILTER)
            if start_hour is not None and end_hour is not None:
                current_hour = self.data.index[i].hour
                # Handle time windows that cross midnight (e.g., 20:00 to 05:00)
                if start_hour <= end_hour:
                    # Normal case: trade between start_hour and end_hour
                    if current_hour < start_hour or current_hour >= end_hour:
                        continue
                else:
                    # Crosses midnight: trade if hour >= start_hour OR hour < end_hour
                    if current_hour < start_hour and current_hour >= end_hour:
                        continue
            
            # Get ATR for this bar
            atr_value = self.data['atr_14'].iloc[i]
            if pd.isna(atr_value) or atr_value <= 0:
                continue
            
            # Determine thresholds
            if use_atr:
                small_threshold = small_atr_mult * atr_value
                big_threshold = big_atr_mult * atr_value
            else:
                recent_ranges = self.data['range'].iloc[i-lookback_period:i]
                small_threshold = recent_ranges.quantile(small_percentile / 100)
                big_threshold = recent_ranges.quantile(big_percentile / 100)
            
            # Check pattern: small candle [-2], big candle [-1]
            setup_range = self.data['range'].iloc[i-2]
            trigger_range = self.data['range'].iloc[i-1]
            
            if setup_range <= small_threshold and trigger_range >= big_threshold:
                setup_bullish = self.data['bullish'].iloc[i-2]
                
                # Trend filter
                current_price = self.data['close'].iloc[i-1]
                trend_up = current_price > self.data['ema_100'].iloc[i-1]
                
                # Determine direction
                if setup_bullish and trend_up:
                    direction = 'buy'
                elif not setup_bullish and not trend_up:
                    direction = 'sell'
                else:
                    continue  # Filtered by trend
                
                # Calculate TP/SL based on ATR
                tp_distance = tp_atr_mult * atr_value
                sl_distance = sl_atr_mult * atr_value
                
                # Simulate trade
                trade_result = self.simulate_trade(i, direction, tp_distance, sl_distance)
                
                if trade_result:
                    trade_result['entry_idx'] = i
                    trade_result['direction'] = direction
                    trade_result['atr'] = atr_value
                    trade_result['tp_distance'] = tp_distance
                    trade_result['sl_distance'] = sl_distance
                    trades.append(trade_result)
                    
                    signals.append({
                        'timestamp': self.data.index[i],
                        'direction': direction,
                        'entry_price': self.data['close'].iloc[i]
                    })
        
        # Calculate performance metrics
        metrics = self.calculate_performance_metrics(trades)
        metrics['signals'] = signals
        metrics['trades'] = trades
        
        return metrics
    
    def analyze_volatility_patterns(self) -> Dict:
        """Analyze volatility patterns to inform TP/SL settings"""
        print("\n" + "="*70)
        print("VOLATILITY ANALYSIS FOR TP/SL OPTIMIZATION")
        print("="*70)
        
        # Calculate typical price movements
        price_moves = self.data['price_change'].abs()
        
        stats = {
            'mean_move': price_moves.mean(),
            'median_move': price_moves.median(),
            'percentiles': {
                p: price_moves.quantile(p/100) 
                for p in [50, 70, 80, 90, 95]
            },
            'mean_atr': self.data['atr_14'].mean()
        }
        
        print(f"\nPrice Movement Statistics (1-minute intervals):")
        print(f"  Mean: ${stats['mean_move']:.2f}")
        print(f"  Median: ${stats['median_move']:.2f}")
        print(f"  Mean ATR: ${stats['mean_atr']:.2f}")
        
        print(f"\nSuggested Take Profit levels (price movement percentiles):")
        for p, value in stats['percentiles'].items():
            print(f"  {p}th percentile: ${value:.2f} (conservative TP)")
        
        print(f"\nSuggested Stop Loss levels (ATR-based):")
        for mult in [1.0, 1.5, 2.0, 2.5]:
            sl_value = stats['mean_atr'] * mult
            print(f"  {mult}x ATR: ${sl_value:.2f}")
        
        return stats
    
    def optimize_tp_sl_ratios(
        self,
        small_percentile: int = 30,
        big_percentile: int = 80,
        tp_range: Tuple[float, float] = (1.0, 3.0),
        sl_range: Tuple[float, float] = (0.5, 2.0),
        step: float = 0.5,
        use_atr: bool = False,
        small_atr_mult: float = 0.5,
        big_atr_mult: float = 1.5,
        start_hour: int = None,
        end_hour: int = None
    ) -> pd.DataFrame:
        """
        Optimize TP/SL ratios using ATR multipliers.
        
        Tests multiple TP/SL combinations and ranks by profitability.
        
        Args:
            small_percentile: Small candle percentile to use (if use_atr=False)
            big_percentile: Big candle percentile to use (if use_atr=False)
            tp_range: Range of TP multipliers (min, max)
            sl_range: Range of SL multipliers (min, max)
            step: Step size for testing
            use_atr: If True, use ATR multipliers for candle detection instead of percentiles
            small_atr_mult: Small candle ATR multiplier (if use_atr=True)
            big_atr_mult: Big candle ATR multiplier (if use_atr=True)
            start_hour: Start hour for time filter (None to disable)
            end_hour: End hour for time filter (None to disable)
        
        Returns:
            DataFrame sorted by total P&L
        """
        print("\n" + "="*70)
        print("OPTIMIZING TP/SL RATIOS")
        print("="*70)
        
        if use_atr:
            print(f"Using ATR-based candle detection: {small_atr_mult}x / {big_atr_mult}x ATR")
        else:
            print(f"Using percentile-based candle detection: {small_percentile}% / {big_percentile}%")
        
        results = []
        
        tp_multipliers = np.arange(tp_range[0], tp_range[1] + step, step)
        sl_multipliers = np.arange(sl_range[0], sl_range[1] + step, step)
        
        total_tests = len(tp_multipliers) * len(sl_multipliers)
        test_count = 0
        
        for tp_mult in tp_multipliers:
            for sl_mult in sl_multipliers:
                test_count += 1
                print(f"Testing {test_count}/{total_tests}: TP={tp_mult:.1f}x ATR, SL={sl_mult:.1f}x ATR", end='\r')
                
                # Run backtest
                backtest = self.backtest_strategy(
                    small_percentile=small_percentile,
                    big_percentile=big_percentile,
                    tp_atr_mult=tp_mult,
                    sl_atr_mult=sl_mult,
                    use_atr=use_atr,
                    small_atr_mult=small_atr_mult,
                    big_atr_mult=big_atr_mult,
                    start_hour=start_hour,
                    end_hour=end_hour
                )
                
                results.append({
                    'tp_multiplier': round(tp_mult, 2),
                    'sl_multiplier': round(sl_mult, 2),
                    'risk_reward_ratio': round(tp_mult / sl_mult, 2),
                    'total_pnl': round(backtest['total_pnl'], 2),
                    'total_trades': backtest['total_trades'],
                    'win_rate': round(backtest['win_rate'], 2),
                    'profit_factor': round(backtest['profit_factor'], 2),
                    'max_drawdown': round(backtest['max_drawdown'], 2),
                    'sharpe_ratio': round(backtest['sharpe_ratio'], 2),
                    'expectancy': round(backtest['expectancy'], 2)
                })
        
        print()  # New line after progress
        df = pd.DataFrame(results)
        df = df.sort_values('total_pnl', ascending=False)
        
        print(f"\n✅ Tested {len(df)} TP/SL combinations")
        print("\nTop 10 Configurations by Total P&L:")
        print(df.head(10).to_string(index=False))
        
        return df
    
    def optimize_candle_sizes_with_profitability(
        self,
        tp_atr_mult: float = 2.0,
        sl_atr_mult: float = 1.0,
        small_range: Tuple[int, int] = (10, 50),
        big_range: Tuple[int, int] = (60, 95),
        step: int = 10,
        use_atr: bool = False,
        atr_small_range: Tuple[float, float] = (0.3, 1.0),
        atr_big_range: Tuple[float, float] = (1.0, 2.5),
        atr_step: float = 0.1,
        start_hour: int = None,
        end_hour: int = None
    ) -> pd.DataFrame:
        """
        Find which candle size thresholds generate the highest profit.
        
        This answers: "Which candle sizes are most profitable?"
        Can test either percentile-based OR ATR-based candle detection.
        
        Args:
            tp_atr_mult: Fixed TP multiplier to use
            sl_atr_mult: Fixed SL multiplier to use
            small_range: Range of small percentiles to test (if use_atr=False)
            big_range: Range of big percentiles to test (if use_atr=False)
            step: Step size for percentile testing
            use_atr: If True, optimize ATR multipliers instead of percentiles
            atr_small_range: Range of small ATR multipliers to test (if use_atr=True)
            atr_big_range: Range of big ATR multipliers to test (if use_atr=True)
            atr_step: Step size for ATR multiplier testing
            start_hour: Start hour for time filter (None to disable)
            end_hour: End hour for time filter (None to disable)
        
        Returns:
            DataFrame sorted by profitability
        """
        print("\n" + "="*70)
        print("FINDING MOST PROFITABLE CANDLE SIZES")
        print("="*70)
        print(f"Using fixed TP/SL: {tp_atr_mult}x / {sl_atr_mult}x ATR")
        
        if use_atr:
            print(f"Optimizing ATR-based candle detection")
        else:
            print(f"Optimizing percentile-based candle detection")
        
        results = []
        
        if use_atr:
            # Test ATR multipliers
            small_multipliers = np.arange(atr_small_range[0], atr_small_range[1] + atr_step, atr_step)
            big_multipliers = np.arange(atr_big_range[0], atr_big_range[1] + atr_step, atr_step)
            
            total_tests = len(small_multipliers) * len(big_multipliers)
            test_count = 0
            
            for small_m in small_multipliers:
                for big_m in big_multipliers:
                    test_count += 1
                    print(f"Testing {test_count}/{total_tests}: Small={small_m:.2f}x, Big={big_m:.2f}x ATR", end='\r')
                    
                    # Run backtest with ATR-based detection
                    backtest = self.backtest_strategy(
                        small_percentile=30,  # Not used when use_atr=True
                        big_percentile=80,    # Not used when use_atr=True
                        tp_atr_mult=tp_atr_mult,
                        sl_atr_mult=sl_atr_mult,
                        use_atr=True,
                        small_atr_mult=small_m,
                        big_atr_mult=big_m,
                        start_hour=start_hour,
                        end_hour=end_hour
                    )
                    
                    results.append({
                        'small_atr_multiplier': round(small_m, 2),
                        'big_atr_multiplier': round(big_m, 2),
                        'total_pnl': round(backtest['total_pnl'], 2),
                        'total_trades': backtest['total_trades'],
                        'win_rate': round(backtest['win_rate'], 2),
                        'profit_factor': round(backtest['profit_factor'], 2),
                        'max_drawdown': round(backtest['max_drawdown'], 2),
                        'expectancy': round(backtest['expectancy'], 2),
                        'sharpe_ratio': round(backtest['sharpe_ratio'], 2)
                    })
        else:
            # Test percentiles
            small_percentiles = range(small_range[0], small_range[1] + 1, step)
            big_percentiles = range(big_range[0], big_range[1] + 1, step)
            
            total_tests = len(list(small_percentiles)) * len(list(big_percentiles))
            test_count = 0
            
            for small_p in range(small_range[0], small_range[1] + 1, step):
                for big_p in range(big_range[0], big_range[1] + 1, step):
                    test_count += 1
                    print(f"Testing {test_count}/{total_tests}: Small={small_p}%, Big={big_p}%", end='\r')
                    
                    # Run backtest with percentile-based detection
                    backtest = self.backtest_strategy(
                        small_percentile=small_p,
                        big_percentile=big_p,
                        tp_atr_mult=tp_atr_mult,
                        sl_atr_mult=sl_atr_mult,
                        use_atr=False,
                        start_hour=start_hour,
                        end_hour=end_hour
                    )
                    
                    results.append({
                        'small_percentile': small_p,
                        'big_percentile': big_p,
                        'total_pnl': round(backtest['total_pnl'], 2),
                        'total_trades': backtest['total_trades'],
                        'win_rate': round(backtest['win_rate'], 2),
                        'profit_factor': round(backtest['profit_factor'], 2),
                        'max_drawdown': round(backtest['max_drawdown'], 2),
                        'expectancy': round(backtest['expectancy'], 2),
                        'sharpe_ratio': round(backtest['sharpe_ratio'], 2)
                    })
        
        print()  # New line
        df = pd.DataFrame(results)
        df = df.sort_values('total_pnl', ascending=False)
        
        print(f"\n✅ Tested {len(df)} candle size combinations")
        print("\nTop 10 Most Profitable Candle Size Configs:")
        print(df.head(10).to_string(index=False))
        
        return df
    
    def optimize_grid_parameters(
        self,
        small_percentile: int = 30,
        big_percentile: int = 80,
        tp_atr_mult: float = 2.0,
        sl_atr_mult: float = 1.0,
        grid_spacing_range: Tuple[float, float] = (2.0, 4.0),
        lot_multiplier_range: Tuple[float, float] = (1.0, 1.2),
        step: float = 0.5,
        use_atr: bool = False,
        small_atr_mult: float = 0.5,
        big_atr_mult: float = 1.5,
        start_hour: int = None,
        end_hour: int = None
    ) -> pd.DataFrame:
        """
        Optimize grid trading parameters (spacing and lot multiplier).
        
        Note: This is a simplified grid simulation. Full grid implementation
        would require position tracking and basket management.
        
        Args:
            small_percentile: Small candle threshold (if use_atr=False)
            big_percentile: Big candle threshold (if use_atr=False)
            tp_atr_mult: TP multiplier
            sl_atr_mult: SL multiplier
            grid_spacing_range: ATR multipliers for grid spacing (min, max)
            lot_multiplier_range: Range of lot multipliers (min, max)
            step: Step size
            use_atr: If True, use ATR-based candle detection
            small_atr_mult: Small candle ATR multiplier (if use_atr=True)
            big_atr_mult: Big candle ATR multiplier (if use_atr=True)
            start_hour: Start hour for time filter (None to disable)
            end_hour: End hour for time filter (None to disable)
        
        Returns:
            DataFrame with grid parameter results
        """
        print("\n" + "="*70)
        print("OPTIMIZING GRID PARAMETERS")
        print("="*70)
        print("Note: Simplified grid simulation (estimates potential benefit)")
        
        if use_atr:
            print(f"Using ATR-based candle detection: {small_atr_mult}x / {big_atr_mult}x ATR")
        else:
            print(f"Using percentile-based candle detection: {small_percentile}% / {big_percentile}%")
        
        results = []
        
        grid_spacings = np.arange(grid_spacing_range[0], grid_spacing_range[1] + step, step)
        lot_multipliers = np.arange(lot_multiplier_range[0], lot_multiplier_range[1] + 0.05, 0.05)
        
        total_tests = len(grid_spacings) * len(lot_multipliers)
        test_count = 0
        
        # First, run baseline without grid
        baseline = self.backtest_strategy(
            small_percentile=small_percentile,
            big_percentile=big_percentile,
            tp_atr_mult=tp_atr_mult,
            sl_atr_mult=sl_atr_mult,
            use_atr=use_atr,
            small_atr_mult=small_atr_mult,
            big_atr_mult=big_atr_mult,
            start_hour=start_hour,
            end_hour=end_hour
        )
        
        for spacing in grid_spacings:
            for lot_mult in lot_multipliers:
                test_count += 1
                print(f"Testing {test_count}/{total_tests}: Spacing={spacing:.1f}x, LotMult={lot_mult:.2f}", end='\r')
                
                # For now, we'll estimate grid benefit by analyzing drawdown periods
                # A full implementation would require multi-position tracking
                
                results.append({
                    'grid_spacing_atr': round(spacing, 2),
                    'lot_multiplier': round(lot_mult, 2),
                    'baseline_pnl': round(baseline['total_pnl'], 2),
                    'baseline_trades': baseline['total_trades'],
                    'baseline_win_rate': round(baseline['win_rate'], 2),
                    'estimated_improvement': 'Grid simulation pending',
                    'note': 'Use these as starting points for live grid testing'
                })
        
        print()  # New line
        df = pd.DataFrame(results)
        
        print(f"\n✅ Generated {len(df)} grid configurations")
        print("\n⚠️  NOTE: This is a SIMPLIFIED grid analysis (baseline only)")
        print("Full grid backtesting requires multi-position tracking (not yet implemented)")
        print("\nRecommended Grid Settings (based on baseline analysis):")
        print(f"  Grid Spacing: 2.5-3.5x ATR (wider = more conservative)")
        print(f"  Lot Multiplier: 1.0-1.1x (lower = less aggressive recovery)")
        print(f"  Baseline Performance: {baseline['total_trades']} trades, {baseline['win_rate']:.1f}% win rate")
        print(f"  Baseline P&L: ${baseline['total_pnl']:.2f}")
        print("\n💡 Test these settings on demo account before live trading")
        
        return df
    
    def generate_recommendations(self) -> Dict:
        """Generate final recommendations based on all analyses"""
        print("\n" + "="*70)
        print("STRATEGY RECOMMENDATIONS")
        print("="*70)
        
        # Analyze distributions
        candle_stats = self.analyze_candle_distribution()
        vol_stats = self.analyze_volatility_patterns()
        
        # Test current default settings
        print("\n📊 Testing Current Default Settings:")
        percentile_default = self.test_two_candle_pattern(20, 90)
        print(f"  Percentile Method (20th/90th): {percentile_default['total_signals']} signals")
        
        atr_default = self.test_atr_pattern(0.5, 1.5)
        print(f"  ATR Method (0.5x/1.5x): {atr_default['total_signals']} signals")
        
        recommendations = {
            'percentile_method': {
                'default': {'small': 20, 'big': 90},
                'signals': percentile_default['total_signals'],
                'recommended': {
                    'small': 20,  # Will be refined by optimization
                    'big': 90,
                    'lookback': 200,
                    'update_frequency': 200
                }
            },
            'atr_method': {
                'default': {'small': 0.5, 'big': 1.5},
                'signals': atr_default['total_signals'],
                'recommended': {
                    'small_multiplier': 0.5,  # Will be refined by optimization
                    'big_multiplier': 1.5,
                    'atr_period': 14
                }
            },
            'risk_management': {
                'mean_atr': vol_stats['mean_atr'],
                'suggested_tp': vol_stats['percentiles'][70],  # 70th percentile of moves
                'suggested_sl': vol_stats['mean_atr'] * 1.5,  # 1.5x ATR
            },
            'market_stats': {
                'candles_analyzed': len(self.data),
                'mean_range': candle_stats['mean_range'],
                'mean_atr': candle_stats['mean_atr']
            }
        }
        
        print("\n✅ Recommendations generated. Run optimization methods for detailed analysis.")
        return recommendations


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Optimize trading strategy parameters using historical data'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        required=True,
        help='Polygon.io API key'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='BTCUSD',
        help='Crypto symbol (default: BTCUSD). Options: BTCUSD, ETHUSD, XAUUSD'
    )
    parser.add_argument(
        '--asset-class',
        type=str,
        default='crypto',
        help='Asset class (default: crypto). Options: crypto, forex, stocks, indices'
    )
    parser.add_argument(
        '--start',
        type=str,
        required=True,
        help='Start date in YYYY-MM-DD format'
    )
    parser.add_argument(
        '--end',
        type=str,
        required=True,
        help='End date in YYYY-MM-DD format'
    )
    parser.add_argument(
        '--optimize-percentile',
        action='store_true',
        help='Run percentile threshold optimization'
    )
    parser.add_argument(
        '--optimize-atr',
        action='store_true',
        help='Run ATR multiplier optimization'
    )
    parser.add_argument(
        '--optimize-tp-sl',
        action='store_true',
        help='Run TP/SL ratio optimization (finds most profitable TP/SL combinations)'
    )
    parser.add_argument(
        '--optimize-candle-profitability',
        action='store_true',
        help='Find which candle sizes generate highest profit (not just signal count)'
    )
    parser.add_argument(
        '--optimize-grid',
        action='store_true',
        help='Run grid parameter optimization (spacing and lot multiplier)'
    )
    parser.add_argument(
        '--optimize-all',
        action='store_true',
        help='Run ALL optimization methods (comprehensive analysis)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='optimization_results.json',
        help='Output file for results (default: optimization_results.json)'
    )
    parser.add_argument(
        '--start-hour',
        type=int,
        default=None,
        help='Start hour for time filter (0-23). If set, only trades during specified hours. Example: --start-hour 5 --end-hour 12'
    )
    parser.add_argument(
        '--end-hour',
        type=int,
        default=None,
        help='End hour for time filter (0-23). Must be used with --start-hour. Trades from start-hour (inclusive) to end-hour (exclusive)'
    )
    parser.add_argument(
        '--use-atr-method',
        action='store_true',
        help='Use ATR-based candle detection instead of percentile-based for profitability optimizations (TP/SL, candle sizes)'
    )
    parser.add_argument(
        '--atr-small-mult',
        type=float,
        default=0.5,
        help='Small candle ATR multiplier when using ATR method (default: 0.5x)'
    )
    parser.add_argument(
        '--atr-big-mult',
        type=float,
        default=1.5,
        help='Big candle ATR multiplier when using ATR method (default: 1.5x)'
    )
    
    args = parser.parse_args()
    
    # Validate time filter arguments
    if (args.start_hour is not None and args.end_hour is None) or (args.start_hour is None and args.end_hour is not None):
        parser.error("--start-hour and --end-hour must be used together or not at all")
    
    if args.start_hour is not None:
        if not (0 <= args.start_hour <= 23) or not (0 <= args.end_hour <= 23):
            parser.error("--start-hour and --end-hour must be between 0 and 23")
        print(f"⏰ Time filter enabled: Trading hours {args.start_hour}:00 - {args.end_hour}:00")
    else:
        print("⚠️  WARNING: Time filter disabled. Optimizer will test 24/7 trading.")
        print("   This may inflate results vs. actual strategy with ENABLE_TIME_FILTER=True")
    
    # Display ATR method selection
    if args.use_atr_method:
        print(f"✅ ATR-based candle detection enabled: {args.atr_small_mult}x / {args.atr_big_mult}x ATR")
        print("   Profitability optimizations will use ATR multipliers instead of percentiles")
    else:
        print("📊 Percentile-based candle detection enabled (default)")
        print("   Use --use-atr-method to optimize with ATR-based detection")
    
    # --- Smart Asset Class Detection ---
    # If user passes XAUUSD but forgets to set asset class, override it
    asset_class = args.asset_class
    if 'XAU' in args.symbol.upper():
        print("💡 Detected XAUUSD symbol. Automatically setting asset class to 'forex'.")
        asset_class = 'forex'
    
    # Download data
    downloader = PolygonDataDownloader(args.api_key)
    data = downloader.download_data(args.symbol, args.start, args.end, asset_class)
    
    # Analyze data
    analyzer = StrategyAnalyzer(data)
    
    # Generate recommendations
    recommendations = analyzer.generate_recommendations()
    
    results = {
        'symbol': args.symbol,
        'asset_class': asset_class,
        'start_date': args.start,
        'end_date': args.end,
        'recommendations': recommendations
    }
    
    # Run optimizations if requested (or all if --optimize-all is set)
    run_all = args.optimize_all
    
    if args.optimize_percentile or run_all:
        print("\n" + "🔍 Running Percentile Optimization...")
        percentile_results = analyzer.optimize_percentile_thresholds(
            start_hour=args.start_hour,
            end_hour=args.end_hour
        )
        results['percentile_optimization'] = percentile_results.to_dict('records')
        
        # Update recommendation with best result
        best = percentile_results.iloc[0]
        print(f"\n🏆 BEST PERCENTILE CONFIG:")
        print(f"   Small: {best['small_percentile']}%")
        print(f"   Big: {best['big_percentile']}%")
        print(f"   Total P&L: ${best['total_pnl']:.2f}")
        print(f"   Trades: {best['total_trades']}")
        print(f"   Win Rate: {best['win_rate']:.1f}%")
        print(f"   Profit Factor: {best['profit_factor']:.2f}")
    
    if args.optimize_atr or run_all:
        print("\n" + "🔍 Running ATR Optimization...")
        atr_results = analyzer.optimize_atr_multipliers(
            start_hour=args.start_hour,
            end_hour=args.end_hour
        )
        results['atr_optimization'] = atr_results.to_dict('records')
        
        # Update recommendation with best result
        best = atr_results.iloc[0]
        print(f"\n🏆 BEST ATR CONFIG:")
        print(f"   Small: {best['small_multiplier']}x")
        print(f"   Big: {best['big_multiplier']}x")
        print(f"   Total P&L: ${best['total_pnl']:.2f}")
        print(f"   Trades: {best['total_trades']}")
        print(f"   Win Rate: {best['win_rate']:.1f}%")
        print(f"   Profit Factor: {best['profit_factor']:.2f}")
    
    if args.optimize_tp_sl or run_all:
        print("\n" + "💰 Running TP/SL Optimization...")
        tp_sl_results = analyzer.optimize_tp_sl_ratios(
            use_atr=args.use_atr_method,
            small_atr_mult=args.atr_small_mult,
            big_atr_mult=args.atr_big_mult,
            start_hour=args.start_hour,
            end_hour=args.end_hour
        )
        results['tp_sl_optimization'] = tp_sl_results.to_dict('records')
        
        best = tp_sl_results.iloc[0]
        print(f"\n🏆 BEST TP/SL CONFIG:")
        print(f"   TP: {best['tp_multiplier']}x ATR")
        print(f"   SL: {best['sl_multiplier']}x ATR")
        print(f"   Risk:Reward: {best['risk_reward_ratio']}")
        print(f"   Total P&L: ${best['total_pnl']:.2f}")
        print(f"   Win Rate: {best['win_rate']:.1f}%")
        print(f"   Profit Factor: {best['profit_factor']:.2f}")
    
    if args.optimize_candle_profitability or run_all:
        print("\n" + "📊 Finding Most Profitable Candle Sizes...")
        candle_profit_results = analyzer.optimize_candle_sizes_with_profitability(
            use_atr=args.use_atr_method,
            start_hour=args.start_hour,
            end_hour=args.end_hour
        )
        results['candle_profitability_optimization'] = candle_profit_results.to_dict('records')
        
        best = candle_profit_results.iloc[0]
        print(f"\n🏆 MOST PROFITABLE CANDLE SIZES:")
        if args.use_atr_method:
            print(f"   Small: {best['small_atr_multiplier']}x ATR")
            print(f"   Big: {best['big_atr_multiplier']}x ATR")
        else:
            print(f"   Small: {best['small_percentile']}%")
            print(f"   Big: {best['big_percentile']}%")
        print(f"   Total P&L: ${best['total_pnl']:.2f}")
        print(f"   Trades: {best['total_trades']}")
        print(f"   Win Rate: {best['win_rate']:.1f}%")
        print(f"   Profit Factor: {best['profit_factor']:.2f}")
    
    if args.optimize_grid or run_all:
        print("\n" + "🔲 Running Grid Parameter Optimization...")
        grid_results = analyzer.optimize_grid_parameters(
            use_atr=args.use_atr_method,
            small_atr_mult=args.atr_small_mult,
            big_atr_mult=args.atr_big_mult,
            start_hour=args.start_hour,
            end_hour=args.end_hour
        )
        results['grid_optimization'] = grid_results.to_dict('records')
        
        print(f"\n💡 GRID RECOMMENDATIONS:")
        print(f"   Use spacing: 2.5-3.5x ATR")
        print(f"   Use lot multiplier: 1.0-1.1x")
        print(f"   Test with caution on demo account first")
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to {args.output}")
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()

