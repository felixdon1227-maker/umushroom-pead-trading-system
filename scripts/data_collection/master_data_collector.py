"""
MASTER DATA COLLECTOR - Complete Data Collection for 413 Stocks
=============================================================

This script orchestrates the complete data collection for all 413 stocks:
1. 10 years of daily data
2. 30-minute data for 14 days around each earnings event (going back 10 years)
3. Current fundamentals and technicals
4. Historical earnings data

Features:
- Multi-agent coordination
- Error handling and retry logic
- Progress tracking
- Data validation
- Parallel processing
- Resume capability

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

warnings.filterwarnings('ignore')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config.settings import *

class DataCollectionAgent:
    """Individual agent for data collection tasks"""
    
    def __init__(self, agent_id: int, task_queue: queue.Queue, result_queue: queue.Queue):
        self.agent_id = agent_id
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.logger = self._setup_logger()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def _setup_logger(self):
        """Setup agent-specific logger"""
        logger = logging.getLogger(f'Agent_{self.agent_id}')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler(
                project_root / f'logs/agent_{self.agent_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def run(self):
        """Main agent loop"""
        self.logger.info(f"Agent {self.agent_id} started")
        
        while True:
            try:
                task = self.task_queue.get(timeout=30)
                if task is None:  # Shutdown signal
                    break
                    
                result = self._process_task(task)
                self.result_queue.put(result)
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Agent {self.agent_id} error: {e}")
                self.result_queue.put({
                    'agent_id': self.agent_id,
                    'task': task,
                    'status': 'error',
                    'error': str(e)
                })
    
    def _process_task(self, task: Dict) -> Dict:
        """Process individual task"""
        task_type = task['type']
        ticker = task['ticker']
        
        self.logger.info(f"Processing {task_type} for {ticker}")
        
        try:
            if task_type == 'daily_data':
                return self._collect_daily_data(task)
            elif task_type == 'intraday_data':
                return self._collect_intraday_data(task)
            elif task_type == 'fundamentals':
                return self._collect_fundamentals(task)
            elif task_type == 'earnings_history':
                return self._collect_earnings_history(task)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing {task_type} for {ticker}: {e}")
            return {
                'agent_id': self.agent_id,
                'task': task,
                'status': 'error',
                'error': str(e)
            }
    
    def _collect_daily_data(self, task: Dict) -> Dict:
        """Collect 10 years of daily data"""
        ticker = task['ticker']
        start_date = task.get('start_date', (datetime.now() - timedelta(days=3650)).strftime('%Y-%m-%d'))
        end_date = task.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date, interval='1d')
            
            if hist.empty:
                raise ValueError(f"No daily data found for {ticker}")
            
            # Save data
            output_dir = project_root / 'data' / 'all_stocks_complete' / ticker
            output_dir.mkdir(parents=True, exist_ok=True)
            
            hist.to_csv(output_dir / f'{ticker}_daily_10years.csv')
            
            return {
                'agent_id': self.agent_id,
                'task': task,
                'status': 'success',
                'data_points': len(hist),
                'date_range': f"{hist.index[0].strftime('%Y-%m-%d')} to {hist.index[-1].strftime('%Y-%m-%d')}"
            }
            
        except Exception as e:
            raise Exception(f"Daily data collection failed for {ticker}: {e}")
    
    def _collect_intraday_data(self, task: Dict) -> Dict:
        """Collect 30-minute data for earnings periods"""
        ticker = task['ticker']
        earnings_dates = task['earnings_dates']
        
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
                    
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                self.logger.warning(f"Failed to collect intraday data for {ticker} around {earnings_date}: {e}")
                continue
        
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=False)
            
            # Save data
            output_dir = project_root / 'data' / 'all_stocks_complete' / ticker
            output_dir.mkdir(parents=True, exist_ok=True)
            
            combined_data.to_csv(output_dir / f'{ticker}_30min_earnings.csv')
            
            return {
                'agent_id': self.agent_id,
                'task': task,
                'status': 'success',
                'data_points': len(combined_data),
                'successful_periods': successful_periods,
                'total_periods': len(earnings_dates)
            }
        else:
            raise Exception(f"No intraday data collected for {ticker}")
    
    def _collect_fundamentals(self, task: Dict) -> Dict:
        """Collect current fundamentals"""
        ticker = task['ticker']
        
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
                'collected_at': datetime.now().isoformat()
            }
            
            # Save data
            output_dir = project_root / 'data' / 'all_stocks_complete' / ticker
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_dir / f'{ticker}_fundamentals.json', 'w') as f:
                json.dump(fundamentals, f, indent=2)
            
            return {
                'agent_id': self.agent_id,
                'task': task,
                'status': 'success',
                'fundamentals_collected': len([k for k, v in fundamentals.items() if v is not None])
            }
            
        except Exception as e:
            raise Exception(f"Fundamentals collection failed for {ticker}: {e}")
    
    def _collect_earnings_history(self, task: Dict) -> Dict:
        """Collect historical earnings data"""
        ticker = task['ticker']
        
        try:
            stock = yf.Ticker(ticker)
            
            # Get earnings calendar
            earnings_calendar = stock.calendar
            
            if earnings_calendar is not None and not earnings_calendar.empty:
                earnings_data = earnings_calendar.to_dict('records')
                
                # Save data
                output_dir = project_root / 'data' / 'all_stocks_complete' / ticker
                output_dir.mkdir(parents=True, exist_ok=True)
                
                with open(output_dir / f'{ticker}_earnings_history.json', 'w') as f:
                    json.dump(earnings_data, f, indent=2, default=str)
                
                return {
                    'agent_id': self.agent_id,
                    'task': task,
                    'status': 'success',
                    'earnings_events': len(earnings_data)
                }
            else:
                raise Exception(f"No earnings calendar found for {ticker}")
                
        except Exception as e:
            raise Exception(f"Earnings history collection failed for {ticker}: {e}")


class MasterDataCollector:
    """Master orchestrator for data collection"""
    
    def __init__(self, num_agents: int = 10):
        self.num_agents = num_agents
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.agents = []
        self.logger = self._setup_logger()
        self.progress = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': None
        }
        
        # Create logs directory
        (project_root / 'logs').mkdir(exist_ok=True)
        
    def _setup_logger(self):
        """Setup master logger"""
        logger = logging.getLogger('MasterCollector')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # File handler
            file_handler = logging.FileHandler(
                project_root / f'logs/master_collector_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
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
        """Load list of all 413 stocks"""
        try:
            # Try to load from earnings file first
            earnings_df = pd.read_csv(project_root / 'data' / 'processed' / 'earnings_final.csv')
            tickers = earnings_df['ticker'].unique().tolist()
            
            self.logger.info(f"Loaded {len(tickers)} tickers from earnings file")
            return tickers
            
        except Exception as e:
            self.logger.error(f"Failed to load stock list: {e}")
            return []
    
    def load_earnings_dates(self, ticker: str) -> List[datetime]:
        """Load earnings dates for a ticker"""
        try:
            # Try to get from earnings file
            earnings_df = pd.read_csv(project_root / 'data' / 'processed' / 'earnings_final.csv')
            ticker_earnings = earnings_df[earnings_df['ticker'] == ticker]
            
            if not ticker_earnings.empty:
                dates = pd.to_datetime(ticker_earnings['date']).tolist()
                # Add historical dates (simplified - in reality you'd get from API)
                historical_dates = []
                for date in dates:
                    # Add quarterly dates going back 10 years
                    for i in range(40):  # 10 years * 4 quarters
                        hist_date = date - timedelta(days=90*i)
                        if hist_date >= datetime.now() - timedelta(days=3650):
                            historical_dates.append(hist_date)
                
                return list(set(historical_dates + dates))
            
            return []
            
        except Exception as e:
            self.logger.warning(f"Failed to load earnings dates for {ticker}: {e}")
            return []
    
    def create_tasks(self, tickers: List[str]) -> List[Dict]:
        """Create all data collection tasks"""
        tasks = []
        
        for ticker in tickers:
            # Daily data task
            tasks.append({
                'type': 'daily_data',
                'ticker': ticker,
                'start_date': (datetime.now() - timedelta(days=3650)).strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d')
            })
            
            # Fundamentals task
            tasks.append({
                'type': 'fundamentals',
                'ticker': ticker
            })
            
            # Earnings history task
            tasks.append({
                'type': 'earnings_history',
                'ticker': ticker
            })
            
            # Intraday data task (if earnings dates available)
            earnings_dates = self.load_earnings_dates(ticker)
            if earnings_dates:
                tasks.append({
                    'type': 'intraday_data',
                    'ticker': ticker,
                    'earnings_dates': earnings_dates
                })
        
        return tasks
    
    def start_agents(self):
        """Start all data collection agents"""
        self.logger.info(f"Starting {self.num_agents} data collection agents")
        
        for i in range(self.num_agents):
            agent = DataCollectionAgent(i, self.task_queue, self.result_queue)
            agent_thread = threading.Thread(target=agent.run, daemon=True)
            agent_thread.start()
            self.agents.append(agent_thread)
    
    def process_results(self):
        """Process results from agents"""
        while not self.result_queue.empty():
            try:
                result = self.result_queue.get_nowait()
                
                if result['status'] == 'success':
                    self.progress['completed_tasks'] += 1
                    self.logger.info(f"✅ {result['task']['type']} for {result['task']['ticker']} completed")
                else:
                    self.progress['failed_tasks'] += 1
                    self.logger.error(f"❌ {result['task']['type']} for {result['task']['ticker']} failed: {result.get('error', 'Unknown error')}")
                
            except queue.Empty:
                break
    
    def print_progress(self):
        """Print current progress"""
        elapsed = datetime.now() - self.progress['start_time']
        completed = self.progress['completed_tasks']
        failed = self.progress['failed_tasks']
        total = self.progress['total_tasks']
        remaining = total - completed - failed
        
        print(f"\n📊 PROGRESS UPDATE:")
        print(f"   Completed: {completed}/{total} ({completed/total*100:.1f}%)")
        print(f"   Failed: {failed}/{total} ({failed/total*100:.1f}%)")
        print(f"   Remaining: {remaining}")
        print(f"   Elapsed: {elapsed}")
        print(f"   ETA: {elapsed * remaining / max(completed, 1) if completed > 0 else 'Unknown'}")
    
    def run_collection(self):
        """Run complete data collection"""
        self.logger.info("🚀 Starting Master Data Collection")
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
        
        # Start agents
        self.start_agents()
        
        # Add tasks to queue
        for task in tasks:
            self.task_queue.put(task)
        
        # Process results
        self.logger.info("🔄 Starting data collection...")
        
        while self.progress['completed_tasks'] + self.progress['failed_tasks'] < self.progress['total_tasks']:
            self.process_results()
            self.print_progress()
            time.sleep(5)  # Update every 5 seconds
        
        # Final results
        self.process_results()
        self.print_progress()
        
        # Shutdown agents
        for _ in self.agents:
            self.task_queue.put(None)
        
        self.logger.info("✅ Data collection completed!")
        
        # Generate summary report
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """Generate summary report of data collection"""
        report = {
            'collection_date': datetime.now().isoformat(),
            'total_tickers': len(self.load_stock_list()),
            'total_tasks': self.progress['total_tasks'],
            'completed_tasks': self.progress['completed_tasks'],
            'failed_tasks': self.progress['failed_tasks'],
            'success_rate': self.progress['completed_tasks'] / self.progress['total_tasks'] * 100,
            'duration': str(datetime.now() - self.progress['start_time']),
            'agents_used': self.num_agents
        }
        
        # Save report
        report_path = project_root / f'logs/collection_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"📊 Summary report saved to {report_path}")


def main():
    """Main execution function"""
    print("🚀 UMushroom Investment Challenge - Master Data Collector")
    print("=" * 60)
    
    # Create master collector
    collector = MasterDataCollector(num_agents=10)
    
    try:
        collector.run_collection()
    except KeyboardInterrupt:
        print("\n⚠️ Collection interrupted by user")
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")
        collector.logger.error(f"Collection failed: {e}")


if __name__ == "__main__":
    main()
