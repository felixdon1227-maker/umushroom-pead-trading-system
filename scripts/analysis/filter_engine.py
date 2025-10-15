"""
Comprehensive Filter Engine for 3-Step Earnings Strategy

This module provides a complete filtering system with 8 filter categories:
1. Volume Filters
2. Beta Filters  
3. VIX Filters
4. Historical Beat Rate Filters
5. Market Cap Filters
6. Surprise Magnitude Filters
7. Consecutive Beats Filters
8. Earnings Timing Filters

Author: UMushroom Competition Strategy
Date: October 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, List, Tuple, Optional


class FilterEngine:
    """Comprehensive filtering system for earnings strategy"""
    
    def __init__(self):
        """Initialize the filter engine with all filter categories"""
        self.filter_stats = {}
        
    # ==================== VOLUME FILTERS ====================
    
    def apply_volume_filters(self, df: pd.DataFrame, 
                            min_spike: float = 1.5,
                            min_avg_volume: float = 100000,
                            min_consistency: float = 0.5) -> pd.DataFrame:
        """
        Apply volume-based filters
        
        Parameters:
        - min_spike: Minimum volume spike multiple (e.g., 2.0 = 200% of average)
        - min_avg_volume: Minimum 90-day average volume for liquidity
        - min_consistency: Minimum volume consistency score (0-1)
        
        Returns:
        - Filtered DataFrame
        """
        initial_count = len(df)
        
        # Apply filters
        filtered = df[
            (df['volume_spike'] >= min_spike) &
            (df['avg_volume_90d'] >= min_avg_volume) &
            (df['volume_consistency'] >= min_consistency)
        ].copy()
        
        # Track statistics
        self.filter_stats['volume'] = {
            'initial': initial_count,
            'passed': len(filtered),
            'filter_rate': len(filtered) / initial_count if initial_count > 0 else 0,
            'criteria': {
                'min_spike': min_spike,
                'min_avg_volume': min_avg_volume,
                'min_consistency': min_consistency
            }
        }
        
        return filtered
    
    def get_volume_tier(self, volume_spike: float) -> str:
        """Categorize volume spike into tiers"""
        if volume_spike >= 3.0:
            return 'very_high'
        elif volume_spike >= 2.5:
            return 'high'
        elif volume_spike >= 2.0:
            return 'medium'
        elif volume_spike >= 1.5:
            return 'low'
        else:
            return 'insufficient'
    
    # ==================== BETA FILTERS ====================
    
    def apply_beta_filters(self, df: pd.DataFrame,
                          min_beta: float = 0.8,
                          max_beta: float = 2.0) -> pd.DataFrame:
        """
        Apply beta-based filters for market correlation
        
        Parameters:
        - min_beta: Minimum acceptable beta
        - max_beta: Maximum acceptable beta
        
        Returns:
        - Filtered DataFrame
        """
        initial_count = len(df)
        
        # Apply filters (handle NaN values)
        filtered = df[
            (df['beta'].notna()) &
            (df['beta'] >= min_beta) &
            (df['beta'] <= max_beta)
        ].copy()
        
        self.filter_stats['beta'] = {
            'initial': initial_count,
            'passed': len(filtered),
            'filter_rate': len(filtered) / initial_count if initial_count > 0 else 0,
            'criteria': {
                'min_beta': min_beta,
                'max_beta': max_beta
            }
        }
        
        return filtered
    
    def get_beta_tier(self, beta: float) -> str:
        """Categorize beta into tiers"""
        if pd.isna(beta):
            return 'unknown'
        elif beta < 0.8:
            return 'low_volatility'
        elif beta <= 1.2:
            return 'low_beta'
        elif beta <= 1.5:
            return 'normal_beta'
        elif beta <= 2.0:
            return 'high_beta'
        else:
            return 'very_high_beta'
    
    # ==================== VIX FILTERS ====================
    
    def apply_vix_filters(self, df: pd.DataFrame,
                         max_vix: float = 25) -> pd.DataFrame:
        """
        Apply VIX-based filters for market volatility
        
        Parameters:
        - max_vix: Maximum acceptable VIX level
        
        Returns:
        - Filtered DataFrame
        """
        initial_count = len(df)
        
        # Apply filters (handle NaN values)
        filtered = df[
            (df['vix'].notna()) &
            (df['vix'] <= max_vix)
        ].copy()
        
        self.filter_stats['vix'] = {
            'initial': initial_count,
            'passed': len(filtered),
            'filter_rate': len(filtered) / initial_count if initial_count > 0 else 0,
            'criteria': {
                'max_vix': max_vix
            }
        }
        
        return filtered
    
    def get_vix_tier(self, vix: float) -> str:
        """Categorize VIX into market condition tiers"""
        if pd.isna(vix):
            return 'unknown'
        elif vix < 15:
            return 'low_volatility'
        elif vix < 20:
            return 'normal_volatility'
        elif vix < 25:
            return 'elevated_volatility'
        elif vix < 30:
            return 'high_volatility'
        else:
            return 'extreme_volatility'
    
    # ==================== HISTORICAL BEAT RATE FILTERS ====================
    
    def apply_beat_rate_filters(self, df: pd.DataFrame,
                                min_beat_rate: float = 0.5) -> pd.DataFrame:
        """
        Apply historical beat rate filters
        
        Parameters:
        - min_beat_rate: Minimum historical beat rate (0-1)
        
        Returns:
        - Filtered DataFrame
        """
        initial_count = len(df)
        
        # Apply filters (handle NaN values)
        filtered = df[
            (df['historical_beat_rate'].notna()) &
            (df['historical_beat_rate'] >= min_beat_rate)
        ].copy()
        
        self.filter_stats['beat_rate'] = {
            'initial': initial_count,
            'passed': len(filtered),
            'filter_rate': len(filtered) / initial_count if initial_count > 0 else 0,
            'criteria': {
                'min_beat_rate': min_beat_rate
            }
        }
        
        return filtered
    
    def get_beat_rate_tier(self, beat_rate: float) -> str:
        """Categorize beat rate into quality tiers"""
        if pd.isna(beat_rate):
            return 'unknown'
        elif beat_rate >= 0.8:
            return 'excellent'
        elif beat_rate >= 0.7:
            return 'very_good'
        elif beat_rate >= 0.6:
            return 'good'
        elif beat_rate >= 0.5:
            return 'acceptable'
        else:
            return 'poor'
    
    # ==================== MARKET CAP FILTERS ====================
    
    def apply_market_cap_filters(self, df: pd.DataFrame,
                                 min_market_cap: float = 1e9) -> pd.DataFrame:
        """
        Apply market cap filters for liquidity and institutional interest
        
        Parameters:
        - min_market_cap: Minimum market cap in dollars (e.g., 1e9 = $1B)
        
        Returns:
        - Filtered DataFrame
        """
        initial_count = len(df)
        
        # Apply filters (handle NaN values)
        filtered = df[
            (df['market_cap'].notna()) &
            (df['market_cap'] >= min_market_cap)
        ].copy()
        
        self.filter_stats['market_cap'] = {
            'initial': initial_count,
            'passed': len(filtered),
            'filter_rate': len(filtered) / initial_count if initial_count > 0 else 0,
            'criteria': {
                'min_market_cap': min_market_cap,
                'min_market_cap_formatted': f"${min_market_cap/1e9:.1f}B"
            }
        }
        
        return filtered
    
    def get_market_cap_tier(self, market_cap: float) -> str:
        """Categorize market cap into size tiers"""
        if pd.isna(market_cap):
            return 'unknown'
        elif market_cap >= 200e9:
            return 'mega_cap'
        elif market_cap >= 10e9:
            return 'large_cap'
        elif market_cap >= 2e9:
            return 'mid_cap'
        elif market_cap >= 300e6:
            return 'small_cap'
        else:
            return 'micro_cap'
    
    # ==================== SURPRISE MAGNITUDE FILTERS ====================
    
    def apply_surprise_filters(self, df: pd.DataFrame,
                               min_surprise: float = 0.0) -> pd.DataFrame:
        """
        Apply earnings surprise magnitude filters
        
        Parameters:
        - min_surprise: Minimum surprise percentage (e.g., 2.0 = 2% beat)
        
        Returns:
        - Filtered DataFrame
        """
        initial_count = len(df)
        
        # Apply filters (handle NaN values)
        filtered = df[
            (df['surprise_pct'].notna()) &
            (df['surprise_pct'] >= min_surprise)
        ].copy()
        
        self.filter_stats['surprise'] = {
            'initial': initial_count,
            'passed': len(filtered),
            'filter_rate': len(filtered) / initial_count if initial_count > 0 else 0,
            'criteria': {
                'min_surprise': min_surprise
            }
        }
        
        return filtered
    
    def get_surprise_tier(self, surprise_pct: float) -> str:
        """Categorize surprise magnitude into tiers"""
        if pd.isna(surprise_pct):
            return 'unknown'
        elif surprise_pct >= 10:
            return 'huge_beat'
        elif surprise_pct >= 5:
            return 'big_beat'
        elif surprise_pct >= 2:
            return 'solid_beat'
        elif surprise_pct > 0:
            return 'small_beat'
        elif surprise_pct == 0:
            return 'in_line'
        elif surprise_pct >= -2:
            return 'small_miss'
        elif surprise_pct >= -5:
            return 'miss'
        else:
            return 'big_miss'
    
    # ==================== CONSECUTIVE BEATS FILTERS ====================
    
    def apply_consecutive_beats_filters(self, df: pd.DataFrame,
                                       min_consecutive: int = 0) -> pd.DataFrame:
        """
        Apply consecutive beats filters for earnings consistency
        
        Parameters:
        - min_consecutive: Minimum consecutive beats required
        
        Returns:
        - Filtered DataFrame
        """
        initial_count = len(df)
        
        # Apply filters (handle NaN values)
        filtered = df[
            (df['consecutive_beats'].notna()) &
            (df['consecutive_beats'] >= min_consecutive)
        ].copy()
        
        self.filter_stats['consecutive_beats'] = {
            'initial': initial_count,
            'passed': len(filtered),
            'filter_rate': len(filtered) / initial_count if initial_count > 0 else 0,
            'criteria': {
                'min_consecutive': min_consecutive
            }
        }
        
        return filtered
    
    def get_consecutive_beats_tier(self, consecutive_beats: float) -> str:
        """Categorize consecutive beats into consistency tiers"""
        if pd.isna(consecutive_beats):
            return 'unknown'
        elif consecutive_beats >= 5:
            return 'very_consistent'
        elif consecutive_beats >= 3:
            return 'consistent'
        elif consecutive_beats >= 1:
            return 'somewhat_consistent'
        else:
            return 'inconsistent'
    
    # ==================== EARNINGS TIMING FILTERS ====================
    
    def apply_earnings_timing_filters(self, df: pd.DataFrame,
                                     allowed_timings: List[str] = ['all']) -> pd.DataFrame:
        """
        Apply earnings timing filters (after-hours, pre-market, during-market)
        
        Parameters:
        - allowed_timings: List of allowed timing types
                          Options: 'after_hours', 'pre_market', 'during_market', 'all'
        
        Returns:
        - Filtered DataFrame with timing category added
        """
        initial_count = len(df)
        
        # Add earnings timing category if not present
        if 'earnings_timing' not in df.columns:
            df = self._categorize_earnings_timing(df)
        
        # Apply filter if not 'all'
        if 'all' not in allowed_timings:
            filtered = df[df['earnings_timing'].isin(allowed_timings)].copy()
        else:
            filtered = df.copy()
        
        self.filter_stats['earnings_timing'] = {
            'initial': initial_count,
            'passed': len(filtered),
            'filter_rate': len(filtered) / initial_count if initial_count > 0 else 0,
            'criteria': {
                'allowed_timings': allowed_timings
            },
            'distribution': filtered['earnings_timing'].value_counts().to_dict() if len(filtered) > 0 else {}
        }
        
        return filtered
    
    def _categorize_earnings_timing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Categorize earnings announcements by time of day"""
        df = df.copy()
        
        def get_timing_category(earnings_date):
            """Determine timing category from earnings date"""
            try:
                if pd.isna(earnings_date):
                    return 'unknown'
                
                # Parse the datetime
                dt = pd.to_datetime(earnings_date)
                hour = dt.hour
                
                # Categorize
                if 6 <= hour < 9:  # 6:00 AM - 9:00 AM
                    return 'pre_market'
                elif 9 <= hour < 16:  # 9:00 AM - 4:00 PM
                    return 'during_market'
                elif 16 <= hour <= 23:  # 4:00 PM - 11:59 PM
                    return 'after_hours'
                else:  # Midnight to 6 AM (unusual, treat as after-hours)
                    return 'after_hours'
            except:
                return 'unknown'
        
        df['earnings_timing'] = df['earnings_date'].apply(get_timing_category)
        return df
    
    def get_timing_adjustment_factor(self, timing: str) -> Dict[str, float]:
        """
        Get position sizing and risk adjustments based on earnings timing
        
        Returns:
        - Dictionary with adjustment factors for position size, stops, targets
        """
        adjustments = {
            'after_hours': {
                'position_size_factor': 0.75,  # Reduce size due to gap risk
                'stop_loss_factor': 1.2,       # Wider stops (10% -> 12%)
                'take_profit_factor': 1.0,     # Standard targets
                'wait_for_day1': True,         # Wait for Day 1 open
                'description': 'Gap risk - smaller positions, wider stops, wait for Day 1'
            },
            'pre_market': {
                'position_size_factor': 1.0,   # Standard size
                'stop_loss_factor': 1.0,       # Standard stops
                'take_profit_factor': 1.0,     # Standard targets
                'wait_for_day1': False,        # Can use Day 0 close
                'description': 'Standard approach - full day to react'
            },
            'during_market': {
                'position_size_factor': 1.0,   # Standard size
                'stop_loss_factor': 1.0,       # Standard stops
                'take_profit_factor': 1.0,     # Standard targets
                'wait_for_day1': False,        # Immediate reaction visible
                'description': 'Immediate reaction - standard approach'
            },
            'unknown': {
                'position_size_factor': 0.75,  # Conservative approach
                'stop_loss_factor': 1.2,       # Wider stops
                'take_profit_factor': 1.0,     # Standard targets
                'wait_for_day1': True,         # Be cautious
                'description': 'Unknown timing - conservative approach'
            }
        }
        
        return adjustments.get(timing, adjustments['unknown'])
    
    # ==================== COMPREHENSIVE FILTERING ====================
    
    def apply_comprehensive_filters(self, df: pd.DataFrame,
                                   filter_config: Dict) -> pd.DataFrame:
        """
        Apply all filters based on configuration
        
        Parameters:
        - filter_config: Dictionary with all filter parameters
        
        Returns:
        - Filtered DataFrame
        """
        filtered = df.copy()
        
        # Apply each filter if specified in config
        if 'volume' in filter_config:
            filtered = self.apply_volume_filters(filtered, **filter_config['volume'])
        
        if 'beta' in filter_config:
            filtered = self.apply_beta_filters(filtered, **filter_config['beta'])
        
        if 'vix' in filter_config:
            filtered = self.apply_vix_filters(filtered, **filter_config['vix'])
        
        if 'beat_rate' in filter_config:
            filtered = self.apply_beat_rate_filters(filtered, **filter_config['beat_rate'])
        
        if 'market_cap' in filter_config:
            filtered = self.apply_market_cap_filters(filtered, **filter_config['market_cap'])
        
        if 'surprise' in filter_config:
            filtered = self.apply_surprise_filters(filtered, **filter_config['surprise'])
        
        if 'consecutive_beats' in filter_config:
            filtered = self.apply_consecutive_beats_filters(filtered, **filter_config['consecutive_beats'])
        
        if 'earnings_timing' in filter_config:
            filtered = self.apply_earnings_timing_filters(filtered, **filter_config['earnings_timing'])
        
        return filtered
    
    def get_filter_statistics(self) -> pd.DataFrame:
        """Get comprehensive statistics on all applied filters"""
        stats_list = []
        
        for filter_name, stats in self.filter_stats.items():
            stats_list.append({
                'filter': filter_name,
                'initial_count': stats['initial'],
                'passed_count': stats['passed'],
                'filter_rate': f"{stats['filter_rate']*100:.1f}%",
                'criteria': str(stats['criteria'])
            })
        
        return pd.DataFrame(stats_list)
    
    def reset_statistics(self):
        """Reset filter statistics"""
        self.filter_stats = {}


