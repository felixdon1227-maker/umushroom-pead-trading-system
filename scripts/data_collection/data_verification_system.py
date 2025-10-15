"""
DATA VERIFICATION SYSTEM - Quality Assurance for Collected Data
=============================================================

This script verifies the completeness and quality of collected data:
1. Checks all 413 stocks have required data files
2. Validates data integrity and completeness
3. Identifies missing or corrupted data
4. Generates quality reports
5. Provides data repair suggestions

Author: UMushroom Investment Strategy
Date: October 2024
"""

import pandas as pd
import numpy as np
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class DataVerificationSystem:
    """Comprehensive data verification and quality assurance"""
    
    def __init__(self):
        self.project_root = project_root
        self.data_dir = self.project_root / 'data' / 'all_stocks_complete'
        self.logger = self._setup_logger()
        self.verification_results = {
            'total_stocks': 0,
            'complete_stocks': 0,
            'incomplete_stocks': 0,
            'missing_files': [],
            'data_quality_issues': [],
            'verification_timestamp': datetime.now().isoformat()
        }
        
    def _setup_logger(self):
        """Setup verification logger"""
        logger = logging.getLogger('DataVerification')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Create logs directory
            (self.project_root / 'logs').mkdir(exist_ok=True)
            
            # File handler
            file_handler = logging.FileHandler(
                self.project_root / f'logs/data_verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
        return logger
    
    def get_expected_stocks(self) -> List[str]:
        """Get list of expected stocks from earnings file"""
        try:
            earnings_df = pd.read_csv(self.project_root / 'data' / 'processed' / 'earnings_final.csv')
            return earnings_df['ticker'].unique().tolist()
        except Exception as e:
            self.logger.error(f"Failed to load expected stocks: {e}")
            return []
    
    def get_actual_stocks(self) -> List[str]:
        """Get list of stocks with data directories"""
        try:
            if not self.data_dir.exists():
                return []
            
            stock_dirs = [d.name for d in self.data_dir.iterdir() if d.is_dir()]
            return sorted(stock_dirs)
        except Exception as e:
            self.logger.error(f"Failed to get actual stocks: {e}")
            return []
    
    def verify_stock_data(self, ticker: str) -> Dict:
        """Verify data completeness for a single stock"""
        stock_dir = self.data_dir / ticker
        verification = {
            'ticker': ticker,
            'has_daily_data': False,
            'has_intraday_data': False,
            'has_fundamentals': False,
            'has_earnings_history': False,
            'daily_data_quality': {},
            'intraday_data_quality': {},
            'fundamentals_quality': {},
            'issues': []
        }
        
        if not stock_dir.exists():
            verification['issues'].append("Stock directory does not exist")
            return verification
        
        # Check daily data
        daily_file = stock_dir / f'{ticker}_daily_10years.csv'
        if daily_file.exists():
            verification['has_daily_data'] = True
            verification['daily_data_quality'] = self._verify_daily_data(daily_file)
        else:
            verification['issues'].append("Missing daily data file")
        
        # Check intraday data
        intraday_file = stock_dir / f'{ticker}_30min_earnings.csv'
        if intraday_file.exists():
            verification['has_intraday_data'] = True
            verification['intraday_data_quality'] = self._verify_intraday_data(intraday_file)
        else:
            verification['issues'].append("Missing intraday data file")
        
        # Check fundamentals
        fundamentals_file = stock_dir / f'{ticker}_fundamentals.json'
        if fundamentals_file.exists():
            verification['has_fundamentals'] = True
            verification['fundamentals_quality'] = self._verify_fundamentals(fundamentals_file)
        else:
            verification['issues'].append("Missing fundamentals file")
        
        # Check earnings history
        earnings_file = stock_dir / f'{ticker}_earnings_history.json'
        if earnings_file.exists():
            verification['has_earnings_history'] = True
        else:
            verification['issues'].append("Missing earnings history file")
        
        return verification
    
    def _verify_daily_data(self, file_path: Path) -> Dict:
        """Verify daily data quality"""
        try:
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            
            quality = {
                'total_records': len(df),
                'date_range_days': (df.index[-1] - df.index[0]).days,
                'missing_values': df.isnull().sum().to_dict(),
                'has_ohlcv': all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']),
                'price_range': {
                    'min_close': df['Close'].min() if 'Close' in df.columns else None,
                    'max_close': df['Close'].max() if 'Close' in df.columns else None
                },
                'volume_stats': {
                    'avg_volume': df['Volume'].mean() if 'Volume' in df.columns else None,
                    'zero_volume_days': (df['Volume'] == 0).sum() if 'Volume' in df.columns else None
                }
            }
            
            # Check for data quality issues
            if quality['total_records'] < 1000:  # Less than ~3 years
                quality['issues'] = ['Insufficient historical data']
            
            if quality['zero_volume_days'] and quality['zero_volume_days'] > 50:
                quality['issues'] = quality.get('issues', []) + ['Many zero volume days']
            
            return quality
            
        except Exception as e:
            return {'error': str(e)}
    
    def _verify_intraday_data(self, file_path: Path) -> Dict:
        """Verify intraday data quality"""
        try:
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            
            quality = {
                'total_records': len(df),
                'unique_earnings_dates': df['earnings_date'].nunique() if 'earnings_date' in df.columns else 0,
                'date_range_days': (df.index[-1] - df.index[0]).days if len(df) > 0 else 0,
                'missing_values': df.isnull().sum().to_dict(),
                'has_ohlcv': all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']),
                'time_intervals': df.index.to_series().diff().dt.total_seconds().value_counts().head().to_dict()
            }
            
            # Check for data quality issues
            if quality['total_records'] < 100:
                quality['issues'] = ['Insufficient intraday data']
            
            if quality['unique_earnings_dates'] < 5:
                quality['issues'] = quality.get('issues', []) + ['Few earnings periods covered']
            
            return quality
            
        except Exception as e:
            return {'error': str(e)}
    
    def _verify_fundamentals(self, file_path: Path) -> Dict:
        """Verify fundamentals data quality"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            quality = {
                'total_fields': len(data),
                'non_null_fields': len([v for v in data.values() if v is not None and v != 0]),
                'has_market_cap': 'market_cap' in data and data['market_cap'] is not None,
                'has_pe_ratio': 'pe_ratio' in data and data['pe_ratio'] is not None,
                'has_sector': 'sector' in data and data['sector'] != 'Unknown',
                'collected_at': data.get('collected_at', 'Unknown')
            }
            
            # Check for data quality issues
            if quality['non_null_fields'] < 10:
                quality['issues'] = ['Insufficient fundamental data']
            
            if not quality['has_market_cap']:
                quality['issues'] = quality.get('issues', []) + ['Missing market cap']
            
            return quality
            
        except Exception as e:
            return {'error': str(e)}
    
    def run_verification(self) -> Dict:
        """Run complete data verification"""
        self.logger.info("🔍 Starting data verification")
        
        # Get expected vs actual stocks
        expected_stocks = self.get_expected_stocks()
        actual_stocks = self.get_actual_stocks()
        
        self.verification_results['total_stocks'] = len(expected_stocks)
        self.verification_results['expected_stocks'] = expected_stocks
        self.verification_results['actual_stocks'] = actual_stocks
        self.verification_results['missing_stocks'] = list(set(expected_stocks) - set(actual_stocks))
        
        self.logger.info(f"📊 Expected: {len(expected_stocks)} stocks")
        self.logger.info(f"📊 Found: {len(actual_stocks)} stocks")
        self.logger.info(f"📊 Missing: {len(self.verification_results['missing_stocks'])} stocks")
        
        # Verify each stock
        stock_verifications = {}
        complete_stocks = 0
        incomplete_stocks = 0
        
        for ticker in actual_stocks:
            self.logger.info(f"🔍 Verifying {ticker}")
            verification = self.verify_stock_data(ticker)
            stock_verifications[ticker] = verification
            
            # Check if stock is complete
            required_files = ['has_daily_data', 'has_intraday_data', 'has_fundamentals', 'has_earnings_history']
            if all(verification.get(req, False) for req in required_files):
                complete_stocks += 1
            else:
                incomplete_stocks += 1
                self.verification_results['missing_files'].append({
                    'ticker': ticker,
                    'missing': [req.replace('has_', '') for req in required_files if not verification.get(req, False)]
                })
        
        self.verification_results['complete_stocks'] = complete_stocks
        self.verification_results['incomplete_stocks'] = incomplete_stocks
        self.verification_results['stock_verifications'] = stock_verifications
        
        # Generate summary
        self._generate_summary()
        
        return self.verification_results
    
    def _generate_summary(self):
        """Generate verification summary"""
        total = self.verification_results['total_stocks']
        complete = self.verification_results['complete_stocks']
        incomplete = self.verification_results['incomplete_stocks']
        missing = len(self.verification_results['missing_stocks'])
        
        completion_rate = (complete / total * 100) if total > 0 else 0
        
        self.logger.info("=" * 60)
        self.logger.info("📊 DATA VERIFICATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Expected Stocks: {total}")
        self.logger.info(f"Complete Stocks: {complete} ({completion_rate:.1f}%)")
        self.logger.info(f"Incomplete Stocks: {incomplete}")
        self.logger.info(f"Missing Stocks: {missing}")
        self.logger.info("=" * 60)
        
        if missing > 0:
            self.logger.warning(f"Missing stocks: {', '.join(self.verification_results['missing_stocks'][:10])}")
            if len(self.verification_results['missing_stocks']) > 10:
                self.logger.warning(f"... and {len(self.verification_results['missing_stocks']) - 10} more")
    
    def generate_report(self) -> str:
        """Generate detailed verification report"""
        report_path = self.project_root / f'logs/data_verification_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(report_path, 'w') as f:
            json.dump(self.verification_results, f, indent=2, default=str)
        
        self.logger.info(f"📄 Detailed report saved to {report_path}")
        return str(report_path)
    
    def get_repair_suggestions(self) -> List[str]:
        """Get suggestions for data repair"""
        suggestions = []
        
        # Missing stocks
        if self.verification_results['missing_stocks']:
            suggestions.append(f"Collect data for {len(self.verification_results['missing_stocks'])} missing stocks")
        
        # Incomplete stocks
        if self.verification_results['incomplete_stocks'] > 0:
            suggestions.append(f"Complete data collection for {self.verification_results['incomplete_stocks']} incomplete stocks")
        
        # Missing files
        missing_files = self.verification_results['missing_files']
        if missing_files:
            suggestions.append("Run targeted data collection for missing files")
        
        return suggestions


def main():
    """Main execution function"""
    print("🔍 UMushroom Investment Challenge - Data Verification System")
    print("=" * 60)
    
    verifier = DataVerificationSystem()
    
    try:
        # Run verification
        results = verifier.run_verification()
        
        # Generate report
        report_path = verifier.generate_report()
        
        # Get repair suggestions
        suggestions = verifier.get_repair_suggestions()
        
        print("\n🔧 REPAIR SUGGESTIONS:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        print(f"\n📄 Detailed report: {report_path}")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        verifier.logger.error(f"Verification failed: {e}")


if __name__ == "__main__":
    main()
