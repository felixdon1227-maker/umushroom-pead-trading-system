#!/usr/bin/env python3
import pandas as pd
import numpy as np
import json
import os

# Quick analysis of collected data
data_dir = 'data/instant_collection'
stock_dirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
print(f'📊 Found {len(stock_dirs)} stock directories')

# Load fundamentals
fundamentals = []
for ticker in stock_dirs:
    fundamentals_file = os.path.join(data_dir, ticker, f'{ticker}_fundamentals.json')
    if os.path.exists(fundamentals_file):
        with open(fundamentals_file, 'r') as f:
            data = json.load(f)
            fundamentals.append(data)

print(f'✅ Loaded {len(fundamentals)} stocks with fundamentals')

# Create DataFrame
df = pd.DataFrame(fundamentals)

# Basic analysis
print(f'\n📈 SECTOR DISTRIBUTION:')
print(df['sector'].value_counts().head(10))

print(f'\n💰 MARKET CAP RANGES:')
df['cap_billions'] = df['market_cap'] / 1e9
print(f'Large Cap (>$100B): {len(df[df["cap_billions"] > 100])} stocks')
print(f'Mid Cap ($10B-$100B): {len(df[(df["cap_billions"] >= 10) & (df["cap_billions"] <= 100)])} stocks')
print(f'Small Cap (<$10B): {len(df[df["cap_billions"] < 10])} stocks')

print(f'\n🏆 TOP 20 STOCKS BY MARKET CAP:')
top_stocks = df.nlargest(20, 'market_cap')[['symbol', 'sector', 'cap_billions', 'pe_ratio']]
for _, stock in top_stocks.iterrows():
    print(f'{stock["symbol"]:6s} | {stock["sector"]:20s} | ${stock["cap_billions"]:6.1f}B | PE: {stock["pe_ratio"]:5.1f}')

# Save results
os.makedirs('analysis_results', exist_ok=True)
df.to_csv('analysis_results/all_stocks_fundamentals.csv', index=False)
top_stocks.to_csv('analysis_results/top_20_stocks.csv', index=False)

print(f'\n✅ Analysis complete! Results saved to analysis_results/')
print(f'🎯 Ready for strategy development with {len(fundamentals)} stocks!')
