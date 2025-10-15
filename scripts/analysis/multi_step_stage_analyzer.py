"""
Multi-Step Strategy Stage Analysis

Analyzes the performance of the 3-Step Earnings Strategy by breaking down:
- Step 1: Initial pre-earnings positions
- Step 2: Day 0 reaction adjustments
- Step 3: New opportunities after Day 0/1
- Hybrid Tiered: Post-earnings opportunities by tier

Shows metrics for each segment to identify best/worst performers.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

def analyze_multi_step_stages():
    """Analyze performance by strategy stages"""
    
    print("=" * 80)
    print("📊 MULTI-STEP STRATEGY STAGE ANALYSIS")
    print("=" * 80)
    
    # Load the filtered dataset
    df = pd.read_csv('/home/fellaki10/Documents/UMushroom Investment challange/strategy2_analysis/strategy2_filtered_data.csv')
    df['earnings_date'] = pd.to_datetime(df['earnings_date'])
    
    print(f"\n✓ Loaded {len(df)} earnings events from {df['ticker'].nunique()} stocks")
    print(f"✓ Date range: {df['earnings_date'].min()} to {df['earnings_date'].max()}")
    
    # Since the actual multi-step strategy backtester is complex,
    # let's analyze the data to show what each step WOULD capture
    
    print("\n" + "=" * 80)
    print("🎯 SIMULATED MULTI-STEP STRATEGY STAGES")
    print("=" * 80)
    
    # Define criteria for each stage
    
    # STEP 1: Pre-earnings positions (before earnings)
    # Criteria: Historical beat rate >70%, volume consistency >0.5
    step1_candidates = df[
        (df['historical_beat_rate'] > 0.7) &
        (df['volume_consistency'] > 0.5)
    ].copy()
    
    step1_candidates['step'] = 1
    step1_candidates['entry_timing'] = 'pre_earnings'
    step1_candidates['position_size'] = 3000  # Conservative pre-earnings
    step1_candidates['exit_return'] = step1_candidates['day10_return']  # Hold through Day 10
    
    print(f"\n📋 STEP 1: PRE-EARNINGS POSITIONS")
    print(f"Criteria: Historical beat rate >70%, Volume consistency >0.5")
    print(f"Trades: {len(step1_candidates)}")
    print(f"Avg Return: {step1_candidates['exit_return'].mean():.2f}%")
    print(f"Win Rate: {(step1_candidates['exit_return'] > 0).sum() / len(step1_candidates) * 100:.1f}%")
    print(f"Std Dev: {step1_candidates['exit_return'].std():.2f}%")
    
    # STEP 2: Day 0 adjustments
    # Criteria: Stocks that had positive Day 0 AND strong volume spike
    step2_candidates = df[
        (df['day0_reaction'] > 1) &
        (df['volume_spike'] > 2.0) &
        (~df.index.isin(step1_candidates.index))  # Not already in Step 1
    ].copy()
    
    step2_candidates['step'] = 2
    step2_candidates['entry_timing'] = 'day0_close'
    step2_candidates['position_size'] = 4000  # Standard position
    step2_candidates['exit_return'] = step2_candidates['day10_return'] - step2_candidates['day0_reaction']  # From Day 0 to Day 10
    
    print(f"\n📋 STEP 2: DAY 0 MOMENTUM ENTRIES")
    print(f"Criteria: Day 0 reaction >1%, Volume spike >2x, Not in Step 1")
    print(f"Trades: {len(step2_candidates)}")
    print(f"Avg Return: {step2_candidates['exit_return'].mean():.2f}%")
    print(f"Win Rate: {(step2_candidates['exit_return'] > 0).sum() / len(step2_candidates) * 100:.1f}%")
    print(f"Std Dev: {step2_candidates['exit_return'].std():.2f}%")
    
    # STEP 3: Day 1+ entries
    # Criteria: Strong Day 1 continuation (Day 0 + Day 1 both positive)
    step3_candidates = df[
        (df['day0_reaction'] > 0) &
        (df['day1_return'] > 0) &
        (df['day0_reaction'] + df['day1_return'] > 2) &
        (~df.index.isin(step1_candidates.index)) &
        (~df.index.isin(step2_candidates.index))  # Not already traded
    ].copy()
    
    step3_candidates['step'] = 3
    step3_candidates['entry_timing'] = 'day1_close'
    step3_candidates['position_size'] = 5000  # Larger position (confirmed move)
    # Return from Day 2 to Day 10
    step3_candidates['exit_return'] = step3_candidates['day10_return'] - (step3_candidates['day0_reaction'] + step3_candidates['day1_return'])
    
    print(f"\n📋 STEP 3: DAY 1 CONTINUATION ENTRIES")
    print(f"Criteria: Day 0+1 both positive, Combined >2%, Not already traded")
    print(f"Trades: {len(step3_candidates)}")
    print(f"Avg Return: {step3_candidates['exit_return'].mean():.2f}%")
    print(f"Win Rate: {(step3_candidates['exit_return'] > 0).sum() / len(step3_candidates) * 100:.1f}%")
    print(f"Std Dev: {step3_candidates['exit_return'].std():.2f}%")
    
    # HYBRID TIERED: Categorize by signal strength
    
    # Tier 1: Strong signals (best opportunities)
    tier1_candidates = df[
        (df['day0_reaction'] > 2) &
        (df['volume_spike'] > 2.5) &
        (df['historical_beat_rate'] > 0.7) &
        (df['is_beat'] == 1)
    ].copy()
    
    tier1_candidates['tier'] = 1
    tier1_candidates['entry_timing'] = 'day0_close'
    tier1_candidates['position_size'] = 6000  # Largest positions
    tier1_candidates['exit_return'] = tier1_candidates['day10_return'] - tier1_candidates['day0_reaction']
    
    print(f"\n📋 TIER 1: STRONG SIGNALS")
    print(f"Criteria: Day 0 >2%, Volume >2.5x, Beat rate >70%, Is beat")
    print(f"Trades: {len(tier1_candidates)}")
    print(f"Avg Return: {tier1_candidates['exit_return'].mean():.2f}%")
    print(f"Win Rate: {(tier1_candidates['exit_return'] > 0).sum() / len(tier1_candidates) * 100:.1f}%")
    print(f"Std Dev: {tier1_candidates['exit_return'].std():.2f}%")
    
    # Tier 2: Moderate signals
    tier2_candidates = df[
        (df['day0_reaction'] > 1) &
        (df['day0_reaction'] <= 2) &
        (df['volume_spike'] > 1.5) &
        (df['historical_beat_rate'] > 0.5)
    ].copy()
    
    tier2_candidates['tier'] = 2
    tier2_candidates['entry_timing'] = 'day0_close'
    tier2_candidates['position_size'] = 4000  # Medium positions
    tier2_candidates['exit_return'] = tier2_candidates['day10_return'] - tier2_candidates['day0_reaction']
    
    print(f"\n📋 TIER 2: MODERATE SIGNALS")
    print(f"Criteria: Day 0 1-2%, Volume >1.5x, Beat rate >50%")
    print(f"Trades: {len(tier2_candidates)}")
    print(f"Avg Return: {tier2_candidates['exit_return'].mean():.2f}%")
    print(f"Win Rate: {(tier2_candidates['exit_return'] > 0).sum() / len(tier2_candidates) * 100:.1f}%")
    print(f"Std Dev: {tier2_candidates['exit_return'].std():.2f}%")
    
    # Tier 3: Weak signals
    tier3_candidates = df[
        (df['day0_reaction'] > 0) &
        (df['day0_reaction'] <= 1) &
        (df['volume_spike'] > 1.0)
    ].copy()
    
    tier3_candidates['tier'] = 3
    tier3_candidates['entry_timing'] = 'day0_close'
    tier3_candidates['position_size'] = 2000  # Smallest positions
    tier3_candidates['exit_return'] = tier3_candidates['day10_return'] - tier3_candidates['day0_reaction']
    
    print(f"\n📋 TIER 3: WEAK SIGNALS")
    print(f"Criteria: Day 0 0-1%, Volume >1x")
    print(f"Trades: {len(tier3_candidates)}")
    print(f"Avg Return: {tier3_candidates['exit_return'].mean():.2f}%")
    print(f"Win Rate: {(tier3_candidates['exit_return'] > 0).sum() / len(tier3_candidates) * 100:.1f}%")
    print(f"Std Dev: {tier3_candidates['exit_return'].std():.2f}%")
    
    # COMBINED ANALYSIS
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE COMPARISON")
    print("=" * 80)
    
    # Combine all strategies
    all_segments = []
    
    for name, segment, strategy_type in [
        ('Step 1: Pre-Earnings', step1_candidates, '3-Step Dynamic'),
        ('Step 2: Day 0 Momentum', step2_candidates, '3-Step Dynamic'),
        ('Step 3: Day 1 Continuation', step3_candidates, '3-Step Dynamic'),
        ('Tier 1: Strong Signals', tier1_candidates, 'Hybrid Tiered'),
        ('Tier 2: Moderate Signals', tier2_candidates, 'Hybrid Tiered'),
        ('Tier 3: Weak Signals', tier3_candidates, 'Hybrid Tiered'),
    ]:
        if len(segment) > 0:
            trades = len(segment)
            avg_return = segment['exit_return'].mean()
            win_rate = (segment['exit_return'] > 0).sum() / len(segment) * 100
            std_dev = segment['exit_return'].std()
            total_pnl = (segment['exit_return'] / 100 * segment['position_size']).sum()
            avg_position = segment['position_size'].mean()
            
            all_segments.append({
                'Segment': name,
                'Strategy Type': strategy_type,
                'Trades': trades,
                'Avg Return (%)': round(avg_return, 2),
                'Win Rate (%)': round(win_rate, 1),
                'Std Dev (%)': round(std_dev, 2),
                'Avg Position ($)': int(avg_position),
                'Total P&L ($)': int(total_pnl)
            })
    
    comparison_df = pd.DataFrame(all_segments)
    print("\n" + comparison_df.to_string(index=False))
    
    # Best and worst segments
    print("\n" + "=" * 80)
    print("🏆 BEST & WORST PERFORMING SEGMENTS")
    print("=" * 80)
    
    best_idx = comparison_df['Avg Return (%)'].idxmax()
    worst_idx = comparison_df['Avg Return (%)'].idxmin()
    
    best = comparison_df.iloc[best_idx]
    worst = comparison_df.iloc[worst_idx]
    
    print(f"\n🥇 BEST SEGMENT: {best['Segment']}")
    print(f"   Strategy Type: {best['Strategy Type']}")
    print(f"   Avg Return: {best['Avg Return (%)']}%")
    print(f"   Win Rate: {best['Win Rate (%)']}%")
    print(f"   Trades: {best['Trades']}")
    print(f"   Total P&L: ${best['Total P&L ($)']:,}")
    
    print(f"\n🥉 WORST SEGMENT: {worst['Segment']}")
    print(f"   Strategy Type: {worst['Strategy Type']}")
    print(f"   Avg Return: {worst['Avg Return (%)']}%")
    print(f"   Win Rate: {worst['Win Rate (%)']}%")
    print(f"   Trades: {worst['Trades']}")
    print(f"   Total P&L: ${worst['Total P&L ($)']:,}")
    
    # Strategy type comparison
    print("\n" + "=" * 80)
    print("🔍 STRATEGY TYPE COMPARISON")
    print("=" * 80)
    
    dynamic_segments = comparison_df[comparison_df['Strategy Type'] == '3-Step Dynamic']
    hybrid_segments = comparison_df[comparison_df['Strategy Type'] == 'Hybrid Tiered']
    
    print(f"\n3-STEP DYNAMIC:")
    print(f"  Total Trades: {dynamic_segments['Trades'].sum()}")
    print(f"  Avg Return: {(dynamic_segments['Avg Return (%)'] * dynamic_segments['Trades']).sum() / dynamic_segments['Trades'].sum():.2f}%")
    print(f"  Total P&L: ${dynamic_segments['Total P&L ($)'].sum():,}")
    
    print(f"\nHYBRID TIERED:")
    print(f"  Total Trades: {hybrid_segments['Trades'].sum()}")
    print(f"  Avg Return: {(hybrid_segments['Avg Return (%)'] * hybrid_segments['Trades']).sum() / hybrid_segments['Trades'].sum():.2f}%")
    print(f"  Total P&L: ${hybrid_segments['Total P&L ($)'].sum():,}")
    
    # Key insights
    print("\n" + "=" * 80)
    print("💡 KEY INSIGHTS")
    print("=" * 80)
    
    print("\n1. BEST PERFORMING STAGE:")
    print(f"   {best['Segment']} delivers the highest returns")
    print(f"   Focus on this segment for maximum profitability")
    
    print("\n2. TRADE VOLUME:")
    total_trades = comparison_df['Trades'].sum()
    print(f"   Total opportunities across all segments: {total_trades}")
    print(f"   3-Step Dynamic contributes: {dynamic_segments['Trades'].sum()} trades")
    print(f"   Hybrid Tiered contributes: {hybrid_segments['Trades'].sum()} trades")
    
    print("\n3. RISK/REWARD:")
    high_return_segments = comparison_df[comparison_df['Avg Return (%)'] > 5]
    print(f"   Segments with >5% avg return: {len(high_return_segments)}")
    if len(high_return_segments) > 0:
        print(f"   These are: {', '.join(high_return_segments['Segment'].tolist())}")
    
    print("\n4. CONSISTENCY:")
    high_winrate_segments = comparison_df[comparison_df['Win Rate (%)'] > 70]
    print(f"   Segments with >70% win rate: {len(high_winrate_segments)}")
    if len(high_winrate_segments) > 0:
        print(f"   These are: {', '.join(high_winrate_segments['Segment'].tolist())}")
    
    # Save results
    print("\n" + "=" * 80)
    print("💾 SAVING RESULTS")
    print("=" * 80)
    
    comparison_df.to_csv('/home/fellaki10/Documents/UMushroom Investment challange/strategy2_analysis/multi_step_stage_breakdown.csv', index=False)
    print("✅ Saved: strategy2_analysis/multi_step_stage_breakdown.csv")
    
    # Save detailed trade data for each segment
    all_trades = pd.concat([
        step1_candidates.assign(segment='Step 1: Pre-Earnings'),
        step2_candidates.assign(segment='Step 2: Day 0 Momentum'),
        step3_candidates.assign(segment='Step 3: Day 1 Continuation'),
        tier1_candidates.assign(segment='Tier 1: Strong Signals'),
        tier2_candidates.assign(segment='Tier 2: Moderate Signals'),
        tier3_candidates.assign(segment='Tier 3: Weak Signals'),
    ], ignore_index=True)
    
    all_trades.to_csv('/home/fellaki10/Documents/UMushroom Investment challange/strategy2_analysis/multi_step_detailed_trades.csv', index=False)
    print("✅ Saved: strategy2_analysis/multi_step_detailed_trades.csv")
    
    print("\n" + "=" * 80)
    print("✅ MULTI-STEP STAGE ANALYSIS COMPLETE!")
    print("=" * 80)
    
    return comparison_df

if __name__ == "__main__":
    analyze_multi_step_stages()

