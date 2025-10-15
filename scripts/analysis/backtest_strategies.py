#!/usr/bin/env python3
"""
Strategy Backtesting Framework
Backtests Strategy 1 (PEAD) and Strategy 2 using historical data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

class StrategyBacktester:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / 'data'
        self.output_dir = self.data_dir / 'enriched' / 'backtest_results'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load all required data
        self.load_data()
        
    def load_data(self):
        """Load all required data for backtesting"""
        print("Loading data for backtesting...")
        
        # Load earnings beat statistics
        self.beat_stats = pd.read_csv(
            self.data_dir / 'enriched' / 'earnings_quality' / 'earnings_beat_statistics.csv'
        )
        print(f"  ✓ Loaded beat statistics for {len(self.beat_stats)} stocks")
        
        # Load post-earnings drift
        self.drift_stats = pd.read_csv(
            self.data_dir / 'enriched' / 'market_conditions' / 'post_earnings_drift.csv'
        )
        print(f"  ✓ Loaded drift statistics for {len(self.drift_stats)} stocks")
        
        # Load PEAD scorecard
        self.scorecard = pd.read_csv(
            self.data_dir / 'enriched' / 'analysis_results' / 'pead_master_scorecard.csv'
        )
        print(f"  ✓ Loaded PEAD scorecard for {len(self.scorecard)} stocks")
        
        # Store paths for historical data
        self.earnings_history_dir = self.data_dir / 'processed' / 'historical_data' / 'earnings_history'
        self.daily_prices_dir = self.data_dir / 'processed' / 'historical_data' / 'daily_prices'
        
        print("  ✓ Data loading complete\n")
    
    def load_stock_history(self, ticker):
        """Load earnings and price history for a single stock"""
        # Load earnings
        earnings_file = self.earnings_history_dir / f"{ticker}_earnings.csv"
        if not earnings_file.exists():
            return None, None
        
        earnings = pd.read_csv(earnings_file)
        earnings['earnings_date'] = pd.to_datetime(earnings['earnings_date'])
        earnings = earnings[earnings['reported_eps'].notna()].copy()
        
        if 'surprise_pct' not in earnings.columns:
            earnings['surprise_pct'] = (
                (earnings['reported_eps'] - earnings['eps_estimate']) / 
                earnings['eps_estimate'].abs() * 100
            )
        
        # Load prices
        prices_file = self.daily_prices_dir / f"{ticker}_daily_10y.csv"
        if not prices_file.exists():
            return earnings, None
        
        prices = pd.read_csv(prices_file)
        prices['date'] = pd.to_datetime(prices['date'], format='%Y%m%d', errors='coerce')
        prices = prices.sort_values('date')
        
        return earnings, prices
    
    def get_price_at_date(self, prices_df, target_date, days_offset=0):
        """Get price N days after target date"""
        if prices_df is None or len(prices_df) == 0:
            return None
        
        # Find prices after target date
        after_date = prices_df[prices_df['date'] > target_date]
        
        if len(after_date) < days_offset + 1:
            return None
        
        return after_date.iloc[days_offset]['close']
    
    def backtest_strategy1_pead(self, 
                                min_beat_rate=0.6,
                                min_surprise=5.0,
                                hold_days=10,
                                stop_loss=-0.08,
                                take_profit=0.12):
        """
        Backtest Strategy 1: PEAD (Post-Earnings Announcement Drift)
        
        Entry: After earnings beat >5%
        Hold: 10 days
        Exit: +12% target or -8% stop loss
        """
        print("=" * 80)
        print("BACKTESTING STRATEGY 1: PEAD")
        print("=" * 80)
        print(f"\nParameters:")
        print(f"  Min beat rate: {min_beat_rate:.0%}")
        print(f"  Min surprise: {min_surprise:.1f}%")
        print(f"  Hold days: {hold_days}")
        print(f"  Stop loss: {stop_loss:.1%}")
        print(f"  Take profit: {take_profit:.1%}")
        
        # Filter stocks meeting criteria
        qualified_stocks = self.scorecard[
            (self.scorecard['beat_rate'] >= min_beat_rate) &
            (self.scorecard['avg_beat_pct'] >= min_surprise)
        ]['ticker'].unique()
        
        print(f"\n  Qualified stocks: {len(qualified_stocks)}")
        
        all_trades = []
        
        for ticker in qualified_stocks:
            earnings, prices = self.load_stock_history(ticker)
            
            if earnings is None or prices is None:
                continue
            
            # Simulate trades on each earnings where surprise >5%
            for _, row in earnings.iterrows():
                surprise = row['surprise_pct']
                
                # Entry criteria: beat >5%
                if surprise <= min_surprise:
                    continue
                
                earnings_date = row['earnings_date']
                
                # Get entry price (1 day after earnings)
                entry_price = self.get_price_at_date(prices, earnings_date, days_offset=0)
                if entry_price is None:
                    continue
                
                # Simulate holding period
                best_exit_price = entry_price
                best_exit_day = 0
                hit_stop = False
                hit_target = False
                
                for day in range(1, hold_days + 1):
                    current_price = self.get_price_at_date(prices, earnings_date, days_offset=day)
                    
                    if current_price is None:
                        break
                    
                    current_return = (current_price - entry_price) / entry_price
                    
                    # Check stop loss
                    if current_return <= stop_loss:
                        best_exit_price = current_price
                        best_exit_day = day
                        hit_stop = True
                        break
                    
                    # Check take profit
                    if current_return >= take_profit:
                        best_exit_price = current_price
                        best_exit_day = day
                        hit_target = True
                        break
                    
                    # Track best price
                    if current_price > best_exit_price:
                        best_exit_price = current_price
                        best_exit_day = day
                
                # If no stop/target hit, exit at hold_days
                if not hit_stop and not hit_target:
                    exit_price = self.get_price_at_date(prices, earnings_date, days_offset=hold_days)
                    if exit_price is not None:
                        best_exit_price = exit_price
                        best_exit_day = hold_days
                
                # Calculate trade result
                trade_return = (best_exit_price - entry_price) / entry_price
                
                all_trades.append({
                    'ticker': ticker,
                    'earnings_date': earnings_date,
                    'surprise_pct': surprise,
                    'entry_price': entry_price,
                    'exit_price': best_exit_price,
                    'exit_day': best_exit_day,
                    'return_pct': trade_return * 100,
                    'hit_stop': hit_stop,
                    'hit_target': hit_target,
                    'strategy': 'PEAD'
                })
        
        # Create results DataFrame
        results_df = pd.DataFrame(all_trades)
        
        if len(results_df) == 0:
            print("\n⚠️  No trades generated. Check data availability.")
            return None
        
        # Calculate statistics
        self.print_strategy_results(results_df, "STRATEGY 1: PEAD")
        
        # Save results
        output_file = self.output_dir / 'strategy1_backtest_results.csv'
        results_df.to_csv(output_file, index=False)
        print(f"\n✓ Results saved to: {output_file}")
        
        return results_df
    
    def backtest_strategy2_recovery(self,
                                    min_drop=-0.15,
                                    max_drop=-0.05,
                                    hold_days=10,
                                    stop_loss=-0.08,
                                    take_profit=0.12):
        """
        Backtest Strategy 2: Post-Earnings Recovery
        
        Entry: After earnings miss causing 5-15% drop
        Hold: 10 days
        Exit: +12% target or -8% stop loss
        """
        print("\n" + "=" * 80)
        print("BACKTESTING STRATEGY 2: POST-EARNINGS RECOVERY")
        print("=" * 80)
        print(f"\nParameters:")
        print(f"  Min drop: {min_drop:.1%}")
        print(f"  Max drop: {max_drop:.1%}")
        print(f"  Hold days: {hold_days}")
        print(f"  Stop loss: {stop_loss:.1%}")
        print(f"  Take profit: {take_profit:.1%}")
        
        all_trades = []
        
        # Get all stocks
        all_tickers = self.scorecard['ticker'].unique()
        print(f"\n  Analyzing {len(all_tickers)} stocks...")
        
        for ticker in all_tickers:
            earnings, prices = self.load_stock_history(ticker)
            
            if earnings is None or prices is None:
                continue
            
            # Look for earnings misses with significant drops
            for _, row in earnings.iterrows():
                surprise = row['surprise_pct']
                earnings_date = row['earnings_date']
                
                # Get price before earnings
                price_before = self.get_price_at_date(prices, earnings_date - timedelta(days=1), days_offset=0)
                if price_before is None:
                    continue
                
                # Get price 1 day after earnings (to measure drop)
                price_after = self.get_price_at_date(prices, earnings_date, days_offset=0)
                if price_after is None:
                    continue
                
                # Calculate drop
                drop = (price_after - price_before) / price_before
                
                # Entry criteria: drop between 5-15%
                if drop > max_drop or drop < min_drop:
                    continue
                
                # Entry at price after drop
                entry_price = price_after
                
                # Simulate holding period
                best_exit_price = entry_price
                best_exit_day = 0
                hit_stop = False
                hit_target = False
                
                for day in range(1, hold_days + 1):
                    current_price = self.get_price_at_date(prices, earnings_date, days_offset=day)
                    
                    if current_price is None:
                        break
                    
                    current_return = (current_price - entry_price) / entry_price
                    
                    # Check stop loss
                    if current_return <= stop_loss:
                        best_exit_price = current_price
                        best_exit_day = day
                        hit_stop = True
                        break
                    
                    # Check take profit
                    if current_return >= take_profit:
                        best_exit_price = current_price
                        best_exit_day = day
                        hit_target = True
                        break
                    
                    # Track best price
                    if current_price > best_exit_price:
                        best_exit_price = current_price
                        best_exit_day = day
                
                # If no stop/target hit, exit at hold_days
                if not hit_stop and not hit_target:
                    exit_price = self.get_price_at_date(prices, earnings_date, days_offset=hold_days)
                    if exit_price is not None:
                        best_exit_price = exit_price
                        best_exit_day = hold_days
                
                # Calculate trade result
                trade_return = (best_exit_price - entry_price) / entry_price
                
                all_trades.append({
                    'ticker': ticker,
                    'earnings_date': earnings_date,
                    'surprise_pct': surprise,
                    'initial_drop_pct': drop * 100,
                    'entry_price': entry_price,
                    'exit_price': best_exit_price,
                    'exit_day': best_exit_day,
                    'return_pct': trade_return * 100,
                    'hit_stop': hit_stop,
                    'hit_target': hit_target,
                    'strategy': 'RECOVERY'
                })
        
        # Create results DataFrame
        results_df = pd.DataFrame(all_trades)
        
        if len(results_df) == 0:
            print("\n⚠️  No trades generated. Check data availability.")
            return None
        
        # Calculate statistics
        self.print_strategy_results(results_df, "STRATEGY 2: RECOVERY")
        
        # Save results
        output_file = self.output_dir / 'strategy2_backtest_results.csv'
        results_df.to_csv(output_file, index=False)
        print(f"\n✓ Results saved to: {output_file}")
        
        return results_df
    
    def print_strategy_results(self, results_df, strategy_name):
        """Print detailed backtest results"""
        print(f"\n{'=' * 80}")
        print(f"{strategy_name} - BACKTEST RESULTS")
        print(f"{'=' * 80}")
        
        total_trades = len(results_df)
        winning_trades = len(results_df[results_df['return_pct'] > 0])
        losing_trades = len(results_df[results_df['return_pct'] <= 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_return = results_df['return_pct'].mean()
        median_return = results_df['return_pct'].median()
        std_return = results_df['return_pct'].std()
        
        avg_win = results_df[results_df['return_pct'] > 0]['return_pct'].mean() if winning_trades > 0 else 0
        avg_loss = results_df[results_df['return_pct'] <= 0]['return_pct'].mean() if losing_trades > 0 else 0
        
        max_win = results_df['return_pct'].max()
        max_loss = results_df['return_pct'].min()
        
        hit_target = results_df['hit_target'].sum()
        hit_stop = results_df['hit_stop'].sum()
        
        # Calculate expectancy
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"  Total trades: {total_trades}")
        print(f"  Winning trades: {winning_trades} ({win_rate:.1%})")
        print(f"  Losing trades: {losing_trades} ({(1-win_rate):.1%})")
        print(f"\n📈 RETURNS:")
        print(f"  Average return: {avg_return:.2f}%")
        print(f"  Median return: {median_return:.2f}%")
        print(f"  Std deviation: {std_return:.2f}%")
        print(f"  Average winner: {avg_win:.2f}%")
        print(f"  Average loser: {avg_loss:.2f}%")
        print(f"  Best trade: {max_win:.2f}%")
        print(f"  Worst trade: {max_loss:.2f}%")
        print(f"\n🎯 EXIT ANALYSIS:")
        print(f"  Hit target (+12%): {hit_target} ({hit_target/total_trades:.1%})")
        print(f"  Hit stop (-8%): {hit_stop} ({hit_stop/total_trades:.1%})")
        print(f"  Time exit: {total_trades - hit_target - hit_stop} ({(total_trades - hit_target - hit_stop)/total_trades:.1%})")
        print(f"\n💰 EXPECTANCY:")
        print(f"  Per trade: {expectancy:.2f}%")
        
        # Risk metrics
        sharpe = (avg_return / std_return) if std_return > 0 else 0
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else float('inf')
        
        print(f"\n📊 RISK METRICS:")
        print(f"  Sharpe ratio: {sharpe:.2f}")
        print(f"  Profit factor: {profit_factor:.2f}")
        
        # Top performing stocks
        print(f"\n⭐ TOP 10 STOCKS BY AVERAGE RETURN:")
        stock_performance = results_df.groupby('ticker').agg({
            'return_pct': ['mean', 'count']
        }).round(2)
        stock_performance.columns = ['avg_return', 'trades']
        stock_performance = stock_performance[stock_performance['trades'] >= 3]  # Min 3 trades
        stock_performance = stock_performance.sort_values('avg_return', ascending=False).head(10)
        print(stock_performance.to_string())
        
        # Worst performing stocks
        print(f"\n⚠️  BOTTOM 10 STOCKS BY AVERAGE RETURN:")
        worst_stocks = results_df.groupby('ticker').agg({
            'return_pct': ['mean', 'count']
        }).round(2)
        worst_stocks.columns = ['avg_return', 'trades']
        worst_stocks = worst_stocks[worst_stocks['trades'] >= 3]
        worst_stocks = worst_stocks.sort_values('avg_return', ascending=True).head(10)
        print(worst_stocks.to_string())
    
    def compare_strategies(self, strat1_results, strat2_results):
        """Compare both strategies side by side"""
        print("\n" + "=" * 80)
        print("STRATEGY COMPARISON")
        print("=" * 80)
        
        if strat1_results is None or strat2_results is None:
            print("\n⚠️  Cannot compare - missing results")
            return
        
        comparison = pd.DataFrame({
            'Metric': [
                'Total Trades',
                'Win Rate',
                'Avg Return',
                'Avg Winner',
                'Avg Loser',
                'Best Trade',
                'Worst Trade',
                'Expectancy',
                'Hit Target Rate',
                'Hit Stop Rate'
            ],
            'Strategy 1 (PEAD)': [
                len(strat1_results),
                f"{(strat1_results['return_pct'] > 0).sum() / len(strat1_results):.1%}",
                f"{strat1_results['return_pct'].mean():.2f}%",
                f"{strat1_results[strat1_results['return_pct'] > 0]['return_pct'].mean():.2f}%",
                f"{strat1_results[strat1_results['return_pct'] <= 0]['return_pct'].mean():.2f}%",
                f"{strat1_results['return_pct'].max():.2f}%",
                f"{strat1_results['return_pct'].min():.2f}%",
                f"{((strat1_results['return_pct'] > 0).sum() / len(strat1_results) * strat1_results[strat1_results['return_pct'] > 0]['return_pct'].mean() + (1 - (strat1_results['return_pct'] > 0).sum() / len(strat1_results)) * strat1_results[strat1_results['return_pct'] <= 0]['return_pct'].mean()):.2f}%",
                f"{strat1_results['hit_target'].sum() / len(strat1_results):.1%}",
                f"{strat1_results['hit_stop'].sum() / len(strat1_results):.1%}"
            ],
            'Strategy 2 (Recovery)': [
                len(strat2_results),
                f"{(strat2_results['return_pct'] > 0).sum() / len(strat2_results):.1%}",
                f"{strat2_results['return_pct'].mean():.2f}%",
                f"{strat2_results[strat2_results['return_pct'] > 0]['return_pct'].mean():.2f}%",
                f"{strat2_results[strat2_results['return_pct'] <= 0]['return_pct'].mean():.2f}%",
                f"{strat2_results['return_pct'].max():.2f}%",
                f"{strat2_results['return_pct'].min():.2f}%",
                f"{((strat2_results['return_pct'] > 0).sum() / len(strat2_results) * strat2_results[strat2_results['return_pct'] > 0]['return_pct'].mean() + (1 - (strat2_results['return_pct'] > 0).sum() / len(strat2_results)) * strat2_results[strat2_results['return_pct'] <= 0]['return_pct'].mean()):.2f}%",
                f"{strat2_results['hit_target'].sum() / len(strat2_results):.1%}",
                f"{strat2_results['hit_stop'].sum() / len(strat2_results):.1%}"
            ]
        })
        
        print("\n" + comparison.to_string(index=False))
        
        # Recommendation
        print("\n" + "=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        
        strat1_expectancy = ((strat1_results['return_pct'] > 0).sum() / len(strat1_results) * 
                            strat1_results[strat1_results['return_pct'] > 0]['return_pct'].mean() + 
                            (1 - (strat1_results['return_pct'] > 0).sum() / len(strat1_results)) * 
                            strat1_results[strat1_results['return_pct'] <= 0]['return_pct'].mean())
        
        strat2_expectancy = ((strat2_results['return_pct'] > 0).sum() / len(strat2_results) * 
                            strat2_results[strat2_results['return_pct'] > 0]['return_pct'].mean() + 
                            (1 - (strat2_results['return_pct'] > 0).sum() / len(strat2_results)) * 
                            strat2_results[strat2_results['return_pct'] <= 0]['return_pct'].mean())
        
        if strat1_expectancy > strat2_expectancy:
            print(f"\n✅ STRATEGY 1 (PEAD) is recommended")
            print(f"   Higher expectancy: {strat1_expectancy:.2f}% vs {strat2_expectancy:.2f}%")
        else:
            print(f"\n✅ STRATEGY 2 (RECOVERY) is recommended")
            print(f"   Higher expectancy: {strat2_expectancy:.2f}% vs {strat1_expectancy:.2f}%")
        
        print(f"\n💡 Consider using BOTH strategies for diversification!")

def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent.parent
    
    # Create backtester
    backtester = StrategyBacktester(base_dir)
    
    # Run Strategy 1 backtest
    strat1_results = backtester.backtest_strategy1_pead(
        min_beat_rate=0.6,
        min_surprise=5.0,
        hold_days=10,
        stop_loss=-0.08,
        take_profit=0.12
    )
    
    # Run Strategy 2 backtest
    strat2_results = backtester.backtest_strategy2_recovery(
        min_drop=-0.15,
        max_drop=-0.05,
        hold_days=10,
        stop_loss=-0.08,
        take_profit=0.12
    )
    
    # Compare strategies
    backtester.compare_strategies(strat1_results, strat2_results)
    
    print("\n" + "=" * 80)
    print("✅ BACKTEST COMPLETE!")
    print("=" * 80)
    print(f"\nResults saved to: {backtester.output_dir}")
    print("\nFiles created:")
    print("  - strategy1_backtest_results.csv")
    print("  - strategy2_backtest_results.csv")

if __name__ == "__main__":
    main()


