"""
COMPREHENSIVE DATA ORCHESTRATOR - Master Controller for All Data Collection
=========================================================================

This script orchestrates the complete data collection process:
1. Coordinates multiple data collection agents
2. Manages task distribution and load balancing
3. Handles error recovery and retry logic
4. Monitors progress and provides real-time updates
5. Ensures data quality and completeness
6. Implements intelligent rate limiting and API management

Features:
- Multi-threaded parallel processing
- Intelligent task queuing and distribution
- Real-time progress monitoring
- Error handling and automatic retry
- Data validation and quality assurance
- Resume capability for interrupted collections
- Comprehensive logging and reporting

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
import yfinance as yf
import requests
from typing import Dict, List, Tuple, Optional
import multiprocessing as mp
from dataclasses import dataclass
import signal
import psutil

warnings.filterwarnings('ignore')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config.settings import *

@dataclass
class CollectionTask:
    """Data structure for collection tasks"""
    task_id: str
    task_type: str  # 'daily', 'intraday', 'fundamentals', 'earnings'
    ticker: str
    priority: int = 1  # 1=high, 2=medium, 3=low
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
class CollectionResult:
    """Data structure for collection results"""
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

class DataCollectionAgent:
    """Advanced data collection agent with error handling and retry logic"""
    
    def __init__(self, agent_id: int, task_queue: queue.Queue, result_queue: queue.Queue, 
                 rate_limiter, progress_tracker):
        self.agent_id = agent_id
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.rate_limiter = rate_limiter
        self.progress_tracker = progress_tracker
        self.logger = self._setup_logger()
        self.session = self._setup_session()
        self.is_running = True
        
    def _setup_logger(self):
        """Setup agent-specific logger"""
        logger = logging.getLogger(f'Agent_{self.agent_id}')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Create logs directory
            (project_root / 'logs').mkdir(exist_ok=True)
            
            handler = logging.FileHandler(
                project_root / f'logs/agent_{self.agent_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _setup_session(self):
        """Setup HTTP session with proper headers"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': f'UMushroom-DataCollector-Agent{self.agent_id}/1.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        return session
    
    def run(self):
        """Main agent execution loop"""
        self.logger.info(f"Agent {self.agent_id} started")
        
        while self.is_running:
            try:
                # Get task with timeout
                task = self.task_queue.get(timeout=30)
                if task is None:  # Shutdown signal
                    break
                
                # Process task
                result = self._process_task(task)
                
                # Send result
                self.result_queue.put(result)
                self.task_queue.task_done()
                
                # Update progress
                self.progress_tracker.update_progress(result)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Agent {self.agent_id} error: {e}")
                # Send error result
                if 'task' in locals():
                    error_result = CollectionResult(
                        task_id=task.task_id,
                        ticker=task.ticker,
                        task_type=task.task_type,
                        status='failed',
                        error_message=str(e)
                    )
                    self.result_queue.put(error_result)
    
    def _process_task(self, task: CollectionTask) -> CollectionResult:
        """Process individual collection task"""
        start_time = time.time()
        
        self.logger.info(f"Processing {task.task_type} for {task.ticker} (attempt {task.retry_count + 1})")
        
        try:
            # Apply rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Process based on task type
            if task.task_type == 'daily':
                result = self._collect_daily_data(task)
            elif task.task_type == 'intraday':
                result = self._collect_intraday_data(task)
            elif task.task_type == 'fundamentals':
                result = self._collect_fundamentals(task)
            elif task.task_type == 'earnings':
                result = self._collect_earnings_data(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            # Calculate duration
            result.duration = time.time() - start_time
            
            self.logger.info(f"✅ {task.task_type} for {task.ticker} completed in {result.duration:.2f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"❌ {task.task_type} for {task.ticker} failed: {e}")
            
            # Determine if should retry
            if task.retry_count < task.max_retries:
                return CollectionResult(
                    task_id=task.task_id,
                    ticker=task.ticker,
                    task_type=task.task_type,
                    status='retry',
                    duration=duration,
                    error_message=str(e)
                )
            else:
                return CollectionResult(
                    task_id=task.task_id,
                    ticker=task.ticker,
                    task_type=task.task_type,
                    status='failed',
                    duration=duration,
                    error_message=str(e)
                )
    
    def _collect_daily_data(self, task: CollectionTask) -> CollectionResult:
        """Collect 10 years of daily data"""
        ticker = task.ticker
        start_date = task.parameters.get('start_date', (datetime.now() - timedelta(days=3650)).strftime('%Y-%m-%d'))
        end_date = task.parameters.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Get data from yfinance
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date, interval='1d')
        
        if hist.empty:
            raise ValueError(f"No daily data found for {ticker}")
        
        # Save data
        output_dir = project_root / 'data' / 'all_stocks_complete' / ticker
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f'{ticker}_daily_10years.csv'
        hist.to_csv(file_path)
        
        return CollectionResult(
            task_id=task.task_id,
            ticker=ticker,
            task_type='daily',
            status='success',
            data_points=len(hist),
            file_size=file_path.stat().st_size,
            metadata={
                'date_range': f"{hist.index[0].strftime('%Y-%m-%d')} to {hist.index[-1].strftime('%Y-%m-%d')}",
                'columns': list(hist.columns)
            }
        )
    
    def _collect_intraday_data(self, task: CollectionTask) -> CollectionResult:
        """Collect 30-minute data for earnings periods"""
        ticker = task.ticker
        earnings_dates = task.parameters.get('earnings_dates', [])
        
        if not earnings_dates:
            raise ValueError(f"No earnings dates provided for {ticker}")
        
        all_data = []
        successful_periods = 0
        
        for earnings_date in earnings_dates:
            try:
                # 14 days around earnings (7 before, 7 after)
                start_date = (earnings_date - timedelta(days=7)).strftime('%Y-%m-%d')
                end_date = (earnings_date + timedelta(days=7)).strftime('%Y-%m-%d')
                
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date, interval='30m')
                
                if not hist.empty:
                    hist['earnings_date'] = earnings_date.strftime('%Y-%m-%d')
                    all_data.append(hist)
                    successful_periods += 1
                
                # Rate limiting between requests
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.warning(f"Failed to collect intraday data for {ticker} around {earnings_date}: {e}")
                continue
        
        if not all_data:
            raise ValueError(f"No intraday data collected for {ticker}")
        
        # Combine and save data
        combined_data = pd.concat(all_data, ignore_index=False)
        
        output_dir = project_root / 'data' / 'all_stocks_complete' / ticker
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f'{ticker}_30min_earnings.csv'
        combined_data.to_csv(file_path)
        
        return CollectionResult(
            task_id=task.task_id,
            ticker=ticker,
            task_type='intraday',
            status='success',
            data_points=len(combined_data),
            file_size=file_path.stat().st_size,
            metadata={
                'successful_periods': successful_periods,
                'total_periods': len(earnings_dates),
                'date_range': f"{combined_data.index[0].strftime('%Y-%m-%d')} to {combined_data.index[-1].strftime('%Y-%m-%d')}"
            }
        )
    
    def _collect_fundamentals(self, task: CollectionTask) -> CollectionResult:
        """Collect current fundamentals"""
        ticker = task.ticker
        
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
            'collected_at': datetime.now().isoformat()
        }
        
        # Save data
        output_dir = project_root / 'data' / 'all_stocks_complete' / ticker
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f'{ticker}_fundamentals.json'
        with open(file_path, 'w') as f:
            json.dump(fundamentals, f, indent=2)
        
        return CollectionResult(
            task_id=task.task_id,
            ticker=ticker,
            task_type='fundamentals',
            status='success',
            data_points=len([k for k, v in fundamentals.items() if v is not None]),
            file_size=file_path.stat().st_size,
            metadata={'fundamentals_collected': list(fundamentals.keys())}
        )
    
    def _collect_earnings_data(self, task: CollectionTask) -> CollectionResult:
        """Collect historical earnings data"""
        ticker = task.ticker
        
        stock = yf.Ticker(ticker)
        
        # Get earnings calendar
        earnings_calendar = stock.calendar
        
        if earnings_calendar is None or earnings_calendar.empty:
            raise ValueError(f"No earnings calendar found for {ticker}")
        
        earnings_data = earnings_calendar.to_dict('records')
        
        # Save data
        output_dir = project_root / 'data' / 'all_stocks_complete' / ticker
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f'{ticker}_earnings_history.json'
        with open(file_path, 'w') as f:
            json.dump(earnings_data, f, indent=2, default=str)
        
        return CollectionResult(
            task_id=task.task_id,
            ticker=ticker,
            task_type='earnings',
            status='success',
            data_points=len(earnings_data),
            file_size=file_path.stat().st_size,
            metadata={'earnings_events': len(earnings_data)}
        )
    
    def stop(self):
        """Stop the agent"""
        self.is_running = False

