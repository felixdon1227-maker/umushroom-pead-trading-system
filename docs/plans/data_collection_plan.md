# BACKGROUND AGENT: COMPREHENSIVE DATA ENRICHMENT PLAN

**OBJECTIVE**: Fetch all additional fundamental, liquidity, and market condition data for 106 stocks to enable comprehensive PEAD analysis.

**CURRENT STATUS**: 
- Historical price data: ✓ In progress (33/106 complete)
- Earnings history: ✓ In progress
- Additional data: ✗ Not started (THIS TASK)

---

## PART 1: FUNDAMENTAL DATA COLLECTION

### 1.1 Stock Fundamentals (Current + Historical)

**Source**: yfinance API (primary), TWS API (backup)

**For Each Stock** in `earnings_clean_filtered.csv` (106 stocks):

#### A. Current Fundamentals (Latest Available)
Fetch using `yf.Ticker(ticker).info`:

```python
# Required fields:
{
    'ticker': str,
    'pe_ratio': float,                    # trailingPE
    'forward_pe': float,                  # forwardPE
    'peg_ratio': float,                   # pegRatio
    'price_to_book': float,               # priceToBook
    'debt_to_equity': float,              # debtToEquity
    'current_ratio': float,               # currentRatio
    'profit_margin': float,               # profitMargins
    'operating_margin': float,            # operatingMargins
    'return_on_equity': float,            # returnOnEquity
    'return_on_assets': float,            # returnOnAssets
    'revenue_growth': float,              # revenueGrowth
    'earnings_growth': float,             # earningsGrowth
    'beta': float,                        # beta
    'shares_outstanding': float,          # sharesOutstanding
    'float_shares': float,                # floatShares
    'institutional_ownership': float,     # heldPercentInstitutions
    'insider_ownership': float,           # heldPercentInsiders
    'short_ratio': float,                 # shortRatio
    'short_percent_float': float,         # shortPercentOfFloat
    'analyst_count': int,                 # number of analysts covering
    'target_price': float,                # targetMeanPrice
    'recommendation': str,                # recommendationKey
    'fifty_two_week_high': float,        # fiftyTwoWeekHigh
    'fifty_two_week_low': float,         # fiftyTwoWeekLow
    'avg_volume_10day': float,            # averageVolume10days
    'avg_volume_3month': float,           # averageVolume
    'market_cap': float,                  # marketCap
    'enterprise_value': float,            # enterpriseValue
    'last_updated': datetime              # timestamp of data fetch
}
```

**Storage**: `fundamental_data/current_fundamentals.csv`

**Format**: One row per stock, all columns above

---

#### B. Historical Fundamentals (At Each Earnings Date)

**Purpose**: Know the stock's valuation/health AT THE TIME of each earnings

For each earnings event in `pead_historical_data/earnings_history/{ticker}_earnings.csv`:

```python
# For each earnings_date, fetch quarterly financials closest to that date
# Use: yf.Ticker(ticker).quarterly_financials
# Use: yf.Ticker(ticker).quarterly_balance_sheet
# Use: yf.Ticker(ticker).quarterly_cashflow

{
    'ticker': str,
    'earnings_date': datetime,
    'quarter_end_date': datetime,        # Actual quarter end
    'revenue': float,                    # Total Revenue
    'revenue_estimate': float,           # Analyst estimate (if available)
    'revenue_surprise_pct': float,       # (actual - estimate) / estimate * 100
    'gross_profit': float,
    'operating_income': float,
    'net_income': float,
    'eps_actual': float,                 # Already have from earnings_history
    'eps_estimate': float,               # Already have from earnings_history
    'total_assets': float,
    'total_liabilities': float,
    'total_debt': float,
    'cash_and_equivalents': float,
    'operating_cash_flow': float,
    'free_cash_flow': float,
    'pe_ratio_at_earnings': float,       # Calculate from price and EPS
    'price_at_earnings': float,          # From daily_prices
}
```

