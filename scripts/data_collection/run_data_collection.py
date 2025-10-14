from historical_data_fetcher import connect_to_tws, PEADHistoricalAnalyzer
import time

print("=" * 80)
print("FULL HISTORICAL PEAD DATA COLLECTION")
print("=" * 80)
print("Task: 10 years daily data + hourly data around earnings")
print("Stocks: 104 companies (>= $1B market cap, M&A exclusions applied)")
print("Estimated time: ~1.5 hours")
print("=" * 80)

# Connect to TWS
print("\nStep 1: Connecting to TWS on port 4002...")
tws = connect_to_tws(port=4002, client_id=25)

if not tws:
    print("✗ Failed to connect. Make sure TWS/IB Gateway is running.")
    exit(1)

time.sleep(2)

# Initialize analyzer
print("\nStep 2: Initializing analyzer...")
analyzer = PEADHistoricalAnalyzer(tws, '../../data/processed/earnings_final.csv')

print(f"✓ Found {len(analyzer.df['ticker'].unique())} stocks to process")

# Run full analysis
print("\nStep 3: Starting full data collection...")
print("=" * 80)

results = analyzer.analyze_all_stocks(limit=None)  # No limit = all stocks

print("\n" + "=" * 80)
print("✅ FULL COLLECTION COMPLETE!")
print("=" * 80)
print(f"Successfully processed: {len(results)} stocks")
print(f"\nData saved in: pead_historical_data/")
print("  - daily_prices/: 10 years daily data per stock")
print("  - hourly_prices/: Hourly data around recent earnings")
print("  - earnings_history/: Historical earnings with surprises")
print("  - collection_summary.csv: Summary of all collected data")

# Disconnect
tws.disconnect()

