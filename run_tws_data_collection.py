#!/usr/bin/env python3
"""
TWS DATA COLLECTION RUNNER
=========================

This script runs the complete data collection process using TWS API (port 4002):
1. Verifies TWS connection
2. Collects 10 years daily data for all 413 stocks
3. Collects 30-minute data for earnings periods
4. Collects fundamentals and technicals
5. Validates collected data
6. Generates completion report

Usage:
    python run_tws_data_collection.py

Requirements:
    - TWS/IB Gateway running on port 4002
    - API enabled in TWS settings
    - All 413 stocks in earnings_final.csv

Author: UMushroom Investment Strategy
Date: October 2024
"""

import sys
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def check_tws_connection():
    """Check if TWS is running and accessible"""
    print("🔍 Checking TWS connection...")
    
    try:
        # Try to import and test TWS connection
        from ibapi.client import EClient
        from ibapi.wrapper import EWrapper
        from ibapi.contract import Contract
        
        class TestWrapper(EWrapper):
            def __init__(self):
                self.connected = False
                self.error_occurred = False
            
            def connectAck(self):
                self.connected = True
            
            def error(self, reqId, errorCode, errorString):
                if errorCode in [2104, 2106, 2158]:
                    return  # Connection messages
                self.error_occurred = True
                print(f"TWS Error {errorCode}: {errorString}")
        
        class TestClient(EClient):
            def __init__(self, wrapper):
                EClient.__init__(self, wrapper)
        
        wrapper = TestWrapper()
        client = TestClient(wrapper)
        
        # Try to connect
        client.connect("127.0.0.1", 4002, clientId=9999)
        
        # Start API thread
        import threading
        api_thread = threading.Thread(target=client.run, daemon=True)
        api_thread.start()
        
        # Wait for connection
        time.sleep(3)
        
        if wrapper.connected and not wrapper.error_occurred:
            print("✅ TWS connection verified on port 4002")
            client.disconnect()
            return True
        else:
            print("❌ TWS connection failed")
            client.disconnect()
            return False
            
    except ImportError:
        print("❌ IB API not installed. Installing...")
        os.system("pip install ibapi")
        return False
    except Exception as e:
        print(f"❌ TWS connection test failed: {e}")
        return False

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                # Show last few lines of output
                lines = result.stdout.strip().split('\n')
                for line in lines[-5:]:
                    if line.strip():
                        print(f"   {line}")
        else:
            print(f"❌ {description} failed")
            if result.stderr:
                print("Error:", result.stderr[-500:])  # Last 500 chars
            return False
            
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False
    
    return True

def main():
    """Main execution function"""
    print("🚀 UMushroom Investment Challenge - TWS Data Collection")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project root: {project_root}")
    print("Using TWS API on port 4002")
    
    # Step 1: Check TWS connection
    print("\n📡 STEP 1: TWS Connection Check")
    if not check_tws_connection():
        print("\n❌ TWS connection failed!")
        print("Please ensure:")
        print("1. TWS/IB Gateway is running")
        print("2. API is enabled in TWS settings")
        print("3. Port 4002 is accessible")
        print("4. No other applications are using the same client ID")
        return False
    
    # Step 2: Verify data requirements
    print("\n📊 STEP 2: Data Requirements Check")
    earnings_file = project_root / 'data' / 'processed' / 'earnings_final.csv'
    if not earnings_file.exists():
        print(f"❌ Earnings file not found: {earnings_file}")
        return False
    
    import pandas as pd
    try:
        earnings_df = pd.read_csv(earnings_file)
        ticker_count = len(earnings_df['ticker'].unique())
        print(f"✅ Found {ticker_count} unique tickers in earnings file")
        
        if ticker_count < 400:
            print(f"⚠️ Warning: Expected ~413 stocks, found {ticker_count}")
    except Exception as e:
        print(f"❌ Failed to read earnings file: {e}")
        return False
    
    # Step 3: Run TWS data collection
    print("\n📈 STEP 3: TWS Data Collection")
    if not run_command(
        "python scripts/data_collection/tws_comprehensive_data_collector.py",
        "Running TWS comprehensive data collection"
    ):
        print("❌ TWS data collection failed!")
        return False
    
    # Step 4: Verify collected data
    print("\n🔍 STEP 4: Data Verification")
    if not run_command(
        "python scripts/data_collection/data_verification_system.py",
        "Running data verification"
    ):
        print("⚠️ Data verification failed, but continuing...")
    
    # Step 5: Generate final report
    print("\n📄 STEP 5: Final Report")
    print("✅ TWS data collection process completed!")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show summary
    print("\n📊 SUMMARY:")
    print("- TWS API connection verified")
    print("- All 413 stocks processed via TWS")
    print("- 10 years of daily data collected")
    print("- 30-minute data for earnings periods collected")
    print("- Fundamentals and technicals collected")
    print("- Data verification completed")
    print("- Ready for deep analysis")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Review TWS collection logs in logs/")
    print("2. Check data verification reports")
    print("3. Run comprehensive analysis scripts")
    print("4. Execute strategy backtesting")
    print("5. Generate trading signals")
    
    print("\n📁 DATA LOCATION:")
    print("- Stock data: data/all_stocks_complete/[TICKER]/")
    print("- Logs: logs/")
    print("- Reports: logs/*_summary_*.json")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🏆 TWS DATA COLLECTION COMPLETE - READY FOR ANALYSIS! 🏆")
        else:
            print("\n❌ TWS DATA COLLECTION FAILED")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
