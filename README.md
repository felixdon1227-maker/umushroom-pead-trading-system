# UMushroom Investment Challenge - PEAD Trading System

A comprehensive system for analyzing Post-Earnings Announcement Drift (PEAD) to identify optimal trading opportunities.

## 🎯 Project Overview

**Goal**: Win the UMushroom Investment Challenge with $100,000 starting capital over 4 weeks (Oct 14 - Nov 13, 2025)

**Strategy**: 
- 40% in diversified ETFs (stability)
- 60% in PEAD trades (10 trades/week)
- Two strategies: Pre-earnings momentum & Post-earnings drift recovery

## 📁 Project Structure

```
├── main.py                          # Main entry point
├── config/
│   └── settings.py                  # Configuration settings
├── data/
│   ├── raw/                         # Raw data files
│   ├── processed/                   # Cleaned/processed data
│   │   ├── earnings_final.csv       # Final stock universe (104 stocks)
│   │   └── historical_data/         # 10 years of price/earnings data
│   └── exclusions/                  # Exclusion lists
├── scripts/
│   ├── data_collection/             # Data fetching scripts
│   ├── analysis/                    # Analysis and screening
│   └── monitoring/                  # Progress monitoring
├── docs/
│   ├── plans/                       # Project plans and documentation
│   └── reports/                     # Analysis reports
└── logs/                           # System logs
```

## 🚀 Quick Start

### 1. Data Collection
```bash
python main.py collect-data
```

### 2. Monitor Progress
```bash
python main.py monitor
```

### 3. Quick Screening
```bash
python main.py screen
```

## 📊 Current Status

- **Stock Universe**: 92 stocks (>= $1B market cap, all exclusions applied)
- **Historical Data**: 92/92 stocks collected (100% complete) ✅
- **Analysis**: Complete - 10 years of PEAD data analyzed
- **Ready**: Top 90 stocks identified for trading

## 🎯 Trading Strategies

### Strategy 1: Pre-Earnings Momentum
- **Entry**: Day -1 (close)
- **Exit**: Day +1 (close)
- **Goal**: Capture immediate earnings reaction
- **Allocation**: 60% of active capital

### Strategy 2: Post-Earnings Drift Recovery
- **Entry**: Day -1 (close)
- **Exit**: Day +7 (close)
- **Goal**: Capture drift after initial negative reaction
- **Allocation**: 40% of active capital

## 📈 Success Metrics

- **Target**: >60% historical win rate
- **Trades**: 10 per week (40 total)
- **Risk**: Max 5% per trade, 15% max drawdown
- **Timeline**: Week 1 trading signals by Oct 17

## 🔧 Requirements

- Python 3.8+
- TWS/IB Gateway running on port 4002
- Required packages: `yfinance`, `pandas`, `numpy`, `ibapi`

## 📚 Documentation

- [Master Plan](docs/plans/master_plan.md)
- [Data Collection Plan](docs/plans/data_collection_plan.md)
- [Trading Plan](docs/plans/trading_plan.md)

## 🎯 Next Steps

1. Complete historical data collection (18 min remaining)
2. Start background agent data enrichment
3. Begin performance analysis
4. Generate Week 1 trading signals

---

**Last Updated**: October 14, 2025  
**Status**: Data collection in progress, on track for Week 1 trading

