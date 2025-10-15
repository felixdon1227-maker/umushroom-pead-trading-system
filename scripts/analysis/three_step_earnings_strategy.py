"""
3-Step Earnings Strategy - Complete Implementation

This is the main strategy engine combining:
1. 3-Step Dynamic Strategy (pre-earnings positioning with dynamic adjustment)
2. Hybrid Tiered Strategy (post-earnings opportunity capture)

Author: UMushroom Competition Strategy
Date: October 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import sys
import os

# Import our custom modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from filter_engine import FilterEngine, FilterPresets
from metrics_tracker import MetricsTracker


class ThreeStepEarningsStrategy:
    """
    Complete 3-Step Earnings Strategy Implementation
    
    Combines two complementary approaches:
    - 3-Step Dynamic: Pre-earnings positioning with dynamic adjustments
    - Hybrid Tiered: Post-earnings opportunity capture with tiered sizing
    """
    
    def __init__(self, initial_capital: float = 100000, strategy_mode: str = 'both'):
        """
        Initialize the strategy
        
        Parameters:
        - initial_capital: Starting capital
        - strategy_mode: 'dynamic', 'hybrid', or 'both' (default)
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.strategy_mode = strategy_mode
        
        # Initialize components
        self.filter_engine = FilterEngine()
        self.metrics_tracker = MetricsTracker(initial_capital)
        
        # Position tracking
        self.active_positions = {}
        self.pending_opportunities = {}
        
        # Strategy configuration
        self.config = self._default_config()
        
    def _default_config(self) -> Dict:
        """Default strategy configuration"""
        return {
            # 3-Step Dynamic Strategy
            'dynamic': {
                'step1_position_size': 2500,  # Initial position size
                'step2_scale_up_strong': 8000,  # Scale to if >5% + strong signals
                'step2_scale_up_good': 6000,    # Scale to if 2-5% + good signals
                'step2_hold': 2500,             # Hold if 0-2%
                'step2_scale_down': 1000,       # Scale down if -2 to 0%
                'step3_tier1_size': 5000,       # New opportunity - Tier 1
                'step3_tier2_size': 3000,       # New opportunity - Tier 2
                'step3_tier3_size': 2000,       # New opportunity - Tier 3
                'max_positions': 12,            # Maximum concurrent positions
                'max_per_sector': 3             # Maximum per sector
            },
            
            # Hybrid Tiered Strategy
            'hybrid': {
                'tier1_size': 6000,  # Strong buy
                'tier2_size': 4000,  # Moderate buy
                'tier3_size': 3000,  # Opportunistic
                'max_positions': 12,
                'max_per_sector': 3
            },
            
            # Risk management (common)
            'risk': {
                'tier1_stop': -10,    # Stop loss %
                'tier1_target': 15,   # Take profit %
                'tier1_hold_days': 15,
                'tier2_stop': -8,
                'tier2_target': 12,
                'tier2_hold_days': 10,
                'tier3_stop': -7,
                'tier3_target': 10,
                'tier3_hold_days': 7,
                'max_portfolio_risk': 0.05,  # 5% portfolio drawdown triggers pause
                'min_cash_reserve': 10000     # Minimum cash to maintain
            }
        }
    
    # ==================== 3-STEP DYNAMIC STRATEGY ====================
    
    def step1_identify_opportunities(self, earnings_calendar: pd.DataFrame,
                                    target_date: str) -> List[Dict]:
        """
        Step 1: Identify stocks with upcoming earnings (Day -1)
        
        Parameters:
        - earnings_calendar: DataFrame with upcoming earnings
        - target_date: Date to look for earnings (format: 'YYYY-MM-DD')
        
        Returns:
        - List of opportunities with analysis
        """
        opportunities = []
        
        # Filter for earnings on target date
        upcoming = earnings_calendar[
            earnings_calendar['earnings_date'].str.startswith(target_date)
        ].copy()
        
        if len(upcoming) == 0:
            return opportunities
        
        # Apply Step 1 filters
        step1_config = {
            'volume': {'min_spike': 1.5, 'min_avg_volume': 100000, 'min_consistency': 0.5},
            'beta': {'min_beta': 0.8, 'max_beta': 1.5},
            'vix': {'max_vix': 25},
            'beat_rate': {'min_beat_rate': 0.6},
            'market_cap': {'min_market_cap': 1e9},
            'consecutive_beats': {'min_consecutive': 2},
            'surprise': {'min_surprise': 0.0}
        }
        
        filtered = self.filter_engine.apply_comprehensive_filters(upcoming, step1_config)
        
        # Rank opportunities
        for _, row in filtered.iterrows():
            score = self._calculate_opportunity_score(row, 'step1')
            
            opportunities.append({
                'ticker': row['ticker'],
                'earnings_date': row['earnings_date'],
                'earnings_timing': self.filter_engine._categorize_earnings_timing(
                    pd.DataFrame([row]))['earnings_timing'].iloc[0],
                'score': score,
                'historical_beat_rate': row.get('historical_beat_rate', 0),
                'volume_spike_expected': row.get('volume_spike', 0),
                'beta': row.get('beta', 1.0),
                'action': 'enter_step1',
                'position_size': self.config['dynamic']['step1_position_size']
            })
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        return opportunities[:8]  # Top 6-8 opportunities
    
    def step2_adjust_positions(self, positions: List[Dict],
                              day0_data: pd.DataFrame) -> List[Dict]:
        """
        Step 2: Dynamically adjust positions based on Day 0/1 reaction
        
        Parameters:
        - positions: Current positions from Step 1
        - day0_data: Data with Day 0/1 reactions
        
        Returns:
        - List of position adjustments
        """
        adjustments = []
        
        for position in positions:
            ticker = position['ticker']
            
            # Find Day 0/1 data
            stock_data = day0_data[day0_data['ticker'] == ticker]
            if len(stock_data) == 0:
                continue
            
            stock_data = stock_data.iloc[0]
            day0_reaction = stock_data.get('day0_reaction', 0)
            day1_reaction = stock_data.get('day1_reaction', 0)
            volume_spike = stock_data.get('volume_spike', 0)
            beat_rate = stock_data.get('historical_beat_rate', 0)
            
            # Determine adjustment
            adjustment = self._determine_step2_adjustment(
                day0_reaction, day1_reaction, volume_spike, beat_rate
            )
            
            adjustments.append({
                'ticker': ticker,
                'current_size': position['position_size'],
                'new_size': adjustment['new_size'],
                'action': adjustment['action'],
                'reason': adjustment['reason'],
                'day0_reaction': day0_reaction,
                'day1_reaction': day1_reaction
            })
        
        return adjustments
    
    def _determine_step2_adjustment(self, day0: float, day1: float,
                                   volume_spike: float, beat_rate: float) -> Dict:
        """Determine Step 2 adjustment based on reactions"""
        cfg = self.config['dynamic']
        
        # Scale UP - Strong winner
        if day0 > 5 and volume_spike > 2.5 and beat_rate > 0.7:
            return {
                'new_size': cfg['step2_scale_up_strong'],
                'action': 'scale_up',
                'reason': f'Strong winner: Day 0 {day0:.1f}%, Vol {volume_spike:.1f}x'
            }
        
        # Scale UP - Good winner
        elif day0 > 2 and volume_spike > 2.0 and beat_rate > 0.6:
            return {
                'new_size': cfg['step2_scale_up_good'],
                'action': 'scale_up',
                'reason': f'Good winner: Day 0 {day0:.1f}%, Vol {volume_spike:.1f}x'
            }
        
        # HOLD - Slight winner
        elif day0 > 0 and volume_spike > 1.5:
            return {
                'new_size': cfg['step2_hold'],
                'action': 'hold',
                'reason': f'Slight winner: Day 0 {day0:.1f}%'
            }
        
        # Scale DOWN - Slight loser
        elif day0 > -2 and volume_spike > 1.5:
            return {
                'new_size': cfg['step2_scale_down'],
                'action': 'scale_down',
                'reason': f'Slight loser: Day 0 {day0:.1f}%'
            }
        
        # EXIT - Clear loser
        else:
            return {
                'new_size': 0,
                'action': 'exit',
                'reason': f'Exit: Day 0 {day0:.1f}% or low volume'
            }
    
    def step3_find_new_opportunities(self, earnings_data: pd.DataFrame,
                                    existing_tickers: List[str]) -> List[Dict]:
        """
        Step 3: Find new opportunities from stocks we didn't initially enter
        
        Parameters:
        - earnings_data: Recent earnings with Day 0/1 reactions
        - existing_tickers: Tickers already in portfolio
        
        Returns:
        - List of new opportunities
        """
        # Filter out existing positions
        new_opps = earnings_data[~earnings_data['ticker'].isin(existing_tickers)].copy()
        
        if len(new_opps) == 0:
            return []
        
        opportunities = []
        
        # Tier 1: Strong opportunities (>3% Day 0, high volume, strong beat rate)
        tier1_config = FilterPresets.tier1_strong_buy()
        tier1 = self.filter_engine.apply_comprehensive_filters(new_opps, tier1_config)
        tier1 = tier1[tier1['day0_reaction'] > 3]
        
        for _, row in tier1.iterrows():
            opportunities.append({
                'ticker': row['ticker'],
                'tier': 1,
                'position_size': self.config['dynamic']['step3_tier1_size'],
                'day0_reaction': row.get('day0_reaction', 0),
                'volume_spike': row.get('volume_spike', 0),
                'score': self._calculate_opportunity_score(row, 'step3_tier1')
            })
        
        # Tier 2: Good opportunities (1-3% Day 0, good volume)
        tier2_config = FilterPresets.tier2_moderate_buy()
        tier2 = self.filter_engine.apply_comprehensive_filters(new_opps, tier2_config)
        tier2 = tier2[(tier2['day0_reaction'] > 1) & (tier2['day0_reaction'] <= 3)]
        
        for _, row in tier2.iterrows():
            if row['ticker'] not in [o['ticker'] for o in opportunities]:
                opportunities.append({
                    'ticker': row['ticker'],
                    'tier': 2,
                    'position_size': self.config['dynamic']['step3_tier2_size'],
                    'day0_reaction': row.get('day0_reaction', 0),
                    'volume_spike': row.get('volume_spike', 0),
                    'score': self._calculate_opportunity_score(row, 'step3_tier2')
                })
        
        # Tier 3: Opportunistic (0-1% Day 0)
        tier3_config = FilterPresets.tier3_opportunistic()
        tier3 = self.filter_engine.apply_comprehensive_filters(new_opps, tier3_config)
        tier3 = tier3[(tier3['day0_reaction'] > 0) & (tier3['day0_reaction'] <= 1)]
        
        for _, row in tier3.iterrows():
            if row['ticker'] not in [o['ticker'] for o in opportunities]:
                opportunities.append({
                    'ticker': row['ticker'],
                    'tier': 3,
                    'position_size': self.config['dynamic']['step3_tier3_size'],
                    'day0_reaction': row.get('day0_reaction', 0),
                    'volume_spike': row.get('volume_spike', 0),
                    'score': self._calculate_opportunity_score(row, 'step3_tier3')
                })
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        return opportunities
    
    # ==================== HYBRID TIERED STRATEGY ====================
    
    def hybrid_scan_opportunities(self, earnings_data: pd.DataFrame) -> List[Dict]:
        """
        Hybrid Tiered Strategy: Scan and categorize all opportunities
        
        Parameters:
        - earnings_data: Recent earnings with Day 0 reactions
        
        Returns:
        - List of categorized opportunities
        """
        opportunities = []
        
        # Tier 1: Strong Buy
        tier1_config = FilterPresets.tier1_strong_buy()
        tier1 = self.filter_engine.apply_comprehensive_filters(earnings_data, tier1_config)
        tier1 = tier1[tier1['day0_reaction'] > 2]  # Strong positive reaction
        
        for _, row in tier1.iterrows():
            opportunities.append({
                'ticker': row['ticker'],
                'tier': 1,
                'tier_name': 'Strong Buy',
                'position_size': self.config['hybrid']['tier1_size'],
                'stop_loss': self.config['risk']['tier1_stop'],
                'take_profit': self.config['risk']['tier1_target'],
                'hold_days': self.config['risk']['tier1_hold_days'],
                'day0_reaction': row.get('day0_reaction', 0),
                'volume_spike': row.get('volume_spike', 0),
                'beat_rate': row.get('historical_beat_rate', 0),
                'score': self._calculate_opportunity_score(row, 'hybrid_tier1')
            })
        
        # Tier 2: Moderate Buy
        tier2_config = FilterPresets.tier2_moderate_buy()
        tier2 = self.filter_engine.apply_comprehensive_filters(earnings_data, tier2_config)
        tier2 = tier2[tier2['day0_reaction'] > 0.5]
        
        for _, row in tier2.iterrows():
            if row['ticker'] not in [o['ticker'] for o in opportunities]:
                opportunities.append({
                    'ticker': row['ticker'],
                    'tier': 2,
                    'tier_name': 'Moderate Buy',
                    'position_size': self.config['hybrid']['tier2_size'],
                    'stop_loss': self.config['risk']['tier2_stop'],
                    'take_profit': self.config['risk']['tier2_target'],
                    'hold_days': self.config['risk']['tier2_hold_days'],
                    'day0_reaction': row.get('day0_reaction', 0),
                    'volume_spike': row.get('volume_spike', 0),
                    'beat_rate': row.get('historical_beat_rate', 0),
                    'score': self._calculate_opportunity_score(row, 'hybrid_tier2')
                })
        
        # Tier 3: Opportunistic
        tier3_config = FilterPresets.tier3_opportunistic()
        tier3 = self.filter_engine.apply_comprehensive_filters(earnings_data, tier3_config)
        tier3 = tier3[tier3['day0_reaction'] > 0]
        
        for _, row in tier3.iterrows():
            if row['ticker'] not in [o['ticker'] for o in opportunities]:
                opportunities.append({
                    'ticker': row['ticker'],
                    'tier': 3,
                    'tier_name': 'Opportunistic',
                    'position_size': self.config['hybrid']['tier3_size'],
                    'stop_loss': self.config['risk']['tier3_stop'],
                    'take_profit': self.config['risk']['tier3_target'],
                    'hold_days': self.config['risk']['tier3_hold_days'],
                    'day0_reaction': row.get('day0_reaction', 0),
                    'volume_spike': row.get('volume_spike', 0),
                    'beat_rate': row.get('historical_beat_rate', 0),
                    'score': self._calculate_opportunity_score(row, 'hybrid_tier3')
                })
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        return opportunities
    
    # ==================== SCORING & UTILITIES ====================
    
    def _calculate_opportunity_score(self, row: pd.Series, context: str) -> float:
        """Calculate opportunity score based on context"""
        base_score = 0
        
        # Get metrics (handle missing values)
        day0 = row.get('day0_reaction', 0)
        volume_spike = row.get('volume_spike', 1.0)
        beat_rate = row.get('historical_beat_rate', 0.5)
        consecutive = row.get('consecutive_beats', 0)
        surprise = row.get('surprise_pct', 0)
        
        # Day 0 reaction (0-40 points)
        base_score += min(day0 * 4, 40)
        
        # Volume spike (0-30 points)
        base_score += min((volume_spike - 1.5) * 15, 30)
        
        # Historical beat rate (0-20 points)
        base_score += beat_rate * 20
        
        # Consecutive beats (0-10 points)
        base_score += min(consecutive * 3, 10)
        
        # Surprise magnitude (bonus if available)
        if surprise > 0:
            base_score += min(surprise, 10)
        
        return base_score
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        deployed = sum(pos.get('market_value', 0) for pos in self.active_positions.values())
        
        return {
            'current_capital': self.current_capital,
            'deployed_capital': deployed,
            'cash_available': self.current_capital - deployed,
            'position_count': len(self.active_positions),
            'positions': list(self.active_positions.keys())
        }
    
    def check_risk_limits(self) -> Dict:
        """Check if risk limits allow new positions"""
        portfolio = self.get_portfolio_summary()
        
        checks = {
            'can_trade': True,
            'reasons': []
        }
        
        # Check position limit
        max_pos = self.config['dynamic']['max_positions'] if self.strategy_mode == 'dynamic' else self.config['hybrid']['max_positions']
        if portfolio['position_count'] >= max_pos:
            checks['can_trade'] = False
            checks['reasons'].append(f"Max positions reached ({max_pos})")
        
        # Check cash reserve
        if portfolio['cash_available'] < self.config['risk']['min_cash_reserve']:
            checks['can_trade'] = False
            checks['reasons'].append("Insufficient cash reserve")
        
        # Check portfolio drawdown
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital
        if total_return < -self.config['risk']['max_portfolio_risk']:
            checks['can_trade'] = False
            checks['reasons'].append("Portfolio drawdown limit reached")
        
        return checks
    
    def generate_action_plan(self, opportunities: List[Dict]) -> str:
        """Generate human-readable action plan"""
        plan = []
        plan.append("=" * 80)
        plan.append("3-STEP EARNINGS STRATEGY - ACTION PLAN")
        plan.append("=" * 80)
        plan.append("")
        
        # Portfolio status
        portfolio = self.get_portfolio_summary()
        plan.append(f"Portfolio Capital: ${portfolio['current_capital']:,.2f}")
        plan.append(f"Cash Available: ${portfolio['cash_available']:,.2f}")
        plan.append(f"Active Positions: {portfolio['position_count']}")
        plan.append("")
        
        # Risk check
        risk_check = self.check_risk_limits()
        if not risk_check['can_trade']:
            plan.append("⚠️  RISK LIMITS REACHED:")
            for reason in risk_check['reasons']:
                plan.append(f"  - {reason}")
            plan.append("")
        
        # Opportunities
        if len(opportunities) == 0:
            plan.append("No opportunities found.")
        else:
            plan.append(f"Found {len(opportunities)} opportunities:")
            plan.append("")
            
            for i, opp in enumerate(opportunities[:10], 1):  # Top 10
                tier_info = f"Tier {opp.get('tier', '-')}" if 'tier' in opp else ""
                plan.append(f"{i}. {opp['ticker']} {tier_info}")
                plan.append(f"   Day 0: {opp.get('day0_reaction', 0):.2f}% | " +
                          f"Volume: {opp.get('volume_spike', 0):.1f}x | " +
                          f"Score: {opp.get('score', 0):.1f}")
                plan.append(f"   Position Size: ${opp['position_size']:,}")
                if 'action' in opp:
                    plan.append(f"   Action: {opp['action']}")
                plan.append("")
        
        plan.append("=" * 80)
        
        return "\n".join(plan)


