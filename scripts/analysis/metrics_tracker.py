"""
Comprehensive Metrics Tracker for 3-Step Earnings Strategy

This module tracks all performance, risk, and trade metrics for the strategy:
- Performance Metrics: Returns, win rate, expectancy, Sharpe ratio
- Risk Metrics: Drawdown, volatility, VAR, concentration
- Trade Metrics: Trade count, hold periods, exit reasons
- Portfolio Metrics: Position utilization, sector exposure, cash management

Author: UMushroom Competition Strategy
Date: October 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json


class MetricsTracker:
    """Comprehensive metrics tracking system"""
    
    def __init__(self, initial_capital: float = 100000):
        """
        Initialize metrics tracker
        
        Parameters:
        - initial_capital: Starting portfolio value
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        self.daily_values = []
        self.positions = {}
        
    # ==================== TRADE TRACKING ====================
    
    def add_trade(self, trade: Dict):
        """
        Add a completed trade to tracking
        
        Parameters:
        - trade: Dictionary with trade details
          Required keys: ticker, entry_date, exit_date, entry_price, exit_price,
                        shares, return_pct, pnl, exit_reason
        """
        trade['trade_id'] = len(self.trades) + 1
        trade['hold_days'] = (pd.to_datetime(trade['exit_date']) - 
                             pd.to_datetime(trade['entry_date'])).days
        self.trades.append(trade)
        
        # Update capital
        self.current_capital += trade['pnl']
    
    def add_daily_value(self, date: str, portfolio_value: float):
        """Track daily portfolio value"""
        self.daily_values.append({
            'date': date,
            'value': portfolio_value,
            'return': (portfolio_value - self.initial_capital) / self.initial_capital * 100
        })
    
    # ==================== PERFORMANCE METRICS ====================
    
    def get_performance_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics"""
        if not self.trades:
            return self._empty_metrics()
        
        df = pd.DataFrame(self.trades)
        
        # Basic metrics
        total_trades = len(df)
        profitable_trades = len(df[df['pnl'] > 0])
        losing_trades = len(df[df['pnl'] < 0])
        breakeven_trades = len(df[df['pnl'] == 0])
        
        # Return metrics
        total_return = (self.current_capital - self.initial_capital) / self.initial_capital * 100
        avg_return = df['return_pct'].mean()
        median_return = df['return_pct'].median()
        
        # Win/Loss metrics
        win_rate = profitable_trades / total_trades * 100 if total_trades > 0 else 0
        avg_win = df[df['pnl'] > 0]['return_pct'].mean() if profitable_trades > 0 else 0
        avg_loss = df[df['pnl'] < 0]['return_pct'].mean() if losing_trades > 0 else 0
        
        # Expectancy
        expectancy = (avg_win * win_rate / 100) + (avg_loss * (100 - win_rate) / 100)
        
        # Sharpe ratio (if we have daily values)
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        # Hold period
        avg_hold_days = df['hold_days'].mean() if 'hold_days' in df.columns else 0
        
        # Largest win/loss
        largest_win = df['return_pct'].max()
        largest_loss = df['return_pct'].min()
        
        return {
            'total_return': total_return,
            'avg_return_per_trade': avg_return,
            'median_return': median_return,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'losing_trades': losing_trades,
            'breakeven_trades': breakeven_trades,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'expectancy': expectancy,
            'sharpe_ratio': sharpe_ratio,
            'avg_hold_days': avg_hold_days,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'current_capital': self.current_capital,
            'total_pnl': self.current_capital - self.initial_capital
        }
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio from daily returns"""
        if len(self.daily_values) < 2:
            return 0.0
        
        df = pd.DataFrame(self.daily_values)
        df['daily_return'] = df['value'].pct_change() * 100
        df = df.dropna()
        
        if len(df) == 0:
            return 0.0
        
        avg_return = df['daily_return'].mean()
        std_return = df['daily_return'].std()
        
        if std_return == 0:
            return 0.0
        
        # Annualize (252 trading days)
        sharpe = (avg_return - risk_free_rate) / std_return * np.sqrt(252)
        return sharpe
    
    # ==================== RISK METRICS ====================
    
    def get_risk_metrics(self) -> Dict:
        """Calculate comprehensive risk metrics"""
        if not self.trades and not self.daily_values:
            return self._empty_risk_metrics()
        
        # Drawdown metrics
        max_drawdown, current_drawdown = self._calculate_drawdowns()
        
        # Volatility metrics
        volatility = self._calculate_volatility()
        
        # Value at Risk (95% confidence)
        var_95 = self._calculate_var(0.95)
        cvar_95 = self._calculate_cvar(0.95)
        
        # Trade-based risk
        df = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
        max_consecutive_losses = self._calculate_max_consecutive_losses(df)
        
        return {
            'max_drawdown': max_drawdown,
            'current_drawdown': current_drawdown,
            'volatility_annual': volatility,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'max_consecutive_losses': max_consecutive_losses,
            'risk_adjusted_return': 0.0  # Calculated separately to avoid recursion
        }
    
    def _calculate_drawdowns(self) -> Tuple[float, float]:
        """Calculate maximum and current drawdown"""
        if not self.daily_values:
            return 0.0, 0.0
        
        df = pd.DataFrame(self.daily_values)
        df['cummax'] = df['value'].cummax()
        df['drawdown'] = (df['value'] - df['cummax']) / df['cummax'] * 100
        
        max_drawdown = df['drawdown'].min()
        current_drawdown = df['drawdown'].iloc[-1] if len(df) > 0 else 0.0
        
        return max_drawdown, current_drawdown
    
    def _calculate_volatility(self) -> float:
        """Calculate annualized volatility"""
        if len(self.daily_values) < 2:
            return 0.0
        
        df = pd.DataFrame(self.daily_values)
        df['daily_return'] = df['value'].pct_change()
        
        # Annualize (252 trading days)
        volatility = df['daily_return'].std() * np.sqrt(252) * 100
        return volatility
    
    def _calculate_var(self, confidence: float = 0.95) -> float:
        """Calculate Value at Risk"""
        if not self.trades:
            return 0.0
        
        df = pd.DataFrame(self.trades)
        returns = df['return_pct'].values
        
        var = np.percentile(returns, (1 - confidence) * 100)
        return var
    
    def _calculate_cvar(self, confidence: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        if not self.trades:
            return 0.0
        
        var = self._calculate_var(confidence)
        df = pd.DataFrame(self.trades)
        returns = df['return_pct'].values
        
        # Average of returns below VaR
        cvar = returns[returns <= var].mean()
        return cvar
    
    def _calculate_max_consecutive_losses(self, df: pd.DataFrame) -> int:
        """Calculate maximum consecutive losing trades"""
        if len(df) == 0:
            return 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for _, trade in df.iterrows():
            if trade['pnl'] < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def calculate_risk_adjusted_score(self) -> float:
        """Calculate risk-adjusted return score (composite metric)"""
        perf = self.get_performance_metrics()
        
        # Weighted score (no circular dependency)
        score = (perf['expectancy'] * 0.4 + 
                perf['win_rate'] * 0.3 + 
                perf['total_trades']/50 * 0.2 +
                perf['sharpe_ratio'] * 0.1)
        
        return score
    
    # ==================== TRADE METRICS ====================
    
    def get_trade_metrics(self) -> Dict:
        """Calculate trade-specific metrics"""
        if not self.trades:
            return self._empty_trade_metrics()
        
        df = pd.DataFrame(self.trades)
        
        # Exit reason distribution
        exit_reasons = df['exit_reason'].value_counts().to_dict()
        
        # Hold period distribution
        hold_periods = {
            'avg_days': df['hold_days'].mean(),
            'median_days': df['hold_days'].median(),
            'min_days': df['hold_days'].min(),
            'max_days': df['hold_days'].max()
        }
        
        # Position sizing
        position_sizes = {
            'avg_position': df['shares'].mean() * df['entry_price'].mean(),
            'largest_position': (df['shares'] * df['entry_price']).max(),
            'smallest_position': (df['shares'] * df['entry_price']).min()
        }
        
        # Ticker distribution
        ticker_distribution = df['ticker'].value_counts().head(10).to_dict()
        
        return {
            'exit_reasons': exit_reasons,
            'hold_periods': hold_periods,
            'position_sizes': position_sizes,
            'ticker_distribution': ticker_distribution,
            'trades_per_month': len(df) / (len(set(df['entry_date'].str[:7])) or 1)
        }
    
    # ==================== PORTFOLIO METRICS ====================
    
    def get_portfolio_metrics(self, current_positions: Dict = None) -> Dict:
        """Calculate current portfolio metrics"""
        if current_positions is None:
            current_positions = self.positions
        
        # Position count and capital deployment
        active_positions = len(current_positions)
        deployed_capital = sum(pos.get('market_value', 0) for pos in current_positions.values())
        cash_reserve = self.current_capital - deployed_capital
        position_utilization = deployed_capital / self.current_capital * 100 if self.current_capital > 0 else 0
        
        # Sector exposure (if available)
        sector_exposure = {}
        for ticker, pos in current_positions.items():
            sector = pos.get('sector', 'Unknown')
            sector_exposure[sector] = sector_exposure.get(sector, 0) + pos.get('market_value', 0)
        
        # Concentration risk (largest position as % of portfolio)
        max_position_value = max([pos.get('market_value', 0) for pos in current_positions.values()]) if current_positions else 0
        concentration_risk = max_position_value / self.current_capital * 100 if self.current_capital > 0 else 0
        
        return {
            'current_capital': self.current_capital,
            'deployed_capital': deployed_capital,
            'cash_reserve': cash_reserve,
            'position_utilization': position_utilization,
            'active_positions': active_positions,
            'sector_exposure': sector_exposure,
            'concentration_risk': concentration_risk,
            'avg_position_size': deployed_capital / active_positions if active_positions > 0 else 0
        }
    
    # ==================== REPORTING ====================
    
    def generate_summary_report(self) -> str:
        """Generate comprehensive summary report"""
        perf = self.get_performance_metrics()
        risk = self.get_risk_metrics()
        trade = self.get_trade_metrics()
        portfolio = self.get_portfolio_metrics()
        
        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                     STRATEGY PERFORMANCE SUMMARY                           ║
╚════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 PERFORMANCE METRICS

Total Return:             {perf['total_return']:>8.2f}%
Average Return/Trade:     {perf['avg_return_per_trade']:>8.2f}%
Median Return/Trade:      {perf['median_return']:>8.2f}%
Win Rate:                 {perf['win_rate']:>8.2f}%
Total Trades:             {perf['total_trades']:>8.0f}
Profitable Trades:        {perf['profitable_trades']:>8.0f}
Losing Trades:            {perf['losing_trades']:>8.0f}

Average Win:              {perf['avg_win']:>8.2f}%
Average Loss:             {perf['avg_loss']:>8.2f}%
Expectancy:               {perf['expectancy']:>8.2f}%
Profit Factor:            {perf['profit_factor']:>8.2f}x

Sharpe Ratio:             {perf['sharpe_ratio']:>8.2f}
Average Hold Days:        {perf['avg_hold_days']:>8.1f}

Largest Win:              {perf['largest_win']:>8.2f}%
Largest Loss:             {perf['largest_loss']:>8.2f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  RISK METRICS

Max Drawdown:             {risk['max_drawdown']:>8.2f}%
Current Drawdown:         {risk['current_drawdown']:>8.2f}%
Annual Volatility:        {risk['volatility_annual']:>8.2f}%
Value at Risk (95%):      {risk['var_95']:>8.2f}%
CVaR (95%):              {risk['cvar_95']:>8.2f}%
Max Consecutive Losses:   {risk['max_consecutive_losses']:>8.0f}
Risk-Adjusted Score:      {risk['risk_adjusted_return']:>8.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💼 PORTFOLIO STATUS

Current Capital:          ${portfolio['current_capital']:>12,.2f}
Deployed Capital:         ${portfolio['deployed_capital']:>12,.2f}
Cash Reserve:             ${portfolio['cash_reserve']:>12,.2f}
Position Utilization:     {portfolio['position_utilization']:>8.2f}%
Active Positions:         {portfolio['active_positions']:>8.0f}
Concentration Risk:       {portfolio['concentration_risk']:>8.2f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 CAPITAL PERFORMANCE

Initial Capital:          ${self.initial_capital:>12,.2f}
Current Capital:          ${self.current_capital:>12,.2f}
Total P&L:               ${perf['total_pnl']:>12,.2f}
Return on Capital:        {perf['total_return']:>8.2f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return report
    
    def export_trades_to_csv(self, filename: str):
        """Export all trades to CSV file"""
        if not self.trades:
            print("No trades to export")
            return
        
        df = pd.DataFrame(self.trades)
        df.to_csv(filename, index=False)
        print(f"✅ Exported {len(df)} trades to {filename}")
    
    def export_metrics_to_json(self, filename: str):
        """Export all metrics to JSON file"""
        metrics = {
            'performance': self.get_performance_metrics(),
            'risk': self.get_risk_metrics(),
            'trade': self.get_trade_metrics(),
            'portfolio': self.get_portfolio_metrics()
        }
        
        with open(filename, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        print(f"✅ Exported metrics to {filename}")
    
    # ==================== HELPER METHODS ====================
    
    def _empty_metrics(self) -> Dict:
        """Return empty performance metrics"""
        return {
            'total_return': 0.0,
            'avg_return_per_trade': 0.0,
            'median_return': 0.0,
            'win_rate': 0.0,
            'total_trades': 0,
            'profitable_trades': 0,
            'losing_trades': 0,
            'breakeven_trades': 0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'expectancy': 0.0,
            'sharpe_ratio': 0.0,
            'avg_hold_days': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'profit_factor': 0.0,
            'current_capital': self.initial_capital,
            'total_pnl': 0.0
        }
    
    def _empty_risk_metrics(self) -> Dict:
        """Return empty risk metrics"""
        return {
            'max_drawdown': 0.0,
            'current_drawdown': 0.0,
            'volatility_annual': 0.0,
            'var_95': 0.0,
            'cvar_95': 0.0,
            'max_consecutive_losses': 0,
            'risk_adjusted_return': 0.0
        }
    
    def _empty_trade_metrics(self) -> Dict:
        """Return empty trade metrics"""
        return {
            'exit_reasons': {},
            'hold_periods': {'avg_days': 0, 'median_days': 0, 'min_days': 0, 'max_days': 0},
            'position_sizes': {'avg_position': 0, 'largest_position': 0, 'smallest_position': 0},
            'ticker_distribution': {},
            'trades_per_month': 0
        }


if __name__ == '__main__':
    # Test the metrics tracker
    print("=" * 80)
    print("METRICS TRACKER TEST")
    print("=" * 80)
    
    # Initialize tracker
    tracker = MetricsTracker(initial_capital=100000)
    
    # Add some sample trades
    sample_trades = [
        {
            'ticker': 'AAPL',
            'entry_date': '2025-01-01',
            'exit_date': '2025-01-15',
            'entry_price': 150.0,
            'exit_price': 165.0,
            'shares': 40,
            'return_pct': 10.0,
            'pnl': 600.0,
            'exit_reason': 'take_profit'
        },
        {
            'ticker': 'GOOGL',
            'entry_date': '2025-01-03',
            'exit_date': '2025-01-12',
            'entry_price': 140.0,
            'exit_price': 133.0,
            'shares': 42,
            'return_pct': -5.0,
            'pnl': -294.0,
            'exit_reason': 'stop_loss'
        },
        {
            'ticker': 'MSFT',
            'entry_date': '2025-01-05',
            'exit_date': '2025-01-20',
            'entry_price': 370.0,
            'exit_price': 407.0,
            'shares': 16,
            'return_pct': 10.0,
            'pnl': 592.0,
            'exit_reason': 'take_profit'
        }
    ]
    
    for trade in sample_trades:
        tracker.add_trade(trade)
    
    # Add daily values
    for i in range(30):
        value = 100000 + i * 100 + np.random.randn() * 200
        tracker.add_daily_value(f'2025-01-{i+1:02d}', value)
    
    # Generate report
    print(tracker.generate_summary_report())
    
    print("\n✅ Metrics tracker test complete!")

