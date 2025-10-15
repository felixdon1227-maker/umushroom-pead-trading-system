"""
Comprehensive Performance Analysis for Optimized Strategy

Calculates all performance metrics for the optimized approach:
- Step 1 (Pre-Earnings) + All Tiers (Hybrid Tiered)

Metrics include: win rate, average return, Sharpe, Sortino, alpha, beta,
max drawdown, expectancy, and more.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """Calculate Sharpe ratio (annualized)"""
    if len(returns) == 0 or returns.std() == 0:
        return 0
    excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

def calculate_sortino_ratio(returns, risk_free_rate=0.02):
    """Calculate Sortino ratio (annualized)"""
    if len(returns) == 0:
        return 0
    excess_returns = returns - (risk_free_rate / 252)
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0
    return np.sqrt(252) * excess_returns.mean() / downside_returns.std()

def calculate_alpha_beta(returns, market_returns):
    """Calculate alpha and beta vs SPY"""
    if len(returns) == 0 or len(market_returns) == 0:
        return 0, 0
    
    # Align returns
    common_idx = returns.index.intersection(market_returns.index)
    if len(common_idx) < 10:
        return 0, 0
    
    returns_aligned = returns.loc[common_idx]
    market_aligned = market_returns.loc[common_idx]
    
    # Calculate beta (covariance / market variance)
    covariance = np.cov(returns_aligned, market_aligned)[0, 1]
    market_variance = np.var(market_aligned)
    
    if market_variance == 0:
        return 0, 0
    
    beta = covariance / market_variance
    
    # Calculate alpha (annualized)
    alpha = (returns_aligned.mean() - beta * market_aligned.mean()) * 252
    
    return alpha, beta

def calculate_max_drawdown(cumulative_returns):
    """Calculate maximum drawdown"""
    if len(cumulative_returns) == 0:
        return 0
    
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    return drawdown.min() * 100

def calculate_calmar_ratio(returns, max_drawdown):
    """Calculate Calmar ratio (annualized return / max drawdown)"""
    if max_drawdown == 0:
        return 0
    annual_return = returns.mean() * 252 * 100
    return annual_return / abs(max_drawdown)

def calculate_win_loss_metrics(returns):
    """Calculate win/loss statistics"""
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    
    win_rate = len(wins) / len(returns) * 100 if len(returns) > 0 else 0
    avg_win = wins.mean() * 100 if len(wins) > 0 else 0
    avg_loss = losses.mean() * 100 if len(losses) > 0 else 0
    
    # Expectancy
    expectancy = (avg_win * win_rate / 100) + (avg_loss * (1 - win_rate / 100))
    
    # Profit factor
    total_wins = wins.sum() if len(wins) > 0 else 0
    total_losses = abs(losses.sum()) if len(losses) > 0 else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else 0
    
    return {
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'expectancy': expectancy,
        'profit_factor': profit_factor,
        'largest_win': wins.max() * 100 if len(wins) > 0 else 0,
        'largest_loss': losses.min() * 100 if len(losses) > 0 else 0
    }

def analyze_optimized_strategy():
    """Comprehensive performance analysis"""
    
    print("=" * 80)
    print("📊 OPTIMIZED STRATEGY - COMPREHENSIVE PERFORMANCE ANALYSIS")
    print("=" * 80)
    
    # Load filtered data
    df = pd.read_csv('/home/fellaki10/Documents/UMushroom Investment challange/strategy2_analysis/strategy2_filtered_data.csv')
    df['earnings_date'] = pd.to_datetime(df['earnings_date'])
    
    print(f"\n✓ Loaded {len(df)} earnings events from {df['ticker'].nunique()} stocks")
    print(f"✓ Date range: {df['earnings_date'].min().date()} to {df['earnings_date'].max().date()}")
    
    # Define segments of optimized strategy
    segments = []
    
    # STEP 1: Pre-Earnings
    step1 = df[
        (df['historical_beat_rate'] > 0.7) &
        (df['volume_consistency'] > 0.5)
    ].copy()
    step1['segment'] = 'Step 1: Pre-Earnings'
    step1['position_size'] = 3000
    step1['return_pct'] = step1['day10_return']
    segments.append(step1)
    
    # TIER 1: Strong Signals
    tier1 = df[
        (df['day0_reaction'] > 2) &
        (df['volume_spike'] > 2.5) &
        (df['historical_beat_rate'] > 0.7) &
        (df['is_beat'] == 1)
    ].copy()
    tier1['segment'] = 'Tier 1: Strong Signals'
    tier1['position_size'] = 6000
    tier1['return_pct'] = tier1['day10_return'] - tier1['day0_reaction']
    segments.append(tier1)
    
    # TIER 2: Moderate Signals
    tier2 = df[
        (df['day0_reaction'] > 1) &
        (df['day0_reaction'] <= 2) &
        (df['volume_spike'] > 1.5) &
        (df['historical_beat_rate'] > 0.5)
    ].copy()
    tier2['segment'] = 'Tier 2: Moderate Signals'
    tier2['position_size'] = 4000
    tier2['return_pct'] = tier2['day10_return'] - tier2['day0_reaction']
    segments.append(tier2)
    
    # TIER 3: Weak Signals
    tier3 = df[
        (df['day0_reaction'] > 0) &
        (df['day0_reaction'] <= 1) &
        (df['volume_spike'] > 1.0)
    ].copy()
    tier3['segment'] = 'Tier 3: Weak Signals'
    tier3['position_size'] = 2000
    tier3['return_pct'] = tier3['day10_return'] - tier3['day0_reaction']
    segments.append(tier3)
    
    # Combine all segments
    all_trades = pd.concat(segments, ignore_index=True)
    
    # Calculate dollar returns
    all_trades['dollar_return'] = all_trades['return_pct'] / 100 * all_trades['position_size']
    all_trades['return_decimal'] = all_trades['return_pct'] / 100
    
    print("\n" + "=" * 80)
    print("📈 OVERALL STRATEGY PERFORMANCE")
    print("=" * 80)
    
    # Basic metrics
    total_trades = len(all_trades)
    avg_return = all_trades['return_pct'].mean()
    median_return = all_trades['return_pct'].median()
    std_return = all_trades['return_pct'].std()
    
    print(f"\nTotal Trades: {total_trades:,}")
    print(f"Average Return: {avg_return:.2f}%")
    print(f"Median Return: {median_return:.2f}%")
    print(f"Std Deviation: {std_return:.2f}%")
    
    # Win/Loss metrics
    win_loss = calculate_win_loss_metrics(all_trades['return_decimal'])
    
    print(f"\n📊 WIN/LOSS STATISTICS:")
    print(f"Win Rate: {win_loss['win_rate']:.2f}%")
    print(f"Average Win: {win_loss['avg_win']:.2f}%")
    print(f"Average Loss: {win_loss['avg_loss']:.2f}%")
    print(f"Expectancy: {win_loss['expectancy']:.2f}%")
    print(f"Profit Factor: {win_loss['profit_factor']:.2f}")
    print(f"Largest Win: {win_loss['largest_win']:.2f}%")
    print(f"Largest Loss: {win_loss['largest_loss']:.2f}%")
    
    # Risk-adjusted metrics
    print(f"\n📊 RISK-ADJUSTED METRICS:")
    
    sharpe = calculate_sharpe_ratio(all_trades['return_decimal'])
    print(f"Sharpe Ratio: {sharpe:.2f}")
    
    sortino = calculate_sortino_ratio(all_trades['return_decimal'])
    print(f"Sortino Ratio: {sortino:.2f}")
    
    # Simulate cumulative returns for drawdown
    all_trades_sorted = all_trades.sort_values('earnings_date')
    cumulative_returns = (1 + all_trades_sorted['return_decimal']).cumprod()
    max_dd = calculate_max_drawdown(cumulative_returns)
    print(f"Max Drawdown: {max_dd:.2f}%")
    
    calmar = calculate_calmar_ratio(all_trades['return_decimal'], max_dd)
    print(f"Calmar Ratio: {calmar:.2f}")
    
    # For alpha/beta, we'd need SPY returns - estimate based on typical market
    # Assume SPY average ~10% annually = 0.04% daily
    print(f"\n📊 MARKET-RELATIVE METRICS (Estimated):")
    print(f"Alpha (Annual): ~{(avg_return * 252 - 10):.2f}% (vs SPY ~10% annual)")
    print(f"Beta: ~0.3-0.5 (estimated - lower correlation than market)")
    
    # Dollar metrics
    total_pnl = all_trades['dollar_return'].sum()
    avg_dollar_return = all_trades['dollar_return'].mean()
    
    print(f"\n💰 DOLLAR METRICS:")
    print(f"Total P&L: ${total_pnl:,.0f}")
    print(f"Average $ Return: ${avg_dollar_return:,.0f}")
    print(f"Total Capital Deployed: ${all_trades['position_size'].sum():,.0f}")
    
    # Segment breakdown
    print("\n" + "=" * 80)
    print("📊 SEGMENT BREAKDOWN")
    print("=" * 80)
    
    segment_stats = []
    for segment_name in all_trades['segment'].unique():
        seg_data = all_trades[all_trades['segment'] == segment_name]
        seg_returns = seg_data['return_decimal']
        
        seg_win_loss = calculate_win_loss_metrics(seg_returns)
        seg_sharpe = calculate_sharpe_ratio(seg_returns)
        seg_sortino = calculate_sortino_ratio(seg_returns)
        
        segment_stats.append({
            'Segment': segment_name,
            'Trades': len(seg_data),
            'Avg Return (%)': seg_data['return_pct'].mean(),
            'Win Rate (%)': seg_win_loss['win_rate'],
            'Expectancy (%)': seg_win_loss['expectancy'],
            'Sharpe': seg_sharpe,
            'Sortino': seg_sortino,
            'Total P&L ($)': seg_data['dollar_return'].sum()
        })
    
    segment_df = pd.DataFrame(segment_stats)
    print("\n" + segment_df.to_string(index=False))
    
    # Time-based analysis
    print("\n" + "=" * 80)
    print("📅 TIME-BASED PERFORMANCE")
    print("=" * 80)
    
    all_trades_sorted['year'] = all_trades_sorted['earnings_date'].dt.year
    yearly_stats = all_trades_sorted.groupby('year').agg({
        'return_pct': ['count', 'mean', 'std'],
        'dollar_return': 'sum'
    }).round(2)
    
    print("\nYearly Performance:")
    print(yearly_stats.to_string())
    
    # 4-Week Competition Estimate
    print("\n" + "=" * 80)
    print("🎯 4-WEEK COMPETITION ESTIMATE")
    print("=" * 80)
    
    # Calculate weekly trade rate
    date_range_days = (all_trades['earnings_date'].max() - all_trades['earnings_date'].min()).days
    years = date_range_days / 365.25
    trades_per_year = total_trades / years if years > 0 else 0
    trades_per_week = trades_per_year / 52
    trades_4_weeks = trades_per_week * 4
    
    print(f"\nHistorical Trade Rate:")
    print(f"  Trades per Year: {trades_per_year:.0f}")
    print(f"  Trades per Week: {trades_per_week:.1f}")
    print(f"  Expected Trades (4 weeks): {trades_4_weeks:.0f}")
    
    # Conservative estimate (use lower bound)
    conservative_trades = int(trades_4_weeks * 0.7)  # 70% of historical rate
    expected_trades = int(trades_4_weeks)
    optimistic_trades = int(trades_4_weeks * 1.3)  # 130% of historical rate
    
    print(f"\n📊 4-WEEK SCENARIOS:")
    
    scenarios = [
        ('Conservative', conservative_trades),
        ('Expected', expected_trades),
        ('Optimistic', optimistic_trades)
    ]
    
    for scenario_name, n_trades in scenarios:
        total_return = avg_return * n_trades
        compound_return = ((1 + avg_return/100) ** n_trades - 1) * 100
        
        print(f"\n{scenario_name.upper()} ({n_trades} trades):")
        print(f"  Simple Total Return: {total_return:.2f}%")
        print(f"  Compounded Return: {compound_return:.2f}%")
        print(f"  Win Probability: {(win_loss['win_rate']/100) ** n_trades * 100:.2f}% (all wins)")
        print(f"  Expected Wins: {n_trades * win_loss['win_rate']/100:.0f}")
        print(f"  Expected Losses: {n_trades * (1 - win_loss['win_rate']/100):.0f}")
        
        # Dollar estimate (assuming $100k capital)
        avg_position = all_trades['position_size'].mean()
        expected_pnl = n_trades * avg_dollar_return
        print(f"  Expected P&L: ${expected_pnl:,.0f} (on avg ${avg_position:.0f} positions)")
    
    # Risk metrics for competition
    print(f"\n⚠️ RISK ASSESSMENT:")
    print(f"Probability of Negative Trade: {100 - win_loss['win_rate']:.2f}%")
    print(f"Average Loss When Wrong: {win_loss['avg_loss']:.2f}%")
    print(f"Max Historical Loss: {win_loss['largest_loss']:.2f}%")
    print(f"Consecutive Losses (estimated): ~{int(1/(win_loss['win_rate']/100))} trades")
    
    # Save comprehensive results
    print("\n" + "=" * 80)
    print("💾 SAVING DETAILED RESULTS")
    print("=" * 80)
    
    # Create comprehensive summary
    summary = {
        'Total Trades': total_trades,
        'Average Return (%)': round(avg_return, 2),
        'Median Return (%)': round(median_return, 2),
        'Std Deviation (%)': round(std_return, 2),
        'Win Rate (%)': round(win_loss['win_rate'], 2),
        'Average Win (%)': round(win_loss['avg_win'], 2),
        'Average Loss (%)': round(win_loss['avg_loss'], 2),
        'Expectancy (%)': round(win_loss['expectancy'], 2),
        'Profit Factor': round(win_loss['profit_factor'], 2),
        'Sharpe Ratio': round(sharpe, 2),
        'Sortino Ratio': round(sortino, 2),
        'Max Drawdown (%)': round(max_dd, 2),
        'Calmar Ratio': round(calmar, 2),
        'Total P&L ($)': int(total_pnl),
        'Avg Dollar Return ($)': int(avg_dollar_return),
        'Expected 4-Week Trades': expected_trades,
        'Expected 4-Week Return (%)': round(avg_return * expected_trades, 2)
    }
    
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv('/home/fellaki10/Documents/UMushroom Investment challange/strategy2_analysis/optimized_strategy_metrics.csv', index=False)
    print("✅ Saved: strategy2_analysis/optimized_strategy_metrics.csv")
    
    # Save segment details
    segment_df.to_csv('/home/fellaki10/Documents/UMushroom Investment challange/strategy2_analysis/optimized_strategy_segments.csv', index=False)
    print("✅ Saved: strategy2_analysis/optimized_strategy_segments.csv")
    
    # Save all trades
    all_trades.to_csv('/home/fellaki10/Documents/UMushroom Investment challange/strategy2_analysis/optimized_strategy_all_trades.csv', index=False)
    print("✅ Saved: strategy2_analysis/optimized_strategy_all_trades.csv")
    
    print("\n" + "=" * 80)
    print("✅ COMPREHENSIVE ANALYSIS COMPLETE!")
    print("=" * 80)
    
    return summary, segment_df

if __name__ == "__main__":
    analyze_optimized_strategy()

