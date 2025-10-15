#!/usr/bin/env python3
"""
Optimization Progress Monitor
============================

Monitor the progress of 3-Step Strategy optimization
"""

import os
import time
import json
from datetime import datetime

def monitor_optimization():
    """Monitor optimization progress"""
    results_dir = '/home/fellaki10/Documents/UMushroom Investment challange/results'
    
    print("🔍 Monitoring 3-Step Strategy Optimization...")
    print("=" * 50)
    
    while True:
        try:
            # Check for results files
            if os.path.exists(results_dir):
                files = os.listdir(results_dir)
                
                print(f"\n📊 Status Update - {datetime.now().strftime('%H:%M:%S')}")
                print(f"📁 Results directory: {results_dir}")
                print(f"📄 Files found: {len(files)}")
                
                for file in sorted(files):
                    if file.endswith('.json'):
                        filepath = os.path.join(results_dir, file)
                        size = os.path.getsize(filepath)
                        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        print(f"  ✅ {file} ({size:,} bytes, {mtime.strftime('%H:%M:%S')})")
                
                # Check if optimization is complete
                if 'three_step_optimization_results.json' in files:
                    print("\n🎉 Optimization appears to be complete!")
                    break
                elif 'three_step_final_backtest.json' in files:
                    print("\n🎉 Final backtest appears to be complete!")
                    break
            
            time.sleep(30)  # Check every 30 seconds
            
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    monitor_optimization()
