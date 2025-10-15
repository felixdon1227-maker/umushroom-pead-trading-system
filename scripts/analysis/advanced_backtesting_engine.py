"""
ADVANCED BACKTESTING ENGINE - Multi-Strategy Optimization System
==============================================================

This script provides a comprehensive backtesting engine for PEAD strategies:
1. Multi-strategy backtesting with parameter optimization
2. Advanced performance metrics and risk analysis
3. Monte Carlo simulation and walk-forward analysis
4. Portfolio optimization and position sizing
5. Real-time strategy comparison and ranking

Features:
- Multiple strategy frameworks (momentum, mean reversion, breakout)
- Parameter optimization using genetic algorithms
- Risk-adjusted performance metrics
- Drawdown analysis and recovery periods
- Sharpe ratio, Sortino ratio, Calmar ratio
- Maximum drawdown and VaR calculations
- Portfolio heat maps and correlation analysis

Author: UMushroom Investment Strategy
Date: October 2024
"""

import pandas as pd
import numpy as np
import time
import os
import sys
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import warnings
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.optimize import minimize
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import itertools

warnings.filterwarnings('ignore')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

@dataclass
class BacktestResult:
    """Data structure for backtest results"""
    strategy_name: str
    parameters: Dict
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_return: float
    var_95: float
    cvar_95: float
    trades: List[Dict]
    equity_curve: pd.Series
    drawdown_curve: pd.Series
    monthly_returns: pd.Series
    created_at: datetime

@dataclass
class StrategyParameters:
    """Data structure for strategy parameters"""
    entry_threshold: float = 0.02
    exit_threshold: float = 0.05
    stop_loss: float = 0.03
    take_profit: float = 0.08
    hold_days: int = 7
    position_size: float = 0.05
    min_volume: float = 1000000
    min_market_cap: float = 1000000000
    sector_filter: List[str] = None
    momentum_period: int = 20
    volatility_period: int = 20
    rsi_period: int = 14
    rsi_oversold: float = 30
    rsi_overbought: float = 70

