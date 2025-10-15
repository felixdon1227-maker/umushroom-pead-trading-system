"""
Comprehensive Strategy Backtest and Analysis
===========================================

Analyzes the three-step earnings strategy on historical data
and generates detailed performance metrics and stock rankings.

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

class ComprehensiveStrategyAnalyzer:
    """
    Comprehensive backtest and analysis of earnings strategy
    """
    
    def __init__(self, earnings_file, data_dir, output_dir='results'):
        self.earnings_file = earnings_file
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Load earnings data
        self.earnings = pd.read_csv(earnings_file)
        self.earnings['date'] = pd.to_datetime(self.earnings['date'])
        
        print(f"✅ Loaded {len(self.earnings)} earnings events")
        print(f"📅 Date range: {self.earnings['date'].min()} to {self.earnings['date'].max()}")
        
        # Results storage
        self.backtest_results = []
        self.stock_rankings = []
        
    def load_stock_data(self, ticker):
        """Load all data for a stock"""
        try:
            base_path = os.path.join(self.data_dir, ticker)
            
            # Load 5-minute data
            five_min_file = os.path.join(base_path, f"{ticker}_5min_data.csv")
            if os.path.exists(five_min_file):
                five_min = pd.read_csv(five_min_file, index_col=0, parse_dates=True)
            else:
                five_min = None
            
            # Load daily data
            daily_file = os.path.join(base_path, f"{ticker}_daily_data.csv")
            if os.path.exists(daily_file):
                daily = pd.read_csv(daily_file)
                if 'Date' in daily.columns:
                    daily['Date'] = pd.to_datetime(daily['Date'], utc=True).dt.tz_localize(None)
                    daily.set_index('Date', inplace=True)
            else:
                daily = None
            
            # Load weekly data
            weekly_file = os.path.join(base_path, f"{ticker}_weekly_data.csv")
            if os.path.exists(weekly_file):
                weekly = pd.read_csv(weekly_file)
                if 'Date' in weekly.columns:
                    weekly['Date'] = pd.to_datetime(weekly['Date'], utc=True).dt.tz_localize(None)
                    weekly.set_index('Date', inplace=True)
            else:
                weekly = None
            
            # Load fundamentals
            fund_file = os.path.join(base_path, f"{ticker}_fundamental_data.csv")
            if os.path.exists(fund_file):
                fundamentals = pd.read_csv(fund_file)
            else:
                fundamentals = None
            
            return {
                '5min': five_min,
                'daily': daily,
                'weekly': weekly,
                'fundamentals': fundamentals
            }
        except Exception as e:
            print(f"  ⚠️ Error loading {ticker}: {e}")
            return None
    
    def analyze_earnings_event(self, row):
        """Analyze a single earnings event"""
        ticker = row['ticker']
        earnings_date = row['date']
        
        # Load stock data
        data = self.load_stock_data(ticker)
        if data is None or data['daily'] is None:
            return None
        
        daily = data['daily']
        
        # Get prices around earnings
        try:
            # Find earnings date in daily data
            if earnings_date not in daily.index:
                # Find closest date
                closest_idx = daily.index.searchsorted(earnings_date)
                if closest_idx >= len(daily):
                    return None
                earnings_date = daily.index[closest_idx]
            
            earnings_idx = daily.index.get_loc(earnings_date)
            
            # Need at least 5 days before and 10 days after
            if earnings_idx < 5 or earnings_idx + 10 >= len(daily):
                return None
            
            # Get prices
            pre_earnings_prices = daily.iloc[earnings_idx-5:earnings_idx]
            post_earnings_prices = daily.iloc[earnings_idx:earnings_idx+11]
            
            if len(post_earnings_prices) < 11:
                return None
            
            # Calculate returns
            day0_close = post_earnings_prices.iloc[0]['Close']
            day1_close = post_earnings_prices.iloc[1]['Close'] if len(post_earnings_prices) > 1 else day0_close
            day3_close = post_earnings_prices.iloc[3]['Close'] if len(post_earnings_prices) > 3 else day0_close
            day5_close = post_earnings_prices.iloc[5]['Close'] if len(post_earnings_prices) > 5 else day0_close
            day10_close = post_earnings_prices.iloc[10]['Close'] if len(post_earnings_prices) > 10 else day0_close
            
            # Day 0 return (earnings day move)
            day0_open = post_earnings_prices.iloc[0]['Open']
            day0_return = (day0_close - day0_open) / day0_open * 100
            
            # Multi-day returns
            day1_return = (day1_close - day0_close) / day0_close * 100
            day3_return = (day3_close - day0_close) / day0_close * 100
            day5_return = (day5_close - day0_close) / day0_close * 100
            day10_return = (day10_close - day0_close) / day0_close * 100
            
            # Pre-earnings momentum
            pre_5day_return = (pre_earnings_prices.iloc[-1]['Close'] - pre_earnings_prices.iloc[0]['Close']) / pre_earnings_prices.iloc[0]['Close'] * 100
            
            # Volatility
            pre_volatility = pre_earnings_prices['Close'].pct_change().std() * np.sqrt(252) * 100
            post_volatility = post_earnings_prices['Close'].pct_change().std() * np.sqrt(252) * 100
            
            # Volume
            avg_volume = pre_earnings_prices['Volume'].mean()
            earnings_volume = post_earnings_prices.iloc[0]['Volume']
            volume_ratio = earnings_volume / avg_volume if avg_volume > 0 else 1
            
            # Fundamental data
            market_cap = row.get('market_cap_usd', 0)
            sector = row.get('sector', 'Unknown')
            
            return {
                'ticker': ticker,
                'earnings_date': earnings_date,
                'sector': sector,
                'market_cap': market_cap,
                'day0_return': day0_return,
                'day1_return': day1_return,
                'day3_return': day3_return,
                'day5_return': day5_return,
                'day10_return': day10_return,
                'total_return_d1_d3': day1_return + day3_return,
                'total_return_d1_d5': day1_return + day5_return,
                'pre_5day_momentum': pre_5day_return,
                'pre_volatility': pre_volatility,
                'post_volatility': post_volatility,
                'volume_ratio': volume_ratio,
                'day0_close': day0_close,
                'day1_close': day1_close,
                'day3_close': day3_close,
                'day5_close': day5_close,
                'day10_close': day10_close
            }
        except Exception as e:
            print(f"  ⚠️ Error analyzing {ticker} on {earnings_date}: {e}")
            return None
    
    def run_backtest(self):
        """Run comprehensive backtest"""
        print("\n" + "="*80)
        print("RUNNING COMPREHENSIVE BACKTEST")
        print("="*80)
        
        total_events = len(self.earnings)
        successful = 0
        
        for idx, row in self.earnings.iterrows():
            result = self.analyze_earnings_event(row)
            if result:
                self.backtest_results.append(result)
                successful += 1
            
            if (idx + 1) % 10 == 0:
                print(f"Progress: {idx+1}/{total_events} ({(idx+1)/total_events*100:.1f}%) - Successful: {successful}")
        
        print(f"\n✅ Backtest complete: {successful}/{total_events} events analyzed")
        
        # Convert to DataFrame
        self.results_df = pd.DataFrame(self.backtest_results)
        
        return self.results_df
    
    def analyze_strategy_performance(self):
        """Analyze strategy performance"""
        if len(self.results_df) == 0:
            print("❌ No results to analyze")
            return
        
        print("\n" + "="*80)
        print("STRATEGY PERFORMANCE ANALYSIS")
        print("="*80)
        
        df = self.results_df
        
        # Overall statistics
        print(f"\n📊 Overall Statistics:")
        print(f"  Total trades analyzed: {len(df)}")
        print(f"  Average Day 0 return: {df['day0_return'].mean():.2f}%")
        print(f"  Average Day 1 return: {df['day1_return'].mean():.2f}%")
        print(f"  Average Day 3 return: {df['day3_return'].mean():.2f}%")
        print(f"  Average Day 5 return: {df['day5_return'].mean():.2f}%")
        print(f"  Average Day 10 return: {df['day10_return'].mean():.2f}%")
        
        # Win rates
        print(f"\n📈 Win Rates:")
        print(f"  Day 0 positive: {(df['day0_return'] > 0).sum() / len(df) * 100:.1f}%")
        print(f"  Day 1 positive: {(df['day1_return'] > 0).sum() / len(df) * 100:.1f}%")
        print(f"  Day 3 positive: {(df['day3_return'] > 0).sum() / len(df) * 100:.1f}%")
        print(f"  Day 5 positive: {(df['day5_return'] > 0).sum() / len(df) * 100:.1f}%")
        print(f"  Day 10 positive: {(df['day10_return'] > 0).sum() / len(df) * 100:.1f}%")
        
        # Strategy scenarios
        print(f"\n🎯 Strategy Scenarios:")
        
        # Scenario 1: Buy on Day 0 close, sell on Day 3
        scenario1_return = df['day3_return'].mean()
        scenario1_winrate = (df['day3_return'] > 0).sum() / len(df) * 100
        print(f"  Scenario 1 (Buy D0 close, Sell D3):")
        print(f"    Average return: {scenario1_return:.2f}%")
        print(f"    Win rate: {scenario1_winrate:.1f}%")
        print(f"    Best trade: {df['day3_return'].max():.2f}%")
        print(f"    Worst trade: {df['day3_return'].min():.2f}%")
        
        # Scenario 2: Buy on Day 1 open, sell on Day 5
        scenario2_return = df['day5_return'].mean()
        scenario2_winrate = (df['day5_return'] > 0).sum() / len(df) * 100
        print(f"  Scenario 2 (Buy D1 open, Sell D5):")
        print(f"    Average return: {scenario2_return:.2f}%")
        print(f"    Win rate: {scenario2_winrate:.1f}%")
        print(f"    Best trade: {df['day5_return'].max():.2f}%")
        print(f"    Worst trade: {df['day5_return'].min():.2f}%")
        
        # Filter by Day 0 reaction
        positive_day0 = df[df['day0_return'] > 0]
        negative_day0 = df[df['day0_return'] < 0]
        
        print(f"\n📊 Performance by Day 0 Reaction:")
        print(f"  Positive Day 0 ({len(positive_day0)} trades):")
        print(f"    Avg Day 3 return: {positive_day0['day3_return'].mean():.2f}%")
        print(f"    Avg Day 5 return: {positive_day0['day5_return'].mean():.2f}%")
        print(f"  Negative Day 0 ({len(negative_day0)} trades):")
        print(f"    Avg Day 3 return: {negative_day0['day3_return'].mean():.2f}%")
        print(f"    Avg Day 5 return: {negative_day0['day5_return'].mean():.2f}%")
        
        # Sector analysis
        print(f"\n🏢 Sector Performance:")
        sector_perf = df.groupby('sector')['day3_return'].agg(['mean', 'count'])
        sector_perf = sector_perf.sort_values('mean', ascending=False)
        for sector, row in sector_perf.iterrows():
            print(f"  {sector}: {row['mean']:.2f}% (n={int(row['count'])})")
        
        return df
    
    def generate_stock_rankings(self):
        """Generate stock rankings for competition"""
        print("\n" + "="*80)
        print("GENERATING STOCK RANKINGS")
        print("="*80)
        
        df = self.results_df
        
        if len(df) == 0:
            print("❌ No data to rank")
            return pd.DataFrame()
        
        # Calculate composite score for each stock
        stock_scores = []
        
        for ticker in df['ticker'].unique():
            ticker_data = df[df['ticker'] == ticker]
            
            # Calculate metrics
            avg_return = ticker_data['day3_return'].mean()
            win_rate = (ticker_data['day3_return'] > 0).sum() / len(ticker_data) * 100
            consistency = -ticker_data['day3_return'].std()  # Lower std is better
            num_events = len(ticker_data)
            
            # Composite score (weighted)
            score = (avg_return * 0.4) + (win_rate * 0.3) + (consistency * 0.2) + (num_events * 0.1)
            
            stock_scores.append({
                'ticker': ticker,
                'avg_return': avg_return,
                'win_rate': win_rate,
                'std_dev': ticker_data['day3_return'].std(),
                'num_events': num_events,
                'composite_score': score,
                'sector': ticker_data.iloc[0]['sector'],
                'market_cap': ticker_data.iloc[0]['market_cap']
            })
        
        # Create rankings DataFrame
        rankings_df = pd.DataFrame(stock_scores)
        rankings_df = rankings_df.sort_values('composite_score', ascending=False)
        
        print(f"\n🏆 Top 20 Stocks:")
        for idx, row in rankings_df.head(20).iterrows():
            print(f"  {idx+1}. {row['ticker']}: Score={row['composite_score']:.2f}, "
                  f"Avg Return={row['avg_return']:.2f}%, Win Rate={row['win_rate']:.1f}%")
        
        return rankings_df
    
    def save_results(self):
        """Save all results"""
        print("\n" + "="*80)
        print("SAVING RESULTS")
        print("="*80)
        
        # Save backtest results
        results_file = os.path.join(self.output_dir, 'backtest_results.csv')
        self.results_df.to_csv(results_file, index=False)
        print(f"✅ Saved backtest results: {results_file}")
        
        # Save rankings
        rankings_file = os.path.join(self.output_dir, 'stock_rankings.csv')
        self.stock_rankings.to_csv(rankings_file, index=False)
        print(f"✅ Saved stock rankings: {rankings_file}")
        
        # Generate summary report
        summary = {
            'total_events_analyzed': len(self.results_df),
            'avg_day3_return': float(self.results_df['day3_return'].mean()),
            'day3_win_rate': float((self.results_df['day3_return'] > 0).sum() / len(self.results_df) * 100),
            'top_10_stocks': self.stock_rankings.head(10)['ticker'].tolist(),
            'analysis_date': datetime.now().isoformat()
        }
        
        summary_file = os.path.join(self.output_dir, 'analysis_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✅ Saved summary: {summary_file}")
    
    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        # Run backtest
        self.run_backtest()
        
        # Analyze performance
        self.analyze_strategy_performance()
        
        # Generate rankings
        self.stock_rankings = self.generate_stock_rankings()
        
        # Save results
        self.save_results()
        
        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE!")
        print("="*80)
        print(f"\nResults saved to: {self.output_dir}/")
        print(f"  - backtest_results.csv")
        print(f"  - stock_rankings.csv")
        print(f"  - analysis_summary.json")

def main():
    """Main execution"""
    analyzer = ComprehensiveStrategyAnalyzer(
        earnings_file='data/processed/earnings_final.csv',
        data_dir='data/bulk_extraction',
        output_dir='results'
    )
    
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()

