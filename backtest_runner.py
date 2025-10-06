"""
Backtesting Runner for GoldCandleKenStrategy

Features:
- Fetches historical data from Polygon.io API
- Runs backtests with configurable parameters
- Outputs comprehensive performance metrics
- Supports multiple symbols and timeframes
- Can run batch tests with different configurations
- Saves results to JSON for later analysis
"""

import argparse
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import backtrader as bt
import pandas as pd
import requests

from ken_gold_candle import GoldCandleKenStrategy


class PolygonDataFetcher:
    """Fetch historical data from Polygon.io API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
    
    def fetch_aggregates(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        timeframe: str = "1",
        timespan: str = "hour",
        adjusted: bool = True,
        limit: int = 50000
    ) -> pd.DataFrame:
        """
        Fetch aggregated bars from Polygon API
        
        Args:
            ticker: Symbol (e.g., "X:XAUUSD" for gold, "AAPL" for stocks)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            timeframe: Multiplier for timespan (e.g., "1" for 1 hour)
            timespan: Time unit (minute, hour, day, week, month)
            adjusted: Whether to adjust for splits
            limit: Maximum number of results (default 50000)
        
        Returns:
            DataFrame with OHLCV data
        """
        url = (
            f"{self.base_url}/v2/aggs/ticker/{ticker}/"
            f"range/{timeframe}/{timespan}/{start_date}/{end_date}"
        )
        
        params = {
            "adjusted": str(adjusted).lower(),
            "sort": "asc",
            "limit": limit,
            "apiKey": self.api_key
        }
        
        logging.info(f"Fetching data for {ticker} from {start_date} to {end_date}")
        logging.info(f"Timeframe: {timeframe} {timespan}")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") != "OK":
            raise Exception(f"Polygon API error: {data.get('error', 'Unknown error')}")
        
        results = data.get("results", [])
        if not results:
            raise Exception(f"No data returned for {ticker}")
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Rename columns to match Backtrader expectations
        column_mapping = {
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume",
            "t": "timestamp"
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # Convert timestamp from milliseconds to datetime
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("datetime", inplace=True)
        
        # Select and order columns for Backtrader
        df = df[["open", "high", "low", "close", "volume"]]
        
        logging.info(f"Fetched {len(df)} bars")
        logging.info(f"Date range: {df.index[0]} to {df.index[-1]}")
        
        return df


class BacktestRunner:
    """Run backtests with comprehensive metrics"""
    
    def __init__(self, initial_cash: float = 10000.0):
        self.initial_cash = initial_cash
        self.results = []
    
    def run_backtest(
        self,
        data_feed: bt.feeds.PandasData,
        strategy_params: Optional[Dict] = None,
        run_name: str = "Backtest"
    ) -> Dict:
        """
        Run a single backtest with specified parameters
        
        Args:
            data_feed: Backtrader data feed
            strategy_params: Dictionary of strategy parameters to override
            run_name: Name/description of this backtest run
        
        Returns:
            Dictionary with backtest results and metrics
        """
        cerebro = bt.Cerebro()
        
        # Add strategy with custom parameters
        if strategy_params:
            cerebro.addstrategy(GoldCandleKenStrategy, **strategy_params)
        else:
            cerebro.addstrategy(GoldCandleKenStrategy)
        
        # Add data
        cerebro.adddata(data_feed)
        
        # Set initial cash
        cerebro.broker.setcash(self.initial_cash)
        
        # Configure broker for XAUUSD
        comminfo = bt.CommInfoBase(
            commission=0.0002,  # 0.02% commission
            mult=100.0,  # 1 lot = 100 oz for XAUUSD
            margin=True,
            commtype=bt.CommInfoBase.COMM_PERC
        )
        cerebro.broker.addcommissioninfo(comminfo)
        
        # Add analyzers for comprehensive metrics
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", timeframe=bt.TimeFrame.Days, annualize=True)
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns", timeframe=bt.TimeFrame.Days)
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        cerebro.addanalyzer(bt.analyzers.VWR, _name="vwr")  # Variability-Weighted Return
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="time_return")
        
        # Record starting value
        starting_value = cerebro.broker.getvalue()
        
        # Run backtest
        logging.info("=" * 80)
        logging.info(f"STARTING BACKTEST: {run_name}")
        logging.info("=" * 80)
        logging.info(f"Initial Portfolio Value: ${starting_value:,.2f}")
        
        # Run strategy
        results = cerebro.run()
        strat = results[0]
        
        # Record ending value
        ending_value = cerebro.broker.getvalue()
        
        # Extract metrics
        metrics = self._extract_metrics(strat, starting_value, ending_value, run_name)
        
        # Print summary
        self._print_summary(metrics)
        
        # Store results
        self.results.append(metrics)
        
        return metrics
    
    def _extract_metrics(
        self,
        strategy,
        starting_value: float,
        ending_value: float,
        run_name: str
    ) -> Dict:
        """Extract all metrics from strategy analyzers"""
        
        # Basic P&L metrics
        total_return = ending_value - starting_value
        return_pct = (total_return / starting_value) * 100.0
        
        # Sharpe Ratio
        sharpe_analysis = strategy.analyzers.sharpe.get_analysis()
        sharpe_ratio = sharpe_analysis.get("sharperatio", None)
        
        # Drawdown
        drawdown_analysis = strategy.analyzers.drawdown.get_analysis()
        max_drawdown_pct = drawdown_analysis.get("max", {}).get("drawdown", 0.0)
        max_drawdown_money = drawdown_analysis.get("max", {}).get("moneydown", 0.0)
        
        # Returns
        returns_analysis = strategy.analyzers.returns.get_analysis()
        avg_return = returns_analysis.get("ravg", 0.0)
        total_compounded_return = returns_analysis.get("rtot", 0.0)
        
        # Trade Analysis
        trade_analysis = strategy.analyzers.trades.get_analysis()
        total_trades = trade_analysis.get("total", {}).get("total", 0)
        won_trades = trade_analysis.get("won", {}).get("total", 0)
        lost_trades = trade_analysis.get("lost", {}).get("total", 0)
        
        win_rate = (won_trades / total_trades * 100.0) if total_trades > 0 else 0.0
        
        # P&L statistics
        pnl_net_total = trade_analysis.get("pnl", {}).get("net", {}).get("total", 0.0)
        pnl_net_avg = trade_analysis.get("pnl", {}).get("net", {}).get("average", 0.0)
        
        won_pnl_total = trade_analysis.get("won", {}).get("pnl", {}).get("total", 0.0)
        won_pnl_avg = trade_analysis.get("won", {}).get("pnl", {}).get("average", 0.0)
        won_pnl_max = trade_analysis.get("won", {}).get("pnl", {}).get("max", 0.0)
        
        lost_pnl_total = trade_analysis.get("lost", {}).get("pnl", {}).get("total", 0.0)
        lost_pnl_avg = trade_analysis.get("lost", {}).get("pnl", {}).get("average", 0.0)
        lost_pnl_max = trade_analysis.get("lost", {}).get("pnl", {}).get("max", 0.0)
        
        # Profit factor
        profit_factor = abs(won_pnl_total / lost_pnl_total) if lost_pnl_total != 0 else 0.0
        
        # Average trade duration
        avg_trade_bars = trade_analysis.get("len", {}).get("average", 0.0)
        
        # Longest winning/losing streaks
        win_streak = trade_analysis.get("streak", {}).get("won", {}).get("longest", 0)
        loss_streak = trade_analysis.get("streak", {}).get("lost", {}).get("longest", 0)
        
        # SQN (System Quality Number)
        sqn_analysis = strategy.analyzers.sqn.get_analysis()
        sqn = sqn_analysis.get("sqn", None)
        
        # VWR (Variability-Weighted Return)
        vwr_analysis = strategy.analyzers.vwr.get_analysis()
        vwr = vwr_analysis.get("vwr", None)
        
        # Build metrics dictionary
        metrics = {
            "run_name": run_name,
            "timestamp": datetime.now().isoformat(),
            "portfolio": {
                "starting_value": starting_value,
                "ending_value": ending_value,
                "total_return": total_return,
                "return_pct": return_pct,
            },
            "performance": {
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown_pct": max_drawdown_pct,
                "max_drawdown_money": max_drawdown_money,
                "avg_daily_return": avg_return,
                "total_compounded_return": total_compounded_return,
                "sqn": sqn,
                "vwr": vwr,
            },
            "trades": {
                "total": total_trades,
                "won": won_trades,
                "lost": lost_trades,
                "win_rate": win_rate,
                "win_streak": win_streak,
                "loss_streak": loss_streak,
                "avg_duration_bars": avg_trade_bars,
            },
            "pnl": {
                "net_total": pnl_net_total,
                "net_avg": pnl_net_avg,
                "profit_factor": profit_factor,
                "won": {
                    "total": won_pnl_total,
                    "avg": won_pnl_avg,
                    "max": won_pnl_max,
                },
                "lost": {
                    "total": lost_pnl_total,
                    "avg": lost_pnl_avg,
                    "max": lost_pnl_max,
                }
            }
        }
        
        return metrics
    
    def _print_summary(self, metrics: Dict):
        """Print formatted backtest summary"""
        logging.info("")
        logging.info("=" * 80)
        logging.info(f"BACKTEST RESULTS: {metrics['run_name']}")
        logging.info("=" * 80)
        
        # Portfolio metrics
        portfolio = metrics["portfolio"]
        logging.info("\n📊 PORTFOLIO PERFORMANCE")
        logging.info(f"  Starting Value:    ${portfolio['starting_value']:,.2f}")
        logging.info(f"  Ending Value:      ${portfolio['ending_value']:,.2f}")
        logging.info(f"  Total Return:      ${portfolio['total_return']:,.2f}")
        logging.info(f"  Return %:          {portfolio['return_pct']:.2f}%")
        
        # Performance metrics
        perf = metrics["performance"]
        logging.info("\n📈 PERFORMANCE METRICS")
        logging.info(f"  Sharpe Ratio:      {perf['sharpe_ratio'] if perf['sharpe_ratio'] else 'N/A'}")
        logging.info(f"  Max Drawdown:      {perf['max_drawdown_pct']:.2f}% (${perf['max_drawdown_money']:,.2f})")
        logging.info(f"  Avg Daily Return:  {perf['avg_daily_return']:.4f}")
        logging.info(f"  SQN:               {perf['sqn'] if perf['sqn'] else 'N/A'}")
        logging.info(f"  VWR:               {perf['vwr'] if perf['vwr'] else 'N/A'}")
        
        # Trade metrics
        trades = metrics["trades"]
        logging.info("\n🎯 TRADE STATISTICS")
        logging.info(f"  Total Trades:      {trades['total']}")
        logging.info(f"  Won:               {trades['won']} ({trades['win_rate']:.2f}%)")
        logging.info(f"  Lost:              {trades['lost']}")
        logging.info(f"  Win Streak:        {trades['win_streak']}")
        logging.info(f"  Loss Streak:       {trades['loss_streak']}")
        logging.info(f"  Avg Duration:      {trades['avg_duration_bars']:.1f} bars")
        
        # P&L metrics
        pnl = metrics["pnl"]
        logging.info("\n💰 PROFIT & LOSS")
        logging.info(f"  Net P&L:           ${pnl['net_total']:,.2f}")
        logging.info(f"  Avg Trade:         ${pnl['net_avg']:,.2f}")
        logging.info(f"  Profit Factor:     {pnl['profit_factor']:.2f}")
        logging.info(f"  Avg Win:           ${pnl['won']['avg']:,.2f}")
        logging.info(f"  Avg Loss:          ${pnl['lost']['avg']:,.2f}")
        logging.info(f"  Largest Win:       ${pnl['won']['max']:,.2f}")
        logging.info(f"  Largest Loss:      ${pnl['lost']['max']:,.2f}")
        
        logging.info("\n" + "=" * 80)
    
    def save_results(self, output_file: str = "backtest_results.json"):
        """Save all backtest results to JSON file"""
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        logging.info(f"\n💾 Results saved to {output_file}")
    
    def print_comparison(self):
        """Print comparison table of all backtest runs"""
        if len(self.results) < 2:
            return
        
        logging.info("\n" + "=" * 80)
        logging.info("BACKTEST COMPARISON")
        logging.info("=" * 80)
        
        # Print header
        logging.info(f"\n{'Run Name':<30} {'Return %':<12} {'Sharpe':<10} {'DD %':<10} {'Win %':<10} {'PF':<8}")
        logging.info("-" * 80)
        
        # Print each run
        for result in self.results:
            name = result["run_name"][:28]
            return_pct = result["portfolio"]["return_pct"]
            sharpe = result["performance"]["sharpe_ratio"]
            dd = result["performance"]["max_drawdown_pct"]
            win_rate = result["trades"]["win_rate"]
            pf = result["pnl"]["profit_factor"]
            
            sharpe_str = f"{sharpe:.2f}" if sharpe else "N/A"
            
            logging.info(
                f"{name:<30} {return_pct:>11.2f}% {sharpe_str:<10} "
                f"{dd:>9.2f}% {win_rate:>9.2f}% {pf:>7.2f}"
            )
        
        logging.info("=" * 80)


def main():
    """Main entry point for backtesting script"""
    parser = argparse.ArgumentParser(description="Run backtests on GoldCandleKenStrategy")
    
    # Data source arguments
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.environ.get("POLYGON_API_KEY"),
        help="Polygon.io API key (or set POLYGON_API_KEY env var)"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default="X:XAUUSD",
        help="Ticker symbol (default: X:XAUUSD for gold)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
        help="Start date (YYYY-MM-DD, default: 1 year ago)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date (YYYY-MM-DD, default: today)"
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="1",
        help="Timeframe multiplier (default: 1)"
    )
    parser.add_argument(
        "--timespan",
        type=str,
        default="hour",
        choices=["minute", "hour", "day", "week", "month"],
        help="Timespan unit (default: hour)"
    )
    
    # Backtest configuration
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=10000.0,
        help="Initial portfolio cash (default: 10000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="backtest_results.json",
        help="Output file for results (default: backtest_results.json)"
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default="Backtest Run",
        help="Name for this backtest run"
    )
    
    # Strategy parameter overrides
    parser.add_argument("--enable-grid", action="store_true", help="Enable grid trading")
    parser.add_argument("--enable-counter-trend", action="store_true", help="Enable counter-trend fade strategy")
    parser.add_argument("--lot-size", type=float, help="Override lot size")
    parser.add_argument("--tp-atr-mult", type=float, help="Override TP ATR multiplier")
    parser.add_argument("--sl-atr-mult", type=float, help="Override SL ATR multiplier")
    parser.add_argument("--max-drawdown", type=float, help="Override max drawdown percent")
    
    # Batch testing
    parser.add_argument(
        "--batch-test",
        action="store_true",
        help="Run multiple backtests with different configurations"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Validate API key
    if not args.api_key:
        logging.error("Polygon API key required. Set --api-key or POLYGON_API_KEY environment variable")
        return
    
    # Fetch data
    try:
        fetcher = PolygonDataFetcher(args.api_key)
        df = fetcher.fetch_aggregates(
            ticker=args.ticker,
            start_date=args.start_date,
            end_date=args.end_date,
            timeframe=args.timeframe,
            timespan=args.timespan
        )
    except Exception as e:
        logging.error(f"Failed to fetch data: {e}")
        return
    
    # Create Backtrader data feed
    data_feed = bt.feeds.PandasData(dataname=df)
    
    # Initialize backtest runner
    runner = BacktestRunner(initial_cash=args.initial_cash)
    
    if args.batch_test:
        # Run multiple backtests with different configurations
        logging.info("\n🔄 Running batch backtests...")
        
        test_configs = [
            {"name": "Default Strategy", "params": {}},
            {"name": "Grid Enabled", "params": {"ENABLE_GRID": True}},
            {"name": "Counter-Trend Fade", "params": {"ENABLE_COUNTER_TREND_FADE": True}},
            {"name": "Aggressive TP (4x ATR)", "params": {"TP_ATR_MULTIPLIER": 4.0}},
            {"name": "Conservative TP (2x ATR)", "params": {"TP_ATR_MULTIPLIER": 2.0}},
            {"name": "Tight SL (0.5x ATR)", "params": {"SL_ATR_MULTIPLIER": 0.5}},
            {"name": "Wide SL (2x ATR)", "params": {"SL_ATR_MULTIPLIER": 2.0}},
            {"name": "Higher Lot Size (0.05)", "params": {"LOT_SIZE": 0.05}},
        ]
        
        for config in test_configs:
            # Create fresh data feed for each test
            test_feed = bt.feeds.PandasData(dataname=df)
            runner.run_backtest(
                data_feed=test_feed,
                strategy_params=config["params"],
                run_name=config["name"]
            )
        
        # Print comparison
        runner.print_comparison()
    else:
        # Single backtest run
        strategy_params = {}
        
        # Apply parameter overrides
        if args.enable_grid:
            strategy_params["ENABLE_GRID"] = True
        if args.enable_counter_trend:
            strategy_params["ENABLE_COUNTER_TREND_FADE"] = True
        if args.lot_size:
            strategy_params["LOT_SIZE"] = args.lot_size
        if args.tp_atr_mult:
            strategy_params["TP_ATR_MULTIPLIER"] = args.tp_atr_mult
        if args.sl_atr_mult:
            strategy_params["SL_ATR_MULTIPLIER"] = args.sl_atr_mult
        if args.max_drawdown:
            strategy_params["MAX_DRAWDOWN_PERCENT"] = args.max_drawdown
        
        runner.run_backtest(
            data_feed=data_feed,
            strategy_params=strategy_params,
            run_name=args.run_name
        )
    
    # Save results
    runner.save_results(args.output)
    
    logging.info("\n✅ Backtesting complete!")


if __name__ == "__main__":
    main()

