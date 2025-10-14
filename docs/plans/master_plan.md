# PEAD Analysis & Stock Selection Framework - MASTER PLAN

## Current Status

**Date**: October 14, 2025
**Challenge Period**: October 14 - November 13, 2025 (4 weeks)
**Starting Capital**: $100,000

### Filters Applied
- ✅ Market cap >= $1 Billion (removed 61 stocks)
- ✅ Data files cleaned for excluded stocks
- **Current Universe**: 106 stocks

### Data Collection Progress
- ✅ Historical price data: In progress (33/106 complete, ETA ~51 min)
- ✅ Earnings history: In progress
- ⏳ Additional enrichment data: Ready to start (see BACKGROUND_AGENT_DATA_COLLECTION_PLAN.md)

---

## Objective

Analyze 10 years of earnings data for 106 stocks to identify the top 80 best opportunities for two distinct earnings strategies:

1. **Strategy 1**: Pre-Earnings Momentum Play (Day -1 to Day +1)
2. **Strategy 2**: Post-Earnings Drift Recovery (Day -1 to Day +7)

Goal: Execute ~10 trades per week (40 total) with >60% win rate

---

## Two Trading Strategies Defined

### Strategy 1: Pre-Earnings Momentum Play
- **Entry**: 1 day before earnings (close of day)
- **Exit**: Next trading day after earnings (close of day)
- **Goal**: Capture immediate earnings reaction
- **Target**: Stocks with history of positive surprises + immediate price jumps
- **Risk**: Higher volatility, binary outcome
- **Allocation**: 60% of active capital

### Strategy 2: Post-Earnings Drift Recovery
- **Entry**: 1 day before earnings (close of day)
- **Exit**: 7 trading days after earnings
- **Goal**: Capture drift effect after initial negative reaction
- **Target**: Stocks that drop initially but recover within 7 days
- **Risk**: Lower but requires patience, opportunity cost
- **Allocation**: 40% of active capital (40% in ETFs for stability)

---

## Data Architecture

### Already Collected (In Progress)
```
pead_historical_data/
├── daily_prices/           # 10 years daily OHLCV
│   └── {TICKER}_daily_10y.csv
├── hourly_prices/          # 2 years hourly around earnings
│   └── {TICKER}_hourly.csv
├── earnings_history/       # EPS estimates, actuals, surprises
│   └── {TICKER}_earnings.csv
└── collection_summary.csv  # Progress tracking
```

### To Be Collected (Background Agent)
**See**: `BACKGROUND_AGENT_DATA_COLLECTION_PLAN.md` for detailed specifications

```
fundamental_data/
├── current_fundamentals.csv              # 106 rows, 30+ columns
└── historical_fundamentals/
    └── {TICKER}_fundamentals.csv         # Quarterly data at each earnings

liquidity_data/
├── volume_metrics.csv                    # ~2000 rows (all earnings events)
└── current_bid_ask.csv                   # 106 rows

market_conditions/
├── vix_historical.csv                    # ~2500 days
├── sector_etf_performance.csv            # ~2000 rows
└── stock_conditions_at_earnings.csv      # ~2000 rows

earnings_quality/
├── consistency_metrics.csv               # 106 rows
└── analyst_coverage.csv                  # 106 rows

risk_indicators/
├── corporate_events.csv                  # 106 rows
└── earnings_consistency.csv              # 106 rows
```

---

## Analysis Pipeline

### Phase 1: Data Enrichment ⏳ READY TO START
**Script**: `fetch_all_enrichment_data.py`
**Runtime**: 2-3 hours
**Status**: Detailed plan created in `BACKGROUND_AGENT_DATA_COLLECTION_PLAN.md`

**Tasks**:
1. Fetch current & historical fundamentals (P/E, margins, debt, ownership)
2. Calculate liquidity metrics (volume, bid-ask spreads)
3. Collect market conditions (VIX, sector ETFs, technical indicators)
4. Analyze earnings quality (beat rate, consistency)
5. Identify risk factors (M&A, reporting issues)

**Output**: 15+ CSV files with comprehensive data

---

### Phase 2: Historical Performance Analysis
**Script**: `pead_performance_analyzer.py`

**For Each Stock's Earnings Events** (10 years):

#### Strategy 1 Metrics (Day -1 to Day +1):
- Entry price (close Day -1)
- Exit price (close Day +1)
- Return %
- Win rate (% positive returns)
- Average win vs average loss
- Sharpe ratio
- Maximum drawdown
- Volatility

