#!/usr/bin/env python3
"""
Real-time progress monitor for PEAD data collection
"""
import pandas as pd
from datetime import datetime
import time
import os

def show_progress():
    """Display current progress"""
    os.system('clear')
    
    print("=" * 80)
    print("📊 PEAD DATA COLLECTION - LIVE MONITOR")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        df = pd.read_csv('pead_historical_data/collection_summary.csv')
        completed = len(df)
        total = 167
        progress_pct = (completed / total) * 100
        
        # Progress bar
        bar_length = 50
        filled = int(bar_length * completed / total)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\n[{bar}] {progress_pct:.1f}%")
        print(f"\n✅ Completed: {completed}/{total} stocks")
        print(f"⏳ Remaining: {total - completed} stocks")
        
        # Speed calculation
        if completed > 0:
            # Estimate based on recent performance
            remaining = total - completed
            eta_minutes = remaining * 0.7  # ~0.7 min per stock with optimization
            eta_hours = eta_minutes / 60
            
            finish_hour = (datetime.now().hour + int(eta_hours)) % 24
            finish_min = (datetime.now().minute + int(eta_minutes % 60)) % 60
            
            print(f"\n⏱️  ETA: {eta_minutes:.0f} minutes ({eta_hours:.1f} hours)")
            print(f"🎯 Expected finish: ~{finish_hour:02d}:{finish_min:02d}")
        
        print(f"\n📊 Data Collected:")
        print(f"  Daily bars: {df['daily_bars'].sum():,}")
        print(f"  Hourly bars: {df['hourly_bars'].sum():,}")
        print(f"  Earnings events: {df['earnings_count'].sum():,}")
        
        print(f"\n🎯 Last 5 Completed:")
        for idx, row in df.tail(5).iterrows():
            print(f"  {row['ticker']:6s}: {row['daily_bars']:,} daily, {row['hourly_bars']:,} hourly, {row['earnings_count']} earnings")
        
        # Performance stats
        avg_daily = df['daily_bars'].mean()
        avg_hourly = df['hourly_bars'].mean()
        avg_earnings = df['earnings_count'].mean()
        
        print(f"\n📈 Averages per Stock:")
        print(f"  Daily bars: {avg_daily:.0f}")
        print(f"  Hourly bars: {avg_hourly:.0f}")
        print(f"  Earnings events: {avg_earnings:.1f}")
        
    except FileNotFoundError:
        print("\n⏳ Waiting for data collection to start...")
    except Exception as e:
        print(f"\n⚠️  Error: {e}")
    
    print("\n" + "=" * 80)
    print("🚀 OPTIMIZATIONS ACTIVE:")
    print("  • 3x faster sleep times (2s→0.5s, 3s→0.8s)")
    print("  • Auto-skip completed stocks")
    print("  • Progress saved every 10 stocks")
    print("=" * 80)
    print("\nPress Ctrl+C to exit monitor")

if __name__ == "__main__":
    try:
        while True:
            show_progress()
            time.sleep(30)  # Update every 30 seconds
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped")

