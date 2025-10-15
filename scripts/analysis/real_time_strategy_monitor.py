"""
REAL-TIME STRATEGY MONITOR - Live Trading Signal Generation
=========================================================

This script provides real-time monitoring and signal generation for PEAD strategies:
1. Real-time data monitoring and signal detection
2. Live strategy execution and position management
3. Risk management and portfolio monitoring
4. Performance tracking and reporting
5. Alert system for trading opportunities

Features:
- Real-time data feeds from TWS API
- Live signal generation and validation
- Position sizing and risk management
- Portfolio heat maps and performance tracking
- Email/SMS alerts for trading opportunities
- Trade execution logging and reporting

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
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import warnings
from pathlib import Path
import yfinance as yf
from dataclasses import dataclass
import queue
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

warnings.filterwarnings('ignore')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# TWS API imports
try:
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    from ibapi.order import Order
    import ibapi.decoder
    import ibapi.connection
except ImportError:
    print("❌ IB API not installed. Installing...")
    os.system("pip install ibapi")
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    from ibapi.order import Order
    import ibapi.decoder
    import ibapi.connection

@dataclass
class TradingSignal:
    """Data structure for trading signals"""
    ticker: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    entry_price: float
    target_price: float
    stop_loss: float
    confidence: float
    strategy: str
    timestamp: datetime
    reasoning: str
    position_size: float

@dataclass
class Position:
    """Data structure for trading positions"""
    ticker: str
    entry_date: datetime
    entry_price: float
    quantity: int
    current_price: float
    unrealized_pnl: float
    stop_loss: float
    take_profit: float
    strategy: str
    status: str  # 'OPEN', 'CLOSED', 'STOPPED'

@dataclass
class Portfolio:
    """Data structure for portfolio management"""
    total_value: float
    cash: float
    positions: List[Position]
    daily_pnl: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    last_updated: datetime

class RealTimeDataFeed(EWrapper, EClient):
    """Real-time data feed from TWS"""
    
    def __init__(self):
        EClient.__init__(self, self)
        self.connected = False
        self.data_queue = queue.Queue()
        self.price_data = {}
        self.volume_data = {}
        
    def connect_to_tws(self, host="127.0.0.1", port=4002, client_id=1000):
        """Connect to TWS"""
        try:
            self.connect(host, port, clientId=client_id)
            self.connected = True
            return True
        except Exception as e:
            print(f"❌ Failed to connect to TWS: {e}")
            return False
    
    def disconnect_from_tws(self):
        """Disconnect from TWS"""
        if self.connected:
            self.disconnect()
            self.connected = False
    
    def error(self, reqId, errorCode, errorString):
        """Handle TWS errors"""
        if errorCode in [2104, 2106, 2158]:
            return
        print(f"TWS Error {errorCode}: {errorString}")
    
    def tickPrice(self, reqId, tickType, price, attrib):
        """Handle real-time price updates"""
        if tickType == 1:  # Bid price
            self.price_data[reqId] = {
                'bid': price,
                'timestamp': datetime.now()
            }
        elif tickType == 2:  # Ask price
            if reqId in self.price_data:
                self.price_data[reqId]['ask'] = price
            else:
                self.price_data[reqId] = {
                    'ask': price,
                    'timestamp': datetime.now()
                }
        elif tickType == 4:  # Last price
            if reqId in self.price_data:
                self.price_data[reqId]['last'] = price
            else:
                self.price_data[reqId] = {
                    'last': price,
                    'timestamp': datetime.now()
                }
    
    def tickSize(self, reqId, tickType, size):
        """Handle real-time volume updates"""
        if tickType == 8:  # Volume
            self.volume_data[reqId] = {
                'volume': size,
                'timestamp': datetime.now()
            }
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price for a ticker"""
        # This is simplified - in practice you'd map tickers to reqIds
        for req_id, data in self.price_data.items():
            if 'last' in data:
                return data['last']
        return None