#### Strategy 2 Metrics (Day -1 to Day +7):
- Entry price (close Day -1)
- Exit price (close Day +7)
- Return %
- Initial reaction (Day 0 to Day +1)
- Recovery pattern (Day +1 to Day +7)
- Win rate after negative Day 1
- Average recovery magnitude
- Consistency score

#### Conditional Analysis:
- Performance by earnings surprise magnitude (large beat, small beat, miss)
- Performance by market volatility (VIX < 15, 15-20, 20-30, > 30)
- Performance by sector momentum (uptrend vs downtrend)
- Performance by P/E levels (cheap vs expensive)
- Performance by volume patterns (high vs low)
- Performance by revenue surprise
- Performance by analyst sentiment

**Output**: 
- `strategy_performance_by_stock.csv` (106 rows, aggregate metrics)
- `strategy_performance_by_event.csv` (~2000 rows, individual events)

---

### Phase 3: Stock Filtering & Ranking
**Script**: `stock_screener.py`

#### Exclusion Criteria (eliminate stocks):
1. ✅ Market cap < $1B (already done)
2. Average daily dollar volume < $1M (illiquid)
3. Win rate < 40% for both strategies (unpredictable)
4. Stocks under acquisition/M&A
5. Stocks that skip earnings (inconsistent reporters)
6. Stocks with < 5 earnings events in dataset (insufficient data)
7. Friday earnings (weekend risk) - except ASTS, FRHC, ACLX

#### Ranking Criteria (weighted scoring):

**Primary Weight (70%)** - Historical Performance:
- Win rate for target strategy (30%)
- Average return magnitude (20%)
- Consistency score (pattern reliability) (20%)

**Secondary Weight (30%)** - Quality & Risk:
- Liquidity score (10%)
- Sector diversification bonus (5%)
- Recent performance trend (last 4 quarters) (10%)
- Risk-adjusted return (Sharpe ratio) (5%)

#### Separate Rankings:
- Top 50 for Strategy 1 (momentum plays)
- Top 50 for Strategy 2 (drift recovery)
- Combined top 80 (overlap allowed)

**Output**: 
- `top_80_stocks_ranked.csv`
- `strategy_1_top_50.csv`
- `strategy_2_top_50.csv`
- `excluded_stocks_reasons.csv`

---

### Phase 4: Sector & Pattern Analysis
**Script**: `sector_pattern_analyzer.py`

#### Sector Performance:
- Best/worst sectors for each strategy
- Sector-specific optimal conditions (VIX, momentum)
- Sector correlation with market conditions
- Diversification recommendations

#### Pattern Recognition:
- Stocks that consistently beat estimates (>70% beat rate)
- Reliable "drop-then-recover" stocks (Strategy 2)
- Optimal entry conditions by pattern type
- Identify "trap" patterns to avoid

#### Risk Analysis:
- High-risk patterns (false breakouts, dead cat bounces)
- Position sizing recommendations by volatility
- Correlated stocks (avoid over-concentration)
- Maximum sector exposure limits

**Output**: 
- `sector_analysis_report.csv`
- `pattern_insights.csv`
- `risk_matrix.csv`
- `position_sizing_guide.csv`

---

### Phase 5: Actionable Trading Signals
**Script**: `trading_signal_generator.py`

**For Upcoming Earnings** (Oct 14 - Nov 16, 2025):

#### Signal Generation:
1. Match each upcoming earnings against historical patterns
2. Calculate probability of success based on:
   - Historical win rate for this stock
   - Current market conditions (VIX, sector momentum)
   - Stock's current technical setup (RSI, price vs MA)
   - Earnings surprise expectations
   - Analyst sentiment
3. Recommend strategy (1 or 2) and confidence level
4. Calculate position size based on risk
5. Set stop-loss and target prices

#### Signal Quality Tiers:
- **High Confidence** (>70% historical win rate + favorable conditions)
- **Medium Confidence** (55-70% win rate)
- **Speculative** (40-55% win rate, small position)
- **Avoid** (<40% win rate or unfavorable conditions)

#### Weekly Trade Selection:
- Target: 10 trades per week
- Prioritize high-confidence signals
- Ensure sector diversification
- Balance Strategy 1 vs Strategy 2
- Reserve capacity for unexpected opportunities

**Output**: 
- `upcoming_earnings_signals.csv` (all upcoming earnings)
- `week1_trade_plan.csv` (10 recommended trades)
- `week2_trade_plan.csv`
- `week3_trade_plan.csv`
- `week4_trade_plan.csv`
- `position_sizing_calculator.csv`

---

## Deliverables

