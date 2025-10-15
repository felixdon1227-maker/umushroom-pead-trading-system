"""
3-Step Strategy Optimized Backtester
====================================

Advanced backtesting system for the 3-Step Earnings Strategy with:
- Multi-threaded data processing
- Parameter optimization
- Real-time performance monitoring
- Comprehensive risk analysis

Author: UMushroom Investment Strategy
Date: October 2025
"""

import pandas as pd
import numpy as np
import os
import json
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class ThreeStepOptimizedBacktester:
    """
    Optimized 3-Step Strategy Backtester with multi-threading and parameter optimization
    """
    
    def __init__(self, earnings_file: str, data_dir: str, output_dir: str = 'results'):
        self.earnings_file = earnings_file
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Load earnings data
        self.earnings = pd.read_csv(earnings_file)
        self.earnings['date'] = pd.to_datetime(self.earnings['date'])
        self.earnings = self.earnings.sort_values('date')
        
        print(f"✅ Loaded {len(self.earnings)} earnings events")
        print(f"📅 Date range: {self.earnings['date'].min()} to {self.earnings['date'].max()}")
        
        # Strategy parameters (optimizable)
        self.params = {
            'step1': {
                'min_beat_rate': 0.7,
                'min_volume_consistency': 0.5,
                'position_size': 3000,
                'hold_days': 10
            },
            'step2': {
                'min_day0_reaction': 1.0,
                'min_volume_spike': 2.0,
                'position_size': 4000,
                'hold_days': 10
            },
            'step3': {
                'min_combined_reaction': 2.0,
                'position_size': 5000,
                'hold_days': 10
            },
            'risk': {
                'max_positions': 12,
                'max_per_sector': 3,
                'stop_loss': -8.0,
                'take_profit': 15.0
            }
        }
        
        # Results storage
        self.backtest_results = []
        self.optimization_results = []
        
    def load_stock_data(self, ticker: str) -> Optional[Dict]:
        """Load all available data for a stock"""
        try:
            base_path = os.path.join(self.data_dir, ticker)
            
            data = {}
            
            # Load daily data
            daily_file = os.path.join(base_path, f"{ticker}_daily_10y.csv")
            if os.path.exists(daily_file):
                daily = pd.read_csv(daily_file)
                if 'Date' in daily.columns:
                    daily['Date'] = pd.to_datetime(daily['Date'], utc=True).dt.tz_localize(None)
                    daily.set_index('Date', inplace=True)
                    data['daily'] = daily.sort_index()
            
            # Load 30-minute earnings data
            intraday_file = os.path.join(base_path, f"{ticker}_30min_all_earnings.csv")
            if os.path.exists(intraday_file):
                intraday = pd.read_csv(intraday_file)
                if 'Date' in intraday.columns:
                    intraday['Date'] = pd.to_datetime(intraday['Date'], utc=True).dt.tz_localize(None)
                    intraday.set_index('Date', inplace=True)
                    data['intraday'] = intraday.sort_index()
            
            # Load fundamentals
            fund_file = os.path.join(base_path, f"{ticker}_fundamentals.json")
            if os.path.exists(fund_file):
                with open(fund_file, 'r') as f:
                    data['fundamentals'] = json.load(f)
            
            return data if data else None
            
        except Exception as e:
            return None
    
    def calculate_earnings_metrics(self, ticker: str, earnings_date: datetime, data: Dict) -> Dict:
        """Calculate comprehensive earnings metrics"""
        metrics = {
            'ticker': ticker,
            'earnings_date': earnings_date,
            'day0_reaction': 0,
            'day1_return': 0,
            'day3_return': 0,
            'day5_return': 0,
            'day10_return': 0,
            'volume_spike': 1.0,
            'historical_beat_rate': 0.5,
            'is_beat': 0,
            'surprise_pct': 0
        }
        
        if 'daily' not in data:
            return metrics
        
        daily = data['daily']
        
        # Find earnings date in data
        earnings_idx = daily.index.get_indexer([earnings_date], method='nearest')[0]
        if earnings_idx == -1:
            return metrics
        
        actual_earnings_date = daily.index[earnings_idx]
        
        # Calculate returns
        try:
            # Day 0 reaction (earnings day)
            if earnings_idx > 0:
                prev_close = daily.iloc[earnings_idx - 1]['Close']
                earnings_close = daily.iloc[earnings_idx]['Close']
                metrics['day0_reaction'] = ((earnings_close - prev_close) / prev_close) * 100
            
            # Day 1 return
            if earnings_idx + 1 < len(daily):
                day1_close = daily.iloc[earnings_idx + 1]['Close']
                metrics['day1_return'] = ((day1_close - earnings_close) / earnings_close) * 100
            
            # Day 3, 5, 10 returns
            for days, key in [(3, 'day3_return'), (5, 'day5_return'), (10, 'day10_return')]:
                if earnings_idx + days < len(daily):
                    future_close = daily.iloc[earnings_idx + days]['Close']
                    metrics[key] = ((future_close - earnings_close) / earnings_close) * 100
            
            # Volume spike
            if earnings_idx > 0:
                avg_volume = daily.iloc[max(0, earnings_idx-20):earnings_idx]['Volume'].mean()
                earnings_volume = daily.iloc[earnings_idx]['Volume']
                if avg_volume > 0:
                    metrics['volume_spike'] = earnings_volume / avg_volume
            
        except Exception as e:
            pass
        
        # Add fundamentals if available
        if 'fundamentals' in data:
            fund = data['fundamentals']
            metrics['historical_beat_rate'] = fund.get('beat_rate', 0.5)
            metrics['is_beat'] = 1 if fund.get('is_beat', False) else 0
            metrics['surprise_pct'] = fund.get('surprise_pct', 0)
        
        return metrics
    
    def analyze_earnings_event(self, row: pd.Series) -> Optional[Dict]:
        """Analyze a single earnings event"""
        ticker = row['ticker']
        earnings_date = row['date']
        
        # Load stock data
        data = self.load_stock_data(ticker)
        if data is None:
            return None
        
        # Calculate metrics
        metrics = self.calculate_earnings_metrics(ticker, earnings_date, data)
        
        # Determine strategy steps
        steps = self.determine_strategy_steps(metrics)
        metrics.update(steps)
        
        return metrics
    
    def determine_strategy_steps(self, metrics: Dict) -> Dict:
        """Determine which strategy steps would be triggered"""
        steps = {
            'step1_triggered': False,
            'step2_triggered': False,
            'step3_triggered': False,
            'step1_return': 0,
            'step2_return': 0,
            'step3_return': 0
        }
        
        # Step 1: Pre-earnings (based on historical metrics)
        if (metrics['historical_beat_rate'] >= self.params['step1']['min_beat_rate'] and
            metrics['volume_spike'] >= 1.5):  # Assume volume consistency
            steps['step1_triggered'] = True
            steps['step1_return'] = metrics['day10_return']  # Hold through Day 10
        
        # Step 2: Day 0 momentum
        if (metrics['day0_reaction'] >= self.params['step2']['min_day0_reaction'] and
            metrics['volume_spike'] >= self.params['step2']['min_volume_spike']):
            steps['step2_triggered'] = True
            steps['step2_return'] = metrics['day10_return'] - metrics['day0_reaction']
        
        # Step 3: Day 1 continuation
        combined_reaction = metrics['day0_reaction'] + metrics['day1_return']
        if (metrics['day0_reaction'] > 0 and 
            metrics['day1_return'] > 0 and
            combined_reaction >= self.params['step3']['min_combined_reaction']):
            steps['step3_triggered'] = True
            steps['step3_return'] = metrics['day10_return'] - combined_reaction
        
        return steps
    
    def backtest_strategy(self, params: Dict = None) -> Dict:
        """Run backtest with given parameters"""
        if params:
            self.params.update(params)
        
        print(f"\n🔄 Running 3-Step Strategy Backtest...")
        print(f"📊 Parameters: {self.params}")
        
        # Process all earnings events
        results = []
        
        # Use threading for faster processing
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_row = {
                executor.submit(self.analyze_earnings_event, row): row 
                for _, row in self.earnings.iterrows()
            }
            
            for future in as_completed(future_to_row):
                result = future.result()
                if result:
                    results.append(result)
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        if len(df) == 0:
            return {'error': 'No valid results'}
        
        # Calculate strategy performance
        performance = self.calculate_strategy_performance(df)
        
        return {
            'parameters': self.params.copy(),
            'total_events': len(df),
            'performance': performance,
            'detailed_results': df
        }
    
    def calculate_strategy_performance(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive performance metrics"""
        performance = {}
        
        # Overall statistics
        performance['total_events'] = len(df)
        performance['avg_day0_reaction'] = df['day0_reaction'].mean()
        performance['avg_day10_return'] = df['day10_return'].mean()
        performance['day0_win_rate'] = (df['day0_reaction'] > 0).mean() * 100
        performance['day10_win_rate'] = (df['day10_return'] > 0).mean() * 100
        
        # Step performance
        for step in ['step1', 'step2', 'step3']:
            triggered = df[df[f'{step}_triggered'] == True]
            if len(triggered) > 0:
                returns = triggered[f'{step}_return']
                performance[f'{step}_trades'] = len(triggered)
                performance[f'{step}_win_rate'] = (returns > 0).mean() * 100
                performance[f'{step}_avg_return'] = returns.mean()
                performance[f'{step}_total_return'] = returns.sum()
            else:
                performance[f'{step}_trades'] = 0
                performance[f'{step}_win_rate'] = 0
                performance[f'{step}_avg_return'] = 0
                performance[f'{step}_total_return'] = 0
        
        # Combined strategy performance
        all_returns = []
        for step in ['step1', 'step2', 'step3']:
            triggered = df[df[f'{step}_triggered'] == True]
            if len(triggered) > 0:
                all_returns.extend(triggered[f'{step}_return'].tolist())
        
        if all_returns:
            all_returns = pd.Series(all_returns)
            performance['combined_trades'] = len(all_returns)
            performance['combined_win_rate'] = (all_returns > 0).mean() * 100
            performance['combined_avg_return'] = all_returns.mean()
            performance['combined_total_return'] = all_returns.sum()
            performance['combined_sharpe'] = all_returns.mean() / all_returns.std() if all_returns.std() > 0 else 0
        else:
            performance['combined_trades'] = 0
            performance['combined_win_rate'] = 0
            performance['combined_avg_return'] = 0
            performance['combined_total_return'] = 0
            performance['combined_sharpe'] = 0
        
        return performance
    
    def optimize_parameters(self, param_ranges: Dict = None) -> Dict:
        """Optimize strategy parameters using grid search"""
        if param_ranges is None:
            param_ranges = {
                'step1': {
                    'min_beat_rate': [0.6, 0.7, 0.8],
                    'position_size': [2500, 3000, 3500]
                },
                'step2': {
                    'min_day0_reaction': [0.5, 1.0, 1.5],
                    'min_volume_spike': [1.5, 2.0, 2.5],
                    'position_size': [3500, 4000, 4500]
                },
                'step3': {
                    'min_combined_reaction': [1.5, 2.0, 2.5],
                    'position_size': [4500, 5000, 5500]
                }
            }
        
        print(f"\n🔍 Starting parameter optimization...")
        print(f"📊 Parameter ranges: {param_ranges}")
        
        best_performance = None
        best_params = None
        optimization_results = []
        
        # Generate parameter combinations
        param_combinations = self.generate_param_combinations(param_ranges)
        total_combinations = len(param_combinations)
        
        print(f"🎯 Testing {total_combinations} parameter combinations...")
        
        for i, params in enumerate(param_combinations):
            print(f"Progress: {i+1}/{total_combinations} ({((i+1)/total_combinations)*100:.1f}%)")
            
            # Run backtest with these parameters
            result = self.backtest_strategy(params)
            
            if 'error' not in result:
                performance = result['performance']
                
                # Score based on combined performance
                score = self.calculate_optimization_score(performance)
                performance['optimization_score'] = score
                
                optimization_results.append({
                    'parameters': params,
                    'performance': performance,
                    'score': score
                })
                
                # Track best performance
                if best_performance is None or score > best_performance['score']:
                    best_performance = performance
                    best_params = params
        
        # Sort by score
        optimization_results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'best_parameters': best_params,
            'best_performance': best_performance,
            'all_results': optimization_results,
            'total_tested': total_combinations
        }
    
    def generate_param_combinations(self, param_ranges: Dict) -> List[Dict]:
        """Generate all parameter combinations for grid search"""
        import itertools
        
        # Flatten parameter ranges
        flat_ranges = {}
        for category, params in param_ranges.items():
            for param, values in params.items():
                flat_ranges[f"{category}_{param}"] = values
        
        # Generate combinations
        param_names = list(flat_ranges.keys())
        param_values = list(flat_ranges.values())
        
        combinations = []
        for combo in itertools.product(*param_values):
            params = {}
            for name, value in zip(param_names, combo):
                category, param = name.split('_', 1)
                if category not in params:
                    params[category] = {}
                params[category][param] = value
            
            combinations.append(params)
        
        return combinations
    
    def calculate_optimization_score(self, performance: Dict) -> float:
        """Calculate optimization score for parameter selection"""
        # Weighted score based on multiple factors
        score = 0
        
        # Combined performance (40% weight)
        if performance['combined_trades'] > 0:
            score += performance['combined_win_rate'] * 0.4
            score += min(performance['combined_avg_return'], 20) * 0.2  # Cap at 20%
            score += min(performance['combined_sharpe'], 3) * 0.1  # Cap at 3
        
        # Trade frequency (20% weight)
        trade_frequency = performance['combined_trades'] / performance['total_events'] * 100
        score += min(trade_frequency, 50) * 0.2  # Cap at 50%
        
        # Individual step performance (20% weight)
        for step in ['step1', 'step2', 'step3']:
            if performance[f'{step}_trades'] > 0:
                score += performance[f'{step}_win_rate'] * 0.067  # 20% / 3 steps
        
        return score
    
    def save_results(self, results: Dict, filename: str = None):
        """Save backtest results"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"three_step_backtest_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert DataFrame to dict for JSON serialization
        if 'detailed_results' in results:
            results['detailed_results'] = results['detailed_results'].to_dict('records')
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Results saved to: {filepath}")
        return filepath
    
    def generate_report(self, results: Dict) -> str:
        """Generate comprehensive performance report"""
        report = []
        report.append("=" * 80)
        report.append("3-STEP STRATEGY BACKTEST REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Parameters
        report.append("📊 STRATEGY PARAMETERS:")
        for category, params in results['parameters'].items():
            report.append(f"  {category.upper()}:")
            for param, value in params.items():
                report.append(f"    {param}: {value}")
        report.append("")
        
        # Performance summary
        perf = results['performance']
        report.append("📈 PERFORMANCE SUMMARY:")
        report.append(f"  Total Events Analyzed: {perf['total_events']}")
        report.append(f"  Average Day 0 Reaction: {perf['avg_day0_reaction']:.2f}%")
        report.append(f"  Average Day 10 Return: {perf['avg_day10_return']:.2f}%")
        report.append(f"  Day 0 Win Rate: {perf['day0_win_rate']:.1f}%")
        report.append(f"  Day 10 Win Rate: {perf['day10_win_rate']:.1f}%")
        report.append("")
        
        # Step performance
        report.append("🎯 STEP PERFORMANCE:")
        for step in ['step1', 'step2', 'step3']:
            report.append(f"  {step.upper()}:")
            report.append(f"    Trades: {perf[f'{step}_trades']}")
            report.append(f"    Win Rate: {perf[f'{step}_win_rate']:.1f}%")
            report.append(f"    Avg Return: {perf[f'{step}_avg_return']:.2f}%")
            report.append(f"    Total Return: {perf[f'{step}_total_return']:.2f}%")
        report.append("")
        
        # Combined performance
        report.append("🏆 COMBINED STRATEGY:")
        report.append(f"  Total Trades: {perf['combined_trades']}")
        report.append(f"  Win Rate: {perf['combined_win_rate']:.1f}%")
        report.append(f"  Average Return: {perf['combined_avg_return']:.2f}%")
        report.append(f"  Total Return: {perf['combined_total_return']:.2f}%")
        report.append(f"  Sharpe Ratio: {perf['combined_sharpe']:.2f}")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Main execution function"""
    print("🚀 3-Step Strategy Optimized Backtester")
    print("=" * 50)
    
    # Initialize backtester
    backtester = ThreeStepOptimizedBacktester(
        earnings_file='/home/fellaki10/Documents/UMushroom Investment challange/data/processed/earnings_final.csv',
        data_dir='/home/fellaki10/Documents/UMushroom Investment challange/data/all_stocks_complete',
        output_dir='/home/fellaki10/Documents/UMushroom Investment challange/results'
    )
    
    # Run basic backtest
    print("\n1️⃣ Running Basic Backtest...")
    basic_results = backtester.backtest_strategy()
    
    if 'error' not in basic_results:
        print(backtester.generate_report(basic_results))
        backtester.save_results(basic_results, 'three_step_basic_backtest.json')
    
    # Run optimization
    print("\n2️⃣ Running Parameter Optimization...")
    optimization_results = backtester.optimize_parameters()
    
    if optimization_results['best_parameters']:
        print(f"\n🏆 BEST PARAMETERS FOUND:")
        print(f"Score: {optimization_results['best_performance']['optimization_score']:.2f}")
        print(f"Parameters: {optimization_results['best_parameters']}")
        
        # Save optimization results
        backtester.save_results(optimization_results, 'three_step_optimization_results.json')
        
        # Run final backtest with best parameters
        print("\n3️⃣ Running Final Backtest with Best Parameters...")
        final_results = backtester.backtest_strategy(optimization_results['best_parameters'])
        
        if 'error' not in final_results:
            print(backtester.generate_report(final_results))
            backtester.save_results(final_results, 'three_step_final_backtest.json')
    
    print("\n✅ Backtesting and optimization complete!")


if __name__ == "__main__":
    main()
