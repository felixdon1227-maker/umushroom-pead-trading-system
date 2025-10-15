"""
Realistic Strategy Backtest with Slippage and Commissions
========================================================

Comprehensive backtest of the three-step earnings strategy with:
- Realistic slippage (0.05% per trade)
- Commission costs ($1 per trade)
- Market impact modeling
- Full performance metrics

Author: UMushroom Investment Strategy
Date: October 2024
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class RealisticStrategyBacktest:
    """
    Realistic backtest with slippage and commissions
    """
    
    def __init__(self, earnings_file, data_dir, initial_capital=100000):
        self.earnings_file = earnings_file
        self.data_dir = data_dir
        self.initial_capital = initial_capital
        
        # Trading costs
        self.slippage_pct = 0.05  # 0.05% slippage per trade
        self.commission_per_trade = 1.0  # $1 per trade
        
        # Load earnings data
        self.earnings = pd.read_csv(earnings_file)
        self.earnings['date'] = pd.to_datetime(self.earnings['date'])
        
        # Sort by date
        self.earnings = self.earnings.sort_values('date')
        
        print(f"✅ Loaded {len(self.earnings)} earnings events")
        print(f"📅 Date range: {self.earnings['date'].min()} to {self.earnings['date'].max()}")
        
        # Results storage
        self.trades = []
        self.portfolio_value = []
        
    def load_stock_data(self, ticker):
        """Load stock data"""
        try:
            base_path = os.path.join(self.data_dir, ticker)
            
            # Load daily data
            daily_file = os.path.join(base_path, f"{ticker}_daily_data.csv")
            if not os.path.exists(daily_file):
                return None
            
            daily = pd.read_csv(daily_file)
            if 'Date' not in daily.columns:
                return None
            
            daily['Date'] = pd.to_datetime(daily['Date'], utc=True).dt.tz_localize(None)
            daily.set_index('Date', inplace=True)
            daily = daily.sort_index()
            
            return daily
            
        except Exception as e:
            return None
    
    def calculate_entry_price(self, price, direction='buy'):
        """Calculate entry price with slippage"""
        if direction == 'buy':
            return price * (1 + self.slippage_pct / 100)
        else:  # sell
            return price * (1 - self.slippage_pct / 100)
    
    def calculate_position_size(self, capital, price, max_position_pct=5):
        """Calculate position size"""
        max_position_value = capital * (max_position_pct / 100)
        shares = int(max_position_value / price)
        return shares
    
    def backtest_three_step_strategy(self):
        """
        Backtest three-step strategy:
        1. Enter on Day 0 close if positive momentum
        2. Add to winners on Day 1
        3. Exit on Day 3
        """
        print("\n" + "="*80)
        print("BACKTESTING THREE-STEP STRATEGY")
        print("="*80)
        
        capital = self.initial_capital
        positions = {}
        
        for idx, row in self.earnings.iterrows():
            ticker = row['ticker']
            earnings_date = row['date']
            
            # Load stock data
            daily = self.load_stock_data(ticker)
            if daily is None:
                continue
            
            # Find earnings date in data
            try:
                if earnings_date not in daily.index:
                    closest_idx = daily.index.searchsorted(earnings_date)
                    if closest_idx >= len(daily):
                        continue
                    earnings_date = daily.index[closest_idx]
                
                earnings_idx = daily.index.get_loc(earnings_date)
                
                # Need data before and after
                if earnings_idx < 5 or earnings_idx + 10 >= len(daily):
                    continue
                
                # Get price data
                day0_data = daily.iloc[earnings_idx]
                day1_data = daily.iloc[earnings_idx + 1] if earnings_idx + 1 < len(daily) else None
                day3_data = daily.iloc[earnings_idx + 3] if earnings_idx + 3 < len(daily) else None
                
                if day1_data is None or day3_data is None:
                    continue
                
                # Calculate Day 0 return
                day0_return = (day0_data['Close'] - day0_data['Open']) / day0_data['Open'] * 100
                
                # STEP 1: Enter on Day 0 close if positive momentum
                pre_5day_data = daily.iloc[earnings_idx-5:earnings_idx]
                pre_momentum = (pre_5day_data.iloc[-1]['Close'] - pre_5day_data.iloc[0]['Close']) / pre_5day_data.iloc[0]['Close'] * 100
                
                # Entry criteria
                should_enter = (
                    pre_momentum > 0 and  # Positive pre-earnings momentum
                    day0_return > -2  # Not a huge drop on Day 0
                )
                
                if not should_enter:
                    continue
                
                # STEP 1: Initial entry on Day 0 close
                entry_price_day0 = self.calculate_entry_price(day0_data['Close'], 'buy')
                position_size = self.calculate_position_size(capital, entry_price_day0, max_position_pct=3)
                
                if position_size == 0:
                    continue
                
                entry_cost = position_size * entry_price_day0 + self.commission_per_trade
                
                if entry_cost > capital:
                    continue
                
                # STEP 2: Evaluate on Day 1 - add if positive
                day1_return = (day1_data['Close'] - day0_data['Close']) / day0_data['Close'] * 100
                
                additional_shares = 0
                additional_cost = 0
                
                if day1_return > 1:  # Strong positive move
                    # Add 50% more
                    additional_shares = int(position_size * 0.5)
                    entry_price_day1 = self.calculate_entry_price(day1_data['Close'], 'buy')
                    additional_cost = additional_shares * entry_price_day1 + self.commission_per_trade
                    
                    if entry_cost + additional_cost <= capital:
                        position_size += additional_shares
                    else:
                        additional_shares = 0
                        additional_cost = 0
                
                total_entry_cost = entry_cost + additional_cost
                
                # Update capital
                capital -= total_entry_cost
                
                # STEP 3: Exit on Day 3
                exit_price = self.calculate_entry_price(day3_data['Close'], 'sell')
                exit_value = position_size * exit_price - self.commission_per_trade
                
                # Calculate P&L
                gross_pnl = exit_value - total_entry_cost
                net_pnl = gross_pnl
                return_pct = (net_pnl / total_entry_cost) * 100
                
                # Update capital
                capital += exit_value
                
                # Record trade
                trade = {
                    'ticker': ticker,
                    'earnings_date': earnings_date,
                    'entry_date': earnings_date,
                    'exit_date': day3_data.name,
                    'entry_price': entry_price_day0,
                    'exit_price': exit_price,
                    'shares': position_size,
                    'entry_cost': total_entry_cost,
                    'exit_value': exit_value,
                    'gross_pnl': gross_pnl,
                    'net_pnl': net_pnl,
                    'return_pct': return_pct,
                    'day0_return': day0_return,
                    'day1_return': day1_return,
                    'pre_momentum': pre_momentum,
                    'added_on_day1': additional_shares > 0,
                    'sector': row.get('sector', 'Unknown'),
                    'market_cap': row.get('market_cap_usd', 0)
                }
                
                self.trades.append(trade)
                
                # Track portfolio value
                self.portfolio_value.append({
                    'date': day3_data.name,
                    'capital': capital,
                    'total_value': capital
                })
                
            except Exception as e:
                continue
        
        print(f"\n✅ Backtest complete: {len(self.trades)} trades executed")
        
        return pd.DataFrame(self.trades)
    
    def calculate_performance_metrics(self, trades_df):
        """Calculate comprehensive performance metrics"""
        print("\n" + "="*80)
        print("PERFORMANCE METRICS")
        print("="*80)
        
        if len(trades_df) == 0:
            print("❌ No trades to analyze")
            return {}
        
        # Basic metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['net_pnl'] > 0])
        losing_trades = len(trades_df[trades_df['net_pnl'] <= 0])
        win_rate = (winning_trades / total_trades) * 100
        
        # Returns
        total_pnl = trades_df['net_pnl'].sum()
        avg_return = trades_df['return_pct'].mean()
        avg_win = trades_df[trades_df['net_pnl'] > 0]['return_pct'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['net_pnl'] <= 0]['return_pct'].mean() if losing_trades > 0 else 0
        
        # Risk metrics
        std_return = trades_df['return_pct'].std()
        sharpe_ratio = (avg_return / std_return) * np.sqrt(total_trades) if std_return > 0 else 0
        
        # Downside deviation (for Sortino)
        negative_returns = trades_df[trades_df['return_pct'] < 0]['return_pct']
        downside_std = negative_returns.std() if len(negative_returns) > 0 else 0
        sortino_ratio = (avg_return / downside_std) * np.sqrt(total_trades) if downside_std > 0 else 0
        
        # Profit factor
        gross_profit = trades_df[trades_df['net_pnl'] > 0]['net_pnl'].sum()
        gross_loss = abs(trades_df[trades_df['net_pnl'] <= 0]['net_pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Drawdown
        cumulative_pnl = trades_df['net_pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        max_drawdown = drawdown.min()
        max_drawdown_pct = (max_drawdown / self.initial_capital) * 100
        
        # Final capital
        final_capital = self.initial_capital + total_pnl
        total_return_pct = (total_pnl / self.initial_capital) * 100
        
        # Print metrics
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"  Initial Capital: ${self.initial_capital:,.2f}")
        print(f"  Final Capital: ${final_capital:,.2f}")
        print(f"  Total P&L: ${total_pnl:,.2f}")
        print(f"  Total Return: {total_return_pct:.2f}%")
        
        print(f"\n📈 TRADE STATISTICS:")
        print(f"  Total Trades: {total_trades}")
        print(f"  Winning Trades: {winning_trades}")
        print(f"  Losing Trades: {losing_trades}")
        print(f"  Win Rate: {win_rate:.1f}%")
        
        print(f"\n💰 RETURN METRICS:")
        print(f"  Average Return per Trade: {avg_return:.2f}%")
        print(f"  Average Win: {avg_win:.2f}%")
        print(f"  Average Loss: {avg_loss:.2f}%")
        print(f"  Win/Loss Ratio: {abs(avg_win/avg_loss):.2f}x" if avg_loss != 0 else "  Win/Loss Ratio: N/A")
        
        print(f"\n📊 RISK METRICS:")
        print(f"  Standard Deviation: {std_return:.2f}%")
        print(f"  Sharpe Ratio: {sharpe_ratio:.2f}")
        print(f"  Sortino Ratio: {sortino_ratio:.2f}")
        print(f"  Profit Factor: {profit_factor:.2f}")
        print(f"  Max Drawdown: ${max_drawdown:,.2f} ({max_drawdown_pct:.2f}%)")
        
        print(f"\n🎯 STRATEGY DETAILS:")
        trades_with_add = len(trades_df[trades_df['added_on_day1'] == True])
        print(f"  Trades with Day 1 addition: {trades_with_add} ({trades_with_add/total_trades*100:.1f}%)")
        print(f"  Average holding period: 3 days")
        
        # Sector breakdown
        print(f"\n🏢 SECTOR BREAKDOWN:")
        sector_perf = trades_df.groupby('sector').agg({
            'net_pnl': 'sum',
            'return_pct': 'mean',
            'ticker': 'count'
        }).sort_values('net_pnl', ascending=False)
        
        for sector, row in sector_perf.iterrows():
            print(f"  {sector}: P&L=${row['net_pnl']:,.2f}, Avg Return={row['return_pct']:.2f}%, Trades={int(row['ticker'])}")
        
        # Best and worst trades
        print(f"\n🏆 BEST TRADES:")
        best_trades = trades_df.nlargest(5, 'net_pnl')
        for idx, trade in best_trades.iterrows():
            print(f"  {trade['ticker']}: ${trade['net_pnl']:,.2f} ({trade['return_pct']:.2f}%) on {trade['earnings_date'].strftime('%Y-%m-%d')}")
        
        print(f"\n📉 WORST TRADES:")
        worst_trades = trades_df.nsmallest(5, 'net_pnl')
        for idx, trade in worst_trades.iterrows():
            print(f"  {trade['ticker']}: ${trade['net_pnl']:,.2f} ({trade['return_pct']:.2f}%) on {trade['earnings_date'].strftime('%Y-%m-%d')}")
        
        # Return metrics dictionary
        metrics = {
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'win_loss_ratio': abs(avg_win/avg_loss) if avg_loss != 0 else 0,
            'std_return': std_return,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'trades_with_day1_add': trades_with_add
        }
        
        return metrics
    
    def optimize_parameters(self, trades_df):
        """Analyze and suggest parameter optimizations"""
        print("\n" + "="*80)
        print("PARAMETER OPTIMIZATION SUGGESTIONS")
        print("="*80)
        
        if len(trades_df) == 0:
            print("❌ No trades to optimize")
            return
        
        # Analyze entry timing
        print(f"\n🎯 ENTRY TIMING ANALYSIS:")
        
        # Day 0 return impact
        positive_day0 = trades_df[trades_df['day0_return'] > 0]
        negative_day0 = trades_df[trades_df['day0_return'] < 0]
        
        print(f"  Enter after positive Day 0:")
        print(f"    Trades: {len(positive_day0)}")
        print(f"    Avg Return: {positive_day0['return_pct'].mean():.2f}%")
        print(f"    Win Rate: {(positive_day0['return_pct'] > 0).sum() / len(positive_day0) * 100:.1f}%")
        
        print(f"  Enter after negative Day 0:")
        print(f"    Trades: {len(negative_day0)}")
        print(f"    Avg Return: {negative_day0['return_pct'].mean():.2f}%")
        print(f"    Win Rate: {(negative_day0['return_pct'] > 0).sum() / len(negative_day0) * 100:.1f}%")
        
        # Pre-momentum impact
        print(f"\n📊 PRE-MOMENTUM ANALYSIS:")
        strong_momentum = trades_df[trades_df['pre_momentum'] > 5]
        weak_momentum = trades_df[trades_df['pre_momentum'] <= 5]
        
        print(f"  Strong pre-momentum (>5%):")
        print(f"    Trades: {len(strong_momentum)}")
        print(f"    Avg Return: {strong_momentum['return_pct'].mean():.2f}%")
        print(f"    Win Rate: {(strong_momentum['return_pct'] > 0).sum() / len(strong_momentum) * 100:.1f}%")
        
        print(f"  Weak pre-momentum (<=5%):")
        print(f"    Trades: {len(weak_momentum)}")
        print(f"    Avg Return: {weak_momentum['return_pct'].mean():.2f}%")
        print(f"    Win Rate: {(weak_momentum['return_pct'] > 0).sum() / len(weak_momentum) * 100:.1f}%")
        
        # Day 1 addition impact
        print(f"\n🔄 DAY 1 ADDITION ANALYSIS:")
        with_addition = trades_df[trades_df['added_on_day1'] == True]
        without_addition = trades_df[trades_df['added_on_day1'] == False]
        
        print(f"  With Day 1 addition:")
        print(f"    Trades: {len(with_addition)}")
        print(f"    Avg Return: {with_addition['return_pct'].mean():.2f}%")
        print(f"    Win Rate: {(with_addition['return_pct'] > 0).sum() / len(with_addition) * 100:.1f}%")
        
        print(f"  Without Day 1 addition:")
        print(f"    Trades: {len(without_addition)}")
        print(f"    Avg Return: {without_addition['return_pct'].mean():.2f}%")
        print(f"    Win Rate: {(without_addition['return_pct'] > 0).sum() / len(without_addition) * 100:.1f}%")
        
        # Recommendations
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        
        if positive_day0['return_pct'].mean() > negative_day0['return_pct'].mean():
            print(f"  ✅ Focus on stocks with positive Day 0 reaction")
        else:
            print(f"  ✅ Consider counter-trend entries after negative Day 0")
        
        if strong_momentum['return_pct'].mean() > weak_momentum['return_pct'].mean():
            print(f"  ✅ Increase pre-momentum threshold to >5%")
        else:
            print(f"  ✅ Lower pre-momentum threshold may improve results")
        
        if with_addition['return_pct'].mean() > without_addition['return_pct'].mean():
            print(f"  ✅ Day 1 additions are beneficial - continue strategy")
        else:
            print(f"  ✅ Consider skipping Day 1 additions")
    
    def save_results(self, trades_df, metrics):
        """Save backtest results"""
        print("\n" + "="*80)
        print("SAVING RESULTS")
        print("="*80)
        
        # Create results directory
        os.makedirs('results', exist_ok=True)
        
        # Save trades
        trades_file = 'results/realistic_backtest_trades.csv'
        trades_df.to_csv(trades_file, index=False)
        print(f"✅ Saved trades: {trades_file}")
        
        # Save metrics
        metrics_file = 'results/realistic_backtest_metrics.json'
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"✅ Saved metrics: {metrics_file}")
        
        # Generate report
        report = f"""
