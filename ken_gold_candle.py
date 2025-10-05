"""
TradeLocker bot (Backtrader) adapted from gold_candle_ken.mq5

Key features:
- Two-candle pattern: small setup bar then big trigger bar
- Adaptive candle sizing: ATR-based OR percentile-based dynamic thresholds
- Grid recovery (optional) with ATR-based spacing and lot multiplier
- Trend filter via Moving Average
- Time window and spread filter (spread filter stubbed; requires broker-specific data)
- Take Profit management and shared TP for grid baskets
- Trailing individual stop-loss per position (optional)
- Trailing equity stop: closes all positions if drawdown from peak exceeds threshold

Adaptive Candle Sizing:
- ATR Method: Dynamically adjusts thresholds based on ATR multipliers (updates every bar)
- Percentile Method: Analyzes last 100 candles and uses percentile thresholds (updates every 100 bars)
- Mutually exclusive: Enable only one method via USE_ATR_CALCULATION or USE_PERCENTILE_CALCULATION

ATR-Based TP/SL (NEW):
- Use USE_ATR_TP_SL = True to enable ATR-based take profit and stop loss
- TP/SL automatically adapt to current market volatility
- Set TP_ATR_MULTIPLIER and SL_ATR_MULTIPLIER from optimizer results
- Example: TP = 2.0x ATR, SL = 1.0x ATR (from strategy_optimizer.py --optimize-tp-sl)

Account Optimization:
- Optimized for $10,000 account with minimum lot size (0.01 lots)
- Uses proper CONTRACT_SIZE = 100 for XAUUSD (1 lot = 100 oz)
- Position size validation prevents over-leverage
- Grid trading enabled with 85% max exposure allowing 2 positions (~79% actual)

Notes:
- Parameters are hardcoded per request since TradeLocker bots typically lack adjustable inputs.
- Backtrader does not provide native account equity; we track portfolio value to simulate equity.
- Spread filtering requires bid/ask; most feeds in Backtrader provide mid. A conservative stub is used.
"""

import logging
from typing import List

import backtrader as bt