**Storage**: `fundamental_data/historical_fundamentals/{ticker}_fundamentals.csv`

**Format**: One row per earnings event per stock

---

### 1.2 Revenue Data Collection

**Critical**: Revenue surprises are as important as EPS surprises for PEAD

**Source**: yfinance `quarterly_financials` or Earnings Calendar API

For each earnings event:
```python
{
    'ticker': str,
    'earnings_date': datetime,
    'revenue_actual': float,
    'revenue_estimate': float,
    'revenue_surprise_pct': float,
    'revenue_yoy_growth': float,         # Year-over-year growth
}
```

**Storage**: Append to `fundamental_data/historical_fundamentals/{ticker}_fundamentals.csv`

---

## PART 2: LIQUIDITY METRICS

### 2.1 Volume Analysis (90-day rolling)

**Source**: Already have in `pead_historical_data/daily_prices/{ticker}_daily_10y.csv`

**Task**: Calculate rolling metrics for each earnings date

For each earnings event:
```python
# Look back 90 days from earnings_date
{
    'ticker': str,
    'earnings_date': datetime,
    'avg_volume_90d': float,             # Average daily volume
    'avg_dollar_volume_90d': float,      # avg_volume * avg_price
    'volume_std_90d': float,             # Standard deviation
    'volume_consistency': float,         # 1 - (std / mean)
    'min_volume_90d': float,
    'max_volume_90d': float,
    'volume_trend': float,               # Linear regression slope
}
```

**Storage**: `liquidity_data/volume_metrics.csv`

**Format**: One row per earnings event per stock

---

### 2.2 Bid-Ask Spread (Current)

**Source**: TWS API - `reqMktData()` with snapshot

For each stock (current data only):
```python
{
    'ticker': str,
    'bid': float,
    'ask': float,
    'bid_ask_spread': float,             # ask - bid
    'spread_percent': float,             # (ask - bid) / mid * 100
    'bid_size': int,
    'ask_size': int,
    'last_price': float,
    'timestamp': datetime
}
```

**Storage**: `liquidity_data/current_bid_ask.csv`

**Format**: One row per stock

---

## PART 3: MARKET CONDITIONS (Historical)

### 3.1 VIX Historical Data

**Source**: yfinance `^VIX`

**Task**: Get VIX level at each earnings date

```python
# Fetch VIX daily data for last 10 years
vix_data = yf.download('^VIX', start='2015-01-01', end='2025-12-31')

# For each earnings event, get VIX on that date
{
    'date': datetime,
    'vix_close': float,
    'vix_high': float,
    'vix_low': float,
    'vix_change': float,                 # Day-over-day change
}
```

**Storage**: `market_conditions/vix_historical.csv`

**Format**: One row per trading day (will be joined to earnings events)

---

### 3.2 Sector ETF Performance

**Purpose**: Know if sector was in uptrend/downtrend at earnings time

**Sector Mapping**:
```python
SECTOR_ETFS = {
    'Financials': 'XLF',
    'Technology': 'XLK',
    'Healthcare': 'XLV',
    'Energy': 'XLE',
    'Industrials': 'XLI',
    'Materials': 'XLB',
    'Consumer': 'XLY',      # Consumer Discretionary
    'Utilities': 'XLU',
    'Other': 'SPY'          # Use S&P 500 as default
}
```

**Task**: For each sector ETF, fetch 10 years daily data

For each earnings event:
```python
{
    'ticker': str,
    'earnings_date': datetime,
    'sector': str,
    'sector_etf': str,
    'etf_price_at_earnings': float,
    'etf_return_1d': float,              # 1 day before earnings
    'etf_return_5d': float,              # 5 days before earnings
    'etf_return_30d': float,             # 30 days before earnings (momentum)
    'etf_return_90d': float,             # 90 days before earnings
    'etf_vs_spy_30d': float,             # Sector relative strength vs SPY
}
```

**Storage**: `market_conditions/sector_etf_performance.csv`

**Format**: One row per earnings event per stock

---

