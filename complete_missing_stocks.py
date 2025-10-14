#!/usr/bin/env python3
"""
Complete data collection for missing stocks
"""

import pandas as pd
import sys
import os

# Add scripts directory to path
sys.path.insert(0, 'scripts/data_collection')

from historical_data_fetcher import connect_to_tws, PEADHistoricalAnalyzer
import time

print("=" * 80)
print("📥 COMPLETING DATA COLLECTION FOR MISSING STOCKS")
print("=" * 80)

# Load missing stocks
missing_file = 'data/processed/missing_stocks.csv'
if not os.path.exists(missing_file):
    print("❌ No missing stocks file found!")
    exit(1)

missing_df = pd.read_csv(missing_file)
missing_tickers = missing_df['ticker'].tolist()

print(f"\n✓ Found {len(missing_tickers)} stocks needing data collection:")
for ticker in missing_tickers:
    print(f"  - {ticker}")

# Connect to TWS
print("\n" + "=" * 80)
print("Step 1: Connecting to TWS on port 4002...")
print("=" * 80)
tws = connect_to_tws(port=4002, client_id=150)

if not tws:
    print("✗ Failed to connect. Make sure TWS/IB Gateway is running.")
    exit(1)

print("✓ Connected to TWS API")

time.sleep(2)

# Initialize analyzer
print("\nStep 2: Initializing analyzer...")
analyzer = PEADHistoricalAnalyzer(tws, 'data/processed/earnings_final.csv')

# Filter to only missing stocks
analyzer.df = analyzer.df[analyzer.df['ticker'].isin(missing_tickers)]

print(f"✓ Ready to process {len(missing_tickers)} stocks")

# Run collection
print("\n" + "=" * 80)
print("Step 3: Starting data collection...")
print("=" * 80)
print(f"Estimated time: ~{len(missing_tickers) * 0.7:.0f} minutes\n")

results = analyzer.analyze_all_stocks(limit=None)

print("\n" + "=" * 80)
print("✅ COLLECTION COMPLETE!")
print("=" * 80)
print(f"Stocks processed: {len(results)}/{len(missing_tickers)}")
print("=" * 80)

# Disconnect
tws.disconnect()

