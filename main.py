#!/usr/bin/env python3
"""
UMushroom Investment Challenge - PEAD Trading System
Main entry point for the project
"""

import os
import sys
import argparse
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / 'scripts'))

def main():
    parser = argparse.ArgumentParser(description='PEAD Trading System')
    parser.add_argument('command', choices=[
        'collect-data', 'monitor', 'analyze', 'screen', 'generate-signals'
    ], help='Command to execute')
    parser.add_argument('--config', default='config/settings.py', 
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("UMUSHROOM INVESTMENT CHALLENGE - PEAD TRADING SYSTEM")
    print("=" * 80)
    
    if args.command == 'collect-data':
        from data_collection.run_data_collection import main as collect_main
        collect_main()
    
    elif args.command == 'monitor':
        from monitoring.progress_monitor import main as monitor_main
        monitor_main()
    
    elif args.command == 'analyze':
        from analysis.run_analysis import main as analyze_main
        analyze_main()
    
    elif args.command == 'screen':
        from analysis.quick_screener import main as screen_main
        screen_main()
    
    elif args.command == 'generate-signals':
        print("Signal generation module - Coming soon")
        # from analysis.signal_generator import main as signals_main
        # signals_main()

if __name__ == "__main__":
    main()