### 3.3 Stock-Specific Market Conditions

**Source**: Calculate from existing `daily_prices` data

For each earnings event (30 days lookback):
```python
{
    'ticker': str,
    'earnings_date': datetime,
    'price_at_earnings': float,          # Close price day before earnings
    'pe_ratio_at_earnings': float,       # price / trailing_eps
    'price_vs_52w_high': float,          # (price / 52w_high) * 100
    'price_vs_52w_low': float,           # (price / 52w_low) * 100
    'rsi_14d': float,                    # Relative Strength Index
    'volatility_30d': float,             # 30-day historical volatility (annualized)
    'avg_true_range_14d': float,         # ATR indicator
    'volume_vs_avg': float,              # Current volume / 90d avg
    'price_trend_30d': float,            # Linear regression slope
    'distance_from_ma_20': float,        # (price - MA20) / MA20 * 100
    'distance_from_ma_50': float,        # (price - MA50) / MA50 * 100
}
```

**Storage**: `market_conditions/stock_conditions_at_earnings.csv`

**Format**: One row per earnings event per stock

---

## PART 4: EARNINGS QUALITY METRICS

### 4.1 Earnings Consistency

**Source**: Analyze `pead_historical_data/earnings_history/{ticker}_earnings.csv`

For each stock (aggregate metrics):
```python
{
    'ticker': str,
    'total_earnings_events': int,
    'earnings_beat_rate': float,         # % of times beat estimate
    'avg_surprise_when_beat': float,
    'avg_surprise_when_miss': float,
    'surprise_consistency': float,       # Std dev of surprises
    'quarters_with_data': int,
    'missing_quarters': int,             # Gaps in reporting
    'consecutive_beats': int,            # Current streak
    'consecutive_misses': int,
    'max_positive_surprise': float,
    'max_negative_surprise': float,
}
```

**Storage**: `earnings_quality/consistency_metrics.csv`

**Format**: One row per stock

---

### 4.2 Analyst Coverage

**Source**: yfinance `analyst_price_target` and `recommendations`

For each stock:
```python
{
    'ticker': str,
    'analyst_count': int,
    'strong_buy': int,
    'buy': int,
    'hold': int,
    'sell': int,
    'strong_sell': int,
    'consensus_rating': float,           # Weighted average (1=strong buy, 5=strong sell)
    'target_high': float,
    'target_low': float,
    'target_mean': float,
    'target_median': float,
    'current_price': float,
    'upside_to_target': float,           # (target_mean - current) / current * 100
}
```

**Storage**: `earnings_quality/analyst_coverage.csv`

**Format**: One row per stock

---

## PART 5: RISK INDICATORS

### 5.1 M&A and Corporate Events

**Source**: yfinance `calendar` or manual check

For each stock:
```python
{
    'ticker': str,
    'is_acquisition_target': bool,
    'is_acquiring': bool,
    'merger_announced': bool,
    'merger_date': datetime,
    'bankruptcy_risk': bool,
    'delisting_risk': bool,
    'recent_stock_split': bool,
    'split_date': datetime,
    'split_ratio': str,
    'notes': str
}
```

**Storage**: `risk_indicators/corporate_events.csv`

**Format**: One row per stock

---

### 5.2 Earnings Date Consistency

**Source**: Analyze `pead_historical_data/earnings_history/{ticker}_earnings.csv`

For each stock:
```python
{
    'ticker': str,
    'expected_quarterly_reports': int,   # Should be ~40 for 10 years
    'actual_reports': int,
    'missing_reports': int,
    'avg_days_between_earnings': float,
    'std_days_between_earnings': float,
    'consistency_score': float,          # 1.0 = perfect quarterly reporting
    'last_earnings_date': datetime,
    'days_since_last_earnings': int,
}
```

**Storage**: `risk_indicators/earnings_consistency.csv`

**Format**: One row per stock

---

## DATA COLLECTION SCRIPT STRUCTURE

### Master Script: `fetch_all_enrichment_data.py`

