from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
import threading
import time
from datetime import datetime, timedelta
import pandas as pd

class TWSConnector(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.nextOrderId = None
        self.positions = {}
        self.account_summary = {}
        self.market_data = {}
        self.contract_details = {}
        self.fundamental_data = {}
        self.data_ready = threading.Event()
        self.connection_ready = threading.Event()
        
    def error(self, reqId, errorCode, errorString):
        """Error handling"""
        if errorCode == 502:
            print(f"⚠️  Warning: {errorString}")
        elif errorCode == 2104 or errorCode == 2106 or errorCode == 2158:
            # Market data farm connection messages - informational
            pass
        else:
            print(f"Error {errorCode}: {errorString}")
        
    def nextValidId(self, orderId):
        """Callback when connection is established"""
        super().nextValidId(orderId)
        self.nextOrderId = orderId
        self.connection_ready.set()
        print(f"✓ Connected to TWS API. Next Order ID: {orderId}")
        
    def position(self, account, contract, position, avgCost):
        """Callback for position updates"""
        self.positions[contract.symbol] = {
            'symbol': contract.symbol,
            'position': position,
            'avgCost': avgCost,
            'value': position * avgCost
        }
        
    def positionEnd(self):
        """Called when all positions have been received"""
        print(f"✓ Received {len(self.positions)} positions")
        
    def accountSummary(self, reqId, account, tag, value, currency):
        """Callback for account summary"""
        self.account_summary[tag] = value
        
    def accountSummaryEnd(self, reqId):
        """Called when account summary is complete"""
        print("✓ Account summary received")
        
    def tickPrice(self, reqId, tickType, price, attrib):
        """Callback for price data"""
        if reqId not in self.market_data:
            self.market_data[reqId] = {}
        
        if tickType == 1:  # BID
            self.market_data[reqId]['bid'] = price
        elif tickType == 2:  # ASK
            self.market_data[reqId]['ask'] = price
        elif tickType == 4:  # LAST
            self.market_data[reqId]['last'] = price
            
    def tickSize(self, reqId, tickType, size):
        """Callback for size data"""
        if reqId not in self.market_data:
            self.market_data[reqId] = {}
            
        if tickType == 0:  # BID_SIZE
            self.market_data[reqId]['bid_size'] = size
        elif tickType == 3:  # ASK_SIZE
            self.market_data[reqId]['ask_size'] = size
        elif tickType == 5:  # LAST_SIZE
            self.market_data[reqId]['last_size'] = size
        elif tickType == 8:  # VOLUME
            self.market_data[reqId]['volume'] = size
            
    def contractDetails(self, reqId, contractDetails):
        """Callback for contract details"""
        self.contract_details[reqId] = contractDetails
        
    def contractDetailsEnd(self, reqId):
        """Called when contract details are complete"""
        self.data_ready.set()
        
    def fundamentalData(self, reqId, data):
        """Callback for fundamental data (includes earnings dates)"""
        self.fundamental_data[reqId] = data
        self.data_ready.set()
        
    def create_stock_contract(self, symbol, exchange="SMART", currency="USD"):
        """Create a stock contract"""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency
        return contract
    
    def get_current_price(self, symbol):
        """Get current market price for a symbol"""
        contract = self.create_stock_contract(symbol)
        reqId = len(self.market_data) + 1
        
        self.reqMktData(reqId, contract, "", False, False, [])
        time.sleep(2)  # Wait for data
        self.cancelMktData(reqId)
        
        if reqId in self.market_data and 'last' in self.market_data[reqId]:
            return self.market_data[reqId]['last']
        return None
    
    def get_account_value(self):
        """Get total account value"""
        self.reqAccountSummary(9001, "All", "NetLiquidation")
        time.sleep(2)
        self.cancelAccountSummary(9001)
        
        return float(self.account_summary.get('NetLiquidation', 0))
    
    def get_positions(self):
        """Get all current positions"""
        self.positions = {}
        self.reqPositions()
        time.sleep(2)
        self.cancelPositions()
        return self.positions

def connect_to_tws(port=4002, client_id=1):
    """Connect to TWS API"""
    app = TWSConnector()
    
    try:
        app.connect("127.0.0.1", port, clientId=client_id)
        
        # Start the socket in a thread
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        
        # Wait for connection with timeout
        if app.connection_ready.wait(timeout=10):
            print(f"✓ Successfully connected to TWS on port {port}")
            return app
        else:
            print(f"✗ Connection timeout - TWS may not be running on port {port}")
            return None
            
    except Exception as e:
        print(f"✗ Failed to connect to TWS: {e}")
        print(f"   Make sure TWS or IB Gateway is running on port {port}")
        return None

if __name__ == "__main__":
    # Test connection
    tws = connect_to_tws(port=4002)
    
    if tws:
        print("\n=== Testing Connection ===")
        
        # Test getting a price
        print("\nTesting market data...")
        price = tws.get_current_price("AAPL")
        if price:
            print(f"AAPL Price: ${price:.2f}")
        
        time.sleep(2)
        tws.disconnect()
        print("\n✓ Connection test complete")



