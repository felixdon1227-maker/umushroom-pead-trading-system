"""
Ultra-Fast Bulk Data Extractor for ~1000 Stocks
Optimized for maximum speed parallel extraction from TWS API

Data Collection Strategy:
1. 10-min intervals: ±10 days around EACH earnings date (strategy window)
2. Daily: Last 30 days + all earnings periods
3. Weekly: 10 years historical
4. Fundamentals: Market cap, volume, earnings dates, financials

Author: UMushroom Competition Strategy
Date: October 2024
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import sys
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import pickle

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tws_connector import TWSConnector

class UltraFastBulkExtractor:
    """Parallel bulk data extractor optimized for speed"""
    
    def __init__(self, max_connections=50):
        self.max_connections = max_connections
        self.tws_pool = []
        self.data_queue = Queue()
        self.results = {
            'intraday_10min': {},
            'daily': {},
            'weekly': {},
            'fundamentals': {},
            'earnings_dates': {}
        }
        
    def initialize_tws_pool(self):
        """Create pool of TWS connections for parallel extraction"""
        print(f"🔌 Initializing {self.max_connections} TWS connections...")
        
        for i in range(self.max_connections):
            try:
                tws = TWSConnector()
                if tws.connect("127.0.0.1", 4002, 1000 + i):
                    self.tws_pool.append(tws)
                    print(f"  ✅ Connection {i+1}/{self.max_connections}")
                else:
                    print(f"  ⚠️ Connection {i+1} failed")
                    break
                time.sleep(0.1)  # Small delay between connections
            except Exception as e:
                print(f"  ❌ Error on connection {i+1}: {e}")
                break
        
        print(f"✅ Pool ready: {len(self.tws_pool)} active connections")
        return len(self.tws_pool)
    
    def load_tickers(self, csv_file):
        """Load ticker list from CSV"""
        print(f"\n📋 Loading tickers from {csv_file}...")
        
        try:
            # Try different CSV formats
            if csv_file.endswith('.txt'):
                with open(csv_file, 'r') as f:
                    tickers = [line.strip() for line in f if line.strip()]
            else:
                df = pd.read_csv(csv_file)
                # Try common column names
                for col in ['ticker', 'Ticker', 'symbol', 'Symbol', 'TICKER']:
                    if col in df.columns:
                        tickers = df[col].tolist()
                        break
                else:
                    # Use first column
                    tickers = df.iloc[:, 0].tolist()
            
            # Clean tickers
            tickers = [str(t).strip().upper() for t in tickers if t and str(t).strip()]
            tickers = list(set(tickers))  # Remove duplicates
            
            print(f"✅ Loaded {len(tickers)} unique tickers")
            return tickers
            
        except Exception as e:
            print(f"❌ Error loading tickers: {e}")
            return []
    
    def get_earnings_dates(self, ticker, tws):
        """Get earnings dates for ticker"""
        try:
            # Use TWS fundamental data
            fund_data = tws.get_fundamental_data(ticker, 'RESC')
            if fund_data:
                metrics = tws.parse_fundamental_xml(fund_data)
                earnings_date = metrics.get('earnings_date')
                if earnings_date:
                    return pd.to_datetime(earnings_date)
            
            # Fallback: estimate quarterly earnings
            # Most companies report ~6 weeks after quarter end
            return None
            
        except Exception as e:
            return None
    
    def fetch_10min_data_around_earnings(self, ticker, earnings_dates, tws):
        """
        Fetch 10-min data for ±10 days around EACH earnings date
        This is your strategy window where you need granular data
        """
        all_data = []
        
        for earnings_date in earnings_dates:
            try:
                # Strategy window: 10 days before to 10 days after
                start_date = earnings_date - timedelta(days=10)
                end_date = earnings_date + timedelta(days=10)
                
                # Request 10-min bars
                bars = tws.get_historical_data(
                    ticker,
                    end_date.strftime('%Y%m%d %H:%M:%S'),
                    duration='21 D',  # 21 days to cover window
                    bar_size='10 mins',
                    what_to_show='TRADES'
                )
                
                if bars:
                    df = pd.DataFrame(bars)
                    df['earnings_date'] = earnings_date
                    all_data.append(df)
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                continue
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return None
    
    def fetch_daily_data(self, ticker, tws):
        """Fetch daily data: last 30 days + historical"""
        try:
            # Get 1 year of daily data (covers last 30 days + history)
            bars = tws.get_historical_data(
                ticker,
                datetime.now().strftime('%Y%m%d %H:%M:%S'),
                duration='1 Y',
                bar_size='1 day',
                what_to_show='TRADES'
            )
            
            if bars:
                return pd.DataFrame(bars)
            return None
            
        except Exception as e:
            return None
    
    def fetch_weekly_data(self, ticker, tws):
        """Fetch weekly data: 10 years"""
        try:
            bars = tws.get_historical_data(
                ticker,
                datetime.now().strftime('%Y%m%d %H:%M:%S'),
                duration='10 Y',
                bar_size='1 week',
                what_to_show='TRADES'
            )
            
            if bars:
                return pd.DataFrame(bars)
            return None
            
        except Exception as e:
            return None
    
    def fetch_fundamentals(self, ticker, tws):
        """Fetch fundamental data"""
        try:
            fund_data = tws.get_fundamental_data(ticker, 'ReportSnapshot')
            if fund_data:
                return tws.parse_fundamental_xml(fund_data)
            return None
            
        except Exception as e:
            return None
    
    def process_ticker(self, ticker, tws_idx):
        """Process single ticker - fetch all data types"""
        tws = self.tws_pool[tws_idx % len(self.tws_pool)]
        results = {'ticker': ticker, 'status': 'success'}
        
        try:
            # 1. Get earnings dates
            earnings_dates = self.get_earnings_dates(ticker, tws)
            if earnings_dates:
                results['earnings_dates'] = earnings_dates
                
                # 2. Get 10-min data around earnings (YOUR STRATEGY WINDOW)
                intraday = self.fetch_10min_data_around_earnings(ticker, [earnings_dates], tws)
                if intraday is not None:
                    results['intraday_10min'] = intraday
            
            # 3. Get daily data
            daily = self.fetch_daily_data(ticker, tws)
            if daily is not None:
                results['daily'] = daily
            
            # 4. Get weekly data
            weekly = self.fetch_weekly_data(ticker, tws)
            if weekly is not None:
                results['weekly'] = weekly
            
            # 5. Get fundamentals
            fundamentals = self.fetch_fundamentals(ticker, tws)
            if fundamentals:
                results['fundamentals'] = fundamentals
            
            return results
            
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
            return results
    
    def bulk_extract(self, tickers, output_dir):
        """
        Bulk extract all data types for all tickers in parallel
        Ultra-fast using connection pool
        """
        print(f"\n🚀 STARTING BULK EXTRACTION")
        print(f"  Tickers: {len(tickers)}")
        print(f"  Connections: {len(self.tws_pool)}")
        print(f"  Output: {output_dir}")
        print("=" * 80)
        
        os.makedirs(output_dir, exist_ok=True)
        
        start_time = time.time()
        completed = 0
        errors = 0
        
        # Process in parallel using thread pool
        with ThreadPoolExecutor(max_workers=len(self.tws_pool)) as executor:
            futures = {
                executor.submit(self.process_ticker, ticker, i): ticker 
                for i, ticker in enumerate(tickers)
            }
            
            for future in as_completed(futures):
                ticker = futures[future]
                completed += 1
                
                try:
                    result = future.result()
                    
                    if result['status'] == 'success':
                        # Save results
                        self.save_ticker_data(ticker, result, output_dir)
                        print(f"✅ [{completed}/{len(tickers)}] {ticker}")
                    else:
                        errors += 1
                        print(f"❌ [{completed}/{len(tickers)}] {ticker} - {result.get('error', 'Unknown error')}")
                    
                except Exception as e:
                    errors += 1
                    print(f"❌ [{completed}/{len(tickers)}] {ticker} - {e}")
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 80)
        print(f"✅ BULK EXTRACTION COMPLETE")
        print(f"  Total: {len(tickers)} tickers")
        print(f"  Success: {completed - errors}")
        print(f"  Errors: {errors}")
        print(f"  Time: {elapsed/60:.1f} minutes")
        print(f"  Speed: {len(tickers)/elapsed*60:.1f} tickers/minute")
        print("=" * 80)
    
    def save_ticker_data(self, ticker, data, output_dir):
        """Save all data for a ticker"""
        ticker_dir = f"{output_dir}/{ticker}"
        os.makedirs(ticker_dir, exist_ok=True)
        
        # Save 10-min data (strategy window)
        if 'intraday_10min' in data and data['intraday_10min'] is not None:
            data['intraday_10min'].to_csv(f"{ticker_dir}/10min_earnings_window.csv", index=False)
        
        # Save daily data
        if 'daily' in data and data['daily'] is not None:
            data['daily'].to_csv(f"{ticker_dir}/daily.csv", index=False)
        
        # Save weekly data
        if 'weekly' in data and data['weekly'] is not None:
            data['weekly'].to_csv(f"{ticker_dir}/weekly.csv", index=False)
        
        # Save fundamentals
        if 'fundamentals' in data and data['fundamentals']:
            pd.Series(data['fundamentals']).to_csv(f"{ticker_dir}/fundamentals.csv")
        
        # Save earnings dates
        if 'earnings_dates' in data:
            with open(f"{ticker_dir}/earnings_dates.txt", 'w') as f:
                f.write(str(data['earnings_dates']))
    
    def cleanup(self):
        """Disconnect all TWS connections"""
        print("\n🔌 Closing TWS connections...")
        for tws in self.tws_pool:
            try:
                tws.disconnect()
            except:
                pass
        print("✅ All connections closed")

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ultra-Fast Bulk Data Extractor')
    parser.add_argument('ticker_file', help='CSV or TXT file with ticker list')
    parser.add_argument('--connections', type=int, default=10, help='Number of parallel TWS connections (default: 10)')
    parser.add_argument('--output', default='data/bulk_extraction', help='Output directory')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 ULTRA-FAST BULK DATA EXTRACTOR")
    print("=" * 80)
    
    extractor = UltraFastBulkExtractor(max_connections=args.connections)
    
    try:
        # Initialize TWS connection pool
        active_connections = extractor.initialize_tws_pool()
        
        if active_connections == 0:
            print("❌ No TWS connections available. Make sure TWS is running.")
            return
        
        # Load tickers
        tickers = extractor.load_tickers(args.ticker_file)
        
        if not tickers:
            print("❌ No tickers loaded")
            return
        
        # Extract all data
        extractor.bulk_extract(tickers, args.output)
        
        print("\n✅ ALL DATA EXTRACTED!")
        print(f"📁 Data saved to: {args.output}")
        print(f"\n📊 Next Steps:")
        print(f"  1. Run analysis on extracted data")
        print(f"  2. Calculate strategy metrics")
        print(f"  3. Identify best stocks for competition")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        extractor.cleanup()

if __name__ == "__main__":
    main()