class GoldCandleKenStrategy(bt.Strategy):
    # Hardcoded defaults from provided template
    # --- Core Strategy Settings ---
    MAGIC_NUMBER = 69
    LOT_SIZE = 0.01  # Minimum broker lot size for XAUUSD (1 oz = ~$3,400)
    MIN_LOT_SIZE = 0.01  # Broker's minimum lot size
    LOT_STEP = 0.01  # Broker's lot size increment
    
    # --- Adaptive Candle Size Settings ---
    USE_ATR_CALCULATION = True  # Dynamically set candle size based on ATR multipliers
    USE_PERCENTILE_CALCULATION = False  # Dynamically set candle size based on percentiles
    
    # Static candle size (used when both adaptive methods are disabled)
    BIG_CANDLE_POINTS = 150  # Increased from 140 - more selective entries
    SMALL_CANDLE_POINTS = 50  # Decreased from 140 - allow smaller setup candles
    
    # ATR-based adaptive settings (when USE_ATR_CALCULATION = True)
    ATR_SMALL_MULTIPLIER = 0.8  # Small candle = 0.5x ATR (~ 30th percentile)
    ATR_BIG_MULTIPLIER = 1.1    # Big candle = 1.5x ATR (~ 75th percentile)
    
    # Percentile-based adaptive settings (when USE_PERCENTILE_CALCULATION = True)
    PERCENTILE_LOOKBACK = 100    # Number of candles to analyze
    PERCENTILE_UPDATE_FREQ = 100 # Recalculate every N candles
    SMALL_CANDLE_PERCENTILE = 40 # Percentile for small candle threshold
    BIG_CANDLE_PERCENTILE = 60   # Percentile for big candle threshold

    # --- Take Profit / Stop Loss Settings ---
    # Choose between fixed points OR ATR-based (not both)
    USE_ATR_TP_SL = False  # If True, use ATR multipliers; if False, use fixed points
    
    # Fixed point-based TP/SL (used when USE_ATR_TP_SL = False)
    TAKE_PROFIT_POINTS = 150  # Fixed points
    POSITION_SL_POINTS = 50  # Fixed points (only if ENABLE_POSITION_SL = True)
    
    # ATR-based TP/SL (used when USE_ATR_TP_SL = True)
    TP_ATR_MULTIPLIER = 3.0  # Take profit = 2.0 x ATR (from optimizer)
    SL_ATR_MULTIPLIER = 2.0  # Stop loss = 1.0 x ATR (from optimizer)

    # --- Grid Settings ---
    ENABLE_GRID = False
    ATR_MULTIPLIER_STEP = 3.5  # Increased from 2.5 - wider spacing between grid levels
    LOT_MULTIPLIER = 1.05  # Decreased from 1.1 - slower position growth
    MAX_OPEN_TRADES = 2  # Limit to 2 positions for $10k account with 0.01 min lot
    GRID_PROFIT_POINTS = 150  # Match regular TP - increased from 20

    # --- Position Stop Loss Settings ---
    ENABLE_POSITION_SL = False  # Enable static stop loss per position

    # ENABLE_TRAILING_POSITION_SL: Trails the price of your individual position
    # Moves the stop-loss as price moves in your favor
    # Operates at the position level (per trade)
    ENABLE_TRAILING_POSITION_SL = True
    TRAILING_POSITION_SL_POINTS = 50  # Increased from 20 if you enable it

    # --- Account Equity Protection Settings ---
    # The hard stop was triggering with a $384 loss on a position that moved IN FAVOR
    # This suggests a broker configuration issue with contract multiplier
    # ENABLE_EQUITY_STOP: Tracks maximum account drawdown from all-time peak
    # Set MAX_DRAWDOWN_PERCENT to limit overall account risk
    ENABLE_EQUITY_STOP = False  # Set to True once broker multiplier is confirmed
    MAX_DRAWDOWN_PERCENT = 1.0  # Increased to 10% while debugging (was 3.0%)

    ENABLE_TRAILING_EQUITY_STOP = False
    # The trailing equity stop ONLY tracks equity when you have an open position, and it resets to None when flat. This means:
    # It's designed to protect profits on individual trades, not overall account drawdown
    # It measures the drop from the peak while a position is open, not from your account's all-time high
    # When you close a position and open a new one, the peak resets
    TRAILING_EQUITY_DROP_PERCENT = 1.0
    MAX_TRAILING_STOPS = 3

    # --- Position Sizing Limits ---
    # Optimized for $10k account with 0.01 lot minimum:
    # - Single position: 0.01 lots = ~$3,857 (38.57% of account)
    # - Grid (2 positions): 0.01 + 0.0105 lots = ~$7,907 (79.07% of account)
    # - Grid (3 positions): Would require ~$12,159 (121.59% - needs leverage)
    # Increasing this will allow us to trade with larger lots , but involves more risk
    MAX_POSITION_SIZE_PERCENT = 100.0  # Allows 2 grid positions with margin buffer
    
    TRADING_DIRECTION = 0
    MAX_SPREAD_POINTS = 20
    ENABLE_TREND_FILTER = True
    MA_PERIOD = 100
    MA_METHOD = 1
    MA_APPLIED_PRICE = 1
    ENABLE_TIME_FILTER = True
    START_HOUR = 5
    END_HOUR = 12

    # --- Indicator Settings ---
    ATR_PERIOD = 14

    # --- Logging Settings ---
    LOG_LEVEL = logging.INFO  # INFO for production, DEBUG for development
    LOG_FILE = None  # Set to file path for file logging, e.g., "/var/log/trading_bot.log"
    
    def __init__(self):
        # Setup logging
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{id(self)}")
        self.logger.setLevel(self.LOG_LEVEL)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create formatter with timestamp
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (optional)
        if self.LOG_FILE:
            file_handler = logging.FileHandler(self.LOG_FILE)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        self.logger.info("=" * 60)
        self.logger.info(f"Initializing {self.__class__.__name__}")
        self.logger.info(f"Log Level: {logging.getLevelName(self.LOG_LEVEL)}")
        
        # Validate mutually exclusive settings
        if self.ENABLE_POSITION_SL and self.ENABLE_TRAILING_POSITION_SL:
            raise ValueError(
                "Configuration Error: Cannot enable both ENABLE_POSITION_SL and ENABLE_TRAILING_POSITION_SL. "
                "Choose one stop-loss method. Set one to False."
            )
        
        if self.ENABLE_EQUITY_STOP and self.ENABLE_TRAILING_EQUITY_STOP:
            raise ValueError(
                "Configuration Error: Cannot enable both ENABLE_EQUITY_STOP and ENABLE_TRAILING_EQUITY_STOP. "
                "Choose one equity protection method. Set one to False."
            )
        
        if self.USE_ATR_CALCULATION and self.USE_PERCENTILE_CALCULATION:
            raise ValueError(
                "Configuration Error: Cannot enable both USE_ATR_CALCULATION and USE_PERCENTILE_CALCULATION. "
                "Choose one adaptive candle sizing method. Set one to False."
            )
        
        # ATR-based TP/SL and trailing stops are incompatible
        # ATR-based uses dynamic distances (e.g., 1.0 x ATR = 50 points today, 60 points tomorrow)
        # Trailing uses fixed TRAILING_POSITION_SL_POINTS (always same distance)
        # Mixing these creates inconsistency and unpredictable behavior
        if self.USE_ATR_TP_SL and self.ENABLE_TRAILING_POSITION_SL:
            raise ValueError(
                "Configuration Error: Cannot enable both USE_ATR_TP_SL and ENABLE_TRAILING_POSITION_SL. "
                "ATR-based TP/SL uses dynamic distances (adapts to volatility), "
                "but trailing SL uses fixed TRAILING_POSITION_SL_POINTS (static distance). "
                "This creates inconsistency. Choose one approach: "
                "\n  1) USE_ATR_TP_SL=True with ENABLE_POSITION_SL=True (ATR-based static SL - RECOMMENDED)"
                "\n  2) USE_ATR_TP_SL=False with ENABLE_TRAILING_POSITION_SL=True (fixed-point trailing SL)"
            )
        
        data = self.datas[0]
        self.data_close = data.close
        self.data_high = data.high
        self.data_low = data.low
        self.data_open = data.open
        self.data_datetime = data.datetime

        # Point size estimation: Backtrader doesn't provide symbol point
        # Assume 1 pip = 0.01 for 2-decimal instruments and 0.0001 for FX; fallback to price resolution.
        self.point = self._infer_point()

        # Bid/Ask presence for spread filtering
        self._has_bidask = hasattr(data, 'ask') and hasattr(data, 'bid')

        # Trend MA
        if self.MA_METHOD == 1:
            self.ma = bt.ind.EMA(data, period=self.MA_PERIOD)
        else:
            self.ma = bt.ind.SMA(data, period=self.MA_PERIOD)

        # ATR for grid spacing
        self.atr = bt.ind.ATR(data, period=self.ATR_PERIOD)

        # Track peak portfolio value for equity stops - SEPARATED for each mechanism
        self.hard_stop_peak = None  # For hard drawdown stop (from initial balance)
        self.trailing_equity_peak = None  # For trailing equity stop (from position peak)
        self.equity_stop_triggered = False  # Flag to stop trading after equity stop
        self.consecutive_trailing_stops = 0  # Count consecutive trailing equity stops

        # Track our entries for grid management
        self._entries: List[dict] = []  # {dir: 1|-1, entry: float, tp: Optional[float], sl: Optional[float]}
        self._last_entry_price = None  # Track last entry for grid spacing

        # Trailing stop tracking
        self.trailing_stop_level = None  # Track current trailing SL level
        
        # New bar detection
        self.last_bar_datetime = None
        
        # Adaptive candle size tracking
        self.candle_ranges = []  # Buffer for percentile calculation
        self.bar_count = 0  # Track bars for percentile recalculation
        self.adaptive_big_candle = self.BIG_CANDLE_POINTS  # Current adaptive threshold
        self.adaptive_small_candle = self.SMALL_CANDLE_POINTS  # Current adaptive threshold

    # Order and Trade Notifications
    def notify_order(self, order):
        """Track order lifecycle - remove failed orders from tracking"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            # Order successfully filled
            if order.isbuy():
                self.log(f"BUY filled: {order.executed.size:.5f} @ {order.executed.price:.5f}")
            else:
                self.log(f"SELL filled: {order.executed.size:.5f} @ {order.executed.price:.5f}")
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            # Order failed - remove from tracking (was added optimistically on submission)
            if self._entries:
                self._entries.pop()
                self._last_entry_price = self._entries[-1]['entry'] if self._entries else None
                self.log(f"Order {order.getstatusname()}: Removed from tracking ({len(self._entries)} remaining)", "WARNING")
    
    def notify_trade(self, trade):
        """Log P&L when positions close"""
        if trade.isclosed:
            self.log(f"Trade closed: P&L=${trade.pnl:.2f}")
    
    # Utilities
    def _infer_point(self) -> float:
        # Try to infer from data price decimals
        # Get two recent closes and compute minimal tick
        lookback = min(len(self.datas[0]), 10)
        if lookback >= 2:
            diffs = []
            for i in range(1, lookback):
                d = abs(self.datas[0].close[-i] - self.datas[0].close[-i - 1])
                if d > 0:
                    diffs.append(d)
            if diffs:
                min_step = min(diffs)
                # round to nearest power of 10 step
                for p in [1e-5, 1e-4, 1e-3, 1e-2, 1e-1]:
                    if min_step >= p:
                        return p
        return 1e-2

    def _spread_points(self) -> float:
        if self._has_bidask:
            try:
                spread_price = float(self.datas[0].ask[0] - self.datas[0].bid[0])
                if self.point > 0:
                    return spread_price / self.point
            except Exception:
                return 0.0
        return 0.0

    def log(self, txt: str, level: str = "INFO") -> None:
        """
        Log a message with specified level.
        
        Args:
            txt: Message to log
            level: Log level - "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        """
        level_upper = level.upper()
        if level_upper == "DEBUG":
            self.logger.debug(txt)
        elif level_upper == "WARNING":
            self.logger.warning(txt)
        elif level_upper == "ERROR":
            self.logger.error(txt)
        elif level_upper == "CRITICAL":
            self.logger.critical(txt)
        else:  # Default to INFO
            self.logger.info(txt)
    
    def _log_position_state(self) -> None:
        """Log current position state from broker for verification"""
        if self.position.size == 0:
            return
        
        CONTRACT_SIZE = 100  # XAUUSD: 1 lot = 100 oz
        current_price = self.data_close[0]
        position_value = abs(self.position.size) * current_price * CONTRACT_SIZE
        account_equity = self.broker.getvalue()
        position_pnl = self.position.size * (current_price - self.position.price) * CONTRACT_SIZE
        
        self.log("BROKER POSITION STATE:")
        self.log(f"   Position Size (broker units): {self.position.size:.5f} ({abs(self.position.size) * CONTRACT_SIZE:.2f} oz)")
        self.log(f"   Position Average Price: {self.position.price:.5f}")
        self.log(f"   Current Market Price: {current_price:.5f}")
        self.log(f"   Position Notional Value: ${position_value:.2f}")
        self.log(f"   Position P&L: ${position_pnl:.2f}")
        self.log(f"   Account Equity: ${account_equity:.2f}")
        self.log(f"   Position % of Equity: {(position_value / account_equity * 100.0):.2f}%")
        self.log(f"   Tracked Entries: {len(self._entries)}")
    
    def _update_adaptive_candle_sizes(self) -> None:
        """Update candle size thresholds based on selected adaptive method"""
        if self.USE_ATR_CALCULATION:
            self._update_atr_based_thresholds()
        elif self.USE_PERCENTILE_CALCULATION:
            self._update_percentile_based_thresholds()
    
    def _update_atr_based_thresholds(self) -> None:
        """ATR-based adaptive candle sizing (updates every bar automatically)"""
        current_atr = float(self.atr[0])
        if current_atr <= 0:
            return
        
        # Convert ATR (price units) to points
        atr_in_points = current_atr / self.point
        
        self.adaptive_small_candle = self.ATR_SMALL_MULTIPLIER * atr_in_points
        self.adaptive_big_candle = self.ATR_BIG_MULTIPLIER * atr_in_points
        
        # Log changes periodically (every 100 bars to avoid spam)
        if len(self.data_close) % 100 == 0:
            self.log(f"ATR Adaptive Update: Small={self.adaptive_small_candle:.1f}pts, Big={self.adaptive_big_candle:.1f}pts (ATR={atr_in_points:.1f}pts)")
    
    def _update_percentile_based_thresholds(self) -> None:
        """Percentile-based adaptive candle sizing (recalculates every N bars)"""
        current_range = abs(self.data_high[0] - self.data_low[0])
        self.candle_ranges.append(current_range)
        self.bar_count += 1
        
        # Maintain rolling window
        if len(self.candle_ranges) > self.PERCENTILE_LOOKBACK:
            self.candle_ranges.pop(0)
        
        # Recalculate every N bars and only if we have enough data
        if self.bar_count % self.PERCENTILE_UPDATE_FREQ == 0 and len(self.candle_ranges) >= self.PERCENTILE_LOOKBACK:
            sorted_ranges = sorted(self.candle_ranges)
            
            # Calculate percentile indices
            small_idx = int(self.SMALL_CANDLE_PERCENTILE / 100.0 * len(sorted_ranges))
            big_idx = int(self.BIG_CANDLE_PERCENTILE / 100.0 * len(sorted_ranges))
            
            # Convert from price units to points
            self.adaptive_small_candle = sorted_ranges[small_idx] / self.point
            self.adaptive_big_candle = sorted_ranges[big_idx] / self.point
            
            self.log(f"Percentile Adaptive Update: Small={self.adaptive_small_candle:.1f}pts ({self.SMALL_CANDLE_PERCENTILE}th%), Big={self.adaptive_big_candle:.1f}pts ({self.BIG_CANDLE_PERCENTILE}th%)")

    # Entry logic is evaluated on each bar
    def next(self):
        # Stop all trading if equity stop was triggered
        if self.equity_stop_triggered:
            return
        
        # 0) Update adaptive candle sizes if enabled
        if self.USE_ATR_CALCULATION or self.USE_PERCENTILE_CALCULATION:
            self._update_adaptive_candle_sizes()
            
        # 1) Equity stops - CHECK FIRST before any position management
        if self.ENABLE_EQUITY_STOP:
            self._check_equity_drawdown_stop()
            if self.equity_stop_triggered:
                return
        
        if self.ENABLE_TRAILING_EQUITY_STOP:
            self._check_trailing_equity_stop()
            if self.equity_stop_triggered:
                return

        # 2) Trailing stop per-position (only for single positions, not grid)
        if self.ENABLE_TRAILING_POSITION_SL and self.position.size != 0 and len(self._entries) <= 1:
            if self._trail_individual_stop():
                return  # Position closed, don't process new entries this bar

        # 3) Manage active position: single vs grid basket (runs every tick)
        if self.position.size != 0:
            # Log actual broker position state periodically (every 10 bars)
            if len(self.data_close) % 10 == 0:
                self._log_position_state()
            
            if len(self._entries) <= 1:
                if self._manage_single_targets():
                    return  # Position closed, don't process new entries this bar
            else:
                if self._manage_grid():
                    return  # Position closed, don't process new entries this bar
        else:
            # Flat - clear any cached entries (handles desync from failed orders)
            if self._entries:
                self._entries.clear()
                self.trailing_stop_level = None
                self._last_entry_price = None

        # 4) Check for new entry signals ONLY on new completed bars
        if not self._is_new_bar():
            return

        # 5) Time filter
        if self.ENABLE_TIME_FILTER:
            hour = self.data_datetime.time(0).hour
            # Handle time windows that cross midnight (e.g., START_HOUR=20, END_HOUR=5)
            if self.START_HOUR <= self.END_HOUR:
                # Normal case: trade between START_HOUR and END_HOUR
                if hour < self.START_HOUR or hour >= self.END_HOUR:
                    return
            else:
                # Crosses midnight: trade if hour >= START_HOUR OR hour < END_HOUR
                if hour < self.START_HOUR and hour >= self.END_HOUR:
                    return

        # 6) Spread filter using bid/ask when available
        if self.MAX_SPREAD_POINTS is not None:
            spread_pts = self._spread_points()
            if spread_pts > self.MAX_SPREAD_POINTS:
                self.log(f"Spread too high: {spread_pts:.2f} > {self.MAX_SPREAD_POINTS}")
                return

        # 7) Check pattern on completed bars: use [-1] and [-2]
        # Need at least 2 completed bars
        if len(self.data_close) < 2:
            return

        # Bars: setup = -2 (older), trigger = -1 (most recent completed)
        big_candle_size = abs(self.data_high[-1] - self.data_low[-1])
        small_candle_size = abs(self.data_high[-2] - self.data_low[-2])
        
        # Use adaptive thresholds if enabled, otherwise use static values
        big_threshold = self.adaptive_big_candle * self.point
        small_threshold = self.adaptive_small_candle * self.point

        if big_candle_size >= big_threshold and small_candle_size <= small_threshold:
            bullish_setup = self.data_close[-2] > self.data_open[-2]
            bearish_setup = self.data_close[-2] < self.data_open[-2]

            # Trend check using most recent completed bar
            allow_buy = self.TRADING_DIRECTION in (0, 1)
            allow_sell = self.TRADING_DIRECTION in (0, 2)
            trend_up = self.data_close[-1] > self.ma[-1]

            if bullish_setup and allow_buy and (not self.ENABLE_TREND_FILTER or trend_up):
                self._open_trade(is_buy=True)
            elif bearish_setup and allow_sell and (not self.ENABLE_TREND_FILTER or not trend_up):
                self._open_trade(is_buy=False)
    
    def _is_new_bar(self) -> bool:
        """Check if a new bar has formed (mimics MT5 IsNewBar)"""
        current_dt = self.data_datetime.datetime(0)
        if self.last_bar_datetime != current_dt:
            self.last_bar_datetime = current_dt
            return True
        return False

    # Hard equity drawdown stop: close all when drawdown from peak exceeds threshold
    def _check_equity_drawdown_stop(self):
        """Hard stop based on max drawdown from peak equity"""
        current_value = self.broker.getvalue()
        
        # Initialize peak on first call
        if self.hard_stop_peak is None:
            self.hard_stop_peak = current_value
            self.log(f"Hard stop peak initialized: {self.hard_stop_peak:.2f}")
            return
        
        # Always update peak if current value exceeds it
        if current_value > self.hard_stop_peak:
            self.hard_stop_peak = current_value
            self.log(f"Hard stop peak updated: {self.hard_stop_peak:.2f}")
            return
        
        # Calculate drawdown from peak
        drawdown_pct = (self.hard_stop_peak - current_value) / self.hard_stop_peak * 100.0
        
        # === ENHANCED DIAGNOSTIC LOGGING ===
        # Log detailed equity breakdown when we have an open position
        if self.position.size != 0:
            CONTRACT_SIZE = 100
            current_price = self.data_close[0]
            
            # Calculate P&L using strategy's CONTRACT_SIZE assumption
            position_pnl_with_multiplier = self.position.size * (current_price - self.position.price) * CONTRACT_SIZE
            
            # Calculate P&L WITHOUT multiplier (what broker might be using)
            position_pnl_no_multiplier = self.position.size * (current_price - self.position.price)
            
            # Get broker's cash (should be starting cash minus/plus realized P&L)
            broker_cash = self.broker.get_cash()
            
            # Calculate what equity SHOULD be with correct multiplier
            expected_equity_with_multiplier = broker_cash + position_pnl_with_multiplier
            
            self.log("=" * 60)
            self.log("EQUITY DIAGNOSTIC (Hard Stop Check):")
            self.log(f"  Position Size: {self.position.size:.5f} broker units")
            self.log(f"  Position Entry Price: {self.position.price:.5f}")
            self.log(f"  Current Price: {current_price:.5f}")
            self.log(f"  Price Difference: {current_price - self.position.price:.5f}")
            self.log(f"  ---")
            self.log(f"  Broker Cash: ${broker_cash:.2f}")
            self.log(f"  Broker Equity (getvalue): ${current_value:.2f}")
            self.log(f"  Broker Implied P&L: ${current_value - broker_cash:.2f}")
            self.log(f"  ---")
            self.log(f"  Expected P&L (WITH x100 multiplier): ${position_pnl_with_multiplier:.2f}")
            self.log(f"  Expected Equity (WITH multiplier): ${expected_equity_with_multiplier:.2f}")
            self.log(f"  Expected P&L (NO multiplier): ${position_pnl_no_multiplier:.2f}")
            self.log(f"  Expected Equity (NO multiplier): ${broker_cash + position_pnl_no_multiplier:.2f}")
            self.log(f"  ---")
            self.log(f"  MISMATCH: ${abs(current_value - expected_equity_with_multiplier):.2f}")
            self.log("=" * 60)
        
        # Log drawdown periodically for monitoring
        if len(self.data_close) % 10 == 0:  # Log every 10 bars
            self.log(f"Current drawdown: {drawdown_pct:.2f}% (Peak: {self.hard_stop_peak:.2f}, Current: {current_value:.2f})")
        
        if drawdown_pct >= self.MAX_DRAWDOWN_PERCENT:
            self.log(
                f"HARD EQUITY STOP TRIGGERED: DD {drawdown_pct:.2f}% >= {self.MAX_DRAWDOWN_PERCENT:.2f}% "
                f"(Peak: {self.hard_stop_peak:.2f}, Current: {current_value:.2f}). CLOSING ALL POSITIONS.",
                "CRITICAL"
            )
            # Close all positions
            if self.position.size != 0:
                self.close()
            # Set flag to stop all further trading (mimics MT5 ExpertRemove)
            self.equity_stop_triggered = True
    
    def _check_trailing_equity_stop(self):
        """Trailing equity stop: closes positions when equity drops X% from peak (locks in profits)"""
        current_value = self.broker.getvalue()
        
        # Only activate trailing if we have an open position
        if self.position.size == 0:
            self.trailing_equity_peak = None  # Reset when flat
            return
            
        # Update peak only when in position
        if self.trailing_equity_peak is None or current_value > self.trailing_equity_peak:
            self.trailing_equity_peak = current_value
            self.log(f"Trailing equity peak updated: {self.trailing_equity_peak:.2f}")
            # Reset counter when reaching new peak (profitable trade)
            if current_value > self.broker.startingcash:
                self.consecutive_trailing_stops = 0
            return
        
        # Calculate drop from peak
        drop_pct = (self.trailing_equity_peak - current_value) / self.trailing_equity_peak * 100.0
        if drop_pct >= self.TRAILING_EQUITY_DROP_PERCENT:
            self.log(
                f"TRAILING EQUITY STOP HIT #{self.consecutive_trailing_stops + 1}: Drop {drop_pct:.2f}% >= {self.TRAILING_EQUITY_DROP_PERCENT:.2f}% "
                f"(Peak: {self.trailing_equity_peak:.2f}, Current: {current_value:.2f}). Closing positions.",
                "WARNING"
            )
            # Close position
            if self.position.size != 0:
                self.close()
            
            # Increment counter
            self.consecutive_trailing_stops += 1
            
            # Stop all trading if max consecutive trailing stops reached
            if self.consecutive_trailing_stops >= self.MAX_TRAILING_STOPS:
                self.log(
                    f"MAX CONSECUTIVE TRAILING STOPS REACHED ({self.consecutive_trailing_stops}). "
                    f"STOPPING ALL TRADING.",
                    "CRITICAL"
                )
                self.equity_stop_triggered = True
            
            # Reset peak after closing
            self.trailing_equity_peak = None

    def _open_trade(self, is_buy: bool):
        # Respect max open trades (use entry count, not position size calc)
        if len(self._entries) >= self.MAX_OPEN_TRADES:
            self.log(f"Max open trades reached: {len(self._entries)}")
            return

        # Calculate next position size
        size = self._next_lot_size()
        price = self.data_close[0]
        
        # Validate position size against account equity
        if not self._validate_position_size(size, price):
            return

        # Calculate TP and SL
        if self.USE_ATR_TP_SL:
            # ATR-based TP/SL (dynamic, adapts to volatility)
            current_atr = float(self.atr[0])
            tp_distance = self.TP_ATR_MULTIPLIER * current_atr
            sl_distance = self.SL_ATR_MULTIPLIER * current_atr if self.ENABLE_POSITION_SL else None
        else:
            # Fixed point-based TP/SL (static)
            tp_distance = self.TAKE_PROFIT_POINTS * self.point
            sl_distance = self.POSITION_SL_POINTS * self.point if self.ENABLE_POSITION_SL else None
        
        # Apply TP/SL to current price
        tp = None
        if is_buy:
            tp = price + tp_distance
        else:
            tp = price - tp_distance

        sl = None
        if self.ENABLE_POSITION_SL and sl_distance:
            if is_buy:
                sl = price - sl_distance
            else:
                sl = price + sl_distance

        # Calculate true notional value with contract size
        CONTRACT_SIZE = 100  # XAUUSD: 1 lot = 100 oz
        true_notional = size * price * CONTRACT_SIZE
        
        # Log trade details
        if self.USE_ATR_TP_SL:
            current_atr = float(self.atr[0])
            tp_sl_mode = f"ATR-based (ATR={current_atr:.2f}, TP={self.TP_ATR_MULTIPLIER}x, SL={self.SL_ATR_MULTIPLIER}x)"
        else:
            tp_sl_mode = f"Fixed points (TP={self.TAKE_PROFIT_POINTS}, SL={self.POSITION_SL_POINTS})"
        
        if is_buy:
            self.buy(size=size)
            self.log(f"BUY ORDER PLACED:")
            self.log(f"   Size: {size} broker units ({size * CONTRACT_SIZE:.2f} oz)")
            self.log(f"   Price: {price:.5f}")
            self.log(f"   TP: {tp:.5f} ({tp_sl_mode})" if tp else "   TP: None")
            self.log(f"   SL: {sl:.5f}" if sl else "   SL: None")
            self.log(f"   Notional Value: ${true_notional:.2f}")
        else:
            self.sell(size=size)
            self.log(f"SELL ORDER PLACED:")
            self.log(f"   Size: {size} broker units ({size * CONTRACT_SIZE:.2f} oz)")
            self.log(f"   Price: {price:.5f}")
            self.log(f"   TP: {tp:.5f} ({tp_sl_mode})" if tp else "   TP: None")
            self.log(f"   SL: {sl:.5f}" if sl else "   SL: None")
            self.log(f"   Notional Value: ${true_notional:.2f}")

        # Cache intended TP/SL levels on strategy for management
        self._last_entry_price = price
        # track entry record
        self._entries.append({
            "dir": 1 if is_buy else -1,
            "entry": price,
            "tp": tp,
            "sl": sl,
        })
        
        # Log position tracking info
        self.log(f"   Entry #{len(self._entries)} tracked (Total entries: {len(self._entries)})")

    def _next_lot_size(self) -> float:
        """
        Calculate next lot size for grid trading.
        Uses LOT_SIZE with LOT_MULTIPLIER for grid recovery.
        Respects broker's minimum lot size and lot step requirements.
        """
        # Apply grid multiplier for subsequent positions
        entries = len(self._entries)
        calculated_size = self.LOT_SIZE * (self.LOT_MULTIPLIER ** entries)
        
        # Round to broker's lot step (e.g., 0.01)
        if self.LOT_STEP > 0:
            rounded_size = round(calculated_size / self.LOT_STEP) * self.LOT_STEP
        else:
            rounded_size = calculated_size
        
        # Ensure meets minimum lot size
        final_size = max(self.MIN_LOT_SIZE, rounded_size)
        
        return round(final_size, 5)
    
    def _validate_position_size(self, new_size: float, price: float) -> bool:
        """Validate that adding new position won't exceed maximum position size limits"""
        # CONTRACT SIZE for XAUUSD: 1 lot = 100 troy ounces
        # So 0.01 lots = 1 oz, and at $3857/oz = $3,857 exposure (not $38.57)
        CONTRACT_SIZE = 100  # Standard for XAUUSD (Gold)
        # Note: For FOREX, this would be 100000 (1 lot = 100k units)
        #       For other instruments, check TradeLocker specifications
        
        # Calculate current total position value
        current_position_value = abs(self.position.size) * price * CONTRACT_SIZE if self.position.size != 0 else 0.0
        
        # Calculate new position value that would be added
        new_position_value = new_size * price * CONTRACT_SIZE
        
        # Total position value after adding new position
        total_position_value = current_position_value + new_position_value
        
        # Get account equity
        account_equity = self.broker.getvalue()
        
        # Calculate maximum allowed position value
        max_position_value = account_equity * (self.MAX_POSITION_SIZE_PERCENT / 100.0)
        
        # === POSITION SIZING DEBUG LOGS ===
        self.log("=" * 60)
        self.log("POSITION SIZE VALIDATION CHECK:")
        self.log(f"  Account Equity: ${account_equity:.2f}")
        self.log(f"  Max Position Size Limit: {self.MAX_POSITION_SIZE_PERCENT}% = ${max_position_value:.2f}")
        self.log(f"  Current Price: {price:.5f}")
        self.log(f"  Current Position Size (broker units): {abs(self.position.size):.5f}")
        self.log(f"  Current Position Value: ${current_position_value:.2f}")
        self.log(f"  New Position Size (broker units): {new_size:.5f}")
        self.log(f"  New Position Value: ${new_position_value:.2f}")
        self.log(f"  Total Position Value After: ${total_position_value:.2f}")
        self.log(f"  Utilization: {(total_position_value / max_position_value * 100.0):.2f}%")
        
        # Validate
        if total_position_value > max_position_value:
            self.log(f"  REJECTED: Would exceed limit by ${total_position_value - max_position_value:.2f}", "ERROR")

            # Check if this is due to LOT_SIZE or minimum lot size being too large
            if len(self._entries) == 0:
                min_required_percent = (new_position_value / account_equity * 100.0)
                self.log(f"  Position size {new_size} lots = ${new_position_value:.2f}", "WARNING")
                self.log(f"  This exceeds your MAX_POSITION_SIZE_PERCENT limit of {self.MAX_POSITION_SIZE_PERCENT}%", "WARNING")
                self.log(f"  OPTIONS:", "WARNING")
                self.log(f"     1. Increase MAX_POSITION_SIZE_PERCENT to at least {min_required_percent:.1f}%", "WARNING")
                self.log(f"     2. OR decrease LOT_SIZE (currently {self.LOT_SIZE})", "WARNING")
                self.log(f"     3. OR increase account size (currently ${account_equity:.2f})", "WARNING")

            self.log("=" * 60)
            return False

        self.log(f"  APPROVED: Within limit (${max_position_value - total_position_value:.2f} remaining)")
        self.log("=" * 60)
        return True

    def _manage_grid(self) -> bool:
        """
        Manage grid trading logic
        Returns True if position was closed, False otherwise
        """
        if not self.ENABLE_GRID:
            return False

        current_price = self.data_close[0]
        direction_is_long = self.position.size > 0
        
        # CRITICAL: Check grid basket stop-loss FIRST using average position price
        if self.ENABLE_POSITION_SL and self.position.size != 0:
            # Use Backtrader's average position price for grid basket SL
            avg_price = self.position.price
            sl_distance = self.POSITION_SL_POINTS * self.point
            
            if direction_is_long:
                basket_sl = avg_price - sl_distance
                if current_price <= basket_sl:
                    self.log(
                        f"Grid basket SL hit @ {current_price:.5f} "
                        f"(Avg: {avg_price:.5f}, SL: {basket_sl:.5f}). Closing all positions."
                    )
                    self.close()
                    return True
            else:
                basket_sl = avg_price + sl_distance
                if current_price >= basket_sl:
                    self.log(
                        f"Grid basket SL hit @ {current_price:.5f} "
                        f"(Avg: {avg_price:.5f}, SL: {basket_sl:.5f}). Closing all positions."
                    )
                    self.close()
                    return True

        # Count basket entries from tracked list
        entries = len(self._entries)
        if entries >= self.MAX_OPEN_TRADES:
            # Still update shared TP for the basket
            return self._update_shared_takeprofit()

        # Determine last entry price directionally and ATR-based step
        recovery_step = float(self.atr[0]) * self.ATR_MULTIPLIER_STEP
        if recovery_step <= 0:
            return False

        # Use last entry price from our tracked entries, or current price as fallback
        last_price = self._last_entry_price if self._last_entry_price is not None else current_price
        distance = abs(current_price - last_price)

        if distance >= recovery_step:
            # Optional trend re-check before adding
            trend_up = self.data_close[0] > self.ma[0]
            if self.ENABLE_TREND_FILTER and ((direction_is_long and not trend_up) or (not direction_is_long and trend_up)):
                self.log("Trend reversed. Halting grid recovery.")
                return False

            size = self._next_lot_size()
            
            # Validate position size before adding to grid
            if not self._validate_position_size(size, current_price):
                self.log("Grid recovery stopped: position size limit would be exceeded.")
                return False
            
            CONTRACT_SIZE = 100  # XAUUSD: 1 lot = 100 oz
            
            if direction_is_long:
                self.buy(size=size)
                self.log(f"GRID BUY RECOVERY #{len(self._entries) + 1}:")
                self.log(f"   Size: {size} broker units ({size * CONTRACT_SIZE:.2f} oz)")
                self.log(f"   Price: {current_price:.5f}")
                self.log(f"   Notional: ${size * current_price * CONTRACT_SIZE:.2f}")
                tp = None
                sl = (current_price - self.POSITION_SL_POINTS * self.point) if self.ENABLE_POSITION_SL else None
                self._entries.append({"dir": 1, "entry": current_price, "tp": tp, "sl": sl})
            else:
                self.sell(size=size)
                self.log(f"GRID SELL RECOVERY #{len(self._entries) + 1}:")
                self.log(f"   Size: {size} broker units ({size * CONTRACT_SIZE:.2f} oz)")
                self.log(f"   Price: {current_price:.5f}")
                self.log(f"   Notional: ${size * current_price * CONTRACT_SIZE:.2f}")
                tp = None
                sl = (current_price + self.POSITION_SL_POINTS * self.point) if self.ENABLE_POSITION_SL else None
                self._entries.append({"dir": -1, "entry": current_price, "tp": tp, "sl": sl})
            self._last_entry_price = current_price
            
            # Log updated total exposure
            self.log(f"   Total Grid Positions: {len(self._entries)}")
            self.log(f"   Average Entry: {self.position.price:.5f} (will update after execution)")

        # Always recompute basket TP
        return self._update_shared_takeprofit()

    def _update_shared_takeprofit(self) -> bool:
        """
        Update and check shared take profit for grid basket
        Returns True if position was closed, False otherwise
        """
        if self.position.size == 0:
            return False

        avg_price = self.position.price
        direction_is_long = self.position.size > 0
        
        # Use ATR-based or fixed points for grid TP (same as regular TP)
        if self.USE_ATR_TP_SL:
            current_atr = float(self.atr[0])
            grid_profit_offset = self.TP_ATR_MULTIPLIER * current_atr
        else:
            grid_profit_offset = self.GRID_PROFIT_POINTS * self.point
        
        if direction_is_long:
            breakeven_plus = avg_price + grid_profit_offset
        else:
            breakeven_plus = avg_price - grid_profit_offset

        # Manage TP by closing when price crosses target
        price = self.data_close[0]
        if (direction_is_long and price >= breakeven_plus) or (not direction_is_long and price <= breakeven_plus):
            self.log(f"Basket TP reached @ {price:.5f} (Target: {breakeven_plus:.5f}). Closing position.")
            self.close()
            return True
        
        return False

    def _trail_individual_stop(self) -> bool:
        """
        Proper trailing stop: tracks highest/lowest and trails behind
        Returns True if position was closed, False otherwise
        """
        if self.position.size == 0 or not self.ENABLE_TRAILING_POSITION_SL:
            return False

        price = self.data_close[0]
        direction_is_long = self.position.size > 0
        trail_offset = self.TRAILING_POSITION_SL_POINTS * self.point

        if direction_is_long:
            # Initialize trailing stop on first call after opening position
            if self.trailing_stop_level is None:
                self.trailing_stop_level = price - trail_offset
                self.log(f"Initialized trailing SL (long) @ {self.trailing_stop_level:.5f}")
            else:
                # Update trailing stop only if price moves up
                new_trail = price - trail_offset
                if new_trail > self.trailing_stop_level:
                    self.trailing_stop_level = new_trail
                    self.log(f"Updated trailing SL (long) @ {self.trailing_stop_level:.5f}")
            
            # Check if price hit trailing stop
            if price <= self.trailing_stop_level:
                self.log(f"Trailing SL hit (long) @ {price:.5f}, SL level: {self.trailing_stop_level:.5f}. Closing.")
                self.close()
                self.trailing_stop_level = None
                return True
        else:
            # Initialize trailing stop for short
            if self.trailing_stop_level is None:
                self.trailing_stop_level = price + trail_offset
                self.log(f"Initialized trailing SL (short) @ {self.trailing_stop_level:.5f}")
            else:
                # Update trailing stop only if price moves down
                new_trail = price + trail_offset
                if new_trail < self.trailing_stop_level:
                    self.trailing_stop_level = new_trail
                    self.log(f"Updated trailing SL (short) @ {self.trailing_stop_level:.5f}")
            
            # Check if price hit trailing stop
            if price >= self.trailing_stop_level:
                self.log(f"Trailing SL hit (short) @ {price:.5f}, SL level: {self.trailing_stop_level:.5f}. Closing.")
                self.close()
                self.trailing_stop_level = None
                return True
        
        return False

    def _manage_single_targets(self) -> bool:
        """
        Manage single position TP/SL
        Returns True if position was closed, False otherwise
        """
        if self.position.size == 0 or not self._entries:
            return False
        price = self.data_close[0]
        entry = self._entries[-1]
        direction_is_long = self.position.size > 0

        # Static SL if enabled - CHECK THIS FIRST (most important)
        if self.ENABLE_POSITION_SL and entry.get("sl") is not None:
            sl_level = entry["sl"]
            if (direction_is_long and price <= sl_level) or (not direction_is_long and price >= sl_level):
                self.log(f"Static SL hit @ {price:.5f} (SL: {sl_level:.5f}). Closing single position.")
                self.close()
                return True

        # Take profit for single trade
        tp = entry.get("tp")
        if tp is not None:
            if (direction_is_long and price >= tp) or (not direction_is_long and price <= tp):
                self.log(f"Single trade TP reached @ {price:.5f} (TP: {tp:.5f}). Closing.")
                self.close()
                return True
        
        return False


# Convenience runner for local testing/backtest
def run_backtest(datafeed):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(GoldCandleKenStrategy)
    cerebro.adddata(datafeed)
    cerebro.broker.setcash(100000.0)
    
    # CRITICAL: Configure broker with correct contract multiplier for XAUUSD
    # Without this, Backtrader will calculate P&L as if 0.01 units = $38.44 exposure
    # instead of 0.01 lots = 1 oz = $3,844 exposure (100x difference!)
    comminfo = bt.CommInfoBase(
        commission=0.0002,  # 0.02% commission
        mult=100.0,         # CONTRACT_SIZE: 1 lot = 100 oz for XAUUSD
        margin=None,        # Not using margin calc, TradeLocker handles this
        commtype=bt.CommInfoBase.COMM_PERC  # Percentage-based commission
    )
    cerebro.broker.addcommissioninfo(comminfo)
    
    return cerebro.run()