# ==================== PRESET FILTER CONFIGURATIONS ====================

class FilterPresets:
    """Predefined filter configurations for different strategy tiers"""
    
    @staticmethod
    def tier1_strong_buy():
        """Tier 1: Highest conviction trades"""
        return {
            'volume': {'min_spike': 2.5, 'min_avg_volume': 100000, 'min_consistency': 0.5},
            'beta': {'min_beta': 0.8, 'max_beta': 1.5},
            'vix': {'max_vix': 20},
            'beat_rate': {'min_beat_rate': 0.7},
            'market_cap': {'min_market_cap': 1e9},
            'surprise': {'min_surprise': 2.0},
            'consecutive_beats': {'min_consecutive': 2},
            'earnings_timing': {'allowed_timings': ['all']}
        }
    
    @staticmethod
    def tier2_moderate_buy():
        """Tier 2: Good quality trades"""
        return {
            'volume': {'min_spike': 2.0, 'min_avg_volume': 100000, 'min_consistency': 0.5},
            'beta': {'min_beta': 0.8, 'max_beta': 2.0},
            'vix': {'max_vix': 25},
            'beat_rate': {'min_beat_rate': 0.6},
            'market_cap': {'min_market_cap': 1e9},
            'surprise': {'min_surprise': 0.0},
            'consecutive_beats': {'min_consecutive': 0},
            'earnings_timing': {'allowed_timings': ['all']}
        }
    
    @staticmethod
    def tier3_opportunistic():
        """Tier 3: Opportunistic trades"""
        return {
            'volume': {'min_spike': 1.5, 'min_avg_volume': 100000, 'min_consistency': 0.5},
            'beta': {'min_beta': 0.8, 'max_beta': 2.0},
            'vix': {'max_vix': 30},
            'beat_rate': {'min_beat_rate': 0.5},
            'market_cap': {'min_market_cap': 1e9},
            'surprise': {'min_surprise': 0.0},
            'consecutive_beats': {'min_consecutive': 0},
            'earnings_timing': {'allowed_timings': ['all']}
        }
    
    @staticmethod
    def optimized_strategy():
        """Optimized strategy from grid search (Day 0 > 2%, Volume > 2.5x)"""
        return {
            'volume': {'min_spike': 2.5, 'min_avg_volume': 100000, 'min_consistency': 0.5},
            'beta': {'min_beta': 0.8, 'max_beta': 2.0},
            'vix': {'max_vix': 30},
            'beat_rate': {'min_beat_rate': 0.5},
            'market_cap': {'min_market_cap': 1e9},
            'surprise': {'min_surprise': 0.0},
            'consecutive_beats': {'min_consecutive': 0},
            'earnings_timing': {'allowed_timings': ['all']}
        }


if __name__ == '__main__':
    # Test the filter engine
    print("=" * 80)
    print("FILTER ENGINE TEST")
    print("=" * 80)
    
    # Load test data
    test_file = 'strategy2_analysis/strategy2_comprehensive_data.csv'
    try:
        df = pd.read_csv(test_file)
        print(f"\n✅ Loaded {len(df)} earnings events from {test_file}")
        
        # Initialize filter engine
        engine = FilterEngine()
        
        # Test Tier 1 filters
        print("\n" + "=" * 80)
        print("TESTING TIER 1 FILTERS (Strong Buy)")
        print("=" * 80)
        
        tier1_config = FilterPresets.tier1_strong_buy()
        tier1_filtered = engine.apply_comprehensive_filters(df, tier1_config)
        
        print(f"\nFiltered from {len(df)} to {len(tier1_filtered)} opportunities")
        print(f"Filter rate: {len(tier1_filtered)/len(df)*100:.1f}%")
        
        # Show statistics
        print("\nFilter Statistics:")
        print(engine.get_filter_statistics().to_string(index=False))
        
        print("\n✅ Filter engine test complete!")
        
    except FileNotFoundError:
        print(f"\n❌ Test file not found: {test_file}")
        print("Filter engine created successfully, but test data not available.")

