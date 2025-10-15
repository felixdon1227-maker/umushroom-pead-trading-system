#!/usr/bin/env python3
"""
3-Step Strategy Master Executor
==============================

Master script to coordinate all 3-Step Strategy systems:
- Data preparation and validation
- Backtesting and optimization
- Performance analysis
- Real-time monitoring
- Results generation

Author: UMushroom Investment Strategy
Date: October 2025
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts', 'analysis'))

from three_step_optimized_backtester import ThreeStepOptimizedBacktester
from three_step_performance_analyzer import ThreeStepPerformanceAnalyzer
from three_step_real_time_monitor import ThreeStepRealTimeMonitor

class ThreeStepMasterExecutor:
    """
    Master executor for 3-Step Strategy system
    """
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            self.project_root = os.path.dirname(os.path.abspath(__file__))
        else:
            self.project_root = project_root
        
        self.earnings_file = os.path.join(self.project_root, 'data', 'processed', 'earnings_final.csv')
        self.data_dir = os.path.join(self.project_root, 'data', 'all_stocks_complete')
        self.results_dir = os.path.join(self.project_root, 'results')
        
        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)
        
        print("🚀 3-Step Strategy Master Executor")
        print("=" * 50)
        print(f"📁 Project Root: {self.project_root}")
        print(f"📊 Earnings File: {self.earnings_file}")
        print(f"📈 Data Directory: {self.data_dir}")
        print(f"💾 Results Directory: {self.results_dir}")
    
    def validate_data(self) -> bool:
        """Validate that all required data is available"""
        print("\n🔍 Validating Data...")
        
        # Check earnings file
        if not os.path.exists(self.earnings_file):
            print(f"❌ Earnings file not found: {self.earnings_file}")
            return False
        
        # Check data directory
        if not os.path.exists(self.data_dir):
            print(f"❌ Data directory not found: {self.data_dir}")
            return False
        
        # Count available stocks
        stock_dirs = [d for d in os.listdir(self.data_dir) if os.path.isdir(os.path.join(self.data_dir, d))]
        print(f"✅ Found {len(stock_dirs)} stock directories")
        
        # Check for required data files
        required_files = ['_daily_10y.csv', '_fundamentals.json']
        available_data = {}
        
        for stock in stock_dirs[:10]:  # Check first 10 stocks
            stock_path = os.path.join(self.data_dir, stock)
            files = os.listdir(stock_path)
            
            for req_file in required_files:
                if any(req_file in f for f in files):
                    if req_file not in available_data:
                        available_data[req_file] = 0
                    available_data[req_file] += 1
        
        print("📊 Data Availability:")
        for file_type, count in available_data.items():
            print(f"  {file_type}: {count}/{len(stock_dirs)} stocks")
        
        return True
    
    def run_backtesting(self, optimize: bool = True) -> str:
        """Run backtesting and optimization"""
        print("\n🔄 Running Backtesting...")
        
        # Initialize backtester
        backtester = ThreeStepOptimizedBacktester(
            earnings_file=self.earnings_file,
            data_dir=self.data_dir,
            output_dir=self.results_dir
        )
        
        # Run basic backtest
        print("1️⃣ Running Basic Backtest...")
        basic_results = backtester.backtest_strategy()
        
        if 'error' in basic_results:
            print(f"❌ Basic backtest failed: {basic_results['error']}")
            return None
        
        # Save basic results
        basic_file = backtester.save_results(basic_results, 'three_step_basic_backtest.json')
        print(f"✅ Basic backtest complete: {basic_file}")
        
        if optimize:
            # Run optimization
            print("2️⃣ Running Parameter Optimization...")
            optimization_results = backtester.optimize_parameters()
            
            if optimization_results['best_parameters']:
                print(f"🏆 Best parameters found with score: {optimization_results['best_performance']['optimization_score']:.2f}")
                
                # Save optimization results
                opt_file = backtester.save_results(optimization_results, 'three_step_optimization_results.json')
                print(f"✅ Optimization complete: {opt_file}")
                
                # Run final backtest with best parameters
                print("3️⃣ Running Final Backtest with Best Parameters...")
                final_results = backtester.backtest_strategy(optimization_results['best_parameters'])
                
                if 'error' not in final_results:
                    final_file = backtester.save_results(final_results, 'three_step_final_backtest.json')
                    print(f"✅ Final backtest complete: {final_file}")
                    return final_file
        
        return basic_file
    
    def run_performance_analysis(self, results_file: str) -> str:
        """Run comprehensive performance analysis"""
        print("\n📊 Running Performance Analysis...")
        
        # Initialize analyzer
        analyzer = ThreeStepPerformanceAnalyzer(
            results_file=results_file,
            output_dir=self.results_dir
        )
        
        # Generate comprehensive report
        report = analyzer.generate_comprehensive_report()
        print(report)
        
        # Generate visualizations
        analyzer.generate_visualizations()
        
        # Save analysis results
        analysis_file = analyzer.save_analysis_results()
        print(f"✅ Performance analysis complete: {analysis_file}")
        
        return analysis_file
    
    def run_real_time_monitoring(self, duration_hours: int = 1) -> None:
        """Run real-time monitoring"""
        print(f"\n📡 Running Real-Time Monitoring for {duration_hours} hours...")
        
        # Initialize monitor
        monitor = ThreeStepRealTimeMonitor()
        
        # Load earnings calendar
        monitor.load_earnings_calendar(self.earnings_file)
        
        # Run monitoring
        try:
            monitor.run_continuous_monitoring(duration_hours=duration_hours)
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")
    
    def generate_summary_report(self) -> str:
        """Generate summary report of all results"""
        print("\n📋 Generating Summary Report...")
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'project_root': self.project_root,
            'data_validation': {
                'earnings_file_exists': os.path.exists(self.earnings_file),
                'data_dir_exists': os.path.exists(self.data_dir),
                'results_dir_exists': os.path.exists(self.results_dir)
            },
            'available_results': [],
            'recommendations': []
        }
        
        # Check for available results
        if os.path.exists(self.results_dir):
            result_files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
            summary['available_results'] = result_files
        
        # Generate recommendations
        if 'three_step_final_backtest.json' in summary['available_results']:
            summary['recommendations'].append("✅ Strategy backtesting complete - ready for live trading")
        
        if 'three_step_performance_analysis' in str(summary['available_results']):
            summary['recommendations'].append("✅ Performance analysis complete - review metrics")
        
        if len(summary['available_results']) == 0:
            summary['recommendations'].append("⚠️ No results found - run backtesting first")
        
        # Save summary
        summary_file = os.path.join(self.results_dir, 'strategy_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Summary report saved: {summary_file}")
        return summary_file
    
    def run_full_pipeline(self, optimize: bool = True, monitor: bool = False) -> Dict:
        """Run the complete 3-Step Strategy pipeline"""
        print("\n🚀 Running Full 3-Step Strategy Pipeline")
        print("=" * 60)
        
        start_time = time.time()
        results = {}
        
        try:
            # 1. Validate data
            if not self.validate_data():
                print("❌ Data validation failed")
                return {'error': 'Data validation failed'}
            
            # 2. Run backtesting
            backtest_file = self.run_backtesting(optimize=optimize)
            if backtest_file:
                results['backtest_file'] = backtest_file
            
            # 3. Run performance analysis
            if backtest_file:
                analysis_file = self.run_performance_analysis(backtest_file)
                results['analysis_file'] = analysis_file
            
            # 4. Run real-time monitoring (optional)
            if monitor:
                self.run_real_time_monitoring(duration_hours=1)
            
            # 5. Generate summary
            summary_file = self.generate_summary_report()
            results['summary_file'] = summary_file
            
            # Calculate total time
            total_time = time.time() - start_time
            results['total_time'] = total_time
            
            print(f"\n✅ Pipeline complete in {total_time:.1f} seconds")
            print(f"📁 Results saved in: {self.results_dir}")
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            results['error'] = str(e)
        
        return results


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='3-Step Strategy Master Executor')
    parser.add_argument('--mode', choices=['backtest', 'analyze', 'monitor', 'full'], 
                       default='full', help='Execution mode')
    parser.add_argument('--optimize', action='store_true', 
                       help='Run parameter optimization')
    parser.add_argument('--monitor-hours', type=int, default=1,
                       help='Hours to run real-time monitoring')
    parser.add_argument('--project-root', type=str,
                       help='Project root directory')
    
    args = parser.parse_args()
    
    # Initialize executor
    executor = ThreeStepMasterExecutor(project_root=args.project_root)
    
    if args.mode == 'backtest':
        executor.run_backtesting(optimize=args.optimize)
    elif args.mode == 'analyze':
        # Find latest backtest results
        results_dir = executor.results_dir
        backtest_files = [f for f in os.listdir(results_dir) if 'backtest' in f and f.endswith('.json')]
        if backtest_files:
            latest_file = os.path.join(results_dir, sorted(backtest_files)[-1])
            executor.run_performance_analysis(latest_file)
        else:
            print("❌ No backtest results found")
    elif args.mode == 'monitor':
        executor.run_real_time_monitoring(duration_hours=args.monitor_hours)
    elif args.mode == 'full':
        executor.run_full_pipeline(optimize=args.optimize, monitor=False)
    
    print("\n🎉 Execution complete!")


if __name__ == "__main__":
    main()
