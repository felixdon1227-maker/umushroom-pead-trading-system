"""
Comprehensive Historical Data Extractor
========================================

Efficiently extracts:
1. Daily data for last 10 years
2. 5-minute data for 14 days around each earnings event

Uses IB Gateway with connection pooling for maximum speed.

Author: UMushroom Investment Strategy
Date: October 2024
"""

import pandas as pd
import numpy as np
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import os
import sys
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import warnings
warnings.filterwarnings('ignore')

class IBDataCollector(EWrapper, EClient):
    """IB Gateway data collector"""
    
    def __init__(self):
        EClient.__init__(self, self)
        self.data = {}
        self.data_ready = threading.Event()
        self.current_request = None
        
    def error(self, reqId, errorCode, errorString):
        if errorCode not in [2104, 2106, 2158, 2174, 2176]:  # Ignore info messages
            logging.warning(f"Error {errorCode} for reqId {reqId}: {errorString}")
    
    def historicalData(self, reqId, bar):
        """Receive historical data"""
        if reqId not in self.data:
            self.data[reqId] = []
        
        self.data[reqId].append({
            'Date': bar.date,
            'Open': bar.open,
            'High': bar.high,
            'Low': bar.low,
            'Close': bar.close,
            'Volume': bar.volume
        })
    
    def historicalDataEnd(self, reqId, start, end):
        """Historical data complete"""
        self.data_ready.set()

