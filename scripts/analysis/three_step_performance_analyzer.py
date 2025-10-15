"""
3-Step Strategy Performance Analyzer
===================================

Comprehensive performance analysis system for the 3-Step Earnings Strategy:
- Advanced metrics calculation
- Risk analysis
- Sector performance breakdown
- Time-based analysis
- Competition simulation
- Visualization generation

Author: UMushroom Investment Strategy
Date: October 2025
"""

import pandas as pd
import numpy as np
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class ThreeStepPerformanceAnalyzer:
    """
    Comprehensive performance analysis for 3-Step Strategy
    """
    
    def __init__(self, results_file: str = None, output_dir: str = 'results'):
        self.results_file = results_file
        self.output_dir = output_dir
        self.results_data = None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Load results if provided
        if results_file and os.path.exists(results_file):
            self.load_results(results_file)
    
    def load_results(self, results_file: str):
        """Load backtest results from file"""
        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
            
            self.results_data = data
            self.df = pd.DataFrame(data['detailed_results'])
            
            print(f"✅ Loaded results: {len(self.df)} events")
            return True
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return False
    
    def calculate_advanced_metrics(self, returns: pd.Series) -> Dict:
        """Calculate advanced performance metrics"""
        if len(returns) == 0:
            return {}
        
        metrics = {}
        
        # Basic statistics
        metrics['count'] = len(returns)
        metrics['mean'] = returns.mean()
        metrics['median'] = returns.median()
        metrics['std'] = returns.std()
        metrics['min'] = returns.min()
        metrics['max'] = returns.max()
        
        # Win/Loss statistics
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        
        metrics['win_rate'] = len(wins) / len(returns) * 100
        metrics['avg_win'] = wins.mean() if len(wins) > 0 else 0
        metrics['avg_loss'] = losses.mean() if len(losses) > 0 else 0
        metrics['win_loss_ratio'] = abs(metrics['avg_win'] / metrics['avg_loss']) if metrics['avg_loss'] != 0 else 0
        
        # Risk metrics
        metrics['sharpe_ratio'] = metrics['mean'] / metrics['std'] if metrics['std'] > 0 else 0
        metrics['sortino_ratio'] = metrics['mean'] / losses.std() if len(losses) > 0 and losses.std() > 0 else 0
        
        # Drawdown analysis
        cumulative = (1 + returns / 100).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        metrics['max_drawdown'] = drawdown.min() * 100
        metrics['avg_drawdown'] = drawdown[drawdown < 0].mean() * 100
        
        # Calmar ratio
        metrics['calmar_ratio'] = metrics['mean'] / abs(metrics['max_drawdown']) if metrics['max_drawdown'] != 0 else 0
        
        # Expectancy
        metrics['expectancy'] = (metrics['avg_win'] * metrics['win_rate'] / 100) + (metrics['avg_loss'] * (100 - metrics['win_rate']) / 100)
        
        # Profit factor
        total_wins = wins.sum() if len(wins) > 0 else 0
        total_losses = abs(losses.sum()) if len(losses) > 0 else 0
        metrics['profit_factor'] = total_wins / total_losses if total_losses > 0 else 0
        
        return metrics
    
    def analyze_step_performance(self) -> Dict:
        """Analyze performance by strategy step"""
        if self.df is None:
            return {}
        
        step_analysis = {}
        
        for step in ['step1', 'step2', 'step3']:
            triggered = self.df[self.df[f'{step}_triggered'] == True]
            
            if len(triggered) > 0:
                returns = triggered[f'{step}_return']
                step_analysis[step] = self.calculate_advanced_metrics(returns)
                step_analysis[step]['trade_frequency'] = len(triggered) / len(self.df) * 100
            else:
                step_analysis[step] = {'count': 0, 'trade_frequency': 0}
        
        return step_analysis
    
    def analyze_sector_performance(self) -> Dict:
        """Analyze performance by sector"""
        if self.df is None or 'sector' not in self.df.columns:
            return {}
        
        sector_analysis = {}
        
        for sector in self.df['sector'].unique():
            sector_data = self.df[self.df['sector'] == sector]
            
            # Calculate combined returns for this sector
            all_returns = []
            for step in ['step1', 'step2', 'step3']:
                triggered = sector_data[sector_data[f'{step}_triggered'] == True]
                if len(triggered) > 0:
                    all_returns.extend(triggered[f'{step}_return'].tolist())
            
            if all_returns:
                returns = pd.Series(all_returns)
                sector_analysis[sector] = self.calculate_advanced_metrics(returns)
                sector_analysis[sector]['total_trades'] = len(all_returns)
            else:
                sector_analysis[sector] = {'count': 0, 'total_trades': 0}
        
        return sector_analysis
    
    def analyze_time_performance(self) -> Dict:
        """Analyze performance over time"""
        if self.df is None:
            return {}
        
        time_analysis = {}
        
        # Monthly analysis
        self.df['month'] = pd.to_datetime(self.df['earnings_date']).dt.to_period('M')
        
        monthly_returns = []
        for month in self.df['month'].unique():
            month_data = self.df[self.df['month'] == month]
            
            # Calculate combined returns for this month
            all_returns = []
            for step in ['step1', 'step2', 'step3']:
                triggered = month_data[month_data[f'{step}_triggered'] == True]
                if len(triggered) > 0:
                    all_returns.extend(triggered[f'{step}_return'].tolist())
            
            if all_returns:
                returns = pd.Series(all_returns)
                time_analysis[str(month)] = self.calculate_advanced_metrics(returns)
                time_analysis[str(month)]['total_trades'] = len(all_returns)
        
        return time_analysis
    
    def analyze_earnings_timing_performance(self) -> Dict:
        """Analyze performance by earnings timing (AM vs PM)"""
        if self.df is None or 'time' not in self.df.columns:
            return {}
        
        timing_analysis = {}
        
        for timing in self.df['time'].unique():
            timing_data = self.df[self.df['time'] == timing]
            
            # Calculate combined returns for this timing
            all_returns = []
            for step in ['step1', 'step2', 'step3']:
                triggered = timing_data[timing_data[f'{step}_triggered'] == True]
                if len(triggered) > 0:
                    all_returns.extend(triggered[f'{step}_return'].tolist())
            
            if all_returns:
                returns = pd.Series(all_returns)
                timing_analysis[timing] = self.calculate_advanced_metrics(returns)
                timing_analysis[timing]['total_trades'] = len(all_returns)
        
        return timing_analysis
    
    def simulate_competition_performance(self, duration_weeks: int = 4) -> Dict:
        """Simulate competition performance over specified duration"""
        if self.df is None:
            return {}
        
        # Calculate trade frequency
        total_events = len(self.df)
        date_range = (self.df['earnings_date'].max() - self.df['earnings_date'].min()).days
        years = date_range / 365.25
        
        trades_per_year = 0
        for step in ['step1', 'step2', 'step3']:
            triggered = self.df[self.df[f'{step}_triggered'] == True]
            trades_per_year += len(triggered)
        
        trades_per_year = trades_per_year / years if years > 0 else 0
        trades_per_week = trades_per_year / 52
        expected_trades = int(trades_per_week * duration_weeks)
        
        # Calculate average performance
        all_returns = []
        for step in ['step1', 'step2', 'step3']:
            triggered = self.df[self.df[f'{step}_triggered'] == True]
            if len(triggered) > 0:
                all_returns.extend(triggered[f'{step}_return'].tolist())
        
        if all_returns:
            returns = pd.Series(all_returns)
            avg_return = returns.mean()
            win_rate = (returns > 0).mean() * 100
            
            # Simulate different scenarios
            scenarios = {
                'conservative': int(expected_trades * 0.7),
                'expected': expected_trades,
                'optimistic': int(expected_trades * 1.3)
            }
            
            simulation_results = {}
            for scenario_name, n_trades in scenarios.items():
                # Simple simulation
                simple_total = avg_return * n_trades
                compound_total = ((1 + avg_return/100) ** n_trades - 1) * 100
                
                simulation_results[scenario_name] = {
                    'trades': n_trades,
                    'simple_return': simple_total,
                    'compound_return': compound_total,
                    'win_probability': (win_rate/100) ** n_trades * 100,
                    'expected_wins': n_trades * win_rate / 100,
                    'expected_losses': n_trades * (1 - win_rate / 100)
                }
            
            return {
                'trade_frequency': {
                    'per_year': trades_per_year,
                    'per_week': trades_per_week,
                    'expected_4_weeks': expected_trades
                },
                'average_performance': {
                    'avg_return': avg_return,
                    'win_rate': win_rate,
                    'total_trades_analyzed': len(all_returns)
                },
                'scenarios': simulation_results
            }
        
        return {}
    
    def generate_visualizations(self):
        """Generate performance visualizations"""
        if self.df is None:
            return
        
        # Set style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('3-Step Strategy Performance Analysis', fontsize=16, fontweight='bold')
        
        # 1. Step Performance Comparison
        step_metrics = self.analyze_step_performance()
        steps = list(step_metrics.keys())
        win_rates = [step_metrics[step].get('win_rate', 0) for step in steps]
        avg_returns = [step_metrics[step].get('mean', 0) for step in steps]
        
        axes[0, 0].bar(steps, win_rates, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        axes[0, 0].set_title('Win Rate by Step')
        axes[0, 0].set_ylabel('Win Rate (%)')
        axes[0, 0].set_ylim(0, 100)
        
        # 2. Average Returns by Step
        axes[0, 1].bar(steps, avg_returns, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
        axes[0, 1].set_title('Average Return by Step')
        axes[0, 1].set_ylabel('Average Return (%)')
        axes[0, 1].axhline(y=0, color='red', linestyle='--', alpha=0.7)
        
        # 3. Sector Performance
        sector_metrics = self.analyze_sector_performance()
        if sector_metrics:
            sectors = list(sector_metrics.keys())
            sector_returns = [sector_metrics[sector].get('mean', 0) for sector in sectors]
            
            axes[0, 2].bar(sectors, sector_returns)
            axes[0, 2].set_title('Average Return by Sector')
            axes[0, 2].set_ylabel('Average Return (%)')
            axes[0, 2].tick_params(axis='x', rotation=45)
            axes[0, 2].axhline(y=0, color='red', linestyle='--', alpha=0.7)
        
        # 4. Return Distribution
        all_returns = []
        for step in ['step1', 'step2', 'step3']:
            triggered = self.df[self.df[f'{step}_triggered'] == True]
            if len(triggered) > 0:
                all_returns.extend(triggered[f'{step}_return'].tolist())
        
        if all_returns:
            axes[1, 0].hist(all_returns, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            axes[1, 0].set_title('Return Distribution')
            axes[1, 0].set_xlabel('Return (%)')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].axvline(x=0, color='red', linestyle='--', alpha=0.7)
        
        # 5. Cumulative Returns
        if all_returns:
            cumulative_returns = (1 + pd.Series(all_returns) / 100).cumprod()
            axes[1, 1].plot(cumulative_returns.index, cumulative_returns.values, linewidth=2)
            axes[1, 1].set_title('Cumulative Returns')
            axes[1, 1].set_xlabel('Trade Number')
            axes[1, 1].set_ylabel('Cumulative Return')
            axes[1, 1].axhline(y=1, color='red', linestyle='--', alpha=0.7)
        
        # 6. Risk-Return Scatter
        if all_returns:
            returns = pd.Series(all_returns)
            axes[1, 2].scatter(returns.std(), returns.mean(), s=100, alpha=0.7)
            axes[1, 2].set_title('Risk vs Return')
            axes[1, 2].set_xlabel('Standard Deviation (%)')
            axes[1, 2].set_ylabel('Average Return (%)')
            axes[1, 2].axhline(y=0, color='red', linestyle='--', alpha=0.7)
            axes[1, 2].axvline(x=0, color='red', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        # Save plot
        plot_file = os.path.join(self.output_dir, 'three_step_performance_analysis.png')
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"✅ Performance visualization saved: {plot_file}")
        
        plt.show()
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive performance report"""
        if self.df is None:
            return "No data available for analysis"
        
        report = []
        report.append("=" * 80)
        report.append("3-STEP STRATEGY COMPREHENSIVE PERFORMANCE ANALYSIS")
        report.append("=" * 80)
        report.append("")
        
        # Overall statistics
        report.append("📊 OVERALL STATISTICS:")
        report.append(f"  Total Events Analyzed: {len(self.df)}")
        report.append(f"  Date Range: {self.df['earnings_date'].min()} to {self.df['earnings_date'].max()}")
        report.append(f"  Unique Stocks: {self.df['ticker'].nunique()}")
        report.append("")
        
        # Step performance
        step_analysis = self.analyze_step_performance()
        report.append("🎯 STEP PERFORMANCE ANALYSIS:")
        for step, metrics in step_analysis.items():
            if metrics.get('count', 0) > 0:
                report.append(f"  {step.upper()}:")
                report.append(f"    Trades: {metrics['count']}")
                report.append(f"    Win Rate: {metrics['win_rate']:.1f}%")
                report.append(f"    Avg Return: {metrics['mean']:.2f}%")
                report.append(f"    Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
                report.append(f"    Max Drawdown: {metrics['max_drawdown']:.2f}%")
                report.append(f"    Trade Frequency: {metrics['trade_frequency']:.1f}%")
        report.append("")
        
        # Sector performance
        sector_analysis = self.analyze_sector_performance()
        if sector_analysis:
            report.append("🏢 SECTOR PERFORMANCE:")
            for sector, metrics in sector_analysis.items():
                if metrics.get('count', 0) > 0:
                    report.append(f"  {sector}:")
                    report.append(f"    Trades: {metrics['total_trades']}")
                    report.append(f"    Win Rate: {metrics['win_rate']:.1f}%")
                    report.append(f"    Avg Return: {metrics['mean']:.2f}%")
                    report.append(f"    Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            report.append("")
        
        # Competition simulation
        competition_analysis = self.simulate_competition_performance()
        if competition_analysis:
            report.append("🏆 COMPETITION SIMULATION (4 WEEKS):")
            report.append(f"  Expected Trades: {competition_analysis['trade_frequency']['expected_4_weeks']}")
            report.append(f"  Average Return: {competition_analysis['average_performance']['avg_return']:.2f}%")
            report.append(f"  Win Rate: {competition_analysis['average_performance']['win_rate']:.1f}%")
            report.append("")
            report.append("  SCENARIOS:")
            for scenario, data in competition_analysis['scenarios'].items():
                report.append(f"    {scenario.upper()}:")
                report.append(f"      Trades: {data['trades']}")
                report.append(f"      Simple Return: {data['simple_return']:.2f}%")
                report.append(f"      Compound Return: {data['compound_return']:.2f}%")
                report.append(f"      Win Probability: {data['win_probability']:.1f}%")
            report.append("")
        
        # Risk analysis
        all_returns = []
        for step in ['step1', 'step2', 'step3']:
            triggered = self.df[self.df[f'{step}_triggered'] == True]
            if len(triggered) > 0:
                all_returns.extend(triggered[f'{step}_return'].tolist())
        
        if all_returns:
            returns = pd.Series(all_returns)
            risk_metrics = self.calculate_advanced_metrics(returns)
            
            report.append("⚠️ RISK ANALYSIS:")
            report.append(f"  Total Trades: {risk_metrics['count']}")
            report.append(f"  Win Rate: {risk_metrics['win_rate']:.1f}%")
            report.append(f"  Average Win: {risk_metrics['avg_win']:.2f}%")
            report.append(f"  Average Loss: {risk_metrics['avg_loss']:.2f}%")
            report.append(f"  Win/Loss Ratio: {risk_metrics['win_loss_ratio']:.2f}")
            report.append(f"  Sharpe Ratio: {risk_metrics['sharpe_ratio']:.2f}")
            report.append(f"  Sortino Ratio: {risk_metrics['sortino_ratio']:.2f}")
            report.append(f"  Max Drawdown: {risk_metrics['max_drawdown']:.2f}%")
            report.append(f"  Calmar Ratio: {risk_metrics['calmar_ratio']:.2f}")
            report.append(f"  Expectancy: {risk_metrics['expectancy']:.2f}%")
            report.append(f"  Profit Factor: {risk_metrics['profit_factor']:.2f}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_analysis_results(self, filename: str = None):
        """Save comprehensive analysis results"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"three_step_performance_analysis_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Compile all analysis results
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_stats': {
                'total_events': len(self.df) if self.df is not None else 0,
                'unique_stocks': self.df['ticker'].nunique() if self.df is not None else 0,
                'date_range': {
                    'start': str(self.df['earnings_date'].min()) if self.df is not None else None,
                    'end': str(self.df['earnings_date'].max()) if self.df is not None else None
                }
            },
            'step_analysis': self.analyze_step_performance(),
            'sector_analysis': self.analyze_sector_performance(),
            'time_analysis': self.analyze_time_performance(),
            'timing_analysis': self.analyze_earnings_timing_performance(),
            'competition_simulation': self.simulate_competition_performance()
        }
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Analysis results saved: {filepath}")
        return filepath


def main():
    """Main execution function"""
    print("🚀 3-Step Strategy Performance Analyzer")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = ThreeStepPerformanceAnalyzer(
        output_dir='/home/fellaki10/Documents/UMushroom Investment challange/results'
    )
    
    # Load results if available
    results_file = '/home/fellaki10/Documents/UMushroom Investment challange/results/three_step_final_backtest.json'
    if os.path.exists(results_file):
        analyzer.load_results(results_file)
        
        # Generate comprehensive report
        report = analyzer.generate_comprehensive_report()
        print(report)
        
        # Generate visualizations
        analyzer.generate_visualizations()
        
        # Save analysis results
        analyzer.save_analysis_results()
    else:
        print("❌ No results file found. Run backtesting first.")


if __name__ == "__main__":
    main()
