from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
import threading
import time
from datetime import datetime, timedelta
import pandas as pd
import xml.etree.ElementTree as ET

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
    
    def get_fundamental_data(self, symbol, report_type='RESC'):
        """
        Get fundamental data from TWS
        
        Parameters:
        - symbol: Stock ticker
        - report_type: Type of report
            'ReportsFinSummary' - Financial summary
            'ReportSnapshot' - Company snapshot
            'RESC' - Analyst estimates (EPS, revenue)
            'ReportsFinStatements' - Financial statements
        
        Returns:
        - XML string with fundamental data
        """
        contract = self.create_stock_contract(symbol)
        reqId = len(self.fundamental_data) + 1000
        
        self.data_ready.clear()
        self.reqFundamentalData(reqId, contract, report_type, [])
        
        # Wait for data with timeout
        if self.data_ready.wait(timeout=10):
            return self.fundamental_data.get(reqId, None)
        return None
    
    def parse_fundamental_xml(self, xml_data):
        """
        Parse TWS fundamental data XML
        
        Returns dict with:
        - eps_estimate: Current quarter EPS estimate
        - revenue_estimate: Current quarter revenue estimate
        - analyst_count: Number of analysts
        - earnings_date: Next earnings date
        """
        if not xml_data:
            return {}
        
        try:
            root = ET.fromstring(xml_data)
            result = {}
            
            # Try to find EPS estimates
            for elem in root.iter():
                if 'EPSEstimate' in elem.tag or 'epsEstimate' in elem.tag:
                    result['eps_estimate'] = float(elem.text) if elem.text else None
                elif 'RevenueEstimate' in elem.tag or 'revenueEstimate' in elem.tag:
                    result['revenue_estimate'] = float(elem.text) if elem.text else None
                elif 'AnalystCount' in elem.tag or 'analystCount' in elem.tag:
                    result['analyst_count'] = int(elem.text) if elem.text else None
                elif 'EarningsDate' in elem.tag or 'earningsDate' in elem.tag:
                    result['earnings_date'] = elem.text
            
            return result
        except Exception as e:
            print(f"Error parsing XML: {e}")
            return {}
    
    def get_earnings_estimates(self, symbol):
        """
        Get earnings estimates for a symbol
        
        Returns dict with EPS and revenue estimates
        """
        xml_data = self.get_fundamental_data(symbol, 'RESC')
        if xml_data:
            return self.parse_fundamental_xml(xml_data)
        return {}

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



