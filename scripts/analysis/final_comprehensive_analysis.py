"""
Final Comprehensive Analysis - All 373 Stocks
============================================

Analyzes all stocks with complete data and generates final rankings
based on multiple metrics for the UMushroom Competition.

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

class FinalComprehensiveAnalyzer:
    """
    Final comprehensive analysis of all stocks
    """
    
    def __init__(self, data_dir, output_dir='results'):
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get list of stocks with complete data
        self.stock_list = self.get_complete_stocks()
        
        print(f"✅ Found {len(self.stock_list)} stocks with complete data")
        
        # Results storage
        self.stock_analysis = []
        
    def get_complete_stocks(self):
        """Get list of stocks with complete data"""
        complete_stocks = []
        
        for ticker_dir in os.listdir(self.data_dir):
            ticker_path = os.path.join(self.data_dir, ticker_dir)
            
            if not os.path.isdir(ticker_path) or ticker_dir in ['logs', '__pycache__'] or len(ticker_dir) > 5:
                continue
            
            # Check for required files
            daily_file = os.path.join(ticker_path, f"{ticker_dir}_daily_data.csv")
            weekly_file = os.path.join(ticker_path, f"{ticker_dir}_weekly_data.csv")
            fund_file = os.path.join(ticker_path, f"{ticker_dir}_fundamental_data.csv")
            five_min_file = os.path.join(ticker_path, f"{ticker_dir}_5min_data.csv")
            
            if (os.path.exists(daily_file) and os.path.getsize(daily_file) > 100 and
                os.path.exists(weekly_file) and os.path.getsize(weekly_file) > 100 and
                os.path.exists(fund_file) and os.path.getsize(fund_file) > 100):
                complete_stocks.append(ticker_dir)
        
        return sorted(complete_stocks)
    
    def load_stock_data(self, ticker):
        """Load all data for a stock"""
        try:
            base_path = os.path.join(self.data_dir, ticker)
            
            # Load daily data
            daily = pd.read_csv(os.path.join(base_path, f"{ticker}_daily_data.csv"))
            daily['Date'] = pd.to_datetime(daily['Date'], utc=True).dt.tz_localize(None)
            daily.set_index('Date', inplace=True)
            
            # Load weekly data
            weekly = pd.read_csv(os.path.join(base_path, f"{ticker}_weekly_data.csv"))
            weekly['Date'] = pd.to_datetime(weekly['Date'], utc=True).dt.tz_localize(None)
            weekly.set_index('Date', inplace=True)
            
            # Load fundamentals
            fundamentals = pd.read_csv(os.path.join(base_path, f"{ticker}_fundamental_data.csv"))
            
            # Load 5-minute data if available
            five_min_file = os.path.join(base_path, f"{ticker}_5min_data.csv")
            if os.path.exists(five_min_file):
                five_min = pd.read_csv(five_min_file, index_col=0, parse_dates=True)
            else:
                five_min = None
            
            return {
                'daily': daily,
                'weekly': weekly,
                'fundamentals': fundamentals,
                '5min': five_min
            }
        except Exception as e:
            print(f"  ⚠️ Error loading {ticker}: {e}")
            return None
    
    def calculate_technical_indicators(self, daily_data):
        """Calculate technical indicators"""
        try:
            # Returns
            daily_returns = daily_data['Close'].pct_change()
            
            # Volatility
            volatility_20d = daily_returns.rolling(20).std() * np.sqrt(252) * 100
            volatility_60d = daily_returns.rolling(60).std() * np.sqrt(252) * 100
            
            # Moving averages
            ma_20 = daily_data['Close'].rolling(20).mean()
            ma_50 = daily_data['Close'].rolling(50).mean()
            ma_200 = daily_data['Close'].rolling(200).mean()
            
            # Momentum
            momentum_5d = (daily_data['Close'] / daily_data['Close'].shift(5) - 1) * 100
            momentum_20d = (daily_data['Close'] / daily_data['Close'].shift(20) - 1) * 100
            momentum_60d = (daily_data['Close'] / daily_data['Close'].shift(60) - 1) * 100
            
            # Volume
            avg_volume = daily_data['Volume'].rolling(20).mean()
            volume_ratio = daily_data['Volume'] / avg_volume
            
            # RSI
            rsi = self.calculate_rsi(daily_data['Close'], 14)
            
            return {
                'current_price': daily_data['Close'].iloc[-1],
                'volatility_20d': volatility_20d.iloc[-1],
                'volatility_60d': volatility_60d.iloc[-1],
                'ma_20': ma_20.iloc[-1],
                'ma_50': ma_50.iloc[-1],
                'ma_200': ma_200.iloc[-1],
                'momentum_5d': momentum_5d.iloc[-1],
                'momentum_20d': momentum_20d.iloc[-1],
                'momentum_60d': momentum_60d.iloc[-1],
                'avg_volume': avg_volume.iloc[-1],
                'volume_ratio': volume_ratio.iloc[-1],
                'rsi': rsi.iloc[-1]
            }
        except Exception as e:
            return {}
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def analyze_stock(self, ticker):
        """Comprehensive analysis of a single stock"""
        try:
            # Load data
            data = self.load_stock_data(ticker)
            if data is None:
                return None
            
            daily = data['daily']
            weekly = data['weekly']
            fundamentals = data['fundamentals']
            
            # Calculate technical indicators
            tech_indicators = self.calculate_technical_indicators(daily)
            
            # Get fundamental metrics
            fund_metrics = {}
            if len(fundamentals) > 0:
                fund_row = fundamentals.iloc[0]
                fund_metrics = {
                    'market_cap': fund_row.get('marketCap', 0),
                    'pe_ratio': fund_row.get('trailingPE', np.nan),
                    'forward_pe': fund_row.get('forwardPE', np.nan),
                    'peg_ratio': fund_row.get('pegRatio', np.nan),
                    'price_to_book': fund_row.get('priceToBook', np.nan),
                    'debt_to_equity': fund_row.get('debtToEquity', np.nan),
                    'current_ratio': fund_row.get('currentRatio', np.nan),
                    'roe': fund_row.get('returnOnEquity', np.nan),
                    'profit_margin': fund_row.get('profitMargins', np.nan),
                    'sector': fund_row.get('sector', 'Unknown'),
                    'industry': fund_row.get('industry', 'Unknown')
                }
            
            # Calculate quality score
            quality_score = self.calculate_quality_score(tech_indicators, fund_metrics)
            
            # Calculate momentum score
            momentum_score = self.calculate_momentum_score(tech_indicators)
            
            # Calculate volatility score (lower is better for risk-adjusted)
            volatility_score = 100 - min(tech_indicators.get('volatility_20d', 100), 100)
            
            # Composite score
            composite_score = (quality_score * 0.3) + (momentum_score * 0.4) + (volatility_score * 0.3)
            
            return {
                'ticker': ticker,
                'composite_score': composite_score,
                'quality_score': quality_score,
                'momentum_score': momentum_score,
                'volatility_score': volatility_score,
                **tech_indicators,
                **fund_metrics
            }
            
        except Exception as e:
            print(f"  ⚠️ Error analyzing {ticker}: {e}")
            return None
    
    def calculate_quality_score(self, tech, fund):
        """Calculate quality score (0-100)"""
        score = 50  # Base score
        
        # Fundamental quality
        if fund.get('roe', 0) > 0.15:
            score += 10
        if fund.get('profit_margin', 0) > 0.10:
            score += 10
        if fund.get('current_ratio', 0) > 1.5:
            score += 10
        if fund.get('debt_to_equity', 100) < 1.0:
            score += 10
        
        # Technical quality
        if tech.get('rsi', 50) > 30 and tech.get('rsi', 50) < 70:
            score += 10
        
        return min(score, 100)
    
    def calculate_momentum_score(self, tech):
        """Calculate momentum score (0-100)"""
        score = 50  # Base score
        
        # Short-term momentum
        if tech.get('momentum_5d', 0) > 0:
            score += 15
        if tech.get('momentum_5d', 0) > 2:
            score += 10
        
        # Medium-term momentum
        if tech.get('momentum_20d', 0) > 0:
            score += 15
        if tech.get('momentum_20d', 0) > 5:
            score += 10
        
        return min(score, 100)
    
    def run_analysis(self):
        """Run comprehensive analysis on all stocks"""
        print("\n" + "="*80)
        print(f"ANALYZING {len(self.stock_list)} STOCKS")
        print("="*80)
        
        for idx, ticker in enumerate(self.stock_list):
            result = self.analyze_stock(ticker)
            if result:
                self.stock_analysis.append(result)
            
            if (idx + 1) % 50 == 0:
                print(f"Progress: {idx+1}/{len(self.stock_list)} ({(idx+1)/len(self.stock_list)*100:.1f}%)")
        
        print(f"\n✅ Analysis complete: {len(self.stock_analysis)}/{len(self.stock_list)} stocks analyzed")
        
        # Convert to DataFrame
        self.results_df = pd.DataFrame(self.stock_analysis)
        
        return self.results_df
    
    def generate_rankings(self):
        """Generate final rankings"""
        print("\n" + "="*80)
        print("GENERATING FINAL RANKINGS")
        print("="*80)
        
        df = self.results_df.sort_values('composite_score', ascending=False)
        
        print(f"\n🏆 Top 50 Stocks for Competition:")
        for idx, row in df.head(50).iterrows():
            print(f"  {idx+1:2d}. {row['ticker']:6s}: Score={row['composite_score']:.2f}, "
                  f"Quality={row['quality_score']:.1f}, Momentum={row['momentum_score']:.1f}, "
                  f"Vol={row['volatility_score']:.1f}, Sector={row.get('sector', 'N/A')}")
        
        return df
    
    def generate_sector_analysis(self):
        """Generate sector-level analysis"""
        print("\n" + "="*80)
        print("SECTOR ANALYSIS")
        print("="*80)
        
        sector_stats = self.results_df.groupby('sector').agg({
            'composite_score': ['mean', 'count'],
            'momentum_score': 'mean',
            'quality_score': 'mean',
            'volatility_score': 'mean'
        }).round(2)
        
        print(f"\n📊 Sector Performance:")
        for sector in sector_stats.index:
            stats = sector_stats.loc[sector]
            print(f"  {sector}:")
            print(f"    Avg Composite Score: {stats[('composite_score', 'mean')]:.2f}")
            print(f"    Count: {int(stats[('composite_score', 'count')])}")
            print(f"    Avg Momentum: {stats[('momentum_score', 'mean')]:.2f}")
            print(f"    Avg Quality: {stats[('quality_score', 'mean')]:.2f}")
        
        return sector_stats
    
    def save_results(self):
        """Save all results"""
        print("\n" + "="*80)
        print("SAVING RESULTS")
        print("="*80)
        
        # Save complete analysis
        analysis_file = os.path.join(self.output_dir, 'complete_stock_analysis.csv')
        self.results_df.to_csv(analysis_file, index=False)
        print(f"✅ Saved complete analysis: {analysis_file}")
        
        # Save top 100 rankings
        top_100_file = os.path.join(self.output_dir, 'top_100_stocks.csv')
        self.results_df.head(100).to_csv(top_100_file, index=False)
        print(f"✅ Saved top 100 rankings: {top_100_file}")
        
        # Save summary
        summary = {
            'total_stocks_analyzed': len(self.results_df),
            'analysis_date': datetime.now().isoformat(),
            'top_10_tickers': self.results_df.head(10)['ticker'].tolist(),
            'avg_composite_score': float(self.results_df['composite_score'].mean()),
            'avg_momentum_score': float(self.results_df['momentum_score'].mean()),
            'avg_quality_score': float(self.results_df['quality_score'].mean()),
            'sectors_analyzed': self.results_df['sector'].nunique()
        }
        
        summary_file = os.path.join(self.output_dir, 'final_analysis_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✅ Saved summary: {summary_file}")
    
    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        # Analyze all stocks
        self.run_analysis()
        
        # Generate rankings
        self.generate_rankings()
        
        # Generate sector analysis
        self.generate_sector_analysis()
        
        # Save results
        self.save_results()
        
        print("\n" + "="*80)
        print("✅ FINAL ANALYSIS COMPLETE!")
        print("="*80)
        print(f"\nResults saved to: {self.output_dir}/")
        print(f"  - complete_stock_analysis.csv ({len(self.results_df)} stocks)")
        print(f"  - top_100_stocks.csv (Top 100 rankings)")
        print(f"  - final_analysis_summary.json")
        print(f"\n🏆 Ready for UMushroom Competition!")

def main():
    """Main execution"""
    analyzer = FinalComprehensiveAnalyzer(
        data_dir='data/bulk_extraction',
        output_dir='results'
    )
    
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()