class StrategyMonitor:
    """Real-time strategy monitoring and signal generation"""
    
    def __init__(self, portfolio_value: float = 100000):
        self.portfolio_value = portfolio_value
        self.logger = self._setup_logger()
        self.data_feed = RealTimeDataFeed()
        self.portfolio = Portfolio(
            total_value=portfolio_value,
            cash=portfolio_value,
            positions=[],
            daily_pnl=0.0,
            total_pnl=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            last_updated=datetime.now()
        )
        self.signals = []
        self.is_monitoring = False
        
        # Create results directory
        (project_root / 'results' / 'live_trading').mkdir(parents=True, exist_ok=True)
        
    def _setup_logger(self):
        """Setup logger"""
        logger = logging.getLogger('StrategyMonitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            (project_root / 'logs').mkdir(exist_ok=True)
            handler = logging.FileHandler(
                project_root / f'logs/strategy_monitor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def connect_to_data_feed(self):
        """Connect to real-time data feed"""
        if not self.data_feed.connect_to_tws():
            return False
        
        # Start API thread
        api_thread = threading.Thread(target=self.data_feed.run, daemon=True)
        api_thread.start()
        
        time.sleep(2)  # Wait for connection
        self.logger.info("Connected to real-time data feed")
        return True
    
    def load_earnings_calendar(self) -> pd.DataFrame:
        """Load earnings calendar"""
        try:
            earnings_df = pd.read_csv(project_root / 'data' / 'processed' / 'earnings_final.csv')
            earnings_df['date'] = pd.to_datetime(earnings_df['date'])
            return earnings_df
        except Exception as e:
            self.logger.error(f"Failed to load earnings calendar: {e}")
            return pd.DataFrame()
    
    def get_upcoming_earnings(self, days_ahead: int = 7) -> List[Dict]:
        """Get upcoming earnings in the next N days"""
        earnings_df = self.load_earnings_calendar()
        if earnings_df.empty:
            return []
        
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        upcoming = earnings_df[
            (earnings_df['date'].dt.date >= today) & 
            (earnings_df['date'].dt.date <= end_date)
        ]
        
        return upcoming.to_dict('records')
    
    def analyze_stock_for_signals(self, ticker: str) -> List[TradingSignal]:
        """Analyze stock for trading signals"""
        signals = []
        
        try:
            # Get current price
            current_price = self.data_feed.get_current_price(ticker)
            if current_price is None:
                # Fallback to yfinance
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    return signals
            
            # Get historical data for analysis
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            
            if hist.empty:
                return signals
            
            # Calculate technical indicators
            hist = self._calculate_technical_indicators(hist)
            
            # Check for PEAD momentum signals
            momentum_signal = self._check_pead_momentum_signal(ticker, hist, current_price)
            if momentum_signal:
                signals.append(momentum_signal)
            
            # Check for mean reversion signals
            reversion_signal = self._check_mean_reversion_signal(ticker, hist, current_price)
            if reversion_signal:
                signals.append(reversion_signal)
            
            # Check for breakout signals
            breakout_signal = self._check_breakout_signal(ticker, hist, current_price)
            if breakout_signal:
                signals.append(breakout_signal)
            
        except Exception as e:
            self.logger.warning(f"Error analyzing {ticker}: {e}")
        
        return signals
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        df = df.copy()
        
        # Moving averages
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        df['sma_50'] = df['Close'].rolling(window=50).mean()
        df['ema_12'] = df['Close'].ewm(span=12).mean()
        df['ema_26'] = df['Close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # Volume indicators
        df['volume_sma'] = df['Volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_sma']
        
        return df
    
    def _check_pead_momentum_signal(self, ticker: str, hist: pd.DataFrame, current_price: float) -> Optional[TradingSignal]:
        """Check for PEAD momentum signals"""
        try:
            latest = hist.iloc[-1]
            
            # Check if earnings are coming up
            upcoming_earnings = self.get_upcoming_earnings(3)  # Next 3 days
            ticker_earnings = [e for e in upcoming_earnings if e['ticker'] == ticker]
            
            if not ticker_earnings:
                return None
            
            # Check momentum conditions
            if (latest['Close'] > latest['sma_20'] and 
                latest['macd'] > latest['macd_signal'] and
                latest['rsi'] > 50 and
                latest['volume_ratio'] > 1.5):
                
                # Calculate targets
                stop_loss = current_price * 0.97  # 3% stop loss
                take_profit = current_price * 1.08  # 8% take profit
                
                confidence = min(0.9, (latest['rsi'] - 50) / 50 + 0.5)
                
                return TradingSignal(
                    ticker=ticker,
                    signal_type='BUY',
                    entry_price=current_price,
                    target_price=take_profit,
                    stop_loss=stop_loss,
                    confidence=confidence,
                    strategy='PEAD_Momentum',
                    timestamp=datetime.now(),
                    reasoning=f"Pre-earnings momentum: RSI={latest['rsi']:.1f}, MACD bullish, Volume={latest['volume_ratio']:.1f}x",
                    position_size=0.05  # 5% position size
                )
        
        except Exception as e:
            self.logger.warning(f"Error checking PEAD momentum for {ticker}: {e}")
        
        return None
    
    def _check_mean_reversion_signal(self, ticker: str, hist: pd.DataFrame, current_price: float) -> Optional[TradingSignal]:
        """Check for mean reversion signals"""
        try:
            latest = hist.iloc[-1]
            
            # Check oversold conditions
            if (latest['rsi'] < 30 and 
                latest['Close'] < latest['bb_lower'] and
                latest['volume_ratio'] > 1.2):
                
                # Calculate targets
                stop_loss = current_price * 0.95  # 5% stop loss
                take_profit = latest['bb_middle']  # Target middle Bollinger Band
                
                confidence = min(0.8, (30 - latest['rsi']) / 30 + 0.3)
                
                return TradingSignal(
                    ticker=ticker,
                    signal_type='BUY',
                    entry_price=current_price,
                    target_price=take_profit,
                    stop_loss=stop_loss,
                    confidence=confidence,
                    strategy='Mean_Reversion',
                    timestamp=datetime.now(),
                    reasoning=f"Oversold conditions: RSI={latest['rsi']:.1f}, Below BB lower, Volume={latest['volume_ratio']:.1f}x",
                    position_size=0.03  # 3% position size
                )
        
        except Exception as e:
            self.logger.warning(f"Error checking mean reversion for {ticker}: {e}")
        
        return None
    
    def _check_breakout_signal(self, ticker: str, hist: pd.DataFrame, current_price: float) -> Optional[TradingSignal]:
        """Check for breakout signals"""
        try:
            latest = hist.iloc[-1]
            
            # Check breakout conditions
            if (current_price > latest['bb_upper'] and
                latest['volume_ratio'] > 2.0 and
                latest['rsi'] > 60):
                
                # Calculate targets
                stop_loss = latest['bb_upper']  # Stop at breakout level
                take_profit = current_price * 1.12  # 12% take profit
                
                confidence = min(0.85, latest['volume_ratio'] / 3.0 + 0.4)
                
                return TradingSignal(
                    ticker=ticker,
                    signal_type='BUY',
                    entry_price=current_price,
                    target_price=take_profit,
                    stop_loss=stop_loss,
                    confidence=confidence,
                    strategy='Breakout',
                    timestamp=datetime.now(),
                    reasoning=f"Breakout: Above BB upper, Volume={latest['volume_ratio']:.1f}x, RSI={latest['rsi']:.1f}",
                    position_size=0.04  # 4% position size
                )
        
        except Exception as e:
            self.logger.warning(f"Error checking breakout for {ticker}: {e}")
        
        return None
    
    def monitor_stocks(self, tickers: List[str], monitoring_interval: int = 300):
        """Monitor stocks for trading signals"""
        self.logger.info(f"Starting monitoring for {len(tickers)} stocks")
        self.is_monitoring = True
        
        while self.is_monitoring:
            try:
                all_signals = []
                
                for ticker in tickers:
                    signals = self.analyze_stock_for_signals(ticker)
                    all_signals.extend(signals)
                    
                    # Small delay to avoid overwhelming the API
                    time.sleep(0.1)
                
                # Process signals
                if all_signals:
                    self._process_signals(all_signals)
                
                # Update portfolio
                self._update_portfolio()
                
                # Log status
                self.logger.info(f"Monitoring cycle complete. Found {len(all_signals)} signals")
                
                # Wait for next cycle
                time.sleep(monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring cycle: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _process_signals(self, signals: List[TradingSignal]):
        """Process trading signals"""
        for signal in signals:
            try:
                # Filter high-confidence signals
                if signal.confidence < 0.6:
                    continue
                
                # Check if we already have a position
                existing_position = self._get_existing_position(signal.ticker)
                if existing_position:
                    continue
                
                # Check portfolio limits
                if not self._check_portfolio_limits(signal):
                    continue
                
                # Execute signal (simulated)
                self._execute_signal(signal)
                
                # Send alert
                self._send_signal_alert(signal)
                
            except Exception as e:
                self.logger.error(f"Error processing signal for {signal.ticker}: {e}")
    
    def _get_existing_position(self, ticker: str) -> Optional[Position]:
        """Get existing position for ticker"""
        for position in self.portfolio.positions:
            if position.ticker == ticker and position.status == 'OPEN':
                return position
        return None
    
    def _check_portfolio_limits(self, signal: TradingSignal) -> bool:
        """Check portfolio limits before executing signal"""
        # Check maximum number of positions
        open_positions = len([p for p in self.portfolio.positions if p.status == 'OPEN'])
        if open_positions >= 20:  # Max 20 positions
            return False
        
        # Check position size limits
        position_value = self.portfolio.total_value * signal.position_size
        if position_value > self.portfolio.cash:
            return False
        
        return True
    
    def _execute_signal(self, signal: TradingSignal):
        """Execute trading signal (simulated)"""
        try:
            # Calculate position size
            position_value = self.portfolio.total_value * signal.position_size
            quantity = int(position_value / signal.entry_price)
            
            if quantity <= 0:
                return
            
            # Create position
            position = Position(
                ticker=signal.ticker,
                entry_date=datetime.now(),
                entry_price=signal.entry_price,
                quantity=quantity,
                current_price=signal.entry_price,
                unrealized_pnl=0.0,
                stop_loss=signal.stop_loss,
                take_profit=signal.target_price,
                strategy=signal.strategy,
                status='OPEN'
            )
            
            # Add to portfolio
            self.portfolio.positions.append(position)
            self.portfolio.cash -= position_value
            
            # Log execution
            self.logger.info(f"Executed {signal.signal_type} signal for {signal.ticker}: "
                           f"{quantity} shares at ${signal.entry_price:.2f}")
            
            # Save signal
            self.signals.append(signal)
            
        except Exception as e:
            self.logger.error(f"Error executing signal for {signal.ticker}: {e}")
    
    def _update_portfolio(self):
        """Update portfolio with current prices"""
        try:
            total_value = self.portfolio.cash
            
            for position in self.portfolio.positions:
                if position.status == 'OPEN':
                    # Get current price
                    current_price = self.data_feed.get_current_price(position.ticker)
                    if current_price:
                        position.current_price = current_price
                        position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
                        
                        # Check stop loss and take profit
                        if current_price <= position.stop_loss:
                            self._close_position(position, 'STOPPED')
                        elif current_price >= position.take_profit:
                            self._close_position(position, 'TAKE_PROFIT')
                    
                    total_value += position.current_price * position.quantity
            
            self.portfolio.total_value = total_value
            self.portfolio.last_updated = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio: {e}")
    
    def _close_position(self, position: Position, reason: str):
        """Close a position"""
        try:
            position.status = 'CLOSED'
            realized_pnl = (position.current_price - position.entry_price) * position.quantity
            
            # Update cash
            self.portfolio.cash += position.current_price * position.quantity
            
            # Log closure
            self.logger.info(f"Closed position for {position.ticker}: "
                           f"P&L=${realized_pnl:.2f}, Reason={reason}")
            
        except Exception as e:
            self.logger.error(f"Error closing position for {position.ticker}: {e}")
    
    def _send_signal_alert(self, signal: TradingSignal):
        """Send signal alert (email/SMS)"""
        try:
            # This is a placeholder - implement actual email/SMS sending
            alert_message = f"""
Trading Signal Alert:
Ticker: {signal.ticker}
Signal: {signal.signal_type}
Entry Price: ${signal.entry_price:.2f}
Target Price: ${signal.target_price:.2f}
Stop Loss: ${signal.stop_loss:.2f}
Confidence: {signal.confidence:.1%}
Strategy: {signal.strategy}
Reasoning: {signal.reasoning}
Time: {signal.timestamp}
            """
            
            self.logger.info(f"Signal Alert: {signal.ticker} {signal.signal_type}")
            # In practice, you would send this via email or SMS
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
    
    def generate_performance_report(self) -> Dict:
        """Generate performance report"""
        try:
            # Calculate metrics
            total_trades = len([p for p in self.portfolio.positions if p.status == 'CLOSED'])
            winning_trades = len([p for p in self.portfolio.positions 
                                if p.status == 'CLOSED' and p.unrealized_pnl > 0])
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            total_pnl = sum([p.unrealized_pnl for p in self.portfolio.positions if p.status == 'CLOSED'])
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'portfolio_value': self.portfolio.total_value,
                'cash': self.portfolio.cash,
                'total_pnl': total_pnl,
                'total_trades': total_trades,
                'win_rate': win_rate,
                'open_positions': len([p for p in self.portfolio.positions if p.status == 'OPEN']),
                'signals_generated': len(self.signals),
                'last_updated': self.portfolio.last_updated.isoformat()
            }
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(project_root / f'results/live_trading/performance_report_{timestamp}.json', 'w') as f:
                json.dump(report, f, indent=2)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {}
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        self.data_feed.disconnect_from_tws()
        self.logger.info("Monitoring stopped")

def main():
    """Main execution function"""
    print("🚀 Real-Time Strategy Monitor")
    print("=" * 40)
    
    # Create monitor
    monitor = StrategyMonitor(portfolio_value=100000)
    
    try:
        # Connect to data feed
        if not monitor.connect_to_data_feed():
            print("❌ Failed to connect to data feed")
            return
        
        # Load stock list
        earnings_df = monitor.load_earnings_calendar()
        if earnings_df.empty:
            print("❌ No earnings calendar found")
            return
        
        tickers = earnings_df['ticker'].unique().tolist()
        print(f"📊 Monitoring {len(tickers)} stocks")
        
        # Start monitoring
        print("🔄 Starting real-time monitoring...")
        monitor.monitor_stocks(tickers, monitoring_interval=300)  # 5 minutes
        
    except KeyboardInterrupt:
        print("\n⚠️ Monitoring interrupted by user")
        monitor.stop_monitoring()
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        monitor.logger.error(f"Monitoring failed: {e}")
    finally:
        # Generate final report
        report = monitor.generate_performance_report()
        print(f"📊 Final Performance Report: {report}")

if __name__ == "__main__":
    main()
