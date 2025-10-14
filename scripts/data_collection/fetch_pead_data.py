import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time
import os
import json

class HistoricalPEADAnalyzer:
    def __init__(self, earnings_csv):
        self.df = pd.read_csv(earnings_csv)
        self.tickers = self.df['ticker'].unique().tolist()
        self.data_dir = 'pead_historical_data'
        
        # Create directories
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f'{self.data_dir}/earnings', exist_ok=True)
        os.makedirs(f'{self.data_dir}/price_data', exist_ok=True)
        
    def fetch_historical_earnings(self, ticker):
        """Fetch quarterly earnings for last 10 years"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get earnings dates and data
            earnings_dates = stock.earnings_dates
            
            if earnings_dates is None or earnings_dates.empty:
                print(f"  ✗ {ticker}: No earnings data available")
                return None
            
            # Remove timezone info and filter for last 10 years
            earnings_dates.index = earnings_dates.index.tz_localize(None)
            ten_years_ago = pd.Timestamp.now().tz_localize(None) - timedelta(days=3650)
            earnings_dates = earnings_dates[earnings_dates.index >= ten_years_ago]
            
            if earnings_dates.empty:
                print(f"  ✗ {ticker}: No earnings in last 10 years")
                return None
            
            # Combine data
            earnings_data = []
            for date, row in earnings_dates.iterrows():
                earnings_data.append({
                    'ticker': ticker,
                    'earnings_date': date,
                    'eps_estimate': row.get('EPS Estimate', None),
                    'reported_eps': row.get('Reported EPS', None),
                    'surprise_pct': row.get('Surprise(%)', None)
                })
            
            df_earnings = pd.DataFrame(earnings_data)
            
            # Save to CSV
            filename = f'{self.data_dir}/earnings/{ticker}_earnings.csv'
            df_earnings.to_csv(filename, index=False)
            
            print(f"  ✓ {ticker}: {len(df_earnings)} earnings reports saved")
            return df_earnings
            
        except Exception as e:
            print(f"  ✗ {ticker}: Error - {str(e)[:80]}")
            return None
    
    def fetch_price_data_around_earnings(self, ticker, earnings_date, days_before=3, days_after=5):
        """Fetch hourly price data around earnings date"""
        try:
            # Calculate date range (add buffer for weekends/holidays)
            start_date = earnings_date - timedelta(days=days_before + 5)
            end_date = earnings_date + timedelta(days=days_after + 5)
            
            # Fetch hourly data
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date, interval='1h')
            
            if hist.empty:
                return None
            
            # Filter to exact window
            hist = hist[
                (hist.index >= earnings_date - timedelta(days=days_before)) &
                (hist.index <= earnings_date + timedelta(days=days_after))
            ]
            
            if hist.empty:
                return None
            
            # Add metadata
            hist['ticker'] = ticker
            hist['earnings_date'] = earnings_date
            hist['hours_from_earnings'] = (hist.index - earnings_date).total_seconds() / 3600
            
            return hist
            
        except Exception as e:
            return None
    
    def analyze_single_stock(self, ticker):
        """Complete analysis for one stock"""
        print(f"\n{'='*80}")
        print(f"Analyzing {ticker}")
        print(f"{'='*80}")
        
        # Step 1: Get historical earnings
        earnings_df = self.fetch_historical_earnings(ticker)
        
        if earnings_df is None or earnings_df.empty:
            return None
        
        # Step 2: Fetch price data around each earnings
        all_price_data = []
        
        for idx, row in earnings_df.iterrows():
            earnings_date = pd.to_datetime(row['earnings_date'])
            
            print(f"  Fetching prices for {earnings_date.strftime('%Y-%m-%d')}...", end='')
            
            price_data = self.fetch_price_data_around_earnings(ticker, earnings_date)
            
            if price_data is not None and not price_data.empty:
                all_price_data.append(price_data)
                print(f" ✓ {len(price_data)} hourly bars")
            else:
                print(f" ✗ No data")
            
            time.sleep(0.5)  # Rate limiting
        
        # Step 3: Combine and save all price data
        if all_price_data:
            combined_prices = pd.concat(all_price_data, ignore_index=False)
            filename = f'{self.data_dir}/price_data/{ticker}_prices.csv'
            combined_prices.to_csv(filename)
            
            print(f"\n  ✅ {ticker}: {len(all_price_data)} earnings events with price data saved")
            
            return {
                'ticker': ticker,
                'earnings_count': len(earnings_df),
                'price_data_count': len(all_price_data),
                'total_hours': len(combined_prices)
            }
        else:
            print(f"\n  ✗ {ticker}: No price data collected")
            return None
    
    def analyze_all_stocks(self, limit=None):
        """Analyze all stocks in the list"""
        print("=" * 80)
        print("HISTORICAL PEAD DATA COLLECTION")
        print("=" * 80)
        print(f"Total stocks to analyze: {len(self.tickers)}")
        print(f"Timeframe: Last 10 years")
        print(f"Price window: 3 days before + 5 days after each earnings")
        print("=" * 80)
        
        results = []
        tickers_to_process = self.tickers[:limit] if limit else self.tickers
        
        for i, ticker in enumerate(tickers_to_process, 1):
            print(f"\n[{i}/{len(tickers_to_process)}] Processing {ticker}...")
            
            result = self.analyze_single_stock(ticker)
            
            if result:
                results.append(result)
            
            # Save progress
            if i % 10 == 0:
                self.save_progress(results)
            
            time.sleep(1)  # Rate limiting between stocks
        
        # Final save
        self.save_progress(results)
        
        return results
    
    def save_progress(self, results):
        """Save progress to JSON"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_stocks_processed': len(results),
            'results': results
        }
        
        with open(f'{self.data_dir}/analysis_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 Progress saved: {len(results)} stocks completed")
    
    def generate_summary_report(self):
        """Generate summary of collected data"""
        print("\n" + "=" * 80)
        print("DATA COLLECTION SUMMARY")
        print("=" * 80)
        
        # Count files
        earnings_files = len([f for f in os.listdir(f'{self.data_dir}/earnings') if f.endswith('.csv')])
        price_files = len([f for f in os.listdir(f'{self.data_dir}/price_data') if f.endswith('.csv')])
        
        print(f"\n📊 Files Created:")
        print(f"  Earnings data files: {earnings_files}")
        print(f"  Price data files: {price_files}")
        
        # Load summary if exists
        summary_file = f'{self.data_dir}/analysis_summary.json'
        if os.path.exists(summary_file):
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            print(f"\n📈 Analysis Summary:")
            print(f"  Stocks processed: {summary['total_stocks_processed']}")
            print(f"  Last updated: {summary['timestamp']}")
            
            if summary['results']:
                total_earnings = sum(r['earnings_count'] for r in summary['results'])
                total_hours = sum(r['total_hours'] for r in summary['results'])
                
                print(f"  Total earnings events: {total_earnings}")
                print(f"  Total hourly price bars: {total_hours:,}")
        
        print("\n" + "=" * 80)

def main():
    """Main execution"""
    print("=" * 80)
    print("HISTORICAL PEAD DATA FETCHER")
    print("=" * 80)
    
    # Initialize analyzer
    analyzer = HistoricalPEADAnalyzer('earnings_clean.csv')
    
    print(f"\nFound {len(analyzer.tickers)} stocks to analyze")
    
    # Ask for confirmation
    response = input("\nThis will take several hours. Start with first 10 stocks as test? (y/n): ")
    
    if response.lower() == 'y':
        print("\n🚀 Starting analysis of first 10 stocks...")
        results = analyzer.analyze_all_stocks(limit=10)
    else:
        print("\n🚀 Starting full analysis...")
        results = analyzer.analyze_all_stocks()
    
    # Generate summary
    analyzer.generate_summary_report()
    
    print("\n" + "=" * 80)
    print("✅ DATA COLLECTION COMPLETE!")
    print("=" * 80)
    print(f"\nData saved in: {analyzer.data_dir}/")
    print("  - earnings/: Historical earnings data per stock")
    print("  - price_data/: Hourly prices around each earnings")
    print("  - analysis_summary.json: Overall summary")

if __name__ == "__main__":
    main()