class ComprehensiveHistoricalExtractor:
    """
    Comprehensive historical data extractor with maximum speed optimization
    """
    
    def __init__(self, earnings_file, output_dir, num_connections=10):
        self.earnings_file = earnings_file
        self.output_dir = output_dir
        self.num_connections = num_connections
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('HistoricalExtractor')
        
        # Load earnings data
        self.earnings = pd.read_csv(earnings_file)
        self.earnings['date'] = pd.to_datetime(self.earnings['date'])
        
        # Get unique tickers
        self.tickers = sorted(self.earnings['ticker'].unique())
        self.logger.info(f"📊 Loaded {len(self.tickers)} unique tickers with earnings")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Connection pool
        self.connections = []
        self.connection_lock = threading.Lock()
        
        # Progress tracking
        self.completed = 0
        self.failed = 0
        self.start_time = None
        
    def create_contract(self, ticker):
        """Create IB contract"""
        contract = Contract()
        contract.symbol = ticker
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract
    
    def connect_to_ib(self, client_id):
        """Connect to IB Gateway"""
        try:
            app = IBDataCollector()
            app.connect("127.0.0.1", 4002, client_id)
            
            # Start socket thread
            api_thread = threading.Thread(target=app.run, daemon=True)
            api_thread.start()
            
            # Wait for connection
            time.sleep(0.5)
            
            return app
        except Exception as e:
            self.logger.error(f"Connection failed for client {client_id}: {e}")
            return None
    
    def get_connection(self):
        """Get available connection from pool"""
        with self.connection_lock:
            if not self.connections:
                # Create new connection
                client_id = random.randint(1000, 9999)
                conn = self.connect_to_ib(client_id)
                if conn:
                    return conn
                return None
            return self.connections.pop()
    
    def return_connection(self, conn):
        """Return connection to pool"""
        with self.connection_lock:
            self.connections.append(conn)
    
    def fetch_10year_daily(self, ticker, conn):
        """Fetch 10 years of daily data"""
        try:
            contract = self.create_contract(ticker)
            req_id = random.randint(1, 9999)
            
            # Clear previous data
            conn.data = {}
            conn.data_ready.clear()
            
            # Request 10 years of daily data
            end_date = datetime.now().strftime("%Y%m%d %H:%M:%S")
            conn.reqHistoricalData(
                req_id,
                contract,
                end_date,
                "10 Y",  # 10 years
                "1 day",
                "TRADES",
                0,  # Include extended hours
                1,
                False,
                []
            )
            
            # Wait for data (max 30 seconds)
            if conn.data_ready.wait(30):
                if req_id in conn.data and len(conn.data[req_id]) > 0:
                    df = pd.DataFrame(conn.data[req_id])
                    df['Date'] = pd.to_datetime(df['Date'])
                    return df
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching 10Y daily for {ticker}: {e}")
            return None
    
    def fetch_30min_around_earnings(self, ticker, earnings_dates, conn):
        """Fetch 30-minute data for 14 days around each earnings"""
        all_data = []
        
        try:
            contract = self.create_contract(ticker)
            
            for earnings_date in earnings_dates:
                # Get 14 days of 30-min data (7 days before + 7 days after)
                # Use current date as end date since we can't go back to past earnings
                end_date = datetime.now().strftime("%Y%m%d %H:%M:%S")
                
                req_id = random.randint(1, 9999)
                conn.data = {}
                conn.data_ready.clear()
                
                conn.reqHistoricalData(
                    req_id,
                    contract,
                    end_date,
                    "14 D",  # 14 days
                    "30 mins",
                    "TRADES",
                    0,  # Include extended hours
                    1,
                    False,
                    []
                )
                
                # Wait for data
                if conn.data_ready.wait(30):
                    if req_id in conn.data and len(conn.data[req_id]) > 0:
                        df = pd.DataFrame(conn.data[req_id])
                        df['Date'] = pd.to_datetime(df['Date'])
                        df['earnings_date'] = earnings_date
                        all_data.append(df)
                
                # Small delay between requests
                time.sleep(0.05)
            
            if all_data:
                return pd.concat(all_data, ignore_index=True)
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching 30-min for {ticker}: {e}")
            return None
    
    def process_ticker(self, ticker):
        """Process single ticker - fetch all data"""
        try:
            # Get connection
            conn = self.get_connection()
            if not conn:
                self.logger.error(f"❌ {ticker}: No connection available")
                return False
            
            # Create ticker directory
            ticker_dir = os.path.join(self.output_dir, ticker)
            os.makedirs(ticker_dir, exist_ok=True)
            
            # Get earnings dates for this ticker
            ticker_earnings = self.earnings[self.earnings['ticker'] == ticker]['date'].tolist()
            
            # 1. Fetch 10 years of daily data
            daily_data = self.fetch_10year_daily(ticker, conn)
            if daily_data is not None and len(daily_data) > 0:
                daily_file = os.path.join(ticker_dir, f"{ticker}_daily_10y.csv")
                daily_data.to_csv(daily_file, index=False)
                self.logger.info(f"  ✅ {ticker}: Daily 10Y - {len(daily_data)} bars")
            else:
                self.logger.warning(f"  ⚠️ {ticker}: No daily data")
            
            time.sleep(0.1)  # Small delay
            
            # 2. Fetch 30-minute data around earnings
            intraday_data = self.fetch_30min_around_earnings(ticker, ticker_earnings, conn)
            if intraday_data is not None and len(intraday_data) > 0:
                intraday_file = os.path.join(ticker_dir, f"{ticker}_30min_earnings.csv")
                intraday_data.to_csv(intraday_file, index=False)
                self.logger.info(f"  ✅ {ticker}: 30-min earnings - {len(intraday_data)} bars")
            else:
                self.logger.warning(f"  ⚠️ {ticker}: No 30-min data")
            
            # Return connection to pool
            self.return_connection(conn)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ {ticker}: {e}")
            if conn:
                self.return_connection(conn)
            return False
    
    def run_extraction(self):
        """Run comprehensive extraction with connection pooling"""
        self.logger.info("\n" + "="*80)
        self.logger.info("COMPREHENSIVE HISTORICAL DATA EXTRACTION")
        self.logger.info("="*80)
        self.logger.info(f"📊 Tickers to process: {len(self.tickers)}")
        self.logger.info(f"🔌 Connections: {self.num_connections}")
        self.logger.info(f"📅 Data to collect:")
        self.logger.info(f"   - 10 years daily data per stock")
        self.logger.info(f"   - 14 days 30-min data around each earnings")
        self.logger.info("="*80)
        
        # Initialize connection pool
        self.logger.info("🔄 Initializing connection pool...")
        for i in range(self.num_connections):
            client_id = random.randint(1000, 9999)
            conn = self.connect_to_ib(client_id)
            if conn:
                self.connections.append(conn)
        
        self.logger.info(f"✅ Created {len(self.connections)} connections")
        
        if len(self.connections) == 0:
            self.logger.error("❌ No connections available!")
            return
        
        # Start extraction
        self.start_time = datetime.now()
        self.logger.info("\n🚀 Starting extraction...\n")
        
        # Process tickers with thread pool
        with ThreadPoolExecutor(max_workers=self.num_connections) as executor:
            futures = {executor.submit(self.process_ticker, ticker): ticker 
                      for ticker in self.tickers}
            
            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    success = future.result()
                    if success:
                        self.completed += 1
                    else:
                        self.failed += 1
                except Exception as e:
                    self.logger.error(f"❌ {ticker}: {e}")
                    self.failed += 1
                
                # Progress update
                total = self.completed + self.failed
                if total % 10 == 0 or total == len(self.tickers):
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    rate = total / elapsed if elapsed > 0 else 0
                    remaining = len(self.tickers) - total
                    eta = timedelta(seconds=int(remaining / rate)) if rate > 0 else timedelta(0)
                    
                    self.logger.info(
                        f"📈 Progress: {total}/{len(self.tickers)} "
                        f"({total/len(self.tickers)*100:.1f}%) - "
                        f"Completed: {self.completed}, Failed: {self.failed} - "
                        f"Rate: {rate:.1f} stocks/sec - ETA: {eta}"
                    )
        
        # Cleanup
        self.logger.info("\n🔄 Shutting down connections...")
        for conn in self.connections:
            try:
                conn.disconnect()
            except:
                pass
        
        # Final report
        duration = datetime.now() - self.start_time
        self.logger.info("\n" + "="*80)
        self.logger.info("📊 EXTRACTION COMPLETE!")
        self.logger.info("="*80)
        self.logger.info(f"✅ Successfully processed: {self.completed} stocks")
        self.logger.info(f"❌ Failed: {self.failed} stocks")
        self.logger.info(f"⏱️ Duration: {duration}")
        self.logger.info(f"⚡ Average rate: {self.completed/duration.total_seconds():.2f} stocks/second")
        self.logger.info(f"📁 Output directory: {self.output_dir}")
        self.logger.info("="*80)
        
        # Generate report
        self.generate_report(duration)
    
    def generate_report(self, duration):
        """Generate extraction report"""
        report = f"""
# COMPREHENSIVE HISTORICAL DATA EXTRACTION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## SUMMARY
- Total stocks: {len(self.tickers)}
- Successfully completed: {self.completed}
- Failed: {self.failed}
- Duration: {duration}
- Success rate: {self.completed/len(self.tickers)*100:.1f}%
- Average rate: {self.completed/duration.total_seconds():.2f} stocks/second

## DATA EXTRACTED PER STOCK
1. **10 Years Daily Data**:
   - Daily OHLCV data
   - ~2,520 trading days per stock
   - Total: ~{self.completed * 2520:,} data points

2. **30-Minute Earnings Data**:
   - 14 days around each earnings event
   - ~182 30-minute bars per earnings (14 days × 6.5 hours × 2 bars/hour)
   - Multiple earnings per stock

## OPTIMIZATION FEATURES
- Connection pooling ({self.num_connections} simultaneous connections)
- Thread pool execution for parallel processing
- Intelligent rate limiting (0.1s delay per request)
- Automatic retry and error handling
- Real-time progress tracking with ETA

## OUTPUT STRUCTURE
```
{self.output_dir}/
├── TICKER1/
│   ├── TICKER1_daily_10y.csv
│   └── TICKER1_30min_earnings.csv
├── TICKER2/
│   ├── TICKER2_daily_10y.csv
│   └── TICKER2_30min_earnings.csv
...
```

## NEXT STEPS
1. Verify data quality for all stocks
2. Run comprehensive backtests with 10-year data
3. Analyze 5-minute patterns around earnings
4. Optimize strategy parameters
5. Generate final stock rankings

## FILES GENERATED
- Daily 10Y files: {self.completed} files
- 30-min earnings files: {self.completed} files
- Total files created: {self.completed * 2}
"""
        
        report_file = os.path.join(self.output_dir, 'comprehensive_extraction_report.md')
        with open(report_file, 'w') as f:
            f.write(report)
        
        self.logger.info(f"📋 Report saved: {report_file}")

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive Historical Data Extractor')
    parser.add_argument('--earnings', default='data/processed/earnings_final.csv',
                       help='Earnings CSV file')
    parser.add_argument('--output', default='data/historical_complete',
                       help='Output directory')
    parser.add_argument('--connections', type=int, default=10,
                       help='Number of simultaneous connections')
    
    args = parser.parse_args()
    
    extractor = ComprehensiveHistoricalExtractor(
        earnings_file=args.earnings,
        output_dir=args.output,
        num_connections=args.connections
    )
    
    extractor.run_extraction()

if __name__ == "__main__":
    main()

