# UMushroom Investment Challenge - PEAD Trading System

[![Status](https://img.shields.io/badge/Status-Ready%20for%20Trading-success)]()
[![Data](https://img.shields.io/badge/Data-373%20Stocks-blue)]()
[![Strategy](https://img.shields.io/badge/Strategy-Optimized-green)]()

A comprehensive **Post-Earnings Announcement Drift (PEAD)** trading system designed to win the UMushroom Investment Challenge with systematic, data-driven strategies.

---

## 🎯 **Competition Overview**

- **Start Date**: October 14, 2025
- **End Date**: November 13, 2025
- **Duration**: 4 weeks
- **Initial Capital**: $100,000
- **Goal**: Maximize returns through optimized PEAD trading

---

## 📊 **Current Status**

### ✅ **Phase 1: Data Collection** - COMPLETE
- **373 stocks** with full multi-timeframe data (5-min, daily, weekly)
- **413 stocks** with fundamental data and 5-minute intraday data
- **92 earnings events** mapped in competition timeframe
- **10 years** of historical price and earnings data

### ✅ **Phase 2: Strategy Development** - COMPLETE
- Three-step dynamic position sizing strategy optimized
- Historical backtesting completed with realistic transaction costs
- Top 100 stocks ranked by PEAD score
- Risk management parameters defined

### 🚀 **Phase 3: Live Trading** - READY
- Real-time monitoring system prepared
- Entry/exit signals defined
- Position sizing rules optimized
- Risk controls implemented

---

## 📁 **Project Structure**

```
UMushroom_Investment_challange/
├── README.md                       # This file
├── main.py                        # Main entry point
├── config/
│   └── settings.py                # Configuration settings
├── data/
│   └── processed/
│       ├── earnings_final.csv     # Final stock universe (92 stocks)
│       └── historical_data/       # 10 years of price/earnings data
├── scripts/
│   ├── data_collection/          # Core data fetching scripts
│   │   ├── ultra_fast_bulk_extractor.py
│   │   ├── ib_gateway_bulk_fast_extractor.py
│   │   ├── extract_all_finviz_stocks.py
│   │   ├── run_tws_scanners.py
│   │   └── filter_scanner_results.py
│   ├── analysis/                  # Strategy analysis scripts
│   │   ├── three_step_earnings_strategy.py
│   │   ├── comprehensive_backtester.py
│   │   ├── strategy_optimizer.py
│   │   ├── filter_engine.py
│   │   └── metrics_tracker.py
│   └── archive/                   # Archived/older scripts
├── docs/
│   ├── reports/                   # Analysis reports
│   ├── guides/                    # User guides
│   └── strategy/                  # Strategy documentation
└── strategy2_analysis/           # Latest strategy analysis results
```

---

## 🎯 **The Optimized Three-Step Strategy**

### **Overview**
A systematic approach to capturing Post-Earnings Announcement Drift with dynamic position sizing based on early performance signals.

### **Step 1: Initial Entry (Day 0 - Earnings Day)**
- **Entry Timing**: Market close on earnings day
- **Entry Criteria**:
  - Stock must be in top 100 ranked by PEAD score
  - Day 0 close must be **positive** (>0% from open)
  - Volume ratio > 1.2x average
- **Position Size**: 2-3% of capital
- **Stop Loss**: Set at -3% from entry

### **Step 2: Dynamic Scaling (Day 1)**
- **Evaluation**: Assess position performance at market close
- **Scaling Rules**:
  - If up **>1%**: Add 50-100% more shares
  - If up **>2%**: Add 100-150% more shares
  - If down **<-3%**: Exit immediately (stop loss)
- **Maximum Position**: 5% of total capital

### **Step 3: Exit (Day 3)**
- **Target Exit**: Market close on Day 3
- **Alternative Exits**:
  - Take profit if +8% hit before Day 3
  - Trailing stop at +5% (trail by 2%)
  - Emergency stop at -3%

### **Risk Management**
- Maximum 15 positions simultaneously
- Maximum 2 stocks per sector
- 15% cash reserve maintained
- Daily portfolio review and rebalancing

---

## 📈 **Expected Performance**

### **Conservative Scenario**
- **Win Rate**: 60-65%
- **Average Win**: 3-5%
- **Average Loss**: -2%
- **Expected Return/Trade**: 1.5-2.5%
- **Total Trades**: 15-20 over 4 weeks
- **Expected Total Return**: **8-12%**

### **Optimistic Scenario**
- **Win Rate**: 70%+
- **Average Win**: 5-8%
- **Average Loss**: -2%
- **Expected Return/Trade**: 3-4%
- **Total Trades**: 20-25 over 4 weeks
- **Expected Total Return**: **15-20%**

### **Key Success Factors**
1. Only enter after **positive Day 0 reaction** (critical!)
2. Aggressively add to winners on Day 1
3. Cut losers quickly with -3% stop loss
4. Focus on top-ranked stocks only

---

## 🚀 **Quick Start Guide**

### **Prerequisites**
- Python 3.8+
- TWS/IB Gateway (optional, for live data)
- Required packages (see Installation)

### **Installation**
```bash
# Clone repository
cd /path/to/project

# Install dependencies
pip install -r requirements.txt

# Verify data
python main.py monitor
```

### **Running Analysis**
```bash
# Run comprehensive backtest
python scripts/analysis/comprehensive_backtester.py

# Generate stock rankings
python scripts/analysis/three_step_earnings_strategy.py

# Optimize strategy parameters
python scripts/analysis/strategy_optimizer.py
```

### **Live Trading Workflow**

#### **Daily Pre-Market (7:00-9:30 AM)**
1. Check earnings calendar for today's announcements
2. Review top-ranked stocks reporting today
3. Prepare entry orders for Day 0 close

#### **Market Hours (9:30 AM - 4:00 PM)**
1. Monitor Day 0 price reactions
2. Execute entries only if Day 0 close is positive
3. Set stop loss orders at -3%

#### **Day 1 Review (Next Trading Day)**
1. Evaluate all positions at close
2. Add to positions up >1%
3. Exit positions down >-3%

#### **Day 3 Exit**
1. Close all positions at market close
2. Record performance metrics
3. Update rankings and prepare for next trades

---

## 🏆 **Top 20 Stocks (By PEAD Score)**

Based on comprehensive 10-year analysis of 373 stocks:

| Rank | Ticker | Score | Sector | Notes |
|------|--------|-------|--------|-------|
| 1 | AIZ | 83.26 | Financial | Best overall |
| 2 | CVS | 83.13 | Healthcare | Strong momentum |
| 3 | FE | 81.32 | Utilities | Defensive |
| 4 | FFIV | 80.86 | Technology | High volatility |
| 5 | OTEX | 80.81 | Technology | Consistent |
| 6 | COR | 80.15 | Healthcare | Quality pick |
| 7 | ATGE | 79.54 | Financial | Strong fundamentals |
| 8 | EQIX | 79.20 | Technology | Data center REIT |
| 9 | ITRI | 79.17 | Technology | Momentum play |
| 10 | CW | 79.11 | Industrials | Quality + momentum |
| 11-20 | ... | ... | ... | See full report in docs/ |

*Complete rankings available in: `strategy2_analysis/optimized_strategy_metrics.csv`*

---

## 📊 **Best Performing Sectors**

1. **Utilities** (75.29 avg score) - Stable, defensive
2. **Consumer Defensive** (70.55 avg score) - Consistent
3. **Healthcare** (66.24 avg score) - Growth potential
4. **Financials** (65.12 avg score) - High volume

**⚠️ Avoid**: Energy sector (57.60 avg score) - too volatile

---

## 📚 **Documentation**

### **Strategy & Analysis**
- [Optimized Strategy Guide](docs/WINNING_STRATEGY_GUIDE.md)
- [Strategy Optimization Report](docs/reports/STRATEGY_OPTIMIZATION_REPORT.md)
- [Backtest Results](docs/BACKTEST_RESULTS_SUMMARY.md)

### **Data & Setup**
- [Data Verification Report](docs/reports/DATA_VERIFICATION_REPORT.md)
- [Quick Start Analysis](docs/guides/QUICK_START_ANALYSIS.md)
- [Competition Quick Start](docs/COMPETITION_QUICK_START.txt)

### **Technical Details**
- [Multi-Step Stage Analysis](docs/reports/MULTI_STEP_STAGE_ANALYSIS.md)
- [PEAD Analysis Complete](docs/PEAD_ANALYSIS_COMPLETE.md)

---

## 🔧 **Technical Requirements**

### **Python Packages**
```
pandas>=1.5.0
numpy>=1.23.0
yfinance>=0.2.0
ibapi>=9.81.0
requests>=2.28.0
beautifulsoup4>=4.11.0
```

### **Data Sources**
- **Historical Data**: Yahoo Finance (yfinance)
- **Real-time Data**: Interactive Brokers TWS/Gateway (optional)
- **Fundamental Data**: Finviz screener
- **Earnings Calendar**: Multiple sources aggregated

### **System Requirements**
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB for data
- **Internet**: Stable connection for real-time data

---

## ⚠️ **Risk Disclosure**

### **Key Risks**
1. **Market Risk**: Earnings can be unpredictable
2. **Execution Risk**: Slippage and timing issues
3. **Model Risk**: Historical performance doesn't guarantee future results
4. **Concentration Risk**: Limited to earnings events

### **Risk Mitigation**
- Strict position sizing (max 5% per trade)
- Stop losses on all positions (-3%)
- Diversification across sectors
- Cash reserves (15%)
- Daily risk monitoring

---

## 🎯 **Next Steps**

### **Immediate Actions**
- [ ] Review top 100 ranked stocks
- [ ] Set up earnings calendar alerts
- [ ] Prepare order templates
- [ ] Test execution system

### **Week 1 (Oct 14-20)**
- [ ] Execute first 3-5 trades
- [ ] Monitor and adjust positions
- [ ] Track performance metrics
- [ ] Refine entry criteria if needed

### **Ongoing**
- [ ] Daily pre-market preparation
- [ ] Real-time monitoring during market hours
- [ ] Day 1 position management
- [ ] Day 3 exits and performance review
- [ ] Weekly strategy review

---

## 📞 **Project Information**

**Version**: 2.0 (Optimized)  
**Last Updated**: October 15, 2025  
**Status**: Production Ready

### **Key Insights from Backtesting**
✅ **Day 1 additions are CRITICAL** (1.87% avg return vs -4.41% without)  
✅ **Positive Day 0 is MANDATORY** (66.7% win rate vs 0% for negative)  
✅ **Top-ranked stocks outperform** significantly  
✅ **Quick stop losses preserve capital** (-3% max loss vs unlimited downside)

---

## 🏆 **Let's Win This Challenge!**

With 373 stocks of complete data, an optimized three-step strategy, and systematic risk management, we're ready to compete. The key is disciplined execution and sticking to the rules, especially:

1. **Only trade top 100 ranked stocks**
2. **Only enter after positive Day 0**
3. **Add aggressively to Day 1 winners**
4. **Cut losses quickly at -3%**

**Good luck! 🚀📈**

---

*For questions or issues, refer to documentation in `docs/` or check analysis outputs in `strategy2_analysis/`*