### 1. Master Dataset
**File**: `enriched_earnings_data.csv`
- All 106 stocks
- 10 years of earnings events
- Complete fundamental, liquidity, and market condition data
- ~2000 rows (all earnings events)
- ~100+ columns

### 2. Performance Report
**File**: `strategy_performance_by_stock.csv`
- Historical performance metrics for both strategies
- 106 rows (one per stock)
- Win rates, average returns, Sharpe ratios, etc.

### 3. Top 80 List
**File**: `top_80_stocks_ranked.csv`
- Filtered and ranked stocks with composite scores
- Separate scores for Strategy 1 and Strategy 2
- Recommended allocation per stock

### 4. Sector Analysis
**File**: `sector_analysis_report.csv`
- Best/worst sectors for each strategy
- Optimal conditions by sector
- Risk correlations

### 5. Trading Signals
**Files**: `week1_trade_plan.csv` through `week4_trade_plan.csv`
- Specific recommendations for each week
- Entry/exit prices, position sizes
- Confidence levels and risk metrics

### 6. Summary Dashboard
**File**: `ANALYSIS_SUMMARY_REPORT.md`
- Key insights and findings
- Best opportunities by strategy
- Risk warnings and limitations
- Expected performance metrics

---

## Success Criteria

1. ✅ Reduce 167 stocks to 106 (market cap filter)
2. ⏳ Reduce 106 stocks to 80 high-quality candidates
3. ⏳ Identify 40 trades total (10 per week × 4 weeks)
4. 🎯 Target: >60% historical win rate for selected stocks
5. 🎯 Target: Average return >3% per trade
6. 🎯 Target: Maximum drawdown <15% on any single trade
7. 🎯 Clear rules for entry, exit, position sizing
8. 🎯 Risk management based on historical patterns

---

## Execution Timeline

### Week 1 (Oct 14-20)
- ✅ Day 1-2: Historical data collection (in progress)
- ⏳ Day 2-3: Data enrichment (background agent)
- ⏳ Day 3-4: Performance analysis
- ⏳ Day 4-5: Stock filtering & ranking
- ⏳ Day 5-6: Generate Week 1 trading signals
- 🎯 Day 6-7: Execute Week 1 trades

### Week 2-4 (Oct 21 - Nov 13)
- Daily: Monitor active positions
- Weekly: Generate next week's signals
- Weekly: Execute 10 new trades
- Daily: Update analysis with new data
- End of challenge: Final performance report

---

## Risk Management Rules

1. **Position Sizing**:
   - High confidence: 3-5% of capital per trade
   - Medium confidence: 2-3% of capital
   - Speculative: 1-2% of capital
   - Maximum 10 concurrent positions

2. **Stop Losses**:
   - Strategy 1: -5% from entry (tight, 1-day hold)
   - Strategy 2: -7% from entry (wider, 7-day hold)
   - Adjust based on stock's historical volatility

3. **Diversification**:
   - Maximum 30% in any single sector
   - Maximum 15% in any single stock
   - Balance between Strategy 1 and Strategy 2

4. **Exit Rules**:
   - Strategy 1: Exit Day +1 regardless of outcome
   - Strategy 2: Exit Day +7 or when target hit
   - Emergency exit if stop loss triggered

---

## Next Steps

1. **IMMEDIATE** (Background Agent):
   - Run `fetch_all_enrichment_data.py`
   - Expected runtime: 2-3 hours
   - Output: 15+ CSV files with enrichment data

2. **After Data Collection**:
   - Run `pead_performance_analyzer.py`
   - Analyze 10 years of historical performance
   - Generate performance metrics

3. **Stock Selection**:
   - Run `stock_screener.py`
   - Filter and rank to top 80 stocks
   - Generate exclusion report

4. **Trading Signals**:
   - Run `trading_signal_generator.py`
   - Generate Week 1 trade recommendations
   - Begin executing trades

---

## Files Reference

- **This Plan**: `PEAD_ANALYSIS_MASTER_PLAN.md`
- **Data Collection Details**: `BACKGROUND_AGENT_DATA_COLLECTION_PLAN.md`
- **Stock List**: `earnings_clean_filtered.csv` (106 stocks)
- **Excluded Stocks**: `excluded_under_1b.csv` (61 stocks)
- **Historical Data**: `pead_historical_data/` directory
- **Progress Tracking**: `pead_historical_data/collection_summary.csv`

---

**Last Updated**: October 14, 2025, 20:15
**Status**: Phase 1 (Data Collection) in progress
**Next Milestone**: Complete enrichment data collection

