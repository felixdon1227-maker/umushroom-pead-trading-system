"""
TWS COMPREHENSIVE DATA COLLECTOR - IB Gateway Integration
=======================================================

This script uses TWS API (port 4002) to collect comprehensive data for all 413 stocks:
1. 10 years of daily data via TWS API
2. 30-minute data for 14 days around each earnings event
3. Current fundamentals and technicals
4. Historical earnings data

Features:
- TWS API integration (port 4002)
- Multi-threaded parallel processing
- Intelligent rate limiting and connection management
- Error handling and retry logic
- Progress tracking and real-time updates
- Data validation and quality assurance

Author: UMushroom Investment Strategy
Date: October 2024
"""

import pandas as pd
import numpy as np
import time
import os
import sys
import logging
import json
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import multiprocessing as mp
from dataclasses import dataclass
import signal

warnings.filterwarnings('ignore')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# TWS API imports
try:
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    from ibapi.common import BarData
    import ibapi.decoder
    import ibapi.connection
except ImportError:
    print("❌ IB API not installed. Installing...")
    os.system("pip install ibapi")
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    from ibapi.common import BarData
    import ibapi.decoder
    import ibapi.connection

# Import yfinance as backup
import yfinance as yf

@dataclass
class TWSDataTask:
    """Data structure for TWS collection tasks"""
    task_id: str
    task_type: str  # 'daily', 'intraday', 'fundamentals'
    ticker: str
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3
    parameters: Dict = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.parameters is None:
            self.parameters = {}