```python
"""
Master data enrichment script for PEAD analysis
Fetches all fundamental, liquidity, and market condition data
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import time
from tqdm import tqdm

class DataEnrichmentPipeline:
    def __init__(self):
        self.stocks_df = pd.read_csv('earnings_clean_filtered.csv')
        self.tickers = self.stocks_df['ticker'].unique()
        
        # Create output directories
        self.create_directories()
        
    def create_directories(self):
        """Create all necessary output directories"""
        dirs = [
            'fundamental_data',
            'liquidity_data',
            'market_conditions',
            'earnings_quality',
            'risk_indicators'
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
            os.makedirs(f'{d}/temp', exist_ok=True)
    
    def run_full_pipeline(self):
        """Execute all data collection steps"""
        print("="*80)
        print("COMPREHENSIVE DATA ENRICHMENT PIPELINE")
        print("="*80)
        print(f"Stocks to process: {len(self.tickers)}")
        print("="*80)
        
        # Step 1: Current Fundamentals
        print("\n[1/10] Fetching current fundamentals...")
        self.fetch_current_fundamentals()
        
        # Step 2: Historical Fundamentals
        print("\n[2/10] Fetching historical fundamentals...")
        self.fetch_historical_fundamentals()
        
        # Step 3: Revenue Data
        print("\n[3/10] Fetching revenue data...")
        self.fetch_revenue_data()
        
        # Step 4: Volume Metrics
        print("\n[4/10] Calculating volume metrics...")
        self.calculate_volume_metrics()
        
        # Step 5: Bid-Ask Spreads (if TWS available)
        print("\n[5/10] Fetching bid-ask spreads...")
        self.fetch_bid_ask_spreads()
        
        # Step 6: VIX Historical
        print("\n[6/10] Fetching VIX historical data...")
        self.fetch_vix_data()
        
        # Step 7: Sector ETF Performance
        print("\n[7/10] Fetching sector ETF performance...")
        self.fetch_sector_etf_data()
        
        # Step 8: Stock Market Conditions
        print("\n[8/10] Calculating stock market conditions...")
        self.calculate_stock_conditions()
        
        # Step 9: Earnings Quality
        print("\n[9/10] Analyzing earnings quality...")
        self.analyze_earnings_quality()
        
        # Step 10: Risk Indicators
        print("\n[10/10] Collecting risk indicators...")
        self.collect_risk_indicators()
        
        print("\n" + "="*80)
        print("✅ DATA ENRICHMENT COMPLETE")
        print("="*80)
        
        # Generate summary report
        self.generate_summary_report()
    
    def fetch_current_fundamentals(self):
        """Step 1: Fetch current fundamental data for all stocks"""
        results = []
        
        for ticker in tqdm(self.tickers, desc="Current Fundamentals"):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                results.append({
                    'ticker': ticker,
                    'pe_ratio': info.get('trailingPE'),
                    'forward_pe': info.get('forwardPE'),
                    'peg_ratio': info.get('pegRatio'),
                    'price_to_book': info.get('priceToBook'),
                    'debt_to_equity': info.get('debtToEquity'),
                    'current_ratio': info.get('currentRatio'),
                    'profit_margin': info.get('profitMargins'),
                    'operating_margin': info.get('operatingMargins'),
                    'return_on_equity': info.get('returnOnEquity'),
                    'return_on_assets': info.get('returnOnAssets'),
                    'revenue_growth': info.get('revenueGrowth'),
                    'earnings_growth': info.get('earningsGrowth'),
                    'beta': info.get('beta'),
                    'shares_outstanding': info.get('sharesOutstanding'),
                    'float_shares': info.get('floatShares'),
                    'institutional_ownership': info.get('heldPercentInstitutions'),
                    'insider_ownership': info.get('heldPercentInsiders'),
                    'short_ratio': info.get('shortRatio'),
                    'short_percent_float': info.get('shortPercentOfFloat'),
                    'analyst_count': info.get('numberOfAnalystOpinions'),
                    'target_price': info.get('targetMeanPrice'),
                    'recommendation': info.get('recommendationKey'),
                    'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                    'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                    'avg_volume_10day': info.get('averageVolume10days'),
                    'avg_volume_3month': info.get('averageVolume'),
                    'market_cap': info.get('marketCap'),
                    'enterprise_value': info.get('enterpriseValue'),
                    'last_updated': datetime.now()
                })
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"  ✗ Error fetching {ticker}: {str(e)[:50]}")
                continue
        
        df = pd.DataFrame(results)
        df.to_csv('fundamental_data/current_fundamentals.csv', index=False)
        print(f"  ✓ Saved {len(df)} stocks")
    
    # ... (implement all other methods following same pattern)
    
    def generate_summary_report(self):
        """Generate summary of collected data"""
        report = []
        report.append("="*80)
        report.append("DATA ENRICHMENT SUMMARY REPORT")
        report.append("="*80)
        report.append(f"Generated: {datetime.now()}")
        report.append(f"Total stocks processed: {len(self.tickers)}")
        report.append("")
        
        # Check each output file
        files_to_check = [
            ('fundamental_data/current_fundamentals.csv', 'Current Fundamentals'),
            ('liquidity_data/volume_metrics.csv', 'Volume Metrics'),
            ('market_conditions/vix_historical.csv', 'VIX Historical'),
            ('market_conditions/sector_etf_performance.csv', 'Sector ETF Performance'),
            ('earnings_quality/consistency_metrics.csv', 'Earnings Quality'),
            ('risk_indicators/corporate_events.csv', 'Risk Indicators'),
        ]
        
        for filepath, name in files_to_check:
            if os.path.exists(filepath):
                df = pd.read_csv(filepath)
                report.append(f"✓ {name}: {len(df)} records")
            else:
                report.append(f"✗ {name}: NOT FOUND")
        
        report.append("="*80)
        
        # Save report
        with open('DATA_ENRICHMENT_REPORT.txt', 'w') as f:
            f.write('\n'.join(report))
        
        print('\n'.join(report))

if __name__ == "__main__":
    pipeline = DataEnrichmentPipeline()
    pipeline.run_full_pipeline()
```