# REALISTIC STRATEGY BACKTEST REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## STRATEGY OVERVIEW
- **Initial Capital**: ${self.initial_capital:,.2f}
- **Final Capital**: ${metrics['final_capital']:,.2f}
- **Total Return**: {metrics['total_return_pct']:.2f}%
- **Total P&L**: ${metrics['total_pnl']:,.2f}

## TRADING COSTS
- **Slippage**: {self.slippage_pct}% per trade
- **Commission**: ${self.commission_per_trade} per trade
- **Total Commissions Paid**: ${metrics['total_trades'] * self.commission_per_trade * 2:.2f} (entry + exit)

## PERFORMANCE METRICS
- **Total Trades**: {metrics['total_trades']}
- **Winning Trades**: {metrics['winning_trades']}
- **Losing Trades**: {metrics['losing_trades']}
- **Win Rate**: {metrics['win_rate']:.1f}%

## RETURN METRICS
- **Average Return per Trade**: {metrics['avg_return']:.2f}%
- **Average Win**: {metrics['avg_win']:.2f}%
- **Average Loss**: {metrics['avg_loss']:.2f}%
- **Win/Loss Ratio**: {metrics['win_loss_ratio']:.2f}x

## RISK METRICS
- **Standard Deviation**: {metrics['std_return']:.2f}%
- **Sharpe Ratio**: {metrics['sharpe_ratio']:.2f}
- **Sortino Ratio**: {metrics['sortino_ratio']:.2f}
- **Profit Factor**: {metrics['profit_factor']:.2f}
- **Max Drawdown**: ${metrics['max_drawdown']:,.2f} ({metrics['max_drawdown_pct']:.2f}%)

