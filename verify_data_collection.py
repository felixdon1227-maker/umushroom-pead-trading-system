#!/usr/bin/env python3
"""
Comprehensive Data Collection Verification Script
Checks every stock to ensure all data has been properly downloaded
"""

import pandas as pd
import os
from pathlib import Path

print("=" * 80)
print("📊 COMPREHENSIVE DATA COLLECTION VERIFICATION")
print("=" * 80)

# Load the stock list
earnings_file = 'data/processed/earnings_final.csv'
df_stocks = pd.read_csv(earnings_file)
all_tickers = sorted(df_stocks['ticker'].unique())

print(f"\n✓ Loaded {len(all_tickers)} stocks from earnings_final.csv")

# Define data directories
data_dir = 'data/processed/historical_data'
earnings_dir = f'{data_dir}/earnings_history'
daily_dir = f'{data_dir}/daily_prices'
hourly_dir = f'{data_dir}/hourly_prices'

# Initialize tracking
complete_stocks = []
missing_earnings = []
missing_daily = []
missing_hourly = []
incomplete_stocks = []

print(f"\n🔍 Checking data for each stock...")
print("=" * 80)

for i, ticker in enumerate(all_tickers, 1):
    # Check files
    earnings_file = f'{earnings_dir}/{ticker}_earnings.csv'
    daily_file = f'{daily_dir}/{ticker}_daily_10y.csv'
    hourly_file = f'{hourly_dir}/{ticker}_hourly.csv'
    
    has_earnings = os.path.exists(earnings_file)
    has_daily = os.path.exists(daily_file)
    has_hourly = os.path.exists(hourly_file)
    
    # Check file sizes
    earnings_size = os.path.getsize(earnings_file) if has_earnings else 0
    daily_size = os.path.getsize(daily_file) if has_daily else 0
    hourly_size = os.path.getsize(hourly_file) if has_hourly else 0
    
    # Determine status
    if has_earnings and has_daily and has_hourly:
        # Check if files have actual data (not just headers)
        if earnings_size > 100 and daily_size > 500 and hourly_size > 100:
            complete_stocks.append(ticker)
            status = "✅ COMPLETE"
        else:
            incomplete_stocks.append(ticker)
            status = "⚠️  INCOMPLETE (files too small)"
    else:
        status_parts = []
        if not has_earnings:
            missing_earnings.append(ticker)
            status_parts.append("❌ No earnings")
        if not has_daily:
            missing_daily.append(ticker)
            status_parts.append("❌ No daily")
        if not has_hourly:
            missing_hourly.append(ticker)
            status_parts.append("❌ No hourly")
        status = " | ".join(status_parts)
    
    # Print progress every 10 stocks
    if i % 10 == 0 or i == len(all_tickers):
        print(f"  Progress: {i}/{len(all_tickers)} stocks checked ({i/len(all_tickers)*100:.1f}%)")

print("\n" + "=" * 80)
print("📊 VERIFICATION RESULTS")
print("=" * 80)

print(f"\n✅ COMPLETE STOCKS: {len(complete_stocks)}/{len(all_tickers)} ({len(complete_stocks)/len(all_tickers)*100:.1f}%)")

if missing_earnings or missing_daily or missing_hourly or incomplete_stocks:
    print(f"\n⚠️  ISSUES FOUND:")
    
    if missing_earnings:
        print(f"\n❌ Missing Earnings History ({len(missing_earnings)} stocks):")
        for ticker in missing_earnings:
            print(f"  - {ticker}")
    
    if missing_daily:
        print(f"\n❌ Missing Daily Prices ({len(missing_daily)} stocks):")
        for ticker in missing_daily:
            print(f"  - {ticker}")
    
    if missing_hourly:
        print(f"\n❌ Missing Hourly Prices ({len(missing_hourly)} stocks):")
        for ticker in missing_hourly:
            print(f"  - {ticker}")
    
    if incomplete_stocks:
        print(f"\n⚠️  Incomplete Data ({len(incomplete_stocks)} stocks):")
        for ticker in incomplete_stocks:
            print(f"  - {ticker}")
    
    # Create list of stocks needing collection
    all_missing = set(missing_earnings + missing_daily + missing_hourly + incomplete_stocks)
    print(f"\n📋 TOTAL STOCKS NEEDING DATA COLLECTION: {len(all_missing)}")
    
    # Save missing stocks to file
    if all_missing:
        missing_df = pd.DataFrame({'ticker': sorted(all_missing)})
        missing_df.to_csv('data/processed/missing_stocks.csv', index=False)
        print(f"✓ Saved list to: data/processed/missing_stocks.csv")

else:
    print(f"\n🎉 ALL STOCKS HAVE COMPLETE DATA!")

# Detailed statistics
print(f"\n" + "=" * 80)
print("📈 DETAILED STATISTICS")
print("=" * 80)

total_earnings_files = len([f for f in os.listdir(earnings_dir) if f.endswith('.csv')])
total_daily_files = len([f for f in os.listdir(daily_dir) if f.endswith('.csv')])
total_hourly_files = len([f for f in os.listdir(hourly_dir) if f.endswith('.csv')])

print(f"\nFiles on disk:")
print(f"  Earnings history files: {total_earnings_files}")
print(f"  Daily price files: {total_daily_files}")
print(f"  Hourly price files: {total_hourly_files}")

# Calculate total data size
def get_dir_size(directory):
    total = 0
    for entry in os.scandir(directory):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            total += get_dir_size(entry.path)
    return total

earnings_size_mb = get_dir_size(earnings_dir) / (1024 * 1024)
daily_size_mb = get_dir_size(daily_dir) / (1024 * 1024)
hourly_size_mb = get_dir_size(hourly_dir) / (1024 * 1024)
total_size_mb = earnings_size_mb + daily_size_mb + hourly_size_mb

print(f"\nData size:")
print(f"  Earnings history: {earnings_size_mb:.2f} MB")
print(f"  Daily prices: {daily_size_mb:.2f} MB")
print(f"  Hourly prices: {hourly_size_mb:.2f} MB")
print(f"  Total: {total_size_mb:.2f} MB")

# Sample data check
print(f"\n" + "=" * 80)
print("🔍 SAMPLE DATA QUALITY CHECK")
print("=" * 80)

if complete_stocks:
    sample_ticker = complete_stocks[0]
    print(f"\nChecking sample stock: {sample_ticker}")
    
    # Check earnings
    earnings_df = pd.read_csv(f'{earnings_dir}/{sample_ticker}_earnings.csv')
    print(f"  Earnings reports: {len(earnings_df)} records")
    
    # Check daily
    daily_df = pd.read_csv(f'{daily_dir}/{sample_ticker}_daily_10y.csv')
    print(f"  Daily prices: {len(daily_df)} days")
    
    # Check hourly
    hourly_df = pd.read_csv(f'{hourly_dir}/{sample_ticker}_hourly.csv')
    print(f"  Hourly prices: {len(hourly_df)} hours")

print("\n" + "=" * 80)
print("✅ VERIFICATION COMPLETE")
print("=" * 80)