---

## EXECUTION INSTRUCTIONS FOR BACKGROUND AGENT

1. **Install Required Packages**:
```bash
pip install yfinance pandas numpy tqdm ta-lib scipy
```

2. **Run Data Collection**:
```bash
python fetch_all_enrichment_data.py
```

3. **Expected Runtime**: ~2-3 hours for 106 stocks

4. **Error Handling**: 
   - Save progress every 10 stocks
   - Log all errors to `enrichment_errors.log`
   - Skip failed stocks, continue with others

5. **Output Verification**:
   - Check `DATA_ENRICHMENT_REPORT.txt` for completion status
   - Verify all CSV files exist and have expected row counts

---

## FINAL DATA STRUCTURE

After completion, you will have:

```
project/
├── fundamental_data/
│   ├── current_fundamentals.csv (106 rows)
│   └── historical_fundamentals/
│       ├── FFIN_fundamentals.csv
│       ├── INDB_fundamentals.csv
│       └── ... (106 files)
├── liquidity_data/
│   ├── volume_metrics.csv (~2000 rows, all earnings events)
│   └── current_bid_ask.csv (106 rows)
├── market_conditions/
│   ├── vix_historical.csv (~2500 rows, daily)
│   ├── sector_etf_performance.csv (~2000 rows)
│   └── stock_conditions_at_earnings.csv (~2000 rows)
├── earnings_quality/
│   ├── consistency_metrics.csv (106 rows)
│   └── analyst_coverage.csv (106 rows)
├── risk_indicators/
│   ├── corporate_events.csv (106 rows)
│   └── earnings_consistency.csv (106 rows)
└── DATA_ENRICHMENT_REPORT.txt
```

All files will be CSV format, compatible with pandas, and ready for Phase 2 analysis.