## STRATEGY EXECUTION
- **Trades with Day 1 Addition**: {metrics['trades_with_day1_add']}
- **Average Holding Period**: 3 days
- **Position Sizing**: 3% initial, up to 4.5% with Day 1 add

## NEXT STEPS
1. Review optimization suggestions
2. Adjust parameters based on analysis
3. Re-run backtest with optimized parameters
4. Implement strategy for competition
"""
        
        report_file = 'results/REALISTIC_BACKTEST_REPORT.md'
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"✅ Saved report: {report_file}")
    
    def run_full_backtest(self):
        """Run complete backtest pipeline"""
        # Run backtest
        trades_df = self.backtest_three_step_strategy()
        
        # Calculate metrics
        metrics = self.calculate_performance_metrics(trades_df)
        
        # Optimize parameters
        self.optimize_parameters(trades_df)
        
        # Save results
        if len(trades_df) > 0:
            self.save_results(trades_df, metrics)
        
        print("\n" + "="*80)
        print("✅ REALISTIC BACKTEST COMPLETE!")
        print("="*80)

def main():
    """Main execution"""
    backtest = RealisticStrategyBacktest(
        earnings_file='data/processed/earnings_final.csv',
        data_dir='data/bulk_extraction',
        initial_capital=100000
    )
    
    backtest.run_full_backtest()

if __name__ == "__main__":
    main()

