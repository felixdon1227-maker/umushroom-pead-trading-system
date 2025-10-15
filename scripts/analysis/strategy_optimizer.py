#!/usr/bin/env python3
"""
Comprehensive Strategy Optimizer with Grid Search
Tests all combinations of entry/exit/filters to find optimal long-only strategy
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class StrategyOptimizer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.output_dir = self.base_dir / 'strategy2_analysis'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load comprehensive data
        self.load_data()
        
        # Results storage
        self.all_results = []
        
    def load_data(self):
        """Load comprehensive earnings data"""
        data_file = self.output_dir / 'strategy2_comprehensive_data.csv'
        
        if not data_file.exists():
            raise FileNotFoundError(f"Data file not found: {data_file}")
        
        self.df = pd.read_csv(data_file)
        print(f"✓ Loaded {len(self.df)} earnings events from {self.df['ticker'].nunique()} stocks")
        
        # Clean data
        self.df = self.df[self.df['day10_return'].notna()].copy()
        print(f"✓ After filtering: {len(self.df)} events with complete data")
    
    def apply_entry_filter(self, df, entry_strategy, filters):
        """Apply entry conditions and filters"""
        mask = pd.Series(True, index=df.index)
        
        # Entry strategy conditions
        if entry_strategy == 'positive_any':
            mask &= df['day0_reaction'] > 0
        elif entry_strategy == 'positive_strong':
            mask &= df['day0_reaction'] > 2
        elif entry_strategy == 'negative_conservative':
            mask &= (df['day0_reaction'] < -2) & (df['day0_reaction'] > -5)
        elif entry_strategy == 'negative_aggressive':
            mask &= df['day0_reaction'] < -2
        elif entry_strategy == 'day1_reversal':
            mask &= (df['day0_reaction'] < 0) & (df['day1_reaction'] > 0)
        elif entry_strategy == 'mixed':
            mask &= (df['day0_reaction'] > 0) | (
                (df['day0_reaction'] < -3) & (df['historical_beat_rate'] > 0.75)
            )
        
        # Apply filters
        if 'volume_spike_min' in filters:
            mask &= df['volume_spike'] > filters['volume_spike_min']
        
        if 'beta_min' in filters:
            mask &= df['beta'] > filters['beta_min']
        if 'beta_max' in filters:
            mask &= df['beta'] < filters['beta_max']
        
        if 'vix_max' in filters and df['vix'].notna().any():
            mask &= (df['vix'] < filters['vix_max']) | df['vix'].isna()
        
        if 'beat_rate_min' in filters:
            mask &= df['historical_beat_rate'] > filters['beat_rate_min']
        
        if 'consecutive_beats_min' in filters:
            mask &= df['consecutive_beats'] >= filters['consecutive_beats_min']
        
        if 'market_cap_min' in filters:
            mask &= df['market_cap'] > filters['market_cap_min']
        
        if 'surprise_min' in filters:
            mask &= df['surprise_pct'] > filters['surprise_min']
        
        return df[mask]
    
    def calculate_position_size(self, row, sizing_method, base_capital=4000):
        """Calculate position size based on method"""
        if sizing_method == 'fixed':
            return base_capital
        
        elif sizing_method == 'signal_based':
            # Size based on Day 0 reaction strength
            if abs(row['day0_reaction']) > 5:
                return base_capital * 1.5  # $6k
            elif abs(row['day0_reaction']) > 2:
                return base_capital  # $4k
            else:
                return base_capital * 0.75  # $3k
        
        elif sizing_method == 'risk_based':
            # Size inversely to beta (lower beta = larger position)
            if pd.isna(row['beta']):
                return base_capital
            if row['beta'] < 1.0:
                return base_capital * 1.25
            elif row['beta'] > 1.5:
                return base_capital * 0.75
            else:
                return base_capital
        
        elif sizing_method == 'tiered':
            # Current best practice
            if row['day0_reaction'] > 5 or row['day0_reaction'] < -5:
                return 6000
            elif abs(row['day0_reaction']) > 2:
                return 4000
            else:
                return 3000
        
        return base_capital
    
    def simulate_trade(self, row, exit_day, stop_loss_pct, take_profit_pct):
        """Simulate a single trade with stops"""
        # Check each day for stop/target hit
        for day in range(1, exit_day + 1):
            day_col = f'day{day}_return'
            if day_col not in row.index or pd.isna(row[day_col]):
                continue
            
            day_return = row[day_col]
            
            # Check stop loss
            if day_return <= stop_loss_pct:
                return stop_loss_pct, day, 'stop'
            
            # Check take profit
            if day_return >= take_profit_pct:
                return take_profit_pct, day, 'target'
        
        # Exit at time limit
        exit_col = f'day{exit_day}_return'
        if exit_col in row.index and not pd.isna(row[exit_col]):
            return row[exit_col], exit_day, 'time'
        
        return None, None, None
    
    def test_strategy(self, entry_strategy, exit_day, sizing_method, filters, 
                     stop_loss_pct=-8, take_profit_pct=12):
        """Test a complete strategy configuration"""
        # Apply entry filters
        filtered_df = self.apply_entry_filter(self.df, entry_strategy, filters)
        
        if len(filtered_df) == 0:
            return None
        
        # Simulate all trades
        trades = []
        for _, row in filtered_df.iterrows():
            position_size = self.calculate_position_size(row, sizing_method)
            trade_return, exit_day_actual, exit_reason = self.simulate_trade(
                row, exit_day, stop_loss_pct, take_profit_pct
            )
            
            if trade_return is not None:
                trades.append({
                    'ticker': row['ticker'],
                    'return_pct': trade_return,
                    'position_size': position_size,
                    'pnl': position_size * trade_return / 100,
                    'exit_day': exit_day_actual,
                    'exit_reason': exit_reason,
                    'day0_reaction': row['day0_reaction']
                })
        
        if len(trades) == 0:
            return None
        
        # Calculate performance metrics
        trades_df = pd.DataFrame(trades)
        
        avg_return = trades_df['return_pct'].mean()
        median_return = trades_df['return_pct'].median()
        win_rate = (trades_df['return_pct'] > 0).sum() / len(trades_df) * 100
        
        winners = trades_df[trades_df['return_pct'] > 0]
        losers = trades_df[trades_df['return_pct'] <= 0]
        
        avg_win = winners['return_pct'].mean() if len(winners) > 0 else 0
        avg_loss = losers['return_pct'].mean() if len(losers) > 0 else 0
        
        # Expectancy
        expectancy = (avg_win * win_rate / 100) + (avg_loss * (100 - win_rate) / 100)
        
        # Sharpe ratio (simplified)
        returns_std = trades_df['return_pct'].std()
        sharpe = avg_return / returns_std if returns_std > 0 else 0
        
        # Max drawdown (simplified - consecutive losses)
        max_dd = 0
        current_dd = 0
        for ret in trades_df['return_pct']:
            if ret < 0:
                current_dd += ret
                max_dd = min(max_dd, current_dd)
            else:
                current_dd = 0
        
        # Total PnL
        total_pnl = trades_df['pnl'].sum()
        
        # Composite score
        trade_count_score = min(len(trades_df) / 50, 1.0)  # Normalize to 1.0 at 50 trades
        score = (expectancy * 0.4) + (win_rate * 0.3) + (trade_count_score * 20 * 0.2) + (sharpe * 0.1)
        
        return {
            'entry_strategy': entry_strategy,
            'exit_day': exit_day,
            'sizing_method': sizing_method,
            'filters': str(filters),
            'stop_loss': stop_loss_pct,
            'take_profit': take_profit_pct,
            'trade_count': len(trades_df),
            'avg_return': avg_return,
            'median_return': median_return,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'expectancy': expectancy,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'total_pnl': total_pnl,
            'score': score,
            'stopped_out': (trades_df['exit_reason'] == 'stop').sum(),
            'hit_target': (trades_df['exit_reason'] == 'target').sum(),
            'time_exit': (trades_df['exit_reason'] == 'time').sum()
        }
    
    def phase1_entry_strategies(self):
        """Phase 1: Test entry strategies with various filters"""
        print("\n" + "=" * 80)
        print("PHASE 1: ENTRY STRATEGY SELECTION")
        print("=" * 80)
        
        entry_strategies = [
            'positive_any',
            'positive_strong',
            'negative_conservative',
            'negative_aggressive',
            'day1_reversal',
            'mixed'
        ]
        
        filter_combinations = [
            {},  # No filters
            {'volume_spike_min': 1.5},
            {'volume_spike_min': 2.0},
            {'volume_spike_min': 2.0, 'beat_rate_min': 0.6},
            {'volume_spike_min': 2.0, 'beat_rate_min': 0.7},
            {'volume_spike_min': 2.0, 'beat_rate_min': 0.7, 'vix_max': 20},
            {'beat_rate_min': 0.7, 'consecutive_beats_min': 2},
            {'beat_rate_min': 0.8, 'consecutive_beats_min': 2},
            {'beta_min': 1.0, 'beta_max': 1.5},
            {'market_cap_min': 1e9}  # >$1B
        ]
        
        # Use baseline exit day for comparison
        baseline_exit = 10
        baseline_sizing = 'tiered'
        
        results = []
        total_tests = len(entry_strategies) * len(filter_combinations)
        test_num = 0
        
        print(f"\nTesting {total_tests} combinations...\n")
        
        for entry_strategy in entry_strategies:
            for filters in filter_combinations:
                test_num += 1
                
                result = self.test_strategy(
                    entry_strategy, baseline_exit, baseline_sizing, filters
                )
                
                if result is not None:
                    results.append(result)
                    
                    if test_num % 10 == 0:
                        print(f"  [{test_num}/{total_tests}] {entry_strategy:25} | "
                              f"Trades: {result['trade_count']:4} | "
                              f"Return: {result['avg_return']:+6.2f}% | "
                              f"Win: {result['win_rate']:5.1f}% | "
                              f"Score: {result['score']:6.2f}")
        
        results_df = pd.DataFrame(results).sort_values('score', ascending=False)
        
        print(f"\n✓ Phase 1 Complete: Tested {len(results)} valid combinations")
        print(f"\nTop 5 Entry Strategies:")
        print(results_df[['entry_strategy', 'filters', 'trade_count', 'avg_return', 
                          'win_rate', 'expectancy', 'score']].head().to_string(index=False))
        
        # Get top 3 for next phase
        top_3 = results_df.head(3).to_dict('records')
        
        return results_df, top_3
    
    def phase2_exit_timing(self, top_entries):
        """Phase 2: Optimize exit timing for top entries"""
        print("\n" + "=" * 80)
        print("PHASE 2: EXIT TIMING OPTIMIZATION")
        print("=" * 80)
        
        exit_days = [3, 5, 7, 10, 15]
        
        results = []
        total_tests = len(top_entries) * len(exit_days)
        test_num = 0
        
        print(f"\nTesting {total_tests} combinations...\n")
        
        for entry_config in top_entries:
            entry_strategy = entry_config['entry_strategy']
            filters = eval(entry_config['filters'])
            sizing = entry_config['sizing_method']
            
            print(f"\nOptimizing exit for: {entry_strategy}")
            
            for exit_day in exit_days:
                test_num += 1
                
                result = self.test_strategy(entry_strategy, exit_day, sizing, filters)
                
                if result is not None:
                    results.append(result)
                    print(f"  Day {exit_day:2}: Return: {result['avg_return']:+6.2f}% | "
                          f"Win: {result['win_rate']:5.1f}% | Score: {result['score']:6.2f}")
        
        results_df = pd.DataFrame(results).sort_values('score', ascending=False)
        
        print(f"\n✓ Phase 2 Complete: Tested {len(results)} combinations")
        print(f"\nTop 3 Entry/Exit Combinations:")
        print(results_df[['entry_strategy', 'exit_day', 'trade_count', 'avg_return', 
                          'win_rate', 'score']].head(3).to_string(index=False))
        
        top_3 = results_df.head(3).to_dict('records')
        
        return results_df, top_3
    
    def phase3_position_sizing(self, top_strategies):
        """Phase 3: Optimize position sizing"""
        print("\n" + "=" * 80)
        print("PHASE 3: POSITION SIZING OPTIMIZATION")
        print("=" * 80)
        
        sizing_methods = ['fixed', 'signal_based', 'risk_based', 'tiered']
        
        results = []
        total_tests = len(top_strategies) * len(sizing_methods)
        test_num = 0
        
        print(f"\nTesting {total_tests} combinations...\n")
        
        for strategy_config in top_strategies:
            entry_strategy = strategy_config['entry_strategy']
            exit_day = strategy_config['exit_day']
            filters = eval(strategy_config['filters'])
            
            print(f"\nOptimizing sizing for: {entry_strategy} (Exit Day {exit_day})")
            
            for sizing in sizing_methods:
                test_num += 1
                
                result = self.test_strategy(entry_strategy, exit_day, sizing, filters)
                
                if result is not None:
                    results.append(result)
                    print(f"  {sizing:15}: Return: {result['avg_return']:+6.2f}% | "
                          f"Win: {result['win_rate']:5.1f}% | "
                          f"Total PnL: ${result['total_pnl']:,.0f} | "
                          f"Score: {result['score']:6.2f}")
        
        results_df = pd.DataFrame(results).sort_values('score', ascending=False)
        
        print(f"\n✓ Phase 3 Complete: Tested {len(results)} combinations")
        print(f"\nTop 3 Strategies with Sizing:")
        print(results_df[['entry_strategy', 'exit_day', 'sizing_method', 'avg_return', 
                          'win_rate', 'total_pnl', 'score']].head(3).to_string(index=False))
        
        top_3 = results_df.head(3).to_dict('records')
        
        return results_df, top_3
    
    def phase4_fine_tune(self, best_strategy):
        """Phase 4: Fine-tune filter thresholds"""
        print("\n" + "=" * 80)
        print("PHASE 4: FINE-TUNE FILTERS")
        print("=" * 80)
        
        entry_strategy = best_strategy['entry_strategy']
        exit_day = best_strategy['exit_day']
        sizing = best_strategy['sizing_method']
        
        print(f"\nFine-tuning: {entry_strategy} | Exit Day {exit_day} | Sizing: {sizing}\n")
        
        # Test various filter combinations
        filter_variations = [
            {},
            {'volume_spike_min': 1.5},
            {'volume_spike_min': 2.0},
            {'volume_spike_min': 2.5},
            {'volume_spike_min': 3.0},
            {'volume_spike_min': 2.0, 'beat_rate_min': 0.6},
            {'volume_spike_min': 2.0, 'beat_rate_min': 0.65},
            {'volume_spike_min': 2.0, 'beat_rate_min': 0.7},
            {'volume_spike_min': 2.0, 'beat_rate_min': 0.75},
            {'volume_spike_min': 2.0, 'beat_rate_min': 0.7, 'vix_max': 25},
            {'volume_spike_min': 2.0, 'beat_rate_min': 0.7, 'vix_max': 20},
            {'volume_spike_min': 2.0, 'beat_rate_min': 0.7, 'vix_max': 15},
            {'beat_rate_min': 0.7, 'consecutive_beats_min': 1},
            {'beat_rate_min': 0.7, 'consecutive_beats_min': 2},
            {'beat_rate_min': 0.7, 'consecutive_beats_min': 3},
            {'beta_min': 0.8, 'beta_max': 1.2},
            {'beta_min': 1.0, 'beta_max': 1.5},
            {'beta_min': 1.2, 'beta_max': 2.0},
            {'market_cap_min': 1e9},
            {'market_cap_min': 5e9},
            {'market_cap_min': 1e10},
        ]
        
        # Also test different stops/targets
        stop_target_combos = [
            (-5, 10),
            (-8, 12),
            (-10, 15),
        ]
        
        results = []
        
        for filters in filter_variations:
            for stop, target in stop_target_combos:
                result = self.test_strategy(
                    entry_strategy, exit_day, sizing, filters, stop, target
                )
                
                if result is not None and result['trade_count'] >= 20:  # Min sample size
                    results.append(result)
        
        results_df = pd.DataFrame(results).sort_values('score', ascending=False)
        
        print(f"✓ Phase 4 Complete: Tested {len(results)} filter combinations")
        print(f"\nTop 10 Optimized Strategies:")
        print(results_df[['filters', 'stop_loss', 'take_profit', 'trade_count', 
                          'avg_return', 'win_rate', 'expectancy', 'score']].head(10).to_string(index=False))
        
        return results_df
    
    def run_full_optimization(self):
        """Run all 4 phases of optimization"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE STRATEGY OPTIMIZATION")
        print("=" * 80)
        print(f"Dataset: {len(self.df)} earnings events")
        print(f"Stocks: {self.df['ticker'].nunique()}")
        print(f"Date Range: {self.df['earnings_date'].min()} to {self.df['earnings_date'].max()}")
        
        # Phase 1: Entry strategies
        phase1_results, top_entries = self.phase1_entry_strategies()
        self.all_results.append(('phase1', phase1_results))
        
        # Phase 2: Exit timing
        phase2_results, top_exit_combos = self.phase2_exit_timing(top_entries)
        self.all_results.append(('phase2', phase2_results))
        
        # Phase 3: Position sizing
        phase3_results, top_sized_strategies = self.phase3_position_sizing(top_exit_combos)
        self.all_results.append(('phase3', phase3_results))
        
        # Phase 4: Fine-tune
        best_strategy = top_sized_strategies[0]
        phase4_results = self.phase4_fine_tune(best_strategy)
        self.all_results.append(('phase4', phase4_results))
        
        # Final best strategy
        final_best = phase4_results.iloc[0]
        
        print("\n" + "=" * 80)
        print("🏆 OPTIMIZATION COMPLETE!")
        print("=" * 80)
        
        return final_best, phase4_results
    
    def save_results(self, final_best, all_optimized):
        """Save optimization results"""
        # Save all results
        output_file = self.output_dir / 'optimization_results.csv'
        all_optimized.to_csv(output_file, index=False)
        print(f"\n✓ Saved all results to: {output_file}")
        
        # Save best strategy details
        best_file = self.output_dir / 'best_strategy_config.csv'
        pd.DataFrame([final_best]).to_csv(best_file, index=False)
        print(f"✓ Saved best strategy to: {best_file}")
        
        return output_file

