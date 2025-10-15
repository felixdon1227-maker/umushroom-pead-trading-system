#!/usr/bin/env python3
"""
Instant Data Collector - Maximum Speed
"""

import yfinance as yf
import pandas as pd
import json
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class InstantDataCollector:
    def __init__(self):
        self.collected = 0
        self.failed = 0
        self.lock = threading.Lock()
        os.makedirs('data/instant_collection', exist_ok=True)
    
    def get_stocks(self):
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B', 'UNH', 'JNJ',
            'V', 'PG', 'JPM', 'XOM', 'HD', 'CVX', 'MA', 'PFE', 'ABBV', 'BAC',
            'KO', 'AVGO', 'PEP', 'TMO', 'COST', 'WMT', 'DHR', 'VZ', 'ADBE', 'ACN',
            'NFLX', 'CRM', 'TXN', 'NKE', 'QCOM', 'LIN', 'ABT', 'NEE', 'PM', 'RTX',
            'HON', 'UNP', 'LOW', 'SPGI', 'INTU', 'GS', 'CAT', 'AXP', 'BKNG', 'DE',
            'ISRG', 'SYK', 'BLK', 'TJX', 'GILD', 'CVS', 'MDT', 'CI', 'ANTM', 'SO',
            'DUK', 'PLD', 'CMCSA', 'FIS', 'ICE', 'SHW', 'ITW', 'MMM', 'EMR', 'ECL',
            'APD', 'CL', 'AON', 'PGR', 'ALL', 'AEP', 'EXC', 'XEL', 'WEC', 'ES',
            'ETR', 'FE', 'AEE', 'CNP', 'ED', 'EIX', 'EXR', 'PEG', 'SRE', 'WTRG',
            'AMD', 'INTC', 'ORCL', 'CSCO', 'IBM', 'UBER', 'LYFT', 'SNAP', 'SQ',
            'PYPL', 'SHOP', 'ZM', 'ROKU', 'PTON', 'DOCU', 'CRWD', 'OKTA', 'SNOW', 'PLTR',
            'RBLX', 'COIN', 'HOOD', 'SOFI', 'AFRM', 'UPST', 'ABNB', 'DASH',
            'NIO', 'XPEV', 'LI', 'BABA', 'JD', 'PDD', 'BIDU', 'TME',
            'WFC', 'C', 'MS', 'COF', 'USB', 'PNC', 'TFC', 'FITB', 'HBAN', 'RF',
            'STT', 'NTRS', 'SCHW', 'ETFC', 'AMTD', 'ALLY', 'CFG', 'KEY', 'ZION',
            'MRK', 'BMY', 'AMGN', 'BIIB', 'REGN', 'VRTX', 'ILMN', 'MRNA', 'BNTX',
            'JAZZ', 'INCY', 'BMRN', 'GILD', 'BIIB', 'REGN', 'VRTX', 'ILMN',
            'INTC', 'CSCO', 'IBM', 'AMD', 'MRVL', 'AMAT', 'LRCX', 'KLAC', 'SNPS',
            'CDNS', 'ANSS', 'ADSK', 'INTU', 'NOW', 'WDAY', 'TEAM', 'ZM', 'DOCU',
            'COP', 'EOG', 'SLB', 'KMI', 'WMB', 'OKE', 'PSX', 'VLO', 'MPC', 'HES',
            'DVN', 'PXD', 'FANG', 'MRO', 'OXY', 'APA', 'NOV', 'HAL', 'FTI',
            'TGT', 'LOW', 'TJX', 'SBUX', 'MCD', 'KMB', 'CHD', 'CLX', 'GIS', 'K',
            'CPB', 'HSY', 'SJM', 'CAG', 'KHC', 'MDLZ', 'CL', 'PG', 'UL', 'NSRGY',
            'BA', 'CAT', 'GE', 'HON', 'MMM', 'UPS', 'FDX', 'LMT', 'NOC', 'GD',
            'TDG', 'EMR', 'ITW', 'PH', 'ETN', 'CMI', 'DE', 'CNHI', 'AGCO', 'TEX'
        ]
    
    def collect_stock(self, ticker):
        try:
            stock_dir = f'data/instant_collection/{ticker}'
            os.makedirs(stock_dir, exist_ok=True)
            
            stock = yf.Ticker(ticker)
            info = stock.info
            if not info:
                return {'ticker': ticker, 'status': 'failed'}
            
            hist = stock.history(period='2y', interval='1d')
            if hist.empty:
                return {'ticker': ticker, 'status': 'failed'}
            
            hist.to_csv(f'{stock_dir}/{ticker}_daily_2y.csv')
            
            fundamentals = {
                'symbol': info.get('symbol', ticker),
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', 'Unknown'),
                'pe_ratio': info.get('trailingPE', 0),
                'beta': info.get('beta', 1.0),
                'current_price': info.get('currentPrice', 0),
                'collected_at': datetime.now().isoformat()
            }
            
            with open(f'{stock_dir}/{ticker}_fundamentals.json', 'w') as f:
                json.dump(fundamentals, f, indent=2)
            
            with self.lock:
                self.collected += 1
            
            return {'ticker': ticker, 'status': 'success', 'bars': len(hist)}
            
        except Exception as e:
            with self.lock:
                self.failed += 1
            return {'ticker': ticker, 'status': 'failed', 'error': str(e)}
    
    def collect_all(self):
        print("🚀 INSTANT DATA COLLECTOR")
        print("=" * 40)
        
        stocks = self.get_stocks()
        print(f"Collecting {len(stocks)} stocks...")
        
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(self.collect_stock, stock): stock for stock in stocks}
            
            for future in as_completed(futures):
                stock = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if len(results) % 20 == 0:
                        elapsed = time.time() - start_time
                        rate = len(results) / elapsed
                        print(f"⚡ {len(results)}/{len(stocks)} ({rate:.1f} stocks/sec)")
                        
                except Exception as e:
                    results.append({'ticker': stock, 'status': 'failed', 'error': str(e)})
        
        elapsed = time.time() - start_time
        successful = [r for r in results if r['status'] == 'success']
        
        print(f"\n✅ COMPLETE in {elapsed:.1f} seconds!")
        print(f"Success: {len(successful)} stocks")
        print(f"Rate: {len(results)/elapsed:.1f} stocks/second")
        print(f"Data saved to: data/instant_collection/")
        
        return len(successful)

if __name__ == "__main__":
    collector = InstantDataCollector()
    success_count = collector.collect_all()
    
    if success_count > 0:
        print("\n🎉 READY FOR STRATEGY ANALYSIS!")
        print("Run: python3 scripts/analysis/three_step_earnings_strategy.py")
