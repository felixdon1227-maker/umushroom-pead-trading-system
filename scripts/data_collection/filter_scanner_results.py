"""
Filter TWS Scanner Results
Apply comprehensive filters to get final stock list for competition

Criteria:
- Earnings between Oct 16 - Nov 30, 2024
- Market cap > $1 billion  
- Volume > 100,000 shares/day
- Exclude Friday earnings
- Exclude acquisitions/negative events
- NYSE or NASDAQ only (exclude ETFs)

Author: UMushroom Competition Strategy  
Date: October 2024
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from tqdm import tqdm
import time

def is_etf(ticker):
    """Check if ticker is an ETF"""
    etf_indicators = ['SQQQ', 'TQQQ', 'SOXL', 'SPY', 'QQQ', 'IWM', 'GLD', 'SLV', 
                      'FXI', 'GDX', 'UNG', 'BOIL', 'DUST', 'NUGT', 'BITI', 'BITX',
                      'TNA', 'TZA', 'TMV', 'AGQ', 'FEZ', 'IAU', 'GLDM', 'IBIT',
                      'NVDX', 'NVDL', 'NVDD', 'NVDS', 'AMDL', 'AMDD', 'TSLL', 'TSLQ',
                      'MSTZ', 'MSTX', 'MSTW', 'MSDD', 'MSTP', 'BITF', 'BITU',
                      'QID', 'ETHA', 'ETHT', 'ETHU', 'SETH', 'PLTW', 'HOOW',
                      'UVIX', 'UVXY', 'YANG', 'YINN', 'YMAG', 'YMAX', 'UGL',
                      'PALL', 'SIL', 'ZSL', 'GLL', 'GDXU', 'BIL', 'VTEB',
                      'BOXX', 'ULTY', 'SOLT', 'SOLZ', 'SDOT', 'XXRP', 'DOJE',
                      'MEME', 'SPYI', 'OKLL', 'BULL', 'BMNU', 'BMNR', 'USAR',
                      'CONL', 'CONI', 'LABX', 'ALAB', 'HOND', 'HOOW', 'GOOX',
                      'BABX', 'NFXS', 'LITM']
    
    return ticker in etf_indicators or len(ticker) == 4 and ticker.endswith('X')

def filter_tickers(ticker_file):
    """Filter tickers based on all criteria"""
    
    print("=" * 80)
    print("🔍 FILTERING TWS SCANNER RESULTS")
    print("=" * 80)
    
    # Load tickers
    with open(ticker_file, 'r') as f:
        all_tickers = [line.strip() for line in f if line.strip()]
    
    print(f"\n📋 Starting with {len(all_tickers)} tickers from TWS scanners")
    
    # Remove ETFs
    stock_tickers = [t for t in all_tickers if not is_etf(t)]
    print(f"  After removing ETFs: {len(stock_tickers)} tickers")
    
    # Filter stocks
    qualified_stocks = []
    
    start_date = pd.to_datetime('2024-10-16')
    end_date = pd.to_datetime('2024-11-30')
    
    print(f"\n🔍 Screening {len(stock_tickers)} stocks...")
    
    for ticker in tqdm(stock_tickers, desc="Filtering stocks"):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Basic criteria
            market_cap = info.get('marketCap', 0)
            volume = info.get('averageVolume', info.get('volume', 0))
            price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            exchange = info.get('exchange', '')
            sector = info.get('sector', 'Other')
            long_name = info.get('longName', '')
            
            # Skip if doesn't meet basic criteria
            if market_cap < 1_000_000_000:  # $1B+
                continue
            if volume < 100_000:  # 100K+
                continue
            if price < 5 or price > 2000:  # Reasonable price range
                continue
            if exchange not in ['NYQ', 'NMS', 'NYSE', 'NASDAQ']:
                continue
                
            # Check for negative events
            negative_keywords = ['acquisition', 'merger', 'bankruptcy', 'delisting', 'suspension']
            if any(keyword in long_name.lower() for keyword in negative_keywords):
                continue
            
            # Check earnings date
            try:
                calendar = stock.calendar
                if calendar is not None and 'Earnings Date' in calendar.index:
                    earnings_date = calendar.loc['Earnings Date']
                    
                    if isinstance(earnings_date, pd.Series):
                        earnings_date = earnings_date.iloc[0]
                    
                    if isinstance(earnings_date, str):
                        earnings_date = pd.to_datetime(earnings_date)
                    
                    # Check if within our date range
                    if start_date <= earnings_date <= end_date:
                        # Check if not Friday
                        if earnings_date.weekday() != 4:  # 4 = Friday
                            qualified_stocks.append({
                                'ticker': ticker,
                                'earnings_date': earnings_date.strftime('%Y-%m-%d'),
                                'day_of_week': earnings_date.strftime('%A'),
                                'market_cap': market_cap,
                                'volume': volume,
                                'price': price,
                                'exchange': exchange,
                                'sector': sector,
                                'long_name': long_name
                            })
            except:
                pass
            
            time.sleep(0.05)  # Rate limiting
            
        except Exception as e:
            continue
    
    return pd.DataFrame(qualified_stocks)

def save_results(df):
    """Save filtered results"""
    if len(df) == 0:
        print("\n❌ No stocks found meeting criteria!")
        return
    
    # Sort by market cap
    df = df.sort_values('market_cap', ascending=False)
    
    # Save to CSV
    output_file = '/home/fellaki10/Documents/UMushroom Investment challange/data/scanner_results/filtered_earnings_stocks.csv'
    df.to_csv(output_file, index=False)
    
    print(f"\n" + "=" * 80)
    print(f"✅ FOUND {len(df)} QUALIFIED STOCKS")
    print("=" * 80)
    
    print(f"\n💾 Saved to: {output_file}")
    
    # Print summary
    print(f"\n📊 SUMMARY:")
    print(f"  Total stocks: {len(df)}")
    print(f"  Average market cap: ${df['market_cap'].mean()/1e9:.1f}B")
    print(f"  Average volume: {df['volume'].mean()/1e6:.1f}M shares/day")
    print(f"  Price range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")
    
    print(f"\n📅 Earnings Distribution:")
    day_counts = df['day_of_week'].value_counts()
    for day, count in day_counts.items():
        print(f"  {day}: {count}")
    
    print(f"\n📈 Sector Distribution:")
    sector_counts = df['sector'].value_counts().head(10)
    for sector, count in sector_counts.items():
        print(f"  {sector}: {count}")
    
    print(f"\n🏆 Top 20 Stocks by Market Cap:")
    for i, (idx, row) in enumerate(df.head(20).iterrows(), 1):
        print(f"  {i:2d}. {row['ticker']:6s} - ${row['market_cap']/1e9:>6.1f}B - {row['earnings_date']} ({row['day_of_week']})")
    
    # Save ticker list
    ticker_file = '/home/fellaki10/Documents/UMushroom Investment challange/data/scanner_results/qualified_tickers.txt'
    with open(ticker_file, 'w') as f:
        for ticker in df['ticker'].tolist():
            f.write(f"{ticker}\n")
    print(f"\n💾 Saved ticker list to: {ticker_file}")

def main():
    """Main execution"""
    ticker_file = '/home/fellaki10/Documents/UMushroom Investment challange/data/scanner_results/ticker_list.txt'
    
    # Filter stocks
    results_df = filter_tickers(ticker_file)
    
    # Save results
    save_results(results_df)
    
    print("\n✅ FILTERING COMPLETE!")

if __name__ == "__main__":
    main()