def main():
    """Main execution"""
    base_dir = Path(__file__).parent.parent.parent
    
    optimizer = StrategyOptimizer(base_dir)
    
    # Run full optimization
    final_best, all_results = optimizer.run_full_optimization()
    
    # Save results
    optimizer.save_results(final_best, all_results)
    
    # Display final recommendation
    print("\n" + "=" * 80)
    print("🎯 FINAL OPTIMIZED STRATEGY")
    print("=" * 80)
    print(f"\nEntry Strategy: {final_best['entry_strategy']}")
    print(f"Exit Day: {final_best['exit_day']}")
    print(f"Position Sizing: {final_best['sizing_method']}")
    print(f"Filters: {final_best['filters']}")
    print(f"Stop Loss: {final_best['stop_loss']}%")
    print(f"Take Profit: {final_best['take_profit']}%")
    print(f"\nPERFORMANCE:")
    print(f"  Trade Count: {final_best['trade_count']}")
    print(f"  Average Return: {final_best['avg_return']:+.2f}%")
    print(f"  Win Rate: {final_best['win_rate']:.1f}%")
    print(f"  Expectancy: {final_best['expectancy']:+.2f}%")
    print(f"  Total PnL: ${final_best['total_pnl']:,.0f}")
    print(f"  Sharpe Ratio: {final_best['sharpe']:.2f}")
    print(f"  Max Drawdown: {final_best['max_drawdown']:.2f}%")
    print(f"  Score: {final_best['score']:.2f}")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

