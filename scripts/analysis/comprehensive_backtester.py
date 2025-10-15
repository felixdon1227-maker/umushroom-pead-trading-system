"""
Comprehensive Backtester for 3-Step Earnings Strategy

This backtester simulates the complete strategy over historical data with:
- Realistic position sizing
- Stop loss and take profit execution
- Commission and slippage modeling
- Daily portfolio valuation
- Complete metrics tracking

Author: UMushroom Competition Strategy
Date: October 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import sys
import os

# Import custom modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from filter_engine import FilterEngine, FilterPresets
from metrics_tracker import MetricsTracker


class ComprehensiveBacktester:
    """Complete backtesting engine for earnings strategies"""
    
    def __init__(self, initial_capital: float = 100000,
                 commission_pct: float = 0.001,
                 slippage_pct: float = 0.001):
        """
        Initialize backtester
        
        Parameters:
        - initial_capital: Starting capital
        - commission_pct: Commission as % of trade value (0.001 = 0.1%)
        - slippage_pct: Slippage as % of trade value
        """
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        
        # Initialize components
        self.filter_engine = FilterEngine()
        self.metrics_tracker = MetricsTracker(initial_capital)
        
        # Reset state
        self.reset()
    
    def reset(self):
        """Reset backtester state"""
        self.current_capital = self.initial_capital
        self.active_positions = {}
        self.trade_history = []
        self.daily_values = []
        self.metrics_tracker = MetricsTracker(self.initial_capital)
    
    # ==================== CORE BACKTESTING ====================
    
    def backtest_strategy(self, data: pd.DataFrame,
                         strategy_config: Dict) -> Dict:
        """
        Run complete backtest on historical data
        
        Parameters:
        - data: DataFrame with earnings events and price data
        - strategy_config: Strategy configuration dict
        
        Returns:
        - Dictionary with complete results
        """
        self.reset()
        
        # Ensure data is sorted by date
        data = data.sort_values('earnings_date').copy()
        
        # Get unique dates
        dates = sorted(data['earnings_date'].unique())
        
        print(f"Backtesting {len(data)} events across {len(dates)} dates...")
        
        for i, date in enumerate(dates):
            if i % 100 == 0:
                print(f"Processing date {i+1}/{len(dates)}: {date}")
            
            # Get events for this date
            day_events = data[data['earnings_date'] == date]
            
            # Simulate this day
            self._simulate_day(day_events, strategy_config)
            
            # Update daily portfolio value
            portfolio_value = self._calculate_portfolio_value()
            self.daily_values.append({
                'date': date,
                'value': portfolio_value
            })
            self.metrics_tracker.add_daily_value(date, portfolio_value)
        
        # Close any remaining positions
        self._close_all_positions()
        
        # Calculate final metrics
        results = {
            'strategy_config': strategy_config,
            'metrics': self.metrics_tracker.get_performance_metrics(),
            'risk': self.metrics_tracker.get_risk_metrics(),
            'trades': self.trade_history,
            'daily_values': self.daily_values
        }
        
        return results
    
    def _simulate_day(self, events: pd.DataFrame, config: Dict):
        """Simulate trading for one day"""
        
        # 1. Check existing positions for stops/targets
        self._check_exit_conditions(events)
        
        # 2. Apply strategy filters to find new opportunities
        opportunities = self._find_opportunities(events, config)
        
        # 3. Enter new positions (if capital available)
        self._enter_positions(opportunities, config)
    
    def _find_opportunities(self, events: pd.DataFrame, config: Dict) -> List[Dict]:
        """Find trading opportunities based on strategy config"""
        
        strategy_type = config.get('strategy_type', 'positive_momentum')
        entry_threshold = config.get('entry_threshold', 0)
        
        # Apply filters
        filters = config.get('filters', {})
        if filters:
            filtered = self.filter_engine.apply_comprehensive_filters(events, filters)
        else:
            filtered = events.copy()
        
        # Apply entry conditions
        if strategy_type == 'positive_momentum':
            qualified = filtered[filtered['day0_reaction'] > entry_threshold]
        elif strategy_type == 'strong_positive':
            qualified = filtered[filtered['day0_reaction'] > 2.0]
        elif strategy_type == 'any_positive':
            qualified = filtered[filtered['day0_reaction'] > 0]
        else:
            qualified = filtered
        
        # Convert to opportunities list
        opportunities = []
        for _, row in qualified.iterrows():
            opportunities.append({
                'ticker': row['ticker'],
                'entry_date': row['earnings_date'],
                'entry_price': row.get('entry_price', 100),  # Use actual entry price if available
                'day0_reaction': row.get('day0_reaction', 0),
                'volume_spike': row.get('volume_spike', 1.0),
                'beat_rate': row.get('historical_beat_rate', 0.5),
                'data': row
            })
        
        return opportunities
    
    def _enter_positions(self, opportunities: List[Dict], config: Dict):
        """Enter new positions"""
        
        position_size = config.get('position_size', 4000)
        max_positions = config.get('max_positions', 12)
        
        # Check if we can enter more positions
        if len(self.active_positions) >= max_positions:
            return
        
        # Check available capital
        available_capital = self.current_capital - sum(
            pos['current_value'] for pos in self.active_positions.values()
        )
        
        for opp in opportunities:
            # Check limits
            if len(self.active_positions) >= max_positions:
                break
            
            if available_capital < position_size:
                break
            
            ticker = opp['ticker']
            
            # Skip if already in position
            if ticker in self.active_positions:
                continue
            
            # Calculate shares
            entry_price = opp['entry_price']
            shares = int(position_size / entry_price)
            
            if shares == 0:
                continue
            
            # Apply commission and slippage
            total_cost = shares * entry_price * (1 + self.commission_pct + self.slippage_pct)
            
            # Enter position
            self.active_positions[ticker] = {
                'ticker': ticker,
                'shares': shares,
                'entry_price': entry_price,
                'entry_date': opp['entry_date'],
                'current_price': entry_price,
                'current_value': total_cost,
                'stop_loss': config.get('stop_loss', -10),
                'take_profit': config.get('take_profit', 15),
                'max_hold_days': config.get('max_hold_days', 15),
                'days_held': 0,
                'data': opp['data']
            }
            
            available_capital -= total_cost
    
    def _check_exit_conditions(self, events: pd.DataFrame):
        """Check if any positions should be exited"""
        
        to_exit = []
        
        for ticker, position in self.active_positions.items():
            # Get current price from events (if available)
            ticker_event = events[events['ticker'] == ticker]
            
            if len(ticker_event) > 0:
                # Use day-by-day return data to simulate
                row = ticker_event.iloc[0]
                days_held = position['days_held']
                
                # Get return for this holding period
                if days_held == 0:
                    return_pct = row.get('day0_return', 0)
                elif days_held == 1:
                    return_pct = row.get('day1_return', 0)
                elif days_held <= 10:
                    return_pct = row.get(f'day{days_held}_return', 0)
                else:
                    return_pct = row.get('day10_return', 0)  # Cap at day 10
                
                current_price = position['entry_price'] * (1 + return_pct / 100)
                position['current_price'] = current_price
                position['current_value'] = position['shares'] * current_price
            
            # Check exit conditions
            entry_price = position['entry_price']
            current_price = position['current_price']
            return_pct = (current_price - entry_price) / entry_price * 100
            
            # Stop loss hit
            if return_pct <= position['stop_loss']:
                to_exit.append((ticker, 'stop_loss', return_pct))
            
            # Take profit hit
            elif return_pct >= position['take_profit']:
                to_exit.append((ticker, 'take_profit', return_pct))
            
            # Max hold period reached
            elif position['days_held'] >= position['max_hold_days']:
                to_exit.append((ticker, 'time_exit', return_pct))
            
            # Increment days held
            position['days_held'] += 1
        
        # Execute exits
        for ticker, reason, return_pct in to_exit:
            self._exit_position(ticker, reason, return_pct)
    
    def _exit_position(self, ticker: str, reason: str, return_pct: float):
        """Exit a position"""
        
        if ticker not in self.active_positions:
            return
        
        position = self.active_positions[ticker]
        
        # Calculate P&L
        exit_price = position['current_price']
        shares = position['shares']
        entry_price = position['entry_price']
        
        # Apply commission and slippage on exit
        exit_value = shares * exit_price * (1 - self.commission_pct - self.slippage_pct)
        entry_value = shares * entry_price * (1 + self.commission_pct + self.slippage_pct)
        
        pnl = exit_value - entry_value
        
        # Record trade
        trade = {
            'ticker': ticker,
            'entry_date': position['entry_date'],
            'exit_date': datetime.now().strftime('%Y-%m-%d'),  # Simplified
            'entry_price': entry_price,
            'exit_price': exit_price,
            'shares': shares,
            'return_pct': return_pct,
            'pnl': pnl,
            'exit_reason': reason,
            'hold_days': position['days_held']
        }
        
        self.trade_history.append(trade)
        self.metrics_tracker.add_trade(trade)
        
        # Update capital
        self.current_capital += pnl
        
        # Remove position
        del self.active_positions[ticker]
    
    def _close_all_positions(self):
        """Close all remaining positions at end of backtest"""
        
        for ticker in list(self.active_positions.keys()):
            position = self.active_positions[ticker]
            return_pct = (position['current_price'] - position['entry_price']) / position['entry_price'] * 100
            self._exit_position(ticker, 'backtest_end', return_pct)
    
    def _calculate_portfolio_value(self) -> float:
        """Calculate current total portfolio value"""
        
        position_value = sum(pos['current_value'] for pos in self.active_positions.values())
        return self.current_capital + position_value
    
    # ==================== STRATEGY COMPARISON ====================
    
    def compare_strategies(self, data: pd.DataFrame,
                          strategies: List[Dict]) -> pd.DataFrame:
        """
        Compare multiple strategy configurations
        
        Parameters:
        - data: Historical earnings data
        - strategies: List of strategy configuration dicts
        
        Returns:
        - DataFrame with comparison results
        """
        results = []
        
        for i, strategy in enumerate(strategies):
            print(f"\nTesting strategy {i+1}/{len(strategies)}: {strategy.get('name', f'Strategy {i+1}')}")
            
            result = self.backtest_strategy(data, strategy)
            metrics = result['metrics']
            risk = result['risk']
            
            results.append({
                'strategy_name': strategy.get('name', f'Strategy {i+1}'),
                'total_return': metrics['total_return'],
                'avg_return': metrics['avg_return_per_trade'],
                'win_rate': metrics['win_rate'],
                'total_trades': metrics['total_trades'],
                'expectancy': metrics['expectancy'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'max_drawdown': risk['max_drawdown'],
                'config': str(strategy)
            })
        
        return pd.DataFrame(results).sort_values('total_return', ascending=False)


# ==================== PRESET STRATEGIES ====================

class StrategyPresets:
    """Predefined strategy configurations for backtesting"""
    
    @staticmethod
    def optimized_strategy():
        """The optimized strategy from grid search"""
        return {
            'name': 'Optimized (Day 0 > 2%, Vol > 2.5x)',
            'strategy_type': 'positive_momentum',
            'entry_threshold': 2.0,
            'position_size': 4000,
            'max_positions': 12,
            'stop_loss': -10,
            'take_profit': 15,
            'max_hold_days': 15,
            'filters': {
                'volume': {'min_spike': 2.5, 'min_avg_volume': 100000, 'min_consistency': 0.5},
                'beta': {'min_beta': 0.8, 'max_beta': 2.0},
                'market_cap': {'min_market_cap': 1e9}
            }
        }
    
    @staticmethod
    def strong_positive():
        """Strong positive momentum only"""
        return {
            'name': 'Strong Positive (Day 0 > 2%)',
            'strategy_type': 'strong_positive',
            'entry_threshold': 2.0,
            'position_size': 4000,
            'max_positions': 12,
            'stop_loss': -10,
            'take_profit': 15,
            'max_hold_days': 15,
            'filters': {
                'volume': {'min_spike': 2.0, 'min_avg_volume': 100000, 'min_consistency': 0.5},
                'market_cap': {'min_market_cap': 1e9}
            }
        }
    
    @staticmethod
    def any_positive():
        """Any positive momentum"""
        return {
            'name': 'Any Positive (Day 0 > 0%)',
            'strategy_type': 'any_positive',
            'entry_threshold': 0.0,
            'position_size': 4000,
            'max_positions': 12,
            'stop_loss': -8,
            'take_profit': 12,
            'max_hold_days': 10,
            'filters': {
                'volume': {'min_spike': 1.5, 'min_avg_volume': 100000, 'min_consistency': 0.5},
                'market_cap': {'min_market_cap': 1e9}
            }
        }


if __name__ == '__main__':
    print("=" * 80)
    print("COMPREHENSIVE BACKTESTER - TEST")
    print("=" * 80)
    
    # Initialize backtester
    backtester = ComprehensiveBacktester(initial_capital=100000)
    
    # Load test data
    test_file = 'strategy2_analysis/strategy2_comprehensive_data.csv'
    try:
        df = pd.read_csv(test_file)
        print(f"\n✅ Loaded {len(df)} earnings events")
        
        # Test with optimized strategy
        print("\n" + "=" * 80)
        print("TESTING OPTIMIZED STRATEGY")
        print("=" * 80)
        
        strategy = StrategyPresets.optimized_strategy()
        results = backtester.backtest_strategy(df, strategy)
        
        # Print results
        print("\n" + backtester.metrics_tracker.generate_summary_report())
        
        # Compare multiple strategies
        print("\n" + "=" * 80)
        print("COMPARING MULTIPLE STRATEGIES")
        print("=" * 80)
        
        strategies = [
            StrategyPresets.optimized_strategy(),
            StrategyPresets.strong_positive(),
            StrategyPresets.any_positive()
        ]
        
        comparison = backtester.compare_strategies(df, strategies)
        print("\nStrategy Comparison:")
        print(comparison[['strategy_name', 'total_return', 'avg_return', 'win_rate', 'total_trades']].to_string(index=False))
        
        print("\n✅ Backtester test complete!")
        
    except FileNotFoundError:
        print(f"\n❌ Test file not found: {test_file}")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

