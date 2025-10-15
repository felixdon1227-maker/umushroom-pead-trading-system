"""
Extract ALL Finviz Stocks - Maximum Speed
==========================================

Collects 10 years daily + 30-min around each earnings for ALL 372 finviz stocks
Uses connection pooling and parallel processing for maximum speed
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
        
    def error(self, reqId, errorCode, errorString):
        if errorCode not in [2104, 2106, 2158, 2174, 2176]:
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

class AllStocksExtractor:
    """Extract all finviz stocks at maximum speed"""
    
    def __init__(self, finviz_ticker_list, earnings_file, output_dir, num_connections=20):
        self.finviz_tickers = finviz_ticker_list
        self.earnings_file = earnings_file
        self.output_dir = output_dir
        self.num_connections = num_connections
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('AllStocksExtractor')
        
        # Load earnings data
        self.earnings = pd.read_csv(earnings_file)
        self.earnings['date'] = pd.to_datetime(self.earnings['date'])
        
        # Get all tickers (finviz list + earnings list combined)
        earnings_tickers = set(self.earnings['ticker'].unique())
        finviz_tickers = set([t.strip() for t in open(finviz_ticker_list).readlines() if t.strip()])
        
        # Combine and deduplicate
        self.all_tickers = sorted(finviz_tickers | earnings_tickers)
        self.logger.info(f"📊 Total unique tickers: {len(self.all_tickers)} (Finviz: {len(finviz_tickers)}, Earnings: {len(earnings_tickers)})")
        
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
            
            api_thread = threading.Thread(target=app.run, daemon=True)
            api_thread.start()
            time.sleep(0.3)
            
            return app
        except Exception as e:
            self.logger.error(f"Connection failed for client {client_id}: {e}")
            return None
    
    def get_connection(self):
        """Get available connection from pool"""
        with self.connection_lock:
            if not self.connections:
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
            
            conn.data = {}
            conn.data_ready.clear()
            
            end_date = datetime.now().strftime("%Y%m%d %H:%M:%S")
            conn.reqHistoricalData(
                req_id, contract, end_date, "10 Y", "1 day",
                "TRADES", 0, 1, False, []
            )
            
            if conn.data_ready.wait(30):
                if req_id in conn.data and len(conn.data[req_id]) > 0:
                    df = pd.DataFrame(conn.data[req_id])
                    df['Date'] = pd.to_datetime(df['Date'])
                    return df
            return None
        except Exception as e:
            return None
    
    def fetch_30min_chunk(self, ticker, end_date, days, conn):
        """Fetch a chunk of 30-minute data"""
        try:
            contract = self.create_contract(ticker)
            req_id = random.randint(1, 9999)
            
            conn.data = {}
            conn.data_ready.clear()
            
            end_str = end_date.strftime("%Y%m%d %H:%M:%S")
            conn.reqHistoricalData(
                req_id, contract, end_str, f"{days} D", "30 mins",
                "TRADES", 0, 1, False, []
            )
            
            if conn.data_ready.wait(30):
                if req_id in conn.data and len(conn.data[req_id]) > 0:
                    return pd.DataFrame(conn.data[req_id])
            return None
        except Exception as e:
            return None
    
    def fetch_30min_around_earnings(self, ticker, earnings_dates, conn):
        """Fetch 30-min data around each earnings - breaking into chunks"""
        all_data = []
        
        for earnings_date in earnings_dates:
            try:
                # Get 14 days in 3-day chunks (7 days before + 7 days after)
                chunks = []
                
                # 7 days after earnings (in 3-day chunks)
                for i in range(0, 7, 3):
                    chunk_end = earnings_date + timedelta(days=min(i+3, 7))
                    chunk = self.fetch_30min_chunk(ticker, chunk_end, 3, conn)
                    if chunk is not None:
                        chunks.append(chunk)
                    time.sleep(0.05)
                
                # 7 days before earnings (in 3-day chunks)
                for i in range(0, 7, 3):
                    chunk_end = earnings_date - timedelta(days=i)
                    chunk = self.fetch_30min_chunk(ticker, chunk_end, 3, conn)
                    if chunk is not None:
                        chunks.append(chunk)
                    time.sleep(0.05)
                
                if chunks:
                    combined = pd.concat(chunks, ignore_index=True)
                    combined['Date'] = pd.to_datetime(combined['Date'])
                    combined = combined.drop_duplicates(subset=['Date']).sort_values('Date')
                    combined['earnings_date'] = earnings_date
                    all_data.append(combined)
                    
            except Exception as e:
                continue
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return None
    
    def get_historical_earnings(self, ticker):
        """Get all earnings for this ticker from last 10 years"""
        ticker_earnings = self.earnings[self.earnings['ticker'] == ticker]['date'].tolist()
        
        # Filter to last 10 years only
        ten_years_ago = datetime.now() - timedelta(days=3650)
        ticker_earnings = [d for d in ticker_earnings if d >= ten_years_ago]
        
        return ticker_earnings
    
    def process_ticker(self, ticker):
        """Process single ticker - fetch all data"""
        try:
            # Check if already exists
            ticker_dir = os.path.join(self.output_dir, ticker)
            daily_file = os.path.join(ticker_dir, f"{ticker}_daily_10y.csv")
            earnings_file = os.path.join(ticker_dir, f"{ticker}_30min_all_earnings.csv")
            
            if os.path.exists(daily_file) and os.path.exists(earnings_file):
                self.logger.info(f"  ⏭️ {ticker}: Already completed")
                return True
            
            conn = self.get_connection()
            if not conn:
                return False
            
            os.makedirs(ticker_dir, exist_ok=True)
            
            # Get earnings dates for last 10 years
            earnings_dates = self.get_historical_earnings(ticker)
            
            # 1. Fetch 10 years of daily data
            if not os.path.exists(daily_file):
                daily_data = self.fetch_10year_daily(ticker, conn)
                if daily_data is not None and len(daily_data) > 0:
                    daily_data.to_csv(daily_file, index=False)
                    self.logger.info(f"  ✅ {ticker}: Daily 10Y - {len(daily_data)} bars")
                else:
                    self.logger.warning(f"  ⚠️ {ticker}: No daily data")
            
            time.sleep(0.1)
            
            # 2. Fetch 30-minute data around ALL earnings
            if earnings_dates and not os.path.exists(earnings_file):
                intraday_data = self.fetch_30min_around_earnings(ticker, earnings_dates, conn)
                if intraday_data is not None and len(intraday_data) > 0:
                    intraday_data.to_csv(earnings_file, index=False)
                    self.logger.info(f"  ✅ {ticker}: 30-min - {len(intraday_data)} bars ({len(earnings_dates)} earnings)")
            
            self.return_connection(conn)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ {ticker}: {e}")
            if conn:
                self.return_connection(conn)
            return False
    
    def run_extraction(self):
        """Run complete extraction"""
        self.logger.info("\n" + "="*80)
        self.logger.info("ALL FINVIZ STOCKS - MAXIMUM SPEED EXTRACTION")
        self.logger.info("="*80)
        self.logger.info(f"📊 Total Tickers: {len(self.all_tickers)}")
        self.logger.info(f"🔌 Connections: {self.num_connections}")
        self.logger.info(f"📅 Data: 10Y daily + 30-min around all earnings")
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
        
        self.start_time = datetime.now()
        self.logger.info("\n🚀 Starting extraction...\n")
        
        # Process tickers
        with ThreadPoolExecutor(max_workers=self.num_connections) as executor:
            futures = {executor.submit(self.process_ticker, ticker): ticker 
                      for ticker in self.all_tickers}
            
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
                if total % 10 == 0 or total == len(self.all_tickers):
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    rate = total / elapsed if elapsed > 0 else 0
                    remaining = len(self.all_tickers) - total
                    eta = timedelta(seconds=int(remaining / rate)) if rate > 0 else timedelta(0)
                    
                    self.logger.info(
                        f"📈 Progress: {total}/{len(self.all_tickers)} "
                        f"({total/len(self.all_tickers)*100:.1f}%) - "
                        f"Completed: {self.completed}, Failed: {self.failed} - "
                        f"Rate: {rate:.2f} stocks/sec - ETA: {eta}"
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

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract All Finviz Stocks')
    parser.add_argument('--finviz', default='data/finviz_all_included/ticker_list.txt',
                       help='Finviz ticker list file')
    parser.add_argument('--earnings', default='data/processed/earnings_final.csv',
                       help='Earnings CSV file')
    parser.add_argument('--output', default='data/all_stocks_complete',
                       help='Output directory')
    parser.add_argument('--connections', type=int, default=20,
                       help='Number of simultaneous connections')
    
    args = parser.parse_args()
    
    extractor = AllStocksExtractor(
        finviz_ticker_list=args.finviz,
        earnings_file=args.earnings,
        output_dir=args.output,
        num_connections=args.connections
    )
    
    extractor.run_extraction()

if __name__ == "__main__":
    main()