if __name__ == '__main__':
    print("=" * 80)
    print("3-STEP EARNINGS STRATEGY - TEST")
    print("=" * 80)
    
    # Initialize strategy
    strategy = ThreeStepEarningsStrategy(initial_capital=100000, strategy_mode='both')
    
    # Load test data
    test_file = 'strategy2_analysis/strategy2_comprehensive_data.csv'
    try:
        df = pd.read_csv(test_file)
        print(f"\n✅ Loaded {len(df)} earnings events")
        
        # Test Hybrid Strategy (simplest to test)
        print("\n" + "=" * 80)
        print("TESTING HYBRID TIERED STRATEGY")
        print("=" * 80)
        
        # Use recent data
        recent = df.head(100).copy()
        opportunities = strategy.hybrid_scan_opportunities(recent)
        
        print(f"\nFound {len(opportunities)} opportunities")
        print(f"  Tier 1 (Strong Buy): {len([o for o in opportunities if o['tier'] == 1])}")
        print(f"  Tier 2 (Moderate): {len([o for o in opportunities if o['tier'] == 2])}")
        print(f"  Tier 3 (Opportunistic): {len([o for o in opportunities if o['tier'] == 3])}")
        
        # Generate action plan
        print("\n" + strategy.generate_action_plan(opportunities))
        
        print("\n✅ Strategy test complete!")
        
    except FileNotFoundError:
        print(f"\n❌ Test file not found: {test_file}")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

