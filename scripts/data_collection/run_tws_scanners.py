"""
TWS API Multiple Scanner Runner
Runs all available scanners to get comprehensive stock list

Author: UMushroom Competition Strategy
Date: October 2024
"""

import pandas as pd
import time
import sys
import os
import threading

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tws_connector import TWSConnector
from ibapi.scanner import ScannerSubscription
from ibapi.tag_value import TagValue

class MultiScanner(TWSConnector):
    """Run multiple TWS scanners to get comprehensive stock list"""
    
    def __init__(self):
        super().__init__()
        self.scanner_results = {}
        self.scanner_data_ready = threading.Event()
        
    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        """Callback for scanner data"""
        if reqId not in self.scanner_results:
            self.scanner_results[reqId] = []
            
        self.scanner_results[reqId].append({
            'rank': rank,
            'symbol': contractDetails.contract.symbol,
            'exchange': contractDetails.contract.primaryExchange,
            'currency': contractDetails.contract.currency,
        })
        
    def scannerDataEnd(self, reqId):
        """Called when scanner data is complete"""
        self.scanner_data_ready.set()
        
    def run_scanner(self, scan_code, req_id, num_rows=1000):
        """Run a single scanner"""
        print(f"\n  Running {scan_code} scanner...")
        
        scan_sub = ScannerSubscription()
        scan_sub.instrument = "STK"
        scan_sub.locationCode = "STK.US.MAJOR"
        scan_sub.scanCode = scan_code
        scan_sub.numberOfRows = num_rows
        
        # Basic filter - just price above $5 to avoid penny stocks
        filter_options = [
            TagValue("priceAbove", "5")
        ]
        
        self.scanner_data_ready.clear()
        
        try:
            self.reqScannerSubscription(req_id, scan_sub, [], filter_options)
            
            if self.scanner_data_ready.wait(timeout=30):
                results = self.scanner_results.get(req_id, [])
                print(f"    ✅ Found {len(results)} stocks")
                return results
            else:
                print(f"    ⚠️ Timeout")
                return []
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return []
    
    def run_all_scanners(self):
        """Run all available scanners"""
        print("=" * 80)
        print("🔍 RUNNING ALL TWS SCANNERS")
        print("=" * 80)
        
        scanners = [
            ("TOP_MARKET_CAP", 1),
            ("TOP_VOLUME_RATE", 2),
            ("MOST_ACTIVE", 3),
            ("HOT_BY_VOLUME", 4),
            ("TOP_PERC_GAIN", 5),
            ("TOP_PERC_LOSE", 6),
            ("HOT_BY_PRICE", 7),
            ("TOP_TRADE_COUNT", 8),
        ]
        
        all_stocks = []
        
        for scan_code, req_id in scanners:
            results = self.run_scanner(scan_code, req_id, num_rows=1000)
            all_stocks.extend(results)
            time.sleep(1)  # Rate limiting between scanners
        
        # Convert to DataFrame and deduplicate
        df = pd.DataFrame(all_stocks)
        
        if len(df) > 0:
            print(f"\n  Total results before dedup: {len(df)}")
            
            # Remove duplicates
            df = df.drop_duplicates(subset=['symbol'])
            print(f"  After dedup: {len(df)}")
            
            # Check what exchanges we have
            if 'exchange' in df.columns:
                print(f"  Exchanges found: {df['exchange'].unique()}")
                # Keep all exchanges for now
                # df = df[df['exchange'].isin(['NYSE', 'NASDAQ', 'ARCA', 'ISLAND', 'AMEX'])]
            
            print(f"\n" + "=" * 80)
            print(f"✅ TOTAL UNIQUE STOCKS: {len(df)}")
            print("=" * 80)
            
            return df
        else:
            print("\n❌ No stocks found!")
            return pd.DataFrame()
    
    def save_results(self, df):
        """Save results to CSV"""
        if len(df) == 0:
            print("No data to save")
            return
            
        output_dir = '/home/fellaki10/Documents/UMushroom Investment challange/data/scanner_results'
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = f'{output_dir}/tws_scanner_tickers.csv'
        df.to_csv(output_file, index=False)
        
        print(f"\n💾 Saved {len(df)} tickers to: {output_file}")
        
        # Also save just ticker list
        ticker_file = f'{output_dir}/ticker_list.txt'
        with open(ticker_file, 'w') as f:
            for ticker in sorted(df['symbol'].tolist()):
                f.write(f"{ticker}\n")
        
        print(f"💾 Saved ticker list to: {ticker_file}")
        
        # Print summary
        print(f"\n📊 SUMMARY:")
        print(f"  Total tickers: {len(df)}")
        print(f"  NYSE: {len(df[df['exchange']=='NYSE'])}")
        print(f"  NASDAQ: {len(df[df['exchange']=='NASDAQ'])}")
        
        print(f"\n🏆 Sample tickers:")
        for ticker in df['symbol'].head(20).tolist():
            print(f"  {ticker}")

def main():
    """Main execution"""
    scanner = MultiScanner()
    
    try:
        # Connect to TWS
        print("🔌 Connecting to TWS...")
        scanner.connect("127.0.0.1", 4002, 888)
        
        # Start socket thread
        api_thread = threading.Thread(target=scanner.run, daemon=True)
        api_thread.start()
        
        # Wait for connection
        if not scanner.connection_ready.wait(timeout=10):
            print("❌ Failed to connect to TWS")
            return
        
        print("✅ Connected to TWS!")
        
        # Run all scanners
        results_df = scanner.run_all_scanners()
        
        # Save results
        if len(results_df) > 0:
            scanner.save_results(results_df)
        
        print("\n✅ COMPLETE! Pass the ticker list to me for filtering.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scanner.disconnect()
        print("\n🔌 Disconnected from TWS")

if __name__ == "__main__":
    main()

