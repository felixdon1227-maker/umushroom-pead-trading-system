from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import pandas as pd
from datetime import datetime, timedelta
import os

class TWSHistoricalData(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.nextOrderId = None
        self.historical_data = {}
        self.data_ready = threading.Event()
        self.connection_ready = threading.Event()
        self.current_request_id = 1000
        
    def error(self, reqId, errorCode, errorString):
        """Error handling"""
        if errorCode in [502, 2104, 2106, 2158]:
            pass  # Informational messages
        else:
            print(f"  ⚠️  Error {errorCode}: {errorString}")
        
    def nextValidId(self, orderId):
        """Callback when connection is established"""
        super().nextValidId(orderId)
        self.nextOrderId = orderId
        self.connection_ready.set()
        print(f"✓ Connected to TWS API on port 4002")
        
    def historicalData(self, reqId, bar):
        """Callback for historical data bars"""
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        
        self.historical_data[reqId].append({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume,
            'average': bar.average,
            'barCount': bar.barCount
        })
    
    def historicalDataEnd(self, reqId, start, end):
        """Called when historical data is complete"""
        self.data_ready.set()
        
    def create_stock_contract(self, symbol):
        """Create a stock contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.primaryExchange = "NASDAQ"  # Try NASDAQ first
        return contract
    
    def get_historical_data(self, ticker, end_date, duration, bar_size, what_to_show='TRADES'):
        """
        Fetch historical data from TWS
        
        Parameters:
        - ticker: Stock symbol
        - end_date: End date (format: 'YYYYMMDD HH:MM:SS')
        - duration: How far back (e.g., '10 Y', '1 M', '5 D')
        - bar_size: Bar size (e.g., '1 hour', '1 day', '5 mins')
        - what_to_show: 'TRADES', 'MIDPOINT', 'BID', 'ASK'
        """
        contract = self.create_stock_contract(ticker)
        
        reqId = self.current_request_id
        self.current_request_id += 1
        
        self.data_ready.clear()
        self.historical_data[reqId] = []
        
        # Request historical data
        self.reqHistoricalData(
            reqId=reqId,
            contract=contract,
            endDateTime=end_date,
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=0,  # 0 = include extended hours, 1 = regular trading hours only
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[]
        )
        
        # Wait for data with timeout
        if self.data_ready.wait(timeout=30):
            data = self.historical_data.get(reqId, [])
            return pd.DataFrame(data) if data else None
        else:
            print(f"  ⚠️  Timeout waiting for {ticker} data")
            return None

class PEADHistoricalAnalyzer:
    def __init__(self, tws_app, earnings_csv):
        self.tws = tws_app
        self.df = pd.read_csv(earnings_csv)
        self.data_dir = 'data/processed/historical_data'
        
        # Create directories
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f'{self.data_dir}/earnings_history', exist_ok=True)
        os.makedirs(f'{self.data_dir}/hourly_prices', exist_ok=True)
        os.makedirs(f'{self.data_dir}/daily_prices', exist_ok=True)
        
    def fetch_10year_daily_prices(self, ticker):
        """Fetch 10 years of daily price data"""
        print(f"  Fetching 10 years daily data for {ticker}...", end='')
        
        end_date = datetime.now().strftime('%Y%m%d %H:%M:%S')
        
        # Get 10 years of daily data
        df = self.tws.get_historical_data(
            ticker=ticker,
            end_date=end_date,
            duration='10 Y',
            bar_size='1 day',
            what_to_show='TRADES'
        )
        
        if df is not None and not df.empty:
            df['ticker'] = ticker
            filename = f'{self.data_dir}/daily_prices/{ticker}_daily_10y.csv'
            df.to_csv(filename, index=False)
            print(f" ✓ {len(df)} days saved")
            return df
        else:
            print(f" ✗ No data")
            return None
    
    def fetch_hourly_around_date(self, ticker, target_date, days_before=3, days_after=5):
        """Fetch hourly data around a specific date"""
        # Calculate end date (days_after from target)
        end_date = (target_date + timedelta(days=days_after)).strftime('%Y%m%d 23:59:59')
        
        # Duration to cover days_before + days_after
        total_days = days_before + days_after + 1
        duration = f'{total_days} D'
        
        df = self.tws.get_historical_data(
            ticker=ticker,
            end_date=end_date,
            duration=duration,
            bar_size='1 hour',
            what_to_show='TRADES'
        )
        
        if df is not None and not df.empty:
            df['ticker'] = ticker
            df['earnings_date'] = target_date
            return df
        
        return None
    
    def analyze_stock_complete(self, ticker):
        """Complete historical analysis for one stock"""
        print(f"\n{'='*80}")
        print(f"Analyzing {ticker}")
        print(f"{'='*80}")
        
        # Step 1: Get 10 years of daily data
        daily_df = self.fetch_10year_daily_prices(ticker)
        
        if daily_df is None:
            print(f"  ✗ {ticker}: No daily data available")
            return None
        
        time.sleep(0.5)  # Pacing - OPTIMIZED
        
        # Step 2: Identify earnings dates from daily data (large gaps or volume spikes)
        # For now, we'll use recent earnings dates from yfinance
        import yfinance as yf
        
        try:
            stock = yf.Ticker(ticker)
            earnings_dates_df = stock.earnings_dates
            
            if earnings_dates_df is not None and not earnings_dates_df.empty:
                # Get last 10 years
                earnings_dates_df.index = earnings_dates_df.index.tz_localize(None)
                ten_years_ago = pd.Timestamp.now() - timedelta(days=3650)
                earnings_dates_df = earnings_dates_df[earnings_dates_df.index >= ten_years_ago]
                
                # Save earnings history
                earnings_data = []
                for date, row in earnings_dates_df.iterrows():
                    earnings_data.append({
                        'ticker': ticker,
                        'earnings_date': date,
                        'eps_estimate': row.get('EPS Estimate', None),
                        'reported_eps': row.get('Reported EPS', None),
                        'surprise_pct': row.get('Surprise(%)', None)
                    })
                
                df_earnings = pd.DataFrame(earnings_data)
                filename = f'{self.data_dir}/earnings_history/{ticker}_earnings.csv'
                df_earnings.to_csv(filename, index=False)
                
                print(f"  ✓ Earnings history: {len(df_earnings)} reports saved")
                
                # Step 3: Fetch hourly data around recent earnings (last 2 years only - TWS limitation)
                recent_earnings = df_earnings[df_earnings['earnings_date'] >= (pd.Timestamp.now() - timedelta(days=730))]
                
                print(f"  Fetching hourly data for {len(recent_earnings)} recent earnings...")
                
                hourly_data_list = []
                for idx, row in recent_earnings.iterrows():
                    earnings_date = pd.to_datetime(row['earnings_date'])
                    
                    print(f"    {earnings_date.strftime('%Y-%m-%d')}...", end='')
                    
                    hourly_df = self.fetch_hourly_around_date(ticker, earnings_date)
                    
                    if hourly_df is not None:
                        hourly_data_list.append(hourly_df)
                        print(f" ✓ {len(hourly_df)} hours")
                    else:
                        print(f" ✗")
                    
                    time.sleep(0.5)  # Pacing between requests - OPTIMIZED
                
                # Combine and save hourly data
                if hourly_data_list:
                    combined_hourly = pd.concat(hourly_data_list, ignore_index=True)
                    filename = f'{self.data_dir}/hourly_prices/{ticker}_hourly.csv'
                    combined_hourly.to_csv(filename, index=False)
                    print(f"  ✓ Hourly data: {len(combined_hourly)} bars saved")
                
                return {
                    'ticker': ticker,
                    'daily_bars': len(daily_df),
                    'earnings_count': len(df_earnings),
                    'recent_earnings_with_hourly': len(hourly_data_list),
                    'hourly_bars': len(combined_hourly) if hourly_data_list else 0
                }
            
        except Exception as e:
            print(f"  ✗ Error getting earnings: {str(e)[:80]}")
            return None
    
    def analyze_all_stocks(self, limit=None):
        """Analyze all stocks"""
        tickers = self.df['ticker'].unique().tolist()
        tickers_to_process = tickers[:limit] if limit else tickers
        
        # Skip already completed stocks
        completed_tickers = set()
        summary_file = f'{self.data_dir}/collection_summary.csv'
        if os.path.exists(summary_file):
            completed_df = pd.read_csv(summary_file)
            completed_tickers = set(completed_df['ticker'].tolist())
            print(f"📋 Found {len(completed_tickers)} already completed stocks - skipping them")
        
        tickers_to_process = [t for t in tickers_to_process if t not in completed_tickers]
        total_stocks = len(tickers_to_process)
        
        if total_stocks == 0:
            print("✅ All stocks already processed!")
            return []
        
        print("=" * 80)
        print("HISTORICAL PEAD DATA COLLECTION VIA TWS")
        print("=" * 80)
        print(f"Total stocks: {total_stocks}")
        print(f"Daily data: 10 years")
        print(f"Hourly data: Last 2 years (around earnings)")
        print("=" * 80)
        
        # Load existing results
        results = []
        if os.path.exists(summary_file):
            existing_df = pd.read_csv(summary_file)
            results = existing_df.to_dict('records')
        
        start_time = time.time()
        
        for i, ticker in enumerate(tickers_to_process, 1):
            # Calculate progress
            completed_count = len(completed_tickers) + i
            total_all = len(self.df['ticker'].unique())
            overall_progress = (completed_count / total_all) * 100
            
            elapsed = time.time() - start_time
            avg_time_per_stock = elapsed / i if i > 0 else 0
            remaining_stocks = total_stocks - i
            eta_seconds = remaining_stocks * avg_time_per_stock
            eta_minutes = eta_seconds / 60
            
            print(f"\n{'='*80}")
            print(f"Overall: {overall_progress:.1f}% ({completed_count}/{total_all}) | Batch: {i}/{total_stocks} | ETA: {eta_minutes:.1f} min | {ticker}")
            print(f"{'='*80}")
            
            result = self.analyze_stock_complete(ticker)
            
            if result:
                results.append(result)
                print(f"  ✅ {ticker} complete: {result['daily_bars']} daily bars, {result['hourly_bars']} hourly bars")
            else:
                print(f"  ⚠️  {ticker} failed")
            
            # Save progress every 10 stocks
            if i % 10 == 0:
                summary_df = pd.DataFrame(results)
                summary_df.to_csv(f'{self.data_dir}/collection_summary.csv', index=False)
                progress_pct = (len(results) / total_stocks) * 100
                print(f"\n💾 Progress saved: {len(results)} stocks completed ({progress_pct:.1f}%)")
            
            # Pacing to avoid rate limits - OPTIMIZED
            time.sleep(0.8)
        
        # Final save
        summary_df = pd.DataFrame(results)
        summary_df.to_csv(f'{self.data_dir}/collection_summary.csv', index=False)
        
        total_time = (time.time() - start_time) / 60
        
        print("\n" + "=" * 80)
        print("✅ COLLECTION COMPLETE!")
        print("=" * 80)
        print(f"Stocks processed: {len(results)}/{total_stocks}")
        print(f"Success rate: {len(results)/total_stocks*100:.1f}%")
        print(f"Total time: {total_time:.1f} minutes")
        if results:
            print(f"Total daily bars: {summary_df['daily_bars'].sum():,}")
            print(f"Total hourly bars: {summary_df['hourly_bars'].sum():,}")
        
        return results

def connect_to_tws(port=4002, client_id=10):
    """Connect to TWS"""
    app = TWSHistoricalData()
    app.connect("127.0.0.1", port, clientId=client_id)
    
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()
    
    if app.connection_ready.wait(timeout=10):
        return app
    else:
        print("✗ Failed to connect to TWS")
        return None

def main():
    print("=" * 80)
    print("TWS HISTORICAL PEAD DATA FETCHER")
    print("=" * 80)
    
    # Connect to TWS
    print("\nConnecting to TWS on port 4002...")
    tws = connect_to_tws(port=4002)
    
    if not tws:
        print("✗ Make sure TWS/IB Gateway is running on port 4002")
        return
    
    # Initialize analyzer
    analyzer = PEADHistoricalAnalyzer(tws, 'earnings_clean.csv')
    
    print(f"\nFound {len(analyzer.df)} stocks to analyze")
    
    # Start with test
    print("\n🚀 Starting with first 5 stocks as test...")
    results = analyzer.analyze_all_stocks(limit=5)
    
    print("\n✅ Test complete!")
    print(f"\nTo process all stocks, run: analyzer.analyze_all_stocks()")
    print(f"Estimated time: ~{len(analyzer.df) * 2} minutes")
    
    # Disconnect
    tws.disconnect()

if __name__ == "__main__":
    main()

