"""
Master data enrichment script for PEAD analysis
Fetches all fundamental, liquidity, and market condition data for 104 stocks
Based on specifications in docs/plans/data_collection_plan.md
"""

import pandas as pd
import yfinance as yf
import numpy as np
import os
import time
import logging
from datetime import datetime, timedelta
from tqdm import tqdm
import talib
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class DataEnrichmentPipeline:
    def __init__(self):
        """Initialize the data enrichment pipeline"""
        self.stocks_df = pd.read_csv('data/processed/earnings_final.csv')
        self.tickers = self.stocks_df['ticker'].unique()
        self.total_stocks = len(self.tickers)
        
        # Create output directories
        self.create_directories()
        
        # Setup logging
        self.setup_logging()
        
        # Sector mapping
        self.sector_etfs = {
            'Financials': 'XLF',
            'Technology': 'XLK', 
            'Healthcare': 'XLV',
            'Energy': 'XLE',
            'Industrials': 'XLI',
            'Materials': 'XLB',
            'Consumer': 'XLY',
            'Utilities': 'XLU',
            'Other': 'SPY'
        }
        
        print(f"Initialized pipeline for {self.total_stocks} stocks")
        
    def create_directories(self):
        """Create all necessary output directories"""
        dirs = [
            'fundamental_data',
            'fundamental_data/historical_fundamentals',
            'liquidity_data',
            'market_conditions',
            'earnings_quality',
            'risk_indicators',
            'logs'
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
    
    def setup_logging(self):
        """Setup logging for error tracking"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/enrichment_errors.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_full_pipeline(self):
        """Execute all data collection steps"""
        print("="*80)
        print("COMPREHENSIVE DATA ENRICHMENT PIPELINE")
        print("="*80)
        print(f"Stocks to process: {self.total_stocks}")
        print(f"Start time: {datetime.now()}")
        print("="*80)
        
        start_time = time.time()
        
        try:
            # Step 1: Current Fundamentals
            print("\n[1/10] Fetching current fundamentals...")
            self.fetch_current_fundamentals()
            
            # Step 2: Historical Fundamentals
            print("\n[2/10] Fetching historical fundamentals...")
            self.fetch_historical_fundamentals()
            
            # Step 3: Volume Metrics
            print("\n[3/10] Calculating volume metrics...")
            self.calculate_volume_metrics()
            
            # Step 4: Bid-Ask Spreads (placeholder - would need TWS)
            print("\n[4/10] Fetching bid-ask spreads...")
            self.fetch_bid_ask_spreads()
            
            # Step 5: VIX Historical
            print("\n[5/10] Fetching VIX historical data...")
            self.fetch_vix_data()
            
            # Step 6: Sector ETF Performance
            print("\n[6/10] Fetching sector ETF performance...")
            self.fetch_sector_etf_data()
            
            # Step 7: Stock Market Conditions
            print("\n[7/10] Calculating stock market conditions...")
            self.calculate_stock_conditions()
            
            # Step 8: Earnings Quality
            print("\n[8/10] Analyzing earnings quality...")
            self.analyze_earnings_quality()
            
            # Step 9: Risk Indicators
            print("\n[9/10] Collecting risk indicators...")
            self.collect_risk_indicators()
            
            # Step 10: Generate Report
            print("\n[10/10] Generating summary report...")
            self.generate_summary_report()
            
            end_time = time.time()
            duration = end_time - start_time
            
            print("\n" + "="*80)
            print("✅ DATA ENRICHMENT COMPLETE")
            print(f"Total runtime: {duration/3600:.2f} hours")
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            raise
    
    def fetch_current_fundamentals(self):
        """Step 1: Fetch current fundamental data for all stocks"""
        results = []
        errors = 0
        
        for i, ticker in enumerate(tqdm(self.tickers, desc="Current Fundamentals")):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Extract fundamental data with error handling
                result = {
                    'ticker': ticker,
                    'pe_ratio': self.safe_get(info, 'trailingPE'),
                    'forward_pe': self.safe_get(info, 'forwardPE'),
                    'peg_ratio': self.safe_get(info, 'pegRatio'),
                    'price_to_book': self.safe_get(info, 'priceToBook'),
                    'debt_to_equity': self.safe_get(info, 'debtToEquity'),
                    'current_ratio': self.safe_get(info, 'currentRatio'),
                    'profit_margin': self.safe_get(info, 'profitMargins'),
                    'operating_margin': self.safe_get(info, 'operatingMargins'),
                    'return_on_equity': self.safe_get(info, 'returnOnEquity'),
                    'return_on_assets': self.safe_get(info, 'returnOnAssets'),
                    'revenue_growth': self.safe_get(info, 'revenueGrowth'),
                    'earnings_growth': self.safe_get(info, 'earningsGrowth'),
                    'beta': self.safe_get(info, 'beta'),
                    'shares_outstanding': self.safe_get(info, 'sharesOutstanding'),
                    'float_shares': self.safe_get(info, 'floatShares'),
                    'institutional_ownership': self.safe_get(info, 'heldPercentInstitutions'),
                    'insider_ownership': self.safe_get(info, 'heldPercentInsiders'),
                    'short_ratio': self.safe_get(info, 'shortRatio'),
                    'short_percent_float': self.safe_get(info, 'shortPercentOfFloat'),
                    'analyst_count': self.safe_get(info, 'numberOfAnalystOpinions'),
                    'target_price': self.safe_get(info, 'targetMeanPrice'),
                    'recommendation': self.safe_get(info, 'recommendationKey'),
                    'fifty_two_week_high': self.safe_get(info, 'fiftyTwoWeekHigh'),
                    'fifty_two_week_low': self.safe_get(info, 'fiftyTwoWeekLow'),
                    'avg_volume_10day': self.safe_get(info, 'averageVolume10days'),
                    'avg_volume_3month': self.safe_get(info, 'averageVolume'),
                    'market_cap': self.safe_get(info, 'marketCap'),
                    'enterprise_value': self.safe_get(info, 'enterpriseValue'),
                    'last_updated': datetime.now()
                }
                
                results.append(result)
                
                # Rate limiting
                time.sleep(0.5)
                
                # Progress update every 10 stocks
                if (i + 1) % 10 == 0:
                    progress = (i + 1) / self.total_stocks * 100
                    print(f"Progress: {i+1}/{self.total_stocks} stocks ({progress:.1f}%)")
                
            except Exception as e:
                errors += 1
                self.logger.error(f"Error fetching {ticker}: {str(e)}")
                continue
        
        # Save results
        df = pd.DataFrame(results)
        df.to_csv('fundamental_data/current_fundamentals.csv', index=False)
        print(f"  ✓ Saved {len(df)} stocks (Errors: {errors})")
    
    def fetch_historical_fundamentals(self):
        """Step 2: Fetch historical fundamentals for each earnings event"""
        errors = 0
        
        for i, ticker in enumerate(tqdm(self.tickers, desc="Historical Fundamentals")):
            try:
                stock = yf.Ticker(ticker)
                
                # Get quarterly financials
                quarterly_financials = stock.quarterly_financials
                quarterly_balance = stock.quarterly_balance_sheet
                quarterly_cashflow = stock.quarterly_cashflow
                
                # Get earnings dates for this ticker
                ticker_earnings = self.stocks_df[self.stocks_df['ticker'] == ticker]
                
                results = []
                for _, row in ticker_earnings.iterrows():
                    earnings_date = pd.to_datetime(row['date'])
                    
                    # Find closest quarterly data
                    if quarterly_financials is not None and not quarterly_financials.empty:
                        # Get the most recent quarter before or on earnings date
                        available_dates = pd.to_datetime(quarterly_financials.columns)
                        valid_dates = available_dates[available_dates <= earnings_date]
                        
                        if len(valid_dates) > 0:
                            closest_date = valid_dates.max()
                            
                            result = {
                                'ticker': ticker,
                                'earnings_date': earnings_date,
                                'quarter_end_date': closest_date,
                                'revenue': self.safe_get(quarterly_financials[closest_date], 'Total Revenue'),
                                'gross_profit': self.safe_get(quarterly_financials[closest_date], 'Gross Profit'),
                                'operating_income': self.safe_get(quarterly_financials[closest_date], 'Operating Income'),
                                'net_income': self.safe_get(quarterly_financials[closest_date], 'Net Income'),
                                'eps_actual': row['eps_estimate'],  # From earnings data
                                'eps_estimate': row['eps_estimate'],  # Same as actual for now
                                'total_assets': self.safe_get(quarterly_balance[closest_date], 'Total Assets'),
                                'total_liabilities': self.safe_get(quarterly_balance[closest_date], 'Total Liabilities'),
                                'total_debt': self.safe_get(quarterly_balance[closest_date], 'Total Debt'),
                                'cash_and_equivalents': self.safe_get(quarterly_balance[closest_date], 'Cash And Cash Equivalents'),
                                'operating_cash_flow': self.safe_get(quarterly_cashflow[closest_date], 'Operating Cash Flow'),
                                'free_cash_flow': self.safe_get(quarterly_cashflow[closest_date], 'Free Cash Flow'),
                                'pe_ratio_at_earnings': None,  # Will calculate from price data
                                'price_at_earnings': None,  # Will get from price data
                            }
                            
                            results.append(result)
                
                # Save individual file
                if results:
                    df = pd.DataFrame(results)
                    df.to_csv(f'fundamental_data/historical_fundamentals/{ticker}_fundamentals.csv', index=False)
                
                time.sleep(0.5)
                
            except Exception as e:
                errors += 1
                self.logger.error(f"Error fetching historical data for {ticker}: {str(e)}")
                continue
        
        print(f"  ✓ Processed historical fundamentals (Errors: {errors})")
    
    def calculate_volume_metrics(self):
        """Step 3: Calculate volume metrics for each earnings event"""
        results = []
        errors = 0
        
        for i, ticker in enumerate(tqdm(self.tickers, desc="Volume Metrics")):
            try:
                # Get historical price data
                stock = yf.Ticker(ticker)
                hist = stock.history(period="10y")
                
                if hist.empty:
                    continue
                
                # Get earnings dates for this ticker
                ticker_earnings = self.stocks_df[self.stocks_df['ticker'] == ticker]
                
                for _, row in ticker_earnings.iterrows():
                    earnings_date = pd.to_datetime(row['date'])
                    
                    # Look back 90 days from earnings date
                    start_date = earnings_date - timedelta(days=90)
                    end_date = earnings_date
                    
                    # Filter data for the 90-day period
                    # Convert timezone-aware datetime to timezone-naive for comparison
                    hist_index = hist.index.tz_localize(None) if hist.index.tz else hist.index
                    period_data = hist[(hist_index >= start_date) & (hist_index <= end_date)]
                    
                    if len(period_data) < 30:  # Need at least 30 days of data
                        continue
                    
                    volumes = period_data['Volume'].dropna()
                    prices = period_data['Close'].dropna()
                    
                    if len(volumes) == 0:
                        continue
                    
                    # Calculate metrics
                    avg_volume = volumes.mean()
                    avg_price = prices.mean()
                    avg_dollar_volume = avg_volume * avg_price
                    volume_std = volumes.std()
                    volume_consistency = 1 - (volume_std / avg_volume) if avg_volume > 0 else 0
                    
                    # Volume trend (linear regression slope)
                    if len(volumes) > 1:
                        x = np.arange(len(volumes))
                        slope, _, _, _, _ = stats.linregress(x, volumes)
                        volume_trend = slope
                    else:
                        volume_trend = 0
                    
                    result = {
                        'ticker': ticker,
                        'earnings_date': earnings_date,
                        'avg_volume_90d': avg_volume,
                        'avg_dollar_volume_90d': avg_dollar_volume,
                        'volume_std_90d': volume_std,
                        'volume_consistency': volume_consistency,
                        'min_volume_90d': volumes.min(),
                        'max_volume_90d': volumes.max(),
                        'volume_trend': volume_trend,
                    }
                    
                    results.append(result)
                
                time.sleep(0.5)
                
            except Exception as e:
                errors += 1
                self.logger.error(f"Error calculating volume metrics for {ticker}: {str(e)}")
                continue
        
        # Save results
        df = pd.DataFrame(results)
        df.to_csv('liquidity_data/volume_metrics.csv', index=False)
        print(f"  ✓ Saved {len(df)} volume records (Errors: {errors})")
    
    def fetch_bid_ask_spreads(self):
        """Step 4: Fetch bid-ask spreads (placeholder - would need TWS API)"""
        # This would require TWS API connection
        # For now, create placeholder data
        results = []
        
        for ticker in self.tickers:
            result = {
                'ticker': ticker,
                'bid': None,
                'ask': None,
                'bid_ask_spread': None,
                'spread_percent': None,
                'bid_size': None,
                'ask_size': None,
                'last_price': None,
                'timestamp': datetime.now(),
                'note': 'TWS API not available - placeholder data'
            }
            results.append(result)
        
        df = pd.DataFrame(results)
        df.to_csv('liquidity_data/current_bid_ask.csv', index=False)
        print(f"  ✓ Created placeholder bid-ask data for {len(df)} stocks")
    
    def fetch_vix_data(self):
        """Step 5: Fetch VIX historical data"""
        try:
            print("  Fetching VIX data...")
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(start="2015-01-01", end="2025-12-31")
            
            if not vix_data.empty:
                vix_df = vix_data.reset_index()
                vix_df['vix_change'] = vix_df['Close'].pct_change() * 100
                
                vix_df = vix_df.rename(columns={
                    'Date': 'date',
                    'Close': 'vix_close',
                    'High': 'vix_high',
                    'Low': 'vix_low'
                })
                
                vix_df.to_csv('market_conditions/vix_historical.csv', index=False)
                print(f"  ✓ Saved {len(vix_df)} VIX records")
            else:
                print("  ✗ No VIX data available")
                
        except Exception as e:
            self.logger.error(f"Error fetching VIX data: {str(e)}")
            print("  ✗ Error fetching VIX data")
    
    def fetch_sector_etf_data(self):
        """Step 6: Fetch sector ETF performance data"""
        results = []
        errors = 0
        
        for i, ticker in enumerate(tqdm(self.tickers, desc="Sector ETF Data")):
            try:
                # Get sector for this ticker
                ticker_data = self.stocks_df[self.stocks_df['ticker'] == ticker].iloc[0]
                sector = ticker_data['sector']
                sector_etf = self.sector_etfs.get(sector, 'SPY')
                
                # Get ETF data
                etf = yf.Ticker(sector_etf)
                etf_hist = etf.history(period="10y")
                
                if etf_hist.empty:
                    continue
                
                # Get earnings dates for this ticker
                ticker_earnings = self.stocks_df[self.stocks_df['ticker'] == ticker]
                
                for _, row in ticker_earnings.iterrows():
                    earnings_date = pd.to_datetime(row['date'])
                    
                    # Get ETF price at earnings date
                    etf_price_at_earnings = self.get_price_at_date(etf_hist, earnings_date)
                    if etf_price_at_earnings is None:
                        continue
                    
                    # Calculate returns
                    etf_return_1d = self.calculate_return(etf_hist, earnings_date, 1)
                    etf_return_5d = self.calculate_return(etf_hist, earnings_date, 5)
                    etf_return_30d = self.calculate_return(etf_hist, earnings_date, 30)
                    etf_return_90d = self.calculate_return(etf_hist, earnings_date, 90)
                    
                    # Calculate relative strength vs SPY
                    spy_etf = yf.Ticker("SPY")
                    spy_hist = spy_etf.history(period="10y")
                    spy_return_30d = self.calculate_return(spy_hist, earnings_date, 30)
                    etf_vs_spy_30d = etf_return_30d - spy_return_30d if spy_return_30d is not None else None
                    
                    result = {
                        'ticker': ticker,
                        'earnings_date': earnings_date,
                        'sector': sector,
                        'sector_etf': sector_etf,
                        'etf_price_at_earnings': etf_price_at_earnings,
                        'etf_return_1d': etf_return_1d,
                        'etf_return_5d': etf_return_5d,
                        'etf_return_30d': etf_return_30d,
                        'etf_return_90d': etf_return_90d,
                        'etf_vs_spy_30d': etf_vs_spy_30d,
                    }
                    
                    results.append(result)
                
                time.sleep(0.5)
                
            except Exception as e:
                errors += 1
                self.logger.error(f"Error fetching sector ETF data for {ticker}: {str(e)}")
                continue
        
        # Save results
        df = pd.DataFrame(results)
        df.to_csv('market_conditions/sector_etf_performance.csv', index=False)
        print(f"  ✓ Saved {len(df)} sector ETF records (Errors: {errors})")
    
    def calculate_stock_conditions(self):
        """Step 7: Calculate stock-specific market conditions"""
        results = []
        errors = 0
        
        for i, ticker in enumerate(tqdm(self.tickers, desc="Stock Conditions")):
            try:
                # Get historical price data
                stock = yf.Ticker(ticker)
                hist = stock.history(period="10y")
                
                if hist.empty:
                    continue
                
                # Get earnings dates for this ticker
                ticker_earnings = self.stocks_df[self.stocks_df['ticker'] == ticker]
                
                for _, row in ticker_earnings.iterrows():
                    earnings_date = pd.to_datetime(row['date'])
                    
                    # Get price at earnings date
                    price_at_earnings = self.get_price_at_date(hist, earnings_date)
                    if price_at_earnings is None:
                        continue
                    
                    # Look back 30 days for technical indicators
                    start_date = earnings_date - timedelta(days=30)
                    end_date = earnings_date
                    
                    # Convert timezone-aware datetime to timezone-naive for comparison
                    hist_index = hist.index.tz_localize(None) if hist.index.tz else hist.index
                    period_data = hist[(hist_index >= start_date) & (hist_index <= end_date)]
                    
                    if len(period_data) < 20:  # Need at least 20 days
                        continue
                    
                    # Calculate technical indicators
                    closes = period_data['Close'].values
                    volumes = period_data['Volume'].values
                    
                    # RSI
                    rsi_14d = talib.RSI(closes, timeperiod=14)[-1] if len(closes) >= 14 else None
                    
                    # Volatility (30-day annualized)
                    returns = period_data['Close'].pct_change().dropna()
                    volatility_30d = returns.std() * np.sqrt(252) if len(returns) > 1 else None
                    
                    # ATR
                    high = period_data['High'].values
                    low = period_data['Low'].values
                    atr_14d = talib.ATR(high, low, closes, timeperiod=14)[-1] if len(closes) >= 14 else None
                    
                    # Moving averages
                    ma_20 = talib.SMA(closes, timeperiod=20)[-1] if len(closes) >= 20 else None
                    ma_50 = talib.SMA(closes, timeperiod=50)[-1] if len(closes) >= 50 else None
                    
                    # Price vs moving averages
                    distance_from_ma_20 = ((price_at_earnings - ma_20) / ma_20 * 100) if ma_20 else None
                    distance_from_ma_50 = ((price_at_earnings - ma_50) / ma_50 * 100) if ma_50 else None
                    
                    # 52-week high/low
                    year_start = earnings_date - timedelta(days=365)
                    hist_index = hist.index.tz_localize(None) if hist.index.tz else hist.index
                    year_data = hist[hist_index >= year_start]
                    if not year_data.empty:
                        year_high = year_data['High'].max()
                        year_low = year_data['Low'].min()
                        price_vs_52w_high = (price_at_earnings / year_high) * 100
                        price_vs_52w_low = (price_at_earnings / year_low) * 100
                    else:
                        price_vs_52w_high = None
                        price_vs_52w_low = None
                    
                    # Volume vs average
                    avg_volume_90d = hist['Volume'].rolling(90).mean().iloc[-1] if len(hist) >= 90 else None
                    current_volume = period_data['Volume'].iloc[-1] if not period_data.empty else None
                    volume_vs_avg = (current_volume / avg_volume_90d) if avg_volume_90d and current_volume else None
                    
                    # Price trend (30-day linear regression)
                    if len(closes) > 1:
                        x = np.arange(len(closes))
                        slope, _, _, _, _ = stats.linregress(x, closes)
                        price_trend_30d = slope
                    else:
                        price_trend_30d = None
                    
                    # PE ratio at earnings (simplified)
                    pe_ratio_at_earnings = None  # Would need EPS data
                    
                    result = {
                        'ticker': ticker,
                        'earnings_date': earnings_date,
                        'price_at_earnings': price_at_earnings,
                        'pe_ratio_at_earnings': pe_ratio_at_earnings,
                        'price_vs_52w_high': price_vs_52w_high,
                        'price_vs_52w_low': price_vs_52w_low,
                        'rsi_14d': rsi_14d,
                        'volatility_30d': volatility_30d,
                        'avg_true_range_14d': atr_14d,
                        'volume_vs_avg': volume_vs_avg,
                        'price_trend_30d': price_trend_30d,
                        'distance_from_ma_20': distance_from_ma_20,
                        'distance_from_ma_50': distance_from_ma_50,
                    }
                    
                    results.append(result)
                
                time.sleep(0.5)
                
            except Exception as e:
                errors += 1
                self.logger.error(f"Error calculating stock conditions for {ticker}: {str(e)}")
                continue
        
        # Save results
        df = pd.DataFrame(results)
        df.to_csv('market_conditions/stock_conditions_at_earnings.csv', index=False)
        print(f"  ✓ Saved {len(df)} stock condition records (Errors: {errors})")
    
    def analyze_earnings_quality(self):
        """Step 8: Analyze earnings quality and consistency"""
        # Consistency metrics
        consistency_results = []
        analyst_results = []
        
        for ticker in tqdm(self.tickers, desc="Earnings Quality"):
            try:
                # Get earnings history (simplified - would need actual earnings data)
                ticker_earnings = self.stocks_df[self.stocks_df['ticker'] == ticker]
                
                # Consistency metrics
                total_earnings = len(ticker_earnings)
                consistency_result = {
                    'ticker': ticker,
                    'total_earnings_events': total_earnings,
                    'earnings_beat_rate': 0.5,  # Placeholder
                    'avg_surprise_when_beat': 0.0,
                    'avg_surprise_when_miss': 0.0,
                    'surprise_consistency': 0.0,
                    'quarters_with_data': total_earnings,
                    'missing_quarters': 0,
                    'consecutive_beats': 0,
                    'consecutive_misses': 0,
                    'max_positive_surprise': 0.0,
                    'max_negative_surprise': 0.0,
                }
                consistency_results.append(consistency_result)
                
                # Analyst coverage
                stock = yf.Ticker(ticker)
                info = stock.info
                
                analyst_result = {
                    'ticker': ticker,
                    'analyst_count': self.safe_get(info, 'numberOfAnalystOpinions'),
                    'strong_buy': 0,  # Would need recommendations data
                    'buy': 0,
                    'hold': 0,
                    'sell': 0,
                    'strong_sell': 0,
                    'consensus_rating': 3.0,  # Neutral
                    'target_high': self.safe_get(info, 'targetHighPrice'),
                    'target_low': self.safe_get(info, 'targetLowPrice'),
                    'target_mean': self.safe_get(info, 'targetMeanPrice'),
                    'target_median': self.safe_get(info, 'targetMedianPrice'),
                    'current_price': self.safe_get(info, 'currentPrice'),
                    'upside_to_target': 0.0,
                }
                
                # Calculate upside
                if analyst_result['target_mean'] and analyst_result['current_price']:
                    analyst_result['upside_to_target'] = (
                        (analyst_result['target_mean'] - analyst_result['current_price']) / 
                        analyst_result['current_price'] * 100
                    )
                
                analyst_results.append(analyst_result)
                
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error analyzing earnings quality for {ticker}: {str(e)}")
                continue
        
        # Save results
        consistency_df = pd.DataFrame(consistency_results)
        consistency_df.to_csv('earnings_quality/consistency_metrics.csv', index=False)
        
        analyst_df = pd.DataFrame(analyst_results)
        analyst_df.to_csv('earnings_quality/analyst_coverage.csv', index=False)
        
        print(f"  ✓ Saved {len(consistency_df)} consistency records")
        print(f"  ✓ Saved {len(analyst_df)} analyst coverage records")
    
    def collect_risk_indicators(self):
        """Step 9: Collect risk indicators"""
        corporate_events = []
        earnings_consistency = []
        
        for ticker in tqdm(self.tickers, desc="Risk Indicators"):
            try:
                # Corporate events (placeholder)
                corporate_result = {
                    'ticker': ticker,
                    'is_acquisition_target': False,
                    'is_acquiring': False,
                    'merger_announced': False,
                    'merger_date': None,
                    'bankruptcy_risk': False,
                    'delisting_risk': False,
                    'recent_stock_split': False,
                    'split_date': None,
                    'split_ratio': None,
                    'notes': 'Manual review required'
                }
                corporate_events.append(corporate_result)
                
                # Earnings consistency
                ticker_earnings = self.stocks_df[self.stocks_df['ticker'] == ticker]
                total_earnings = len(ticker_earnings)
                
                # Calculate days between earnings (simplified)
                if total_earnings > 1:
                    dates = pd.to_datetime(ticker_earnings['date']).sort_values()
                    days_between = dates.diff().dt.days.dropna()
                    avg_days = days_between.mean()
                    std_days = days_between.std()
                else:
                    avg_days = 90  # Default quarterly
                    std_days = 0
                
                consistency_result = {
                    'ticker': ticker,
                    'expected_quarterly_reports': 40,  # 10 years * 4 quarters
                    'actual_reports': total_earnings,
                    'missing_reports': max(0, 40 - total_earnings),
                    'avg_days_between_earnings': avg_days,
                    'std_days_between_earnings': std_days,
                    'consistency_score': min(1.0, total_earnings / 40),
                    'last_earnings_date': ticker_earnings['date'].max(),
                    'days_since_last_earnings': (datetime.now() - pd.to_datetime(ticker_earnings['date'].max())).days,
                }
                earnings_consistency.append(consistency_result)
                
            except Exception as e:
                self.logger.error(f"Error collecting risk indicators for {ticker}: {str(e)}")
                continue
        
        # Save results
        corporate_df = pd.DataFrame(corporate_events)
        corporate_df.to_csv('risk_indicators/corporate_events.csv', index=False)
        
        consistency_df = pd.DataFrame(earnings_consistency)
        consistency_df.to_csv('risk_indicators/earnings_consistency.csv', index=False)
        
        print(f"  ✓ Saved {len(corporate_df)} corporate event records")
        print(f"  ✓ Saved {len(consistency_df)} earnings consistency records")
    
    def generate_summary_report(self):
        """Step 10: Generate comprehensive summary report"""
        report = []
        report.append("="*80)
        report.append("DATA ENRICHMENT SUMMARY REPORT")
        report.append("="*80)
        report.append(f"Generated: {datetime.now()}")
        report.append(f"Total stocks processed: {self.total_stocks}")
        report.append("")
        
        # Check each output file
        files_to_check = [
            ('fundamental_data/current_fundamentals.csv', 'Current Fundamentals'),
            ('fundamental_data/historical_fundamentals/', 'Historical Fundamentals Directory'),
            ('liquidity_data/volume_metrics.csv', 'Volume Metrics'),
            ('liquidity_data/current_bid_ask.csv', 'Bid-Ask Spreads'),
            ('market_conditions/vix_historical.csv', 'VIX Historical'),
            ('market_conditions/sector_etf_performance.csv', 'Sector ETF Performance'),
            ('market_conditions/stock_conditions_at_earnings.csv', 'Stock Conditions'),
            ('earnings_quality/consistency_metrics.csv', 'Earnings Consistency'),
            ('earnings_quality/analyst_coverage.csv', 'Analyst Coverage'),
            ('risk_indicators/corporate_events.csv', 'Corporate Events'),
            ('risk_indicators/earnings_consistency.csv', 'Earnings Consistency Risk'),
        ]
        
        total_records = 0
        for filepath, name in files_to_check:
            if os.path.exists(filepath):
                if os.path.isdir(filepath):
                    file_count = len([f for f in os.listdir(filepath) if f.endswith('.csv')])
                    report.append(f"✓ {name}: {file_count} files")
                else:
                    df = pd.read_csv(filepath)
                    record_count = len(df)
                    total_records += record_count
                    report.append(f"✓ {name}: {record_count} records")
            else:
                report.append(f"✗ {name}: NOT FOUND")
        
        report.append("")
        report.append(f"Total data records collected: {total_records:,}")
        report.append("="*80)
        
        # Save report
        with open('DATA_ENRICHMENT_REPORT.txt', 'w') as f:
            f.write('\n'.join(report))
        
        print('\n'.join(report))
    
    def safe_get(self, data, key, default=None):
        """Safely get value from dictionary with default"""
        try:
            value = data.get(key, default)
            return value if value is not None else default
        except:
            return default
    
    def get_price_at_date(self, hist_data, target_date):
        """Get price at or before target date"""
        try:
            # Find the closest date on or before target_date
            valid_dates = hist_data.index[hist_data.index <= target_date]
            if len(valid_dates) == 0:
                return None
            
            closest_date = valid_dates.max()
            return hist_data.loc[closest_date, 'Close']
        except:
            return None
    
    def calculate_return(self, hist_data, target_date, days_back):
        """Calculate return over specified days"""
        try:
            price_at_date = self.get_price_at_date(hist_data, target_date)
            if price_at_date is None:
                return None
            
            start_date = target_date - timedelta(days=days_back)
            price_start = self.get_price_at_date(hist_data, start_date)
            
            if price_start is None or price_start == 0:
                return None
            
            return (price_at_date - price_start) / price_start * 100
        except:
            return None

if __name__ == "__main__":
    pipeline = DataEnrichmentPipeline()
    pipeline.run_full_pipeline()