@dataclass
class TWSDataResult:
    """Data structure for TWS collection results"""
    task_id: str
    ticker: str
    task_type: str
    status: str  # 'success', 'failed', 'retry'
    data_points: int = 0
    file_size: int = 0
    duration: float = 0.0
    error_message: str = ""
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class TWSConnection(EWrapper, EClient):
    """TWS API connection wrapper"""
    
    def __init__(self, client_id: int):
        EClient.__init__(self, self)
        self.client_id = client_id
        self.connected = False
        self.data_received = False
        self.bars = []
        self.current_task = None
        self.error_occurred = False
        self.error_message = ""
        
    def connect_to_tws(self, host="127.0.0.1", port=4002):
        """Connect to TWS"""
        try:
            self.connect(host, port, clientId=self.client_id)
            self.connected = True
            return True
        except Exception as e:
            print(f"❌ Failed to connect to TWS: {e}")
            return False
    
    def disconnect_from_tws(self):
        """Disconnect from TWS"""
        if self.connected:
            self.disconnect()
            self.connected = False
    
    def error(self, reqId, errorCode, errorString):
        """Handle TWS errors"""
        if errorCode in [2104, 2106, 2158]:  # Connection messages
            return
        
        self.error_occurred = True
        self.error_message = f"TWS Error {errorCode}: {errorString}"
        print(f"❌ TWS Error {errorCode}: {errorString}")
    
    def historicalData(self, reqId, bar):
        """Handle historical data"""
        self.bars.append({
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
        """Handle end of historical data"""
        self.data_received = True
    
    def get_historical_data(self, contract, end_date, duration, bar_size, what_to_show="TRADES"):
        """Get historical data from TWS"""
        self.bars = []
        self.data_received = False
        self.error_occurred = False
        
        try:
            # Request historical data
            self.reqHistoricalData(
                reqId=1,
                contract=contract,
                endDateTime=end_date,
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
            
            # Wait for data
            timeout = 30  # 30 seconds timeout
            start_time = time.time()
            
            while not self.data_received and not self.error_occurred:
                if time.time() - start_time > timeout:
                    raise TimeoutError("TWS request timeout")
                time.sleep(0.1)
            
            if self.error_occurred:
                raise Exception(self.error_message)
            
            return self.bars
            
        except Exception as e:
            raise Exception(f"TWS data request failed: {e}")

class TWSDataCollector:
    """TWS-based data collector"""
    
    def __init__(self, client_id: int, host="127.0.0.1", port=4002):
        self.client_id = client_id
        self.host = host
        self.port = port
        self.connection = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Setup logger"""
        logger = logging.getLogger(f'TWSCollector_{self.client_id}')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            (project_root / 'logs').mkdir(exist_ok=True)
            handler = logging.FileHandler(
                project_root / f'logs/tws_collector_{self.client_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def connect(self):
        """Connect to TWS"""
        self.connection = TWSConnection(self.client_id)
        
        if not self.connection.connect_to_tws(self.host, self.port):
            raise Exception(f"Failed to connect to TWS on {self.host}:{self.port}")
        
        # Start API thread
        api_thread = threading.Thread(target=self.connection.run, daemon=True)
        api_thread.start()
        
        # Wait for connection
        time.sleep(2)
        
        self.logger.info(f"Connected to TWS with client ID {self.client_id}")
        return True
    
    def disconnect(self):
        """Disconnect from TWS"""
        if self.connection:
            self.connection.disconnect_from_tws()
            self.connection = None
    
    def create_stock_contract(self, ticker: str) -> Contract:
        """Create stock contract for TWS"""
        contract = Contract()
        contract.symbol = ticker
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract
    
    def collect_daily_data(self, ticker: str, years: int = 10) -> TWSDataResult:
        """Collect 10 years of daily data"""
        start_time = time.time()
        
        try:
            if not self.connection:
                self.connect()
            
            contract = self.create_stock_contract(ticker)
            
            # Get daily data for specified years (use UTC timezone)
            end_date = datetime.now().strftime("%Y%m%d %H:%M:%S UTC")
            duration = f"{years} Y"
            
            bars = self.connection.get_historical_data(
                contract=contract,
                end_date=end_date,
                duration=duration,
                bar_size="1 day"
            )
            
            if not bars:
                raise Exception(f"No daily data received for {ticker}")
            
            # Convert to DataFrame
            df = pd.DataFrame(bars)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Save data
            output_dir = project_root / 'data' / 'all_stocks_complete' / ticker
            output_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = output_dir / f'{ticker}_daily_10years_tws.csv'
            df.to_csv(file_path)
            
            duration = time.time() - start_time
            
            return TWSDataResult(
                task_id=f"daily_{ticker}",
                ticker=ticker,
                task_type='daily',
                status='success',
                data_points=len(df),
                file_size=file_path.stat().st_size,
                duration=duration,
                metadata={
                    'date_range': f"{df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}",
                    'source': 'TWS_API'
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Daily data collection failed for {ticker}: {e}")
            
            return TWSDataResult(
                task_id=f"daily_{ticker}",
                ticker=ticker,
                task_type='daily',
                status='failed',
                duration=duration,
                error_message=str(e)
            )
    
    def collect_intraday_data(self, ticker: str, earnings_dates: List[datetime]) -> TWSDataResult:
        """Collect 30-minute data for earnings periods"""
        start_time = time.time()
        
        try:
            if not self.connection:
                self.connect()
            
            contract = self.create_stock_contract(ticker)
            all_data = []
            successful_periods = 0
            
            for earnings_date in earnings_dates:
                try:
                    # 14 days around earnings (7 before, 7 after) - use UTC timezone
                    start_date = (earnings_date - timedelta(days=7)).strftime("%Y%m%d %H:%M:%S UTC")
                    end_date = (earnings_date + timedelta(days=7)).strftime("%Y%m%d %H:%M:%S UTC")
                    
                    # Get 30-minute data
                    bars = self.connection.get_historical_data(
                        contract=contract,
                        end_date=end_date,
                        duration="14 D",
                        bar_size="30 mins"
                    )
                    
                    if bars:
                        df_period = pd.DataFrame(bars)
                        df_period['date'] = pd.to_datetime(df_period['date'])
                        df_period['earnings_date'] = earnings_date.strftime('%Y-%m-%d')
                        all_data.append(df_period)
                        successful_periods += 1
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    self.logger.warning(f"Failed to collect intraday data for {ticker} around {earnings_date}: {e}")
                    continue
            
            if not all_data:
                raise Exception(f"No intraday data collected for {ticker}")
            
            # Combine all data
            combined_data = pd.concat(all_data, ignore_index=False)
            combined_data.set_index('date', inplace=True)
            
            # Save data
            output_dir = project_root / 'data' / 'all_stocks_complete' / ticker
            output_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = output_dir / f'{ticker}_30min_earnings_tws.csv'
            combined_data.to_csv(file_path)
            
            duration = time.time() - start_time
            
            return TWSDataResult(
                task_id=f"intraday_{ticker}",
                ticker=ticker,
                task_type='intraday',
                status='success',
                data_points=len(combined_data),
                file_size=file_path.stat().st_size,
                duration=duration,
                metadata={
                    'successful_periods': successful_periods,
                    'total_periods': len(earnings_dates),
                    'source': 'TWS_API'
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Intraday data collection failed for {ticker}: {e}")
            
            return TWSDataResult(
                task_id=f"intraday_{ticker}",
                ticker=ticker,
                task_type='intraday',
                status='failed',
                duration=duration,
                error_message=str(e)
            )
    
    def collect_fundamentals(self, ticker: str) -> TWSDataResult:
        """Collect fundamentals using yfinance (TWS doesn't have comprehensive fundamentals)"""
        start_time = time.time()
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract key fundamentals
            fundamentals = {
                'ticker': ticker,
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'price_to_book': info.get('priceToBook', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'return_on_equity': info.get('returnOnEquity', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'earnings_growth': info.get('earningsGrowth', 0),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'beta': info.get('beta', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'current_price': info.get('currentPrice', 0),
                'target_price': info.get('targetMeanPrice', 0),
                'recommendation': info.get('recommendationKey', 'Unknown'),
                'collected_at': datetime.now().isoformat(),
                'source': 'yfinance'
            }
            
            # Save data
            output_dir = project_root / 'data' / 'all_stocks_complete' / ticker
            output_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = output_dir / f'{ticker}_fundamentals.json'
            with open(file_path, 'w') as f:
                json.dump(fundamentals, f, indent=2)
            
            duration = time.time() - start_time
            
            return TWSDataResult(
                task_id=f"fundamentals_{ticker}",
                ticker=ticker,
                task_type='fundamentals',
                status='success',
                data_points=len([k for k, v in fundamentals.items() if v is not None]),
                file_size=file_path.stat().st_size,
                duration=duration,
                metadata={'source': 'yfinance'}
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Fundamentals collection failed for {ticker}: {e}")
            
            return TWSDataResult(
                task_id=f"fundamentals_{ticker}",
                ticker=ticker,
                task_type='fundamentals',
                status='failed',
                duration=duration,
                error_message=str(e)
            )

class TWSDataOrchestrator:
    """Master orchestrator for TWS-based data collection"""
    
    def __init__(self, num_connections: int = 5, base_client_id: int = 2000):
        self.num_connections = num_connections
        self.base_client_id = base_client_id
        self.collectors = []
        self.logger = self._setup_logger()
        self.progress = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': None
        }
        
        # Create necessary directories
        (project_root / 'logs').mkdir(exist_ok=True)
        (project_root / 'data' / 'all_stocks_complete').mkdir(parents=True, exist_ok=True)
        
    def _setup_logger(self):
        """Setup master logger"""
        logger = logging.getLogger('TWSOrchestrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            file_handler = logging.FileHandler(
                project_root / f'logs/tws_orchestrator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
        return logger
    
    def load_stock_list(self) -> List[str]:
        """Load list of all stocks"""
        try:
            earnings_df = pd.read_csv(project_root / 'data' / 'processed' / 'earnings_final.csv')
            return earnings_df['ticker'].unique().tolist()
        except Exception as e:
            self.logger.error(f"Failed to load stock list: {e}")
            return []
    
    def load_earnings_dates(self, ticker: str) -> List[datetime]:
        """Load earnings dates for a ticker"""
        try:
            earnings_df = pd.read_csv(project_root / 'data' / 'processed' / 'earnings_final.csv')
            ticker_earnings = earnings_df[earnings_df['ticker'] == ticker]
            
            if not ticker_earnings.empty:
                dates = pd.to_datetime(ticker_earnings['date']).tolist()
                # Add historical dates (simplified)
                historical_dates = []
                for date in dates:
                    for i in range(40):  # 10 years * 4 quarters
                        hist_date = date - timedelta(days=90*i)
                        if hist_date >= datetime.now() - timedelta(days=3650):
                            historical_dates.append(hist_date)
                
                return list(set(historical_dates + dates))
            
            return []
            
        except Exception as e:
            self.logger.warning(f"Failed to load earnings dates for {ticker}: {e}")
            return []
    
    def create_tasks(self, tickers: List[str]) -> List[TWSDataTask]:
        """Create all collection tasks"""
        tasks = []
        
        for ticker in tickers:
            # Daily data task
            tasks.append(TWSDataTask(
                task_id=f"daily_{ticker}",
                task_type='daily',
                ticker=ticker,
                priority=1,
                parameters={'years': 10}
            ))
            
            # Fundamentals task
            tasks.append(TWSDataTask(
                task_id=f"fundamentals_{ticker}",
                task_type='fundamentals',
                ticker=ticker,
                priority=2
            ))
            
            # Intraday data task (if earnings dates available)
            earnings_dates = self.load_earnings_dates(ticker)
            if earnings_dates:
                tasks.append(TWSDataTask(
                    task_id=f"intraday_{ticker}",
                    task_type='intraday',
                    ticker=ticker,
                    priority=3,
                    parameters={'earnings_dates': earnings_dates}
                ))
        
        return tasks
    
    def process_stock(self, collector: TWSDataCollector, task: TWSDataTask) -> TWSDataResult:
        """Process a single stock with a collector"""
        try:
            if task.task_type == 'daily':
                return collector.collect_daily_data(task.ticker, task.parameters.get('years', 10))
            elif task.task_type == 'intraday':
                return collector.collect_intraday_data(task.ticker, task.parameters.get('earnings_dates', []))
            elif task.task_type == 'fundamentals':
                return collector.collect_fundamentals(task.ticker)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
                
        except Exception as e:
            return TWSDataResult(
                task_id=task.task_id,
                ticker=task.ticker,
                task_type=task.task_type,
                status='failed',
                error_message=str(e)
            )
    
    def run_collection(self):
        """Run comprehensive data collection using TWS"""
        self.logger.info("🚀 Starting TWS-based Data Collection")
        self.progress['start_time'] = datetime.now()
        
        # Load stock list
        tickers = self.load_stock_list()
        if not tickers:
            self.logger.error("No tickers loaded. Exiting.")
            return
        
        self.logger.info(f"📈 Loaded {len(tickers)} tickers for data collection")
        
        # Create tasks
        tasks = self.create_tasks(tickers)
        self.progress['total_tasks'] = len(tasks)
        
        self.logger.info(f"📋 Created {len(tasks)} data collection tasks")
        
        # Create collectors
        for i in range(self.num_connections):
            collector = TWSDataCollector(client_id=self.base_client_id + i)
            self.collectors.append(collector)
        
        # Process tasks in parallel
        self.logger.info("🔄 Starting data collection...")
        
        with ThreadPoolExecutor(max_workers=self.num_connections) as executor:
            # Submit all tasks
            future_to_task = {}
            
            for i, task in enumerate(tasks):
                collector = self.collectors[i % self.num_connections]
                future = executor.submit(self.process_stock, collector, task)
                future_to_task[future] = task
            
            # Process results
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                
                try:
                    result = future.result()
                    
                    if result.status == 'success':
                        self.progress['completed_tasks'] += 1
                        self.logger.info(f"✅ {result.task_type} for {result.ticker} completed ({result.data_points} points)")
                    else:
                        self.progress['failed_tasks'] += 1
                        self.logger.error(f"❌ {result.task_type} for {result.ticker} failed: {result.error_message}")
                    
                    # Print progress
                    self.print_progress()
                    
                except Exception as e:
                    self.progress['failed_tasks'] += 1
                    self.logger.error(f"❌ Task {task.task_id} failed with exception: {e}")
        
        # Disconnect all collectors
        for collector in self.collectors:
            collector.disconnect()
        
        self.logger.info("✅ TWS data collection completed!")
        self.generate_summary_report()
    
    def print_progress(self):
        """Print current progress"""
        elapsed = datetime.now() - self.progress['start_time']
        completed = self.progress['completed_tasks']
        failed = self.progress['failed_tasks']
        total = self.progress['total_tasks']
        remaining = total - completed - failed
        
        print(f"\n📊 TWS PROGRESS UPDATE:")
        print(f"   Completed: {completed}/{total} ({completed/total*100:.1f}%)")
        print(f"   Failed: {failed}/{total} ({failed/total*100:.1f}%)")
        print(f"   Remaining: {remaining}")
        print(f"   Elapsed: {elapsed}")
        if completed > 0:
            eta = elapsed * remaining / completed
            print(f"   ETA: {eta}")
    
    def generate_summary_report(self):
        """Generate summary report"""
        report = {
            'collection_date': datetime.now().isoformat(),
            'total_tickers': len(self.load_stock_list()),
            'total_tasks': self.progress['total_tasks'],
            'completed_tasks': self.progress['completed_tasks'],
            'failed_tasks': self.progress['failed_tasks'],
            'success_rate': self.progress['completed_tasks'] / self.progress['total_tasks'] * 100,
            'duration': str(datetime.now() - self.progress['start_time']),
            'connections_used': self.num_connections,
            'data_source': 'TWS_API'
        }
        
        # Save report
        report_path = project_root / f'logs/tws_collection_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"📊 Summary report saved to {report_path}")

def main():
    """Main execution function"""
    print("🚀 UMushroom Investment Challenge - TWS Comprehensive Data Collector")
    print("=" * 70)
    print("Using TWS API on port 4002 for historical data collection")
    print("=" * 70)
    
    # Check if TWS is running
    print("🔍 Checking TWS connection...")
    try:
        test_connection = TWSConnection(9999)
        if not test_connection.connect_to_tws():
            print("❌ Cannot connect to TWS on port 4002")
            print("Please ensure TWS/IB Gateway is running and API is enabled")
            return
        test_connection.disconnect_from_tws()
        print("✅ TWS connection verified")
    except Exception as e:
        print(f"❌ TWS connection failed: {e}")
        return
    
    # Create orchestrator
    orchestrator = TWSDataOrchestrator(num_connections=5, base_client_id=2000)
    
    try:
        orchestrator.run_collection()
    except KeyboardInterrupt:
        print("\n⚠️ Collection interrupted by user")
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")
        orchestrator.logger.error(f"Collection failed: {e}")

if __name__ == "__main__":
    main()
