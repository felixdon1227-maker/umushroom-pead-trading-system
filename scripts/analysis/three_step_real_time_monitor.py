"""
3-Step Strategy Real-Time Monitor
================================

Real-time monitoring and execution system for the 3-Step Earnings Strategy:
- Live earnings calendar monitoring
- Real-time opportunity detection
- Position tracking and management
- Performance monitoring
- Risk management alerts

Author: UMushroom Investment Strategy
Date: October 2025
"""

import pandas as pd
import numpy as np
import os
import json
import time
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class ThreeStepRealTimeMonitor:
    """
    Real-time monitoring and execution system for 3-Step Strategy
    """
    
    def __init__(self, config_file: str = None):
        self.config = self.load_config(config_file)
        self.active_positions = {}
        self.pending_opportunities = {}
        self.performance_history = []
        
        # Initialize data sources
        self.earnings_calendar = None
        self.market_data = {}
        
        print("🚀 3-Step Strategy Real-Time Monitor Initialized")
        print(f"📊 Configuration: {self.config}")
    
    def load_config(self, config_file: str = None) -> Dict:
        """Load configuration from file or use defaults"""
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            'strategy': {
                'step1': {
                    'min_beat_rate': 0.7,
                    'min_volume_consistency': 0.5,
                    'position_size': 3000,
                    'hold_days': 10
                },
                'step2': {
                    'min_day0_reaction': 1.0,
                    'min_volume_spike': 2.0,
                    'position_size': 4000,
                    'hold_days': 10
                },
                'step3': {
                    'min_combined_reaction': 2.0,
                    'position_size': 5000,
                    'hold_days': 10
                }
            },
            'risk': {
                'max_positions': 12,
                'max_per_sector': 3,
                'stop_loss': -8.0,
                'take_profit': 15.0,
                'max_portfolio_risk': 0.05
            },
            'monitoring': {
                'update_interval': 300,  # 5 minutes
                'earnings_lookahead_days': 7,
                'data_sources': ['yfinance', 'earnings_calendar']
            },
            'portfolio': {
                'initial_capital': 100000,
                'cash_reserve': 10000
            }
        }
    
    def load_earnings_calendar(self, file_path: str) -> pd.DataFrame:
        """Load earnings calendar from file"""
        try:
            df = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(df['date'])
            self.earnings_calendar = df
            print(f"✅ Loaded earnings calendar: {len(df)} events")
            return df
        except Exception as e:
            print(f"❌ Error loading earnings calendar: {e}")
            return pd.DataFrame()
    
    def get_upcoming_earnings(self, days_ahead: int = 7) -> pd.DataFrame:
        """Get upcoming earnings events"""
        if self.earnings_calendar is None:
            return pd.DataFrame()
        
        today = datetime.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        upcoming = self.earnings_calendar[
            (self.earnings_calendar['date'].dt.date >= today) &
            (self.earnings_calendar['date'].dt.date <= future_date)
        ].copy()
        
        return upcoming.sort_values('date')
    
    def get_stock_data(self, ticker: str, period: str = '1mo') -> Optional[pd.DataFrame]:
        """Get real-time stock data"""
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period)
            if len(data) > 0:
                self.market_data[ticker] = data
                return data
        except Exception as e:
            print(f"❌ Error getting data for {ticker}: {e}")
        return None
    
    def calculate_volume_metrics(self, ticker: str) -> Dict:
        """Calculate volume metrics for a stock"""
        if ticker not in self.market_data:
            data = self.get_stock_data(ticker)
            if data is None:
                return {'volume_spike': 1.0, 'avg_volume': 0}
        
        data = self.market_data[ticker]
        
        if len(data) < 20:
            return {'volume_spike': 1.0, 'avg_volume': 0}
        
        # Calculate 20-day average volume
        avg_volume = data['Volume'].tail(20).mean()
        current_volume = data['Volume'].iloc[-1]
        
        volume_spike = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        return {
            'volume_spike': volume_spike,
            'avg_volume': avg_volume,
            'current_volume': current_volume
        }
    
    def calculate_historical_beat_rate(self, ticker: str) -> float:
        """Calculate historical beat rate (simplified)"""
        # In a real implementation, this would use historical earnings data
        # For now, return a default value
        return 0.6
    
    def scan_step1_opportunities(self) -> List[Dict]:
        """Scan for Step 1 (pre-earnings) opportunities"""
        opportunities = []
        upcoming = self.get_upcoming_earnings()
        
        for _, row in upcoming.iterrows():
            ticker = row['ticker']
            
            # Get stock data
            data = self.get_stock_data(ticker)
            if data is None:
                continue
            
            # Calculate metrics
            volume_metrics = self.calculate_volume_metrics(ticker)
            beat_rate = self.calculate_historical_beat_rate(ticker)
            
            # Check Step 1 criteria
            if (beat_rate >= self.config['strategy']['step1']['min_beat_rate'] and
                volume_metrics['volume_spike'] >= 1.5):
                
                opportunities.append({
                    'ticker': ticker,
                    'step': 1,
                    'entry_date': row['date'],
                    'earnings_date': row['date'],
                    'position_size': self.config['strategy']['step1']['position_size'],
                    'beat_rate': beat_rate,
                    'volume_spike': volume_metrics['volume_spike'],
                    'reason': f'Pre-earnings: Beat rate {beat_rate:.2f}, Volume {volume_metrics["volume_spike"]:.1f}x'
                })
        
        return opportunities
    
    def scan_step2_opportunities(self) -> List[Dict]:
        """Scan for Step 2 (Day 0 momentum) opportunities"""
        opportunities = []
        
        # Get earnings from today
        today = datetime.now().date()
        today_earnings = self.earnings_calendar[
            self.earnings_calendar['date'].dt.date == today
        ]
        
        for _, row in today_earnings.iterrows():
            ticker = row['ticker']
            
            # Get stock data
            data = self.get_stock_data(ticker)
            if data is None or len(data) < 2:
                continue
            
            # Calculate Day 0 reaction
            current_price = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2]
            day0_reaction = ((current_price - prev_close) / prev_close) * 100
            
            # Calculate volume metrics
            volume_metrics = self.calculate_volume_metrics(ticker)
            
            # Check Step 2 criteria
            if (day0_reaction >= self.config['strategy']['step2']['min_day0_reaction'] and
                volume_metrics['volume_spike'] >= self.config['strategy']['step2']['min_volume_spike']):
                
                opportunities.append({
                    'ticker': ticker,
                    'step': 2,
                    'entry_date': today,
                    'earnings_date': today,
                    'position_size': self.config['strategy']['step2']['position_size'],
                    'day0_reaction': day0_reaction,
                    'volume_spike': volume_metrics['volume_spike'],
                    'reason': f'Day 0 momentum: {day0_reaction:.2f}%, Volume {volume_metrics["volume_spike"]:.1f}x'
                })
        
        return opportunities
    
    def scan_step3_opportunities(self) -> List[Dict]:
        """Scan for Step 3 (Day 1 continuation) opportunities"""
        opportunities = []
        
        # Get earnings from yesterday
        yesterday = datetime.now().date() - timedelta(days=1)
        yesterday_earnings = self.earnings_calendar[
            self.earnings_calendar['date'].dt.date == yesterday
        ]
        
        for _, row in yesterday_earnings.iterrows():
            ticker = row['ticker']
            
            # Get stock data
            data = self.get_stock_data(ticker)
            if data is None or len(data) < 3:
                continue
            
            # Calculate Day 0 and Day 1 reactions
            current_price = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2]
            day_before = data['Close'].iloc[-3]
            
            day0_reaction = ((prev_close - day_before) / day_before) * 100
            day1_reaction = ((current_price - prev_close) / prev_close) * 100
            combined_reaction = day0_reaction + day1_reaction
            
            # Check Step 3 criteria
            if (day0_reaction > 0 and 
                day1_reaction > 0 and
                combined_reaction >= self.config['strategy']['step3']['min_combined_reaction']):
                
                opportunities.append({
                    'ticker': ticker,
                    'step': 3,
                    'entry_date': datetime.now().date(),
                    'earnings_date': yesterday,
                    'position_size': self.config['strategy']['step3']['position_size'],
                    'day0_reaction': day0_reaction,
                    'day1_reaction': day1_reaction,
                    'combined_reaction': combined_reaction,
                    'reason': f'Day 1 continuation: Combined {combined_reaction:.2f}%'
                })
        
        return opportunities
    
    def scan_all_opportunities(self) -> List[Dict]:
        """Scan for all strategy opportunities"""
        all_opportunities = []
        
        # Scan each step
        step1_opps = self.scan_step1_opportunities()
        step2_opps = self.scan_step2_opportunities()
        step3_opps = self.scan_step3_opportunities()
        
        all_opportunities.extend(step1_opps)
        all_opportunities.extend(step2_opps)
        all_opportunities.extend(step3_opps)
        
        # Remove duplicates (same ticker in multiple steps)
        seen_tickers = set()
        unique_opportunities = []
        
        for opp in all_opportunities:
            if opp['ticker'] not in seen_tickers:
                unique_opportunities.append(opp)
                seen_tickers.add(opp['ticker'])
        
        return unique_opportunities
    
    def check_risk_limits(self, new_opportunity: Dict) -> bool:
        """Check if new opportunity meets risk limits"""
        # Check position limit
        if len(self.active_positions) >= self.config['risk']['max_positions']:
            return False
        
        # Check sector limit (simplified)
        sector_count = {}
        for pos in self.active_positions.values():
            sector = pos.get('sector', 'Unknown')
            sector_count[sector] = sector_count.get(sector, 0) + 1
        
        new_sector = new_opportunity.get('sector', 'Unknown')
        if sector_count.get(new_sector, 0) >= self.config['risk']['max_per_sector']:
            return False
        
        return True
    
    def add_position(self, opportunity: Dict) -> bool:
        """Add a new position"""
        if not self.check_risk_limits(opportunity):
            return False
        
        position_id = f"{opportunity['ticker']}_{opportunity['step']}_{opportunity['entry_date']}"
        
        position = {
            'id': position_id,
            'ticker': opportunity['ticker'],
            'step': opportunity['step'],
            'entry_date': opportunity['entry_date'],
            'earnings_date': opportunity['entry_date'],
            'position_size': opportunity['position_size'],
            'entry_price': self.get_current_price(opportunity['ticker']),
            'stop_loss': self.config['risk']['stop_loss'],
            'take_profit': self.config['risk']['take_profit'],
            'status': 'active',
            'reason': opportunity['reason']
        }
        
        self.active_positions[position_id] = position
        print(f"✅ Added position: {position_id}")
        return True
    
    def get_current_price(self, ticker: str) -> float:
        """Get current price for a ticker"""
        if ticker in self.market_data:
            return self.market_data[ticker]['Close'].iloc[-1]
        
        data = self.get_stock_data(ticker)
        if data is not None:
            return data['Close'].iloc[-1]
        
        return 0.0
    
    def update_positions(self):
        """Update all active positions"""
        positions_to_close = []
        
        for position_id, position in self.active_positions.items():
            if position['status'] != 'active':
                continue
            
            ticker = position['ticker']
            current_price = self.get_current_price(ticker)
            
            if current_price == 0:
                continue
            
            # Calculate return
            entry_price = position['entry_price']
            return_pct = ((current_price - entry_price) / entry_price) * 100
            
            # Check stop loss
            if return_pct <= position['stop_loss']:
                position['status'] = 'stopped_out'
                position['exit_price'] = current_price
                position['return_pct'] = return_pct
                position['exit_date'] = datetime.now().date()
                positions_to_close.append(position_id)
                print(f"🛑 Stop loss triggered: {position_id} ({return_pct:.2f}%)")
            
            # Check take profit
            elif return_pct >= position['take_profit']:
                position['status'] = 'take_profit'
                position['exit_price'] = current_price
                position['return_pct'] = return_pct
                position['exit_date'] = datetime.now().date()
                positions_to_close.append(position_id)
                print(f"🎯 Take profit hit: {position_id} ({return_pct:.2f}%)")
            
            # Check hold period
            elif (datetime.now().date() - position['entry_date']).days >= position.get('hold_days', 10):
                position['status'] = 'time_exit'
                position['exit_price'] = current_price
                position['return_pct'] = return_pct
                position['exit_date'] = datetime.now().date()
                positions_to_close.append(position_id)
                print(f"⏰ Time exit: {position_id} ({return_pct:.2f}%)")
            
            # Update current return
            position['current_return'] = return_pct
        
        # Remove closed positions
        for position_id in positions_to_close:
            self.active_positions.pop(position_id, None)
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        total_positions = len(self.active_positions)
        total_invested = sum(pos['position_size'] for pos in self.active_positions.values())
        
        # Calculate current P&L
        total_pnl = 0
        for position in self.active_positions.values():
            if 'current_return' in position:
                pnl = position['position_size'] * (position['current_return'] / 100)
                total_pnl += pnl
        
        return {
            'total_positions': total_positions,
            'total_invested': total_invested,
            'total_pnl': total_pnl,
            'available_capital': self.config['portfolio']['initial_capital'] - total_invested,
            'positions': list(self.active_positions.keys())
        }
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        print(f"\n🔄 Monitoring Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Update existing positions
        self.update_positions()
        
        # Scan for new opportunities
        opportunities = self.scan_all_opportunities()
        
        print(f"📊 Found {len(opportunities)} opportunities:")
        for opp in opportunities:
            print(f"  - {opp['ticker']} (Step {opp['step']}): {opp['reason']}")
        
        # Add new positions
        for opportunity in opportunities:
            if self.add_position(opportunity):
                print(f"✅ Added: {opportunity['ticker']} (Step {opportunity['step']})")
        
        # Portfolio summary
        portfolio = self.get_portfolio_summary()
        print(f"\n📈 Portfolio Summary:")
        print(f"  Positions: {portfolio['total_positions']}")
        print(f"  Invested: ${portfolio['total_invested']:,.0f}")
        print(f"  P&L: ${portfolio['total_pnl']:,.0f}")
        print(f"  Available: ${portfolio['available_capital']:,.0f}")
    
    def run_continuous_monitoring(self, duration_hours: int = 24):
        """Run continuous monitoring for specified duration"""
        print(f"🚀 Starting continuous monitoring for {duration_hours} hours...")
        
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        
        while time.time() < end_time:
            try:
                self.run_monitoring_cycle()
                
                # Wait for next cycle
                time.sleep(self.config['monitoring']['update_interval'])
                
            except KeyboardInterrupt:
                print("\n⏹️ Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in monitoring cycle: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
        
        print("✅ Monitoring session complete")


def main():
    """Main execution function"""
    print("🚀 3-Step Strategy Real-Time Monitor")
    print("=" * 50)
    
    # Initialize monitor
    monitor = ThreeStepRealTimeMonitor()
    
    # Load earnings calendar
    earnings_file = '/home/fellaki10/Documents/UMushroom Investment challange/data/processed/earnings_final.csv'
    monitor.load_earnings_calendar(earnings_file)
    
    # Run one monitoring cycle
    monitor.run_monitoring_cycle()
    
    # Optionally run continuous monitoring
    # monitor.run_continuous_monitoring(duration_hours=24)


if __name__ == "__main__":
    main()
