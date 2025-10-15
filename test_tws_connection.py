#!/usr/bin/env python3
"""
TWS CONNECTION TEST
==================

Quick test to verify TWS API connection and basic functionality.

Usage:
    python test_tws_connection.py

Author: UMushroom Investment Strategy
Date: October 2024
"""

import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    from ibapi.common import BarData
except ImportError:
    print("❌ IB API not installed. Installing...")
    import os
    os.system("pip install ibapi")
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    from ibapi.common import BarData

class TWSConnectionTest(EWrapper, EClient):
    """Test TWS connection and basic functionality"""
    
    def __init__(self):
        EClient.__init__(self, self)
        self.connected = False
        self.data_received = False
        self.bars = []
        self.error_occurred = False
        self.error_message = ""
        
    def connectAck(self):
        """Connection acknowledged"""
        self.connected = True
        print("✅ TWS connection acknowledged")
    
    def error(self, reqId, errorCode, errorString):
        """Handle TWS errors"""
        if errorCode in [2104, 2106, 2158]:  # Connection messages
            print(f"ℹ️ TWS Info {errorCode}: {errorString}")
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
            'volume': bar.volume
        })
    
    def historicalDataEnd(self, reqId, start, end):
        """Handle end of historical data"""
        self.data_received = True
        print(f"✅ Received {len(self.bars)} bars of historical data")
    
    def test_connection(self, host="127.0.0.1", port=4002, client_id=9999):
        """Test TWS connection"""
        print(f"🔍 Testing TWS connection to {host}:{port} with client ID {client_id}")
        
        try:
            # Connect
            self.connect(host, port, clientId=client_id)
            
            # Start API thread
            api_thread = threading.Thread(target=self.run, daemon=True)
            api_thread.start()
            
            # Wait for connection
            print("⏳ Waiting for connection...")
            timeout = 10
            start_time = time.time()
            
            while not self.connected and not self.error_occurred:
                if time.time() - start_time > timeout:
                    print("❌ Connection timeout")
                    return False
                time.sleep(0.1)
            
            if self.error_occurred:
                print(f"❌ Connection failed: {self.error_message}")
                return False
            
            print("✅ TWS connection successful!")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed with exception: {e}")
            return False
    
    def test_historical_data(self, ticker="AAPL"):
        """Test historical data retrieval"""
        print(f"📊 Testing historical data retrieval for {ticker}")
        
        try:
            # Create contract
            contract = Contract()
            contract.symbol = ticker
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"
            
            # Request historical data (use UTC timezone)
            end_date = datetime.now().strftime("%Y%m%d %H:%M:%S UTC")
            duration = "1 Y"
            
            print(f"📈 Requesting 1 year of daily data for {ticker}")
            self.reqHistoricalData(
                reqId=1,
                contract=contract,
                endDateTime=end_date,
                durationStr=duration,
                barSizeSetting="1 day",
                whatToShow="TRADES",
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
            
            # Wait for data
            timeout = 30
            start_time = time.time()
            
            while not self.data_received and not self.error_occurred:
                if time.time() - start_time > timeout:
                    print("❌ Data request timeout")
                    return False
                time.sleep(0.1)
            
            if self.error_occurred:
                print(f"❌ Data request failed: {self.error_message}")
                return False
            
            if self.bars:
                print(f"✅ Successfully retrieved {len(self.bars)} bars")
                print(f"   Date range: {self.bars[0]['date']} to {self.bars[-1]['date']}")
                print(f"   Latest close: ${self.bars[-1]['close']}")
                return True
            else:
                print("❌ No data received")
                return False
                
        except Exception as e:
            print(f"❌ Historical data test failed: {e}")
            return False
    
    def disconnect_test(self):
        """Disconnect from TWS"""
        if self.connected:
            self.disconnect()
            print("✅ Disconnected from TWS")

def main():
    """Main test function"""
    print("🚀 TWS Connection Test")
    print("=" * 40)
    
    # Create test connection
    test_connection = TWSConnectionTest()
    
    try:
        # Test connection
        if not test_connection.test_connection():
            print("\n❌ TWS connection test failed!")
            print("\nTroubleshooting:")
            print("1. Ensure TWS/IB Gateway is running")
            print("2. Check API is enabled in TWS settings")
            print("3. Verify port 4002 is accessible")
            print("4. Check no other apps are using client ID 9999")
            return False
        
        # Test historical data
        if not test_connection.test_historical_data("AAPL"):
            print("\n❌ Historical data test failed!")
            print("This may indicate data subscription issues")
            return False
        
        print("\n✅ All tests passed!")
        print("TWS API is ready for data collection")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        return False
        
    finally:
        test_connection.disconnect_test()

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎯 Ready to run data collection!")
            print("Next step: python run_tws_data_collection.py")
        else:
            print("\n❌ TWS connection test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