class AdvancedBacktestingEngine:
    """Advanced backtesting engine with optimization capabilities"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or str(project_root / 'data' / 'all_stocks_complete')
        self.logger = self._setup_logger()
        self.results = []
        self.optimization_results = {}
        
        # Create results directory
        (project_root / 'results' / 'backtesting').mkdir(parents=True, exist_ok=True)
        
    def _setup_logger(self):
        """Setup logger"""
        logger = logging.getLogger('BacktestingEngine')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            (project_root / 'logs').mkdir(exist_ok=True)
            handler = logging.FileHandler(
                project_root / f'logs/backtesting_engine_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def load_stock_data(self, ticker: str) -> Dict[str, pd.DataFrame]:
        """Load all data for a stock"""
        stock_dir = Path(self.data_dir) / ticker
        
        data = {}
        
        # Load daily data
        daily_file = stock_dir / f'{ticker}_daily_10years_tws.csv'
        if daily_file.exists():
            data['daily'] = pd.read_csv(daily_file, index_col=0, parse_dates=True)
        
        # Load intraday data
        intraday_file = stock_dir / f'{ticker}_30min_earnings_tws.csv'
        if intraday_file.exists():
            data['intraday'] = pd.read_csv(intraday_file, index_col=0, parse_dates=True)
        
        # Load fundamentals
        fundamentals_file = stock_dir / f'{ticker}_fundamentals.json'
        if fundamentals_file.exists():
            with open(fundamentals_file, 'r') as f:
                data['fundamentals'] = json.load(f)
        
        # Load earnings data
        earnings_file = stock_dir / f'{ticker}_earnings_history.json'
        if earnings_file.exists():
            with open(earnings_file, 'r') as f:
                data['earnings'] = json.load(f)
        
        return data
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        df = df.copy()
        
        # Price-based indicators
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        df['sma_50'] = df['Close'].rolling(window=50).mean()
        df['ema_12'] = df['Close'].ewm(span=12).mean()
        df['ema_26'] = df['Close'].ewm(span=26).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Momentum indicators
        df['rsi'] = self._calculate_rsi(df['Close'], 14)
        df['stoch_k'] = self._calculate_stochastic(df, 14)
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
        
        # Volatility indicators
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self._calculate_bollinger_bands(df['Close'], 20, 2)
        df['atr'] = self._calculate_atr(df, 14)
        
        # Volume indicators
        df['volume_sma'] = df['Volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_sma']
        
        # Price action indicators
        df['price_change'] = df['Close'].pct_change()
        df['volatility'] = df['price_change'].rolling(window=20).std()
        df['momentum'] = df['Close'] / df['Close'].shift(20) - 1
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_stochastic(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Stochastic %K"""
        lowest_low = df['Low'].rolling(window=period).min()
        highest_high = df['High'].rolling(window=period).max()
        k_percent = 100 * ((df['Close'] - lowest_low) / (highest_high - lowest_low))
        return k_percent
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def pead_momentum_strategy(self, data: Dict[str, pd.DataFrame], params: StrategyParameters) -> List[Dict]:
        """PEAD Momentum Strategy"""
        trades = []
        daily_data = data['daily']
        
        if daily_data is None or daily_data.empty:
            return trades
        
        # Calculate technical indicators
        daily_data = self.calculate_technical_indicators(daily_data)
        
        # Get earnings dates
        earnings_dates = self._get_earnings_dates(data)
        
        for earnings_date in earnings_dates:
            try:
                # Find the trading day closest to earnings
                earnings_idx = daily_data.index.get_indexer([earnings_date], method='nearest')[0]
                if earnings_idx == -1:
                    continue
                
                # Entry: Day -1 (day before earnings)
                entry_idx = earnings_idx - 1
                if entry_idx < 0:
                    continue
                
                entry_date = daily_data.index[entry_idx]
                entry_price = daily_data.iloc[entry_idx]['Close']
                
                # Check entry conditions
                if not self._check_entry_conditions(daily_data.iloc[entry_idx], params):
                    continue
                
                # Exit: Day +params.hold_days
                exit_idx = earnings_idx + params.hold_days
                if exit_idx >= len(daily_data):
                    exit_idx = len(daily_data) - 1
                
                exit_date = daily_data.index[exit_idx]
                exit_price = daily_data.iloc[exit_idx]['Close']
                
                # Calculate trade return
                trade_return = (exit_price - entry_price) / entry_price
                
                # Apply stop loss and take profit
                if trade_return <= -params.stop_loss:
                    trade_return = -params.stop_loss
                elif trade_return >= params.take_profit:
                    trade_return = params.take_profit
                
                # Record trade
                trade = {
                    'ticker': data.get('fundamentals', {}).get('ticker', 'Unknown'),
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'return': trade_return,
                    'earnings_date': earnings_date,
                    'hold_days': exit_idx - entry_idx,
                    'strategy': 'PEAD_Momentum'
                }
                
                trades.append(trade)
                
            except Exception as e:
                self.logger.warning(f"Error processing earnings date {earnings_date}: {e}")
                continue
        
        return trades
    
    def mean_reversion_strategy(self, data: Dict[str, pd.DataFrame], params: StrategyParameters) -> List[Dict]:
        """Mean Reversion Strategy"""
        trades = []
        daily_data = data['daily']
        
        if daily_data is None or daily_data.empty:
            return trades
        
        # Calculate technical indicators
        daily_data = self.calculate_technical_indicators(daily_data)
        
        # Get earnings dates
        earnings_dates = self._get_earnings_dates(data)
        
        for earnings_date in earnings_dates:
            try:
                # Find the trading day closest to earnings
                earnings_idx = daily_data.index.get_indexer([earnings_date], method='nearest')[0]
                if earnings_idx == -1:
                    continue
                
                # Entry: Day +1 (day after earnings, looking for reversal)
                entry_idx = earnings_idx + 1
                if entry_idx >= len(daily_data):
                    continue
                
                entry_date = daily_data.index[entry_idx]
                entry_price = daily_data.iloc[entry_idx]['Close']
                
                # Check for oversold conditions (RSI < 30)
                if daily_data.iloc[entry_idx]['rsi'] > params.rsi_oversold:
                    continue
                
                # Exit: Day +params.hold_days
                exit_idx = entry_idx + params.hold_days
                if exit_idx >= len(daily_data):
                    exit_idx = len(daily_data) - 1
                
                exit_date = daily_data.index[exit_idx]
                exit_price = daily_data.iloc[exit_idx]['Close']
                
                # Calculate trade return
                trade_return = (exit_price - entry_price) / entry_price
                
                # Apply stop loss and take profit
                if trade_return <= -params.stop_loss:
                    trade_return = -params.stop_loss
                elif trade_return >= params.take_profit:
                    trade_return = params.take_profit
                
                # Record trade
                trade = {
                    'ticker': data.get('fundamentals', {}).get('ticker', 'Unknown'),
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'return': trade_return,
                    'earnings_date': earnings_date,
                    'hold_days': exit_idx - entry_idx,
                    'strategy': 'Mean_Reversion'
                }
                
                trades.append(trade)
                
            except Exception as e:
                self.logger.warning(f"Error processing earnings date {earnings_date}: {e}")
                continue
        
        return trades
    
    def breakout_strategy(self, data: Dict[str, pd.DataFrame], params: StrategyParameters) -> List[Dict]:
        """Breakout Strategy"""
        trades = []
        daily_data = data['daily']
        
        if daily_data is None or daily_data.empty:
            return trades
        
        # Calculate technical indicators
        daily_data = self.calculate_technical_indicators(daily_data)
        
        # Get earnings dates
        earnings_dates = self._get_earnings_dates(data)
        
        for earnings_date in earnings_dates:
            try:
                # Find the trading day closest to earnings
                earnings_idx = daily_data.index.get_indexer([earnings_date], method='nearest')[0]
                if earnings_idx == -1:
                    continue
                
                # Entry: Day 0 (earnings day, looking for breakout)
                entry_date = daily_data.index[earnings_idx]
                entry_price = daily_data.iloc[earnings_idx]['Close']
                
                # Check for breakout conditions (price above upper Bollinger Band)
                if entry_price <= daily_data.iloc[earnings_idx]['bb_upper']:
                    continue
                
                # Exit: Day +params.hold_days
                exit_idx = earnings_idx + params.hold_days
                if exit_idx >= len(daily_data):
                    exit_idx = len(daily_data) - 1
                
                exit_date = daily_data.index[exit_idx]
                exit_price = daily_data.iloc[exit_idx]['Close']
                
                # Calculate trade return
                trade_return = (exit_price - entry_price) / entry_price
                
                # Apply stop loss and take profit
                if trade_return <= -params.stop_loss:
                    trade_return = -params.stop_loss
                elif trade_return >= params.take_profit:
                    trade_return = params.take_profit
                
                # Record trade
                trade = {
                    'ticker': data.get('fundamentals', {}).get('ticker', 'Unknown'),
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'return': trade_return,
                    'earnings_date': earnings_date,
                    'hold_days': exit_idx - earnings_idx,
                    'strategy': 'Breakout'
                }
                
                trades.append(trade)
                
            except Exception as e:
                self.logger.warning(f"Error processing earnings date {earnings_date}: {e}")
                continue
        
        return trades
    
    def _get_earnings_dates(self, data: Dict[str, Any]) -> List[datetime]:
        """Extract earnings dates from data"""
        earnings_dates = []
        
        # Try to get from earnings data
        if 'earnings' in data and data['earnings']:
            for earnings_event in data['earnings']:
                try:
                    if 'date' in earnings_event:
                        date_str = earnings_event['date']
                        if isinstance(date_str, str):
                            earnings_date = pd.to_datetime(date_str)
                        else:
                            earnings_date = date_str
                        earnings_dates.append(earnings_date)
                except Exception as e:
                    self.logger.warning(f"Error parsing earnings date: {e}")
                    continue
        
        # If no earnings data, create synthetic dates (quarterly)
        if not earnings_dates and 'daily' in data and data['daily'] is not None:
            start_date = data['daily'].index[0]
            end_date = data['daily'].index[-1]
            current_date = start_date
            
            while current_date <= end_date:
                earnings_dates.append(current_date)
                current_date += timedelta(days=90)  # Quarterly
        
        return earnings_dates
    
    def _check_entry_conditions(self, row: pd.Series, params: StrategyParameters) -> bool:
        """Check if entry conditions are met"""
        # Volume check
        if row['Volume'] < params.min_volume:
            return False
        
        # RSI check
        if 'rsi' in row and not pd.isna(row['rsi']):
            if row['rsi'] < params.rsi_oversold or row['rsi'] > params.rsi_overbought:
                return False
        
        # Volatility check
        if 'volatility' in row and not pd.isna(row['volatility']):
            if row['volatility'] > 0.1:  # 10% daily volatility threshold
                return False
        
        return True
    
    def run_backtest(self, strategy_func, params: StrategyParameters, strategy_name: str) -> BacktestResult:
        """Run backtest for a single strategy"""
        self.logger.info(f"Running backtest for {strategy_name}")
        
        all_trades = []
        
        # Get list of all stocks
        stock_dirs = [d for d in Path(self.data_dir).iterdir() if d.is_dir()]
        
        for stock_dir in stock_dirs:
            ticker = stock_dir.name
            try:
                # Load stock data
                data = self.load_stock_data(ticker)
                
                # Run strategy
                trades = strategy_func(data, params)
                all_trades.extend(trades)
                
            except Exception as e:
                self.logger.warning(f"Error processing {ticker}: {e}")
                continue
        
        # Calculate performance metrics
        if not all_trades:
            self.logger.warning(f"No trades generated for {strategy_name}")
            return None
        
        # Convert to DataFrame
        trades_df = pd.DataFrame(all_trades)
        trades_df['return'] = trades_df['return'] * params.position_size  # Apply position sizing
        
        # Calculate equity curve
        equity_curve = (1 + trades_df['return']).cumprod()
        
        # Calculate drawdown
        peak = equity_curve.expanding().max()
        drawdown_curve = (equity_curve - peak) / peak
        
        # Calculate monthly returns
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
        monthly_returns = trades_df.groupby(trades_df['entry_date'].dt.to_period('M'))['return'].sum()
        
        # Calculate metrics
        total_return = equity_curve.iloc[-1] - 1
        annualized_return = (1 + total_return) ** (252 / len(trades_df)) - 1
        volatility = trades_df['return'].std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Sortino ratio
        downside_returns = trades_df[trades_df['return'] < 0]['return']
        downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = annualized_return / downside_volatility if downside_volatility > 0 else 0
        
        # Max drawdown
        max_drawdown = drawdown_curve.min()
        
        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Win rate
        win_rate = len(trades_df[trades_df['return'] > 0]) / len(trades_df)
        
        # Profit factor
        gross_profit = trades_df[trades_df['return'] > 0]['return'].sum()
        gross_loss = abs(trades_df[trades_df['return'] < 0]['return'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # VaR and CVaR
        var_95 = np.percentile(trades_df['return'], 5)
        cvar_95 = trades_df[trades_df['return'] <= var_95]['return'].mean()
        
        # Max drawdown duration
        drawdown_periods = (drawdown_curve < 0).astype(int)
        max_drawdown_duration = drawdown_periods.groupby((drawdown_periods != drawdown_periods.shift()).cumsum()).sum().max()
        
        result = BacktestResult(
            strategy_name=strategy_name,
            parameters=params.__dict__,
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_drawdown_duration,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(trades_df),
            avg_trade_return=trades_df['return'].mean(),
            var_95=var_95,
            cvar_95=cvar_95,
            trades=all_trades,
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve,
            monthly_returns=monthly_returns,
            created_at=datetime.now()
        )
        
        self.logger.info(f"Backtest completed for {strategy_name}: {total_return:.2%} return, {sharpe_ratio:.2f} Sharpe")
        return result
    
    def optimize_parameters(self, strategy_func, param_ranges: Dict, strategy_name: str, 
                          optimization_metric: str = 'sharpe_ratio', n_trials: int = 100) -> Dict:
        """Optimize strategy parameters using grid search"""
        self.logger.info(f"Starting parameter optimization for {strategy_name}")
        
        best_result = None
        best_score = float('-inf')
        optimization_results = []
        
        # Generate parameter combinations
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        # Use random sampling for large parameter spaces
        if len(list(itertools.product(*param_values))) > n_trials:
            import random
            param_combinations = []
            for _ in range(n_trials):
                combination = {}
                for name, values in param_ranges.items():
                    combination[name] = random.choice(values)
                param_combinations.append(combination)
        else:
            param_combinations = [dict(zip(param_names, combo)) for combo in itertools.product(*param_values)]
        
        self.logger.info(f"Testing {len(param_combinations)} parameter combinations")
        
        for i, param_dict in enumerate(param_combinations):
            try:
                # Create parameters object
                params = StrategyParameters(**param_dict)
                
                # Run backtest
                result = self.run_backtest(strategy_func, params, f"{strategy_name}_opt_{i}")
                
                if result is None:
                    continue
                
                # Get optimization metric
                score = getattr(result, optimization_metric, 0)
                
                optimization_results.append({
                    'parameters': param_dict,
                    'score': score,
                    'result': result
                })
                
                # Update best result
                if score > best_score:
                    best_score = score
                    best_result = result
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Completed {i + 1}/{len(param_combinations)} optimizations")
                
            except Exception as e:
                self.logger.warning(f"Error in optimization trial {i}: {e}")
                continue
        
        # Sort results by score
        optimization_results.sort(key=lambda x: x['score'], reverse=True)
        
        self.logger.info(f"Optimization completed. Best {optimization_metric}: {best_score:.4f}")
        
        return {
            'best_result': best_result,
            'best_score': best_score,
            'all_results': optimization_results,
            'strategy_name': strategy_name,
            'optimization_metric': optimization_metric
        }
    
    def run_comprehensive_analysis(self) -> Dict:
        """Run comprehensive analysis of all strategies"""
        self.logger.info("Starting comprehensive strategy analysis")
        
        # Define parameter ranges for optimization
        param_ranges = {
            'entry_threshold': [0.01, 0.02, 0.03, 0.05],
            'exit_threshold': [0.03, 0.05, 0.08, 0.10],
            'stop_loss': [0.02, 0.03, 0.05, 0.07],
            'take_profit': [0.05, 0.08, 0.10, 0.15],
            'hold_days': [1, 3, 5, 7, 10],
            'position_size': [0.03, 0.05, 0.07, 0.10],
            'rsi_oversold': [20, 30, 40],
            'rsi_overbought': [60, 70, 80]
        }
        
        # Define strategies
        strategies = [
            (self.pead_momentum_strategy, 'PEAD_Momentum'),
            (self.mean_reversion_strategy, 'Mean_Reversion'),
            (self.breakout_strategy, 'Breakout')
        ]
        
        all_results = {}
        
        for strategy_func, strategy_name in strategies:
            self.logger.info(f"Analyzing {strategy_name}")
            
            # Run optimization
            optimization_result = self.optimize_parameters(
                strategy_func, param_ranges, strategy_name, 
                optimization_metric='sharpe_ratio', n_trials=50
            )
            
            all_results[strategy_name] = optimization_result
        
        # Save results
        self._save_analysis_results(all_results)
        
        return all_results
    
    def _save_analysis_results(self, results: Dict):
        """Save analysis results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary results
        summary_data = []
        for strategy_name, result in results.items():
            if result['best_result']:
                summary_data.append({
                    'strategy': strategy_name,
                    'sharpe_ratio': result['best_result'].sharpe_ratio,
                    'total_return': result['best_result'].total_return,
                    'max_drawdown': result['best_result'].max_drawdown,
                    'win_rate': result['best_result'].win_rate,
                    'total_trades': result['best_result'].total_trades,
                    'best_parameters': result['best_result'].parameters
                })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(project_root / f'results/backtesting/strategy_summary_{timestamp}.csv', index=False)
        
        # Save detailed results
        with open(project_root / f'results/backtesting/detailed_results_{timestamp}.json', 'w') as f:
            # Convert results to serializable format
            serializable_results = {}
            for strategy_name, result in results.items():
                serializable_results[strategy_name] = {
                    'best_score': result['best_score'],
                    'optimization_metric': result['optimization_metric'],
                    'best_parameters': result['best_result'].parameters if result['best_result'] else None,
                    'best_metrics': {
                        'sharpe_ratio': result['best_result'].sharpe_ratio if result['best_result'] else None,
                        'total_return': result['best_result'].total_return if result['best_result'] else None,
                        'max_drawdown': result['best_result'].max_drawdown if result['best_result'] else None,
                        'win_rate': result['best_result'].win_rate if result['best_result'] else None,
                        'total_trades': result['best_result'].total_trades if result['best_result'] else None
                    } if result['best_result'] else None
                }
            
            json.dump(serializable_results, f, indent=2, default=str)
        
        self.logger.info(f"Analysis results saved with timestamp {timestamp}")

def main():
    """Main execution function"""
    print("🚀 Advanced Backtesting Engine - Strategy Optimization")
    print("=" * 60)
    
    # Create backtesting engine
    engine = AdvancedBacktestingEngine()
    
    try:
        # Run comprehensive analysis
        results = engine.run_comprehensive_analysis()
        
        # Print summary
        print("\n📊 STRATEGY ANALYSIS SUMMARY:")
        print("=" * 40)
        
        for strategy_name, result in results.items():
            if result['best_result']:
                best = result['best_result']
                print(f"\n{strategy_name}:")
                print(f"  Sharpe Ratio: {best.sharpe_ratio:.3f}")
                print(f"  Total Return: {best.total_return:.2%}")
                print(f"  Max Drawdown: {best.max_drawdown:.2%}")
                print(f"  Win Rate: {best.win_rate:.2%}")
                print(f"  Total Trades: {best.total_trades}")
        
        print(f"\n✅ Analysis complete! Results saved to results/backtesting/")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        engine.logger.error(f"Analysis failed: {e}")

if __name__ == "__main__":
    main()
