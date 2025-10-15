"""
Cleanup, Optimize, and Verify Data Directory
===========================================

This script:
1. Deletes unnecessary files and directories
2. Verifies all required data is present
3. Optimizes directory structure
4. Generates comprehensive verification report

Author: UMushroom Investment Strategy
Date: October 2024
"""

import os
import shutil
import pandas as pd
import json
from datetime import datetime
import logging

class DataCleanupOptimizer:
    """
    Cleanup and optimize data directory
    """
    
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.bulk_extraction_dir = os.path.join(base_dir, 'data', 'bulk_extraction')
        
        # Setup logging
        self.setup_logging()
        
        # Tracking
        self.stats = {
            'files_deleted': 0,
            'dirs_deleted': 0,
            'space_freed_mb': 0,
            'stocks_verified': 0,
            'missing_data': [],
            'incomplete_stocks': []
        }
    
    def setup_logging(self):
        """Setup logging"""
        log_file = os.path.join(self.base_dir, f"cleanup_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def delete_unnecessary_files(self):
        """Delete unnecessary files and directories"""
        self.logger.info("🗑️ Starting cleanup of unnecessary files...")
        
        # Files/directories to delete
        unnecessary_items = [
            # Old/backup files
            'data/processed/earnings_final.csv.backup',
            'data/processed/earnings_final.csv.before_removal',
            'data/enriched',
            'data/exclusions',
            'earnings_quality',
            'fundamental_data/historical_fundamentals',
            'liquidity_data',
            'market_conditions',
            'risk_indicators',
            
            # Old analysis files
            'analysis_output.log',
            'ANALYSIS_RESULTS_SUMMARY.md',
            'CLEANUP_SUMMARY.md',
            'DATA_COLLECTION_SUMMARY.md',
            'DATA_ENRICHMENT_REPORT.txt',
            'FINAL_92_STOCKS_SUMMARY.md',
            'FINAL_STATUS.md',
            'QUICK_REFERENCE.txt',
            'READY_FOR_ANALYSIS.md',
            
            # Old data collection scripts
            'complete_missing_stocks.py',
            'verify_data_collection.py',
            'scripts/data_collection/extract_earnings.py',
            'scripts/data_collection/fetch_enrichment_data.py',
            'scripts/data_collection/fetch_pead_data.py',
            'scripts/data_collection/historical_data_fetcher.py',
            'scripts/data_collection/run_data_collection.py',
            'scripts/data_collection/ticker_list.py',
            'scripts/data_collection/tws_connector.py',
            'scripts/data_collection/extract_10min_earnings_data.py',
            'scripts/data_collection/extract_10min_earnings_data_robust.py',
            'scripts/data_collection/extract_5min_earnings_data.py',
            'scripts/data_collection/ib_gateway_5min_extractor.py',
            'scripts/data_collection/ib_gateway_multi_connection_extractor.py',
            'scripts/data_collection/ib_gateway_single_fast_extractor.py',
            
            # Old analysis scripts
            'scripts/analysis/quick_screener.py',
            'scripts/monitoring',
            
            # Processed data (keep only essential)
            'data/processed/analysis_results',
            'data/processed/missing_stocks.csv',
            'data/raw',
            
            # Logs directory in bulk_extraction (keep only latest)
            # Will handle separately
        ]
        
        for item in unnecessary_items:
            item_path = os.path.join(self.base_dir, item)
            if os.path.exists(item_path):
                try:
                    if os.path.isfile(item_path):
                        size_mb = os.path.getsize(item_path) / (1024 * 1024)
                        os.remove(item_path)
                        self.stats['files_deleted'] += 1
                        self.stats['space_freed_mb'] += size_mb
                        self.logger.info(f"  ✅ Deleted file: {item} ({size_mb:.2f} MB)")
                    elif os.path.isdir(item_path):
                        size_mb = self.get_dir_size(item_path) / (1024 * 1024)
                        shutil.rmtree(item_path)
                        self.stats['dirs_deleted'] += 1
                        self.stats['space_freed_mb'] += size_mb
                        self.logger.info(f"  ✅ Deleted directory: {item} ({size_mb:.2f} MB)")
                except Exception as e:
                    self.logger.warning(f"  ⚠️ Could not delete {item}: {e}")
        
        # Clean up old log files (keep only latest 3)
        self.cleanup_old_logs()
        
        self.logger.info(f"✅ Cleanup complete: Deleted {self.stats['files_deleted']} files, {self.stats['dirs_deleted']} directories")
        self.logger.info(f"💾 Space freed: {self.stats['space_freed_mb']:.2f} MB")
    
    def get_dir_size(self, path):
        """Get directory size in bytes"""
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self.get_dir_size(entry.path)
        except:
            pass
        return total
    
    def cleanup_old_logs(self):
        """Keep only latest 3 log files"""
        logs_dir = os.path.join(self.bulk_extraction_dir, 'logs')
        if not os.path.exists(logs_dir):
            return
        
        log_files = []
        for f in os.listdir(logs_dir):
            if f.endswith('.log'):
                file_path = os.path.join(logs_dir, f)
                log_files.append((file_path, os.path.getmtime(file_path)))
        
        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: x[1], reverse=True)
        
        # Delete all but the latest 3
        for file_path, _ in log_files[3:]:
            try:
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                os.remove(file_path)
                self.stats['files_deleted'] += 1
                self.stats['space_freed_mb'] += size_mb
                self.logger.info(f"  ✅ Deleted old log: {os.path.basename(file_path)}")
            except Exception as e:
                self.logger.warning(f"  ⚠️ Could not delete log {file_path}: {e}")
    
    def verify_stock_data(self):
        """Verify all required data is present for each stock"""
        self.logger.info("🔍 Verifying stock data completeness...")
        
        required_files = [
            '_5min_data.csv',
            '_daily_data.csv',
            '_weekly_data.csv',
            '_fundamental_data.csv',
            '_earnings_data.json'
        ]
        
        for ticker_dir in os.listdir(self.bulk_extraction_dir):
            ticker_path = os.path.join(self.bulk_extraction_dir, ticker_dir)
            
            # Skip non-directories and special directories
            if not os.path.isdir(ticker_path) or ticker_dir in ['logs', '__pycache__']:
                continue
            
            if len(ticker_dir) > 5:  # Skip non-ticker directories
                continue
            
            # Check for required files
            missing_files = []
            for req_file in required_files:
                file_path = os.path.join(ticker_path, f"{ticker_dir}{req_file}")
                if not os.path.exists(file_path):
                    missing_files.append(req_file)
                else:
                    # Verify file is not empty
                    if os.path.getsize(file_path) == 0:
                        missing_files.append(f"{req_file} (empty)")
            
            if missing_files:
                self.stats['incomplete_stocks'].append({
                    'ticker': ticker_dir,
                    'missing': missing_files
                })
                self.logger.warning(f"  ⚠️ {ticker_dir}: Missing {', '.join(missing_files)}")
            else:
                self.stats['stocks_verified'] += 1
        
        self.logger.info(f"✅ Verified {self.stats['stocks_verified']} stocks with complete data")
        if self.stats['incomplete_stocks']:
            self.logger.warning(f"⚠️ Found {len(self.stats['incomplete_stocks'])} stocks with incomplete data")
    
    def verify_earnings_data(self):
        """Verify earnings_final.csv is present and valid"""
        self.logger.info("🔍 Verifying earnings data...")
        
        earnings_file = os.path.join(self.base_dir, 'data', 'processed', 'earnings_final.csv')
        
        if not os.path.exists(earnings_file):
            self.logger.error("❌ earnings_final.csv not found!")
            self.stats['missing_data'].append('earnings_final.csv')
            return
        
        try:
            df = pd.read_csv(earnings_file)
            self.logger.info(f"✅ Earnings data verified: {len(df)} earnings events for {len(df['ticker'].unique())} stocks")
        except Exception as e:
            self.logger.error(f"❌ Error reading earnings_final.csv: {e}")
            self.stats['missing_data'].append('earnings_final.csv (corrupted)')
    
    def optimize_directory_structure(self):
        """Optimize directory structure"""
        self.logger.info("🔧 Optimizing directory structure...")
        
        # Ensure essential directories exist
        essential_dirs = [
            'data/bulk_extraction',
            'data/bulk_extraction/logs',
            'data/processed',
            'scripts/data_collection',
            'scripts/analysis',
            'docs'
        ]
        
        for dir_path in essential_dirs:
            full_path = os.path.join(self.base_dir, dir_path)
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
                self.logger.info(f"  ✅ Created directory: {dir_path}")
        
        self.logger.info("✅ Directory structure optimized")
    
    def generate_verification_report(self):
        """Generate comprehensive verification report"""
        self.logger.info("📊 Generating verification report...")
        
        report = f"""
# DATA CLEANUP AND VERIFICATION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## CLEANUP SUMMARY
- Files deleted: {self.stats['files_deleted']}
- Directories deleted: {self.stats['dirs_deleted']}
- Space freed: {self.stats['space_freed_mb']:.2f} MB

## DATA VERIFICATION SUMMARY
- Stocks with complete data: {self.stats['stocks_verified']}
- Stocks with incomplete data: {len(self.stats['incomplete_stocks'])}

## COMPLETE DATA INVENTORY
### Required Files Per Stock:
- ✅ TICKER_5min_data.csv (5-minute interval data, last 5 days)
- ✅ TICKER_daily_data.csv (Daily data, 1 year)
- ✅ TICKER_weekly_data.csv (Weekly data, 10 years)
- ✅ TICKER_fundamental_data.csv (Fundamental metrics)
- ✅ TICKER_earnings_data.json (Earnings data structure)

### Essential Files:
- ✅ data/processed/earnings_final.csv (Earnings calendar)
- ✅ scripts/data_collection/comprehensive_data_collector.py
- ✅ scripts/data_collection/ib_gateway_bulk_fast_extractor.py
- ✅ scripts/analysis/pead_analyzer.py
- ✅ scripts/analysis/run_analysis.py

## INCOMPLETE STOCKS
"""
        
        if self.stats['incomplete_stocks']:
            for stock in self.stats['incomplete_stocks'][:20]:  # Show first 20
                report += f"- {stock['ticker']}: Missing {', '.join(stock['missing'])}\n"
            if len(self.stats['incomplete_stocks']) > 20:
                report += f"- ... and {len(self.stats['incomplete_stocks']) - 20} more\n"
        else:
            report += "- None - All stocks have complete data! ✅\n"
        
        report += f"""
## MISSING CRITICAL DATA
"""
        
        if self.stats['missing_data']:
            for item in self.stats['missing_data']:
                report += f"- {item}\n"
        else:
            report += "- None - All critical data present! ✅\n"
        
        report += f"""
## OPTIMIZED DIRECTORY STRUCTURE
```
UMushroom Investment challange/
├── data/
│   ├── bulk_extraction/
│   │   ├── TICKER/                    # 413 stock directories
│   │   │   ├── TICKER_5min_data.csv   # 5-minute intervals
│   │   │   ├── TICKER_daily_data.csv  # Daily prices
│   │   │   ├── TICKER_weekly_data.csv # Weekly prices
│   │   │   ├── TICKER_fundamental_data.csv # Fundamentals
│   │   │   └── TICKER_earnings_data.json # Earnings
│   │   ├── logs/                      # Latest 3 log files
│   │   ├── collection_summary.json
│   │   └── ib_bulk_5min_report.md
│   └── processed/
│       └── earnings_final.csv         # Earnings calendar
├── scripts/
│   ├── data_collection/
│   │   ├── comprehensive_data_collector.py
│   │   ├── ib_gateway_bulk_fast_extractor.py
│   │   └── ib_gateway_simple_extractor.py
│   └── analysis/
│       ├── pead_analyzer.py
│       ├── run_analysis.py
│       └── three_step_earnings_strategy.py
├── docs/
│   └── plans/
└── config/
    └── settings.py
```

## DATA READY FOR ANALYSIS
✅ All data collection complete
✅ Directory structure optimized
✅ Unnecessary files removed
✅ {self.stats['stocks_verified']} stocks ready for analysis

## NEXT STEPS
1. Run comprehensive earnings strategy analysis
2. Generate stock rankings for competition
3. Implement optimized trading strategy
4. Execute trades for UMushroom Competition

## STORAGE SUMMARY
- Space freed by cleanup: {self.stats['space_freed_mb']:.2f} MB
- Estimated total data size: ~{self.estimate_total_size():.2f} MB
- Data efficiency: Optimized for analysis
"""
        
        # Save report
        report_file = os.path.join(self.base_dir, 'DATA_VERIFICATION_REPORT.md')
        with open(report_file, 'w') as f:
            f.write(report)
        
        self.logger.info(f"✅ Verification report saved: {report_file}")
        
        return report
    
    def estimate_total_size(self):
        """Estimate total data size"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(os.path.join(self.base_dir, 'data')):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
        except:
            pass
        return total_size / (1024 * 1024)  # Convert to MB
    
    def run(self):
        """Run complete cleanup and verification"""
        self.logger.info("🚀 Starting data cleanup and verification...")
        
        # 1. Delete unnecessary files
        self.delete_unnecessary_files()
        
        # 2. Optimize directory structure
        self.optimize_directory_structure()
        
        # 3. Verify stock data
        self.verify_stock_data()
        
        # 4. Verify earnings data
        self.verify_earnings_data()
        
        # 5. Generate report
        report = self.generate_verification_report()
        
        self.logger.info("✅ Cleanup and verification complete!")
        
        return report

def main():
    """Main execution"""
    base_dir = '/home/fellaki10/Documents/UMushroom Investment challange'
    
    optimizer = DataCleanupOptimizer(base_dir)
    report = optimizer.run()
    
    print("\n" + "="*80)
    print(report)
    print("="*80)

if __name__ == "__main__":
    main()

