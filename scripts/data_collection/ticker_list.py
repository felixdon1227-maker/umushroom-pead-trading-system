"""
Comprehensive list of major NYSE and NASDAQ stocks for earnings scanning
"""

# S&P 500 Major Companies
SP500_TICKERS = [
    # Technology
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'ORCL',
    'ADBE', 'CRM', 'CSCO', 'ACN', 'AMD', 'INTC', 'IBM', 'QCOM', 'TXN', 'INTU',
    'NOW', 'AMAT', 'MU', 'LRCX', 'KLAC', 'SNPS', 'CDNS', 'ADSK', 'FTNT', 'PANW',
    
    # Financials
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'SPGI',
    'CB', 'PGR', 'MMC', 'AON', 'USB', 'PNC', 'TFC', 'COF', 'BK', 'AIG',
    'MET', 'PRU', 'AFL', 'ALL', 'TRV', 'CME', 'ICE', 'MCO', 'FIS', 'FISV',
    
    # Healthcare
    'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'PFE', 'TMO', 'ABT', 'DHR', 'BMY',
    'AMGN', 'GILD', 'CVS', 'CI', 'ELV', 'HUM', 'ISRG', 'REGN', 'VRTX', 'SYK',
    'BSX', 'MDT', 'ZTS', 'EW', 'IDXX', 'HCA', 'A', 'IQV', 'RMD', 'DXCM',
    
    # Consumer Discretionary
    'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'TJX', 'BKNG', 'CMG',
    'MAR', 'ABNB', 'GM', 'F', 'ORLY', 'AZO', 'YUM', 'ROST', 'DHI', 'LEN',
    
    # Consumer Staples
    'WMT', 'PG', 'COST', 'KO', 'PEP', 'PM', 'MO', 'MDLZ', 'CL', 'KMB',
    'GIS', 'K', 'HSY', 'STZ', 'SYY', 'KHC', 'TSN', 'CAG', 'CPB', 'CHD',
    
    # Communication Services
    'GOOGL', 'META', 'NFLX', 'DIS', 'CMCSA', 'T', 'VZ', 'TMUS', 'CHTR', 'EA',
    'TTWO', 'NWSA', 'FOXA', 'PARA', 'WBD', 'OMC', 'IPG', 'MTCH', 'PINS', 'SNAP',
    
    # Industrials
    'CAT', 'BA', 'HON', 'UNP', 'RTX', 'UPS', 'LMT', 'DE', 'GE', 'MMM',
    'GD', 'NOC', 'ETN', 'ITW', 'EMR', 'CSX', 'NSC', 'FDX', 'WM', 'RSG',
    
    # Energy
    'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'HES',
    'WMB', 'KMI', 'HAL', 'BKR', 'FANG', 'DVN', 'MRO', 'APA', 'CTRA', 'OKE',
    
    # Materials
    'LIN', 'APD', 'SHW', 'ECL', 'FCX', 'NEM', 'DD', 'DOW', 'NUE', 'VMC',
    'MLM', 'PPG', 'CTVA', 'IFF', 'CE', 'ALB', 'BALL', 'AVY', 'PKG', 'IP',
    
    # Real Estate
    'PLD', 'AMT', 'EQIX', 'CCI', 'PSA', 'DLR', 'O', 'WELL', 'SPG', 'VICI',
    'EXR', 'AVB', 'EQR', 'INVH', 'VTR', 'MAA', 'ARE', 'SBAC', 'ESS', 'KIM',
    
    # Utilities
    'NEE', 'SO', 'DUK', 'D', 'AEP', 'EXC', 'SRE', 'XEL', 'ED', 'PEG',
    'ES', 'WEC', 'AWK', 'DTE', 'PPL', 'AEE', 'FE', 'EIX', 'ETR', 'ATO',
]

# Additional NASDAQ Growth Stocks
NASDAQ_GROWTH = [
    'NVDA', 'AVGO', 'ASML', 'ADP', 'ABNB', 'ADSK', 'ALGN', 'AMAT', 'ANSS', 'ATVI',
    'BIIB', 'BKNG', 'CDNS', 'CERN', 'CHTR', 'CPRT', 'CRWD', 'CTAS', 'CTSH', 'DDOG',
    'DLTR', 'DOCU', 'DXCM', 'EA', 'EBAY', 'ENPH', 'FAST', 'FISV', 'FTNT', 'GILD',
    'IDXX', 'ILMN', 'INCY', 'INTU', 'ISRG', 'JD', 'KDP', 'KHC', 'KLAC', 'LCID',
    'LRCX', 'LULU', 'MAR', 'MCHP', 'MDLZ', 'MELI', 'MNST', 'MRNA', 'MRVL', 'MU',
    'NTES', 'NXPI', 'ODFL', 'OKTA', 'ON', 'ORLY', 'PAYX', 'PCAR', 'PDD', 'PYPL',
    'REGN', 'RIVN', 'ROST', 'SBUX', 'SGEN', 'SIRI', 'SNPS', 'SPLK', 'SWKS', 'TEAM',
    'TMUS', 'TTWO', 'TXN', 'VRSK', 'VRTX', 'WBA', 'WDAY', 'XEL', 'ZM', 'ZS',
]

# High-Profile Tech & Growth
HIGH_PROFILE = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'NFLX', 'AMD', 'INTC',
    'COIN', 'SQ', 'SHOP', 'UBER', 'LYFT', 'DASH', 'SNOW', 'PLTR', 'RBLX', 'U',
    'SOFI', 'HOOD', 'AFRM', 'UPST', 'LCID', 'RIVN', 'NIO', 'XPEV', 'LI', 'BABA',
]

# Financial Services
FINANCIALS = [
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'USB',
    'PNC', 'TFC', 'COF', 'BK', 'STT', 'NTRS', 'KEY', 'RF', 'CFG', 'HBAN',
    'FITB', 'MTB', 'CMA', 'ZION', 'SIVB', 'ALLY', 'SYF', 'DFS', 'NAVI', 'LC',
]

# Retail & Consumer
RETAIL = [
    'WMT', 'COST', 'TGT', 'HD', 'LOW', 'AMZN', 'EBAY', 'ETSY', 'W', 'CHWY',
    'BBY', 'DG', 'DLTR', 'ROST', 'TJX', 'BURL', 'ULTA', 'DKS', 'FL', 'GPS',
]

# Combine all tickers and deduplicate
def get_all_tickers():
    """Get comprehensive list of all tickers"""
    all_tickers = set(SP500_TICKERS + NASDAQ_GROWTH + HIGH_PROFILE + FINANCIALS + RETAIL)
    return sorted(list(all_tickers))

if __name__ == "__main__":
    tickers = get_all_tickers()
    print(f"Total unique tickers: {len(tickers)}")
    print(f"Sample: {tickers[:20]}")