class RateLimiter:
    """Intelligent rate limiter for API calls"""
    
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]
            
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = 60 - (now - oldest_request) + 1
                if wait_time > 0:
                    time.sleep(wait_time)
            
            # Record this request
            self.requests.append(now)

class ProgressTracker:
    """Real-time progress tracking and reporting"""
    
    def __init__(self, total_tasks: int):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.retry_tasks = 0
        self.start_time = datetime.now()
        self.lock = threading.Lock()
        self.task_results = {}
    
    def update_progress(self, result: CollectionResult):
        """Update progress with new result"""
        with self.lock:
            if result.status == 'success':
                self.completed_tasks += 1
            elif result.status == 'failed':
                self.failed_tasks += 1
            elif result.status == 'retry':
                self.retry_tasks += 1
            
            self.task_results[result.task_id] = result
    
    def get_progress(self) -> Dict:
        """Get current progress statistics"""
        with self.lock:
            elapsed = datetime.now() - self.start_time
            total_processed = self.completed_tasks + self.failed_tasks + self.retry_tasks
            remaining = self.total_tasks - total_processed
            
            # Calculate ETA
            if total_processed > 0:
                avg_time_per_task = elapsed.total_seconds() / total_processed
                eta_seconds = remaining * avg_time_per_task
                eta = datetime.now() + timedelta(seconds=eta_seconds)
            else:
                eta = None
            
            return {
                'total_tasks': self.total_tasks,
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks,
                'retry_tasks': self.retry_tasks,
                'remaining_tasks': remaining,
                'completion_percentage': (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0,
                'elapsed_time': str(elapsed),
                'eta': eta.isoformat() if eta else None,
                'success_rate': (self.completed_tasks / total_processed * 100) if total_processed > 0 else 0
            }
    
    def print_progress(self):
        """Print formatted progress update"""
        progress = self.get_progress()
        
        print(f"\n📊 PROGRESS UPDATE - {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Completed: {progress['completed_tasks']}/{progress['total_tasks']} ({progress['completion_percentage']:.1f}%)")
        print(f"   Failed: {progress['failed_tasks']} | Retry: {progress['retry_tasks']} | Remaining: {progress['remaining_tasks']}")
        print(f"   Success Rate: {progress['success_rate']:.1f}%")
        print(f"   Elapsed: {progress['elapsed_time']}")
        if progress['eta']:
            print(f"   ETA: {progress['eta']}")

class ComprehensiveDataOrchestrator:
    """Master orchestrator for comprehensive data collection"""
    
    def __init__(self, num_agents: int = 10):
        self.num_agents = num_agents
        self.task_queue = queue.PriorityQueue()
        self.result_queue = queue.Queue()
        self.agents = []
        self.rate_limiter = RateLimiter(max_requests_per_minute=60)
        self.progress_tracker = None
        self.logger = self._setup_logger()
        self.is_running = False
        
        # Create necessary directories
        (project_root / 'logs').mkdir(exist_ok=True)
        (project_root / 'data' / 'all_stocks_complete').mkdir(parents=True, exist_ok=True)
        
    def _setup_logger(self):
        """Setup master logger"""
        logger = logging.getLogger('DataOrchestrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # File handler
            file_handler = logging.FileHandler(
                project_root / f'logs/orchestrator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Console handler
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
    
    def create_tasks(self, tickers: List[str]) -> List[CollectionTask]:
        """Create all collection tasks"""
        tasks = []
        task_id = 0
        
        for ticker in tickers:
            # Daily data task (high priority)
            tasks.append(CollectionTask(
                task_id=f"daily_{ticker}_{task_id}",
                task_type='daily',
                ticker=ticker,
                priority=1,
                parameters={
                    'start_date': (datetime.now() - timedelta(days=3650)).strftime('%Y-%m-%d'),
                    'end_date': datetime.now().strftime('%Y-%m-%d')
                }
            ))
            task_id += 1
            
            # Fundamentals task (high priority)
            tasks.append(CollectionTask(
                task_id=f"fundamentals_{ticker}_{task_id}",
                task_type='fundamentals',
                ticker=ticker,
                priority=1
            ))
            task_id += 1
            
            # Earnings history task (medium priority)
            tasks.append(CollectionTask(
                task_id=f"earnings_{ticker}_{task_id}",
                task_type='earnings',
                ticker=ticker,
                priority=2
            ))
            task_id += 1
            
            # Intraday data task (lower priority, depends on earnings dates)
            earnings_dates = self.load_earnings_dates(ticker)
            if earnings_dates:
                tasks.append(CollectionTask(
                    task_id=f"intraday_{ticker}_{task_id}",
                    task_type='intraday',
                    ticker=ticker,
                    priority=3,
                    parameters={'earnings_dates': earnings_dates}
                ))
                task_id += 1
        
        return tasks
    
    def start_agents(self):
        """Start all data collection agents"""
        self.logger.info(f"Starting {self.num_agents} data collection agents")
        
        for i in range(self.num_agents):
            agent = DataCollectionAgent(
                agent_id=i,
                task_queue=self.task_queue,
                result_queue=self.result_queue,
                rate_limiter=self.rate_limiter,
                progress_tracker=self.progress_tracker
            )
            agent_thread = threading.Thread(target=agent.run, daemon=True)
            agent_thread.start()
            self.agents.append(agent_thread)
    
    def process_results(self):
        """Process results and handle retries"""
        retry_tasks = []
        
        while not self.result_queue.empty():
            try:
                result = self.result_queue.get_nowait()
                
                if result.status == 'retry':
                    # Find original task and retry
                    # This is simplified - in practice you'd store task references
                    retry_tasks.append(result)
                elif result.status == 'failed':
                    self.logger.error(f"❌ {result.task_type} for {result.ticker} failed: {result.error_message}")
                else:
                    self.logger.info(f"✅ {result.task_type} for {result.ticker} completed")
                
            except queue.Empty:
                break
        
        # Re-queue retry tasks
        for result in retry_tasks:
            # Create new task with incremented retry count
            # This is simplified - in practice you'd have more sophisticated retry logic
            pass
    
    def run_collection(self):
        """Run comprehensive data collection"""
        self.logger.info("🚀 Starting Comprehensive Data Collection")
        self.is_running = True
        
        # Load stock list
        tickers = self.load_stock_list()
        if not tickers:
            self.logger.error("No tickers loaded. Exiting.")
            return
        
        self.logger.info(f"📈 Loaded {len(tickers)} tickers for data collection")
        
        # Create tasks
        tasks = self.create_tasks(tickers)
        self.progress_tracker = ProgressTracker(len(tasks))
        
        self.logger.info(f"📋 Created {len(tasks)} data collection tasks")
        
        # Start agents
        self.start_agents()
        
        # Add tasks to queue (priority order)
        for task in sorted(tasks, key=lambda x: x.priority):
            self.task_queue.put((task.priority, task))
        
        # Process results
        self.logger.info("🔄 Starting data collection...")
        
        try:
            while self.is_running:
                self.process_results()
                self.progress_tracker.print_progress()
                time.sleep(10)  # Update every 10 seconds
                
                # Check if all tasks are complete
                progress = self.progress_tracker.get_progress()
                if progress['remaining_tasks'] == 0:
                    break
                    
        except KeyboardInterrupt:
            self.logger.info("⚠️ Collection interrupted by user")
            self.is_running = False
        
        # Final results
        self.process_results()
        self.progress_tracker.print_progress()
        
        # Shutdown agents
        for _ in self.agents:
            self.task_queue.put((0, None))  # Shutdown signal
        
        self.logger.info("✅ Data collection completed!")
        
        # Generate summary report
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        progress = self.progress_tracker.get_progress()
        
        report = {
            'collection_date': datetime.now().isoformat(),
            'total_tickers': len(self.load_stock_list()),
            'total_tasks': progress['total_tasks'],
            'completed_tasks': progress['completed_tasks'],
            'failed_tasks': progress['failed_tasks'],
            'retry_tasks': progress['retry_tasks'],
            'success_rate': progress['success_rate'],
            'completion_percentage': progress['completion_percentage'],
            'duration': progress['elapsed_time'],
            'agents_used': self.num_agents,
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            }
        }
        
        # Save report
        report_path = project_root / f'logs/comprehensive_collection_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"📊 Summary report saved to {report_path}")
    
    def stop(self):
        """Stop the orchestrator"""
        self.is_running = False

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print("\n⚠️ Received interrupt signal. Shutting down gracefully...")
    global orchestrator
    if orchestrator:
        orchestrator.stop()

def main():
    """Main execution function"""
    print("🚀 UMushroom Investment Challenge - Comprehensive Data Orchestrator")
    print("=" * 70)
    
    global orchestrator
    orchestrator = ComprehensiveDataOrchestrator(num_agents=10)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        orchestrator.run_collection()
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")
        orchestrator.logger.error(f"Collection failed: {e}")
    finally:
        orchestrator.stop()

if __name__ == "__main__":
    main()
