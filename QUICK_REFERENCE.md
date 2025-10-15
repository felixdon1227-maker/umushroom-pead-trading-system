# UMushroom Investment Challenge - Quick Reference

## 📖 Essential Files

| File | Purpose | When to Use |
|------|---------|-------------|
| **README.md** | Quick start guide | Starting point, top stocks, quick commands |
| **PROJECT_SUMMARY.md** | Complete project overview | Understanding full system, strategy details |
| **OPTIMIZATION_COMPLETE.md** | Optimization report | See what was cleaned up and why |
| **main.py** | Entry point script | Running main operations |

## 📂 Directory Guide

```
├── config/              → System configuration
├── data/processed/      → Earnings calendar (92 events)
├── scripts/
│   ├── data_collection/ → 4 data fetching scripts
│   └── analysis/        → 11 strategy & analysis scripts
├── docs/
│   ├── reports/         → Analysis & verification reports
│   ├── strategy/        → Strategy documentation
│   └── archive/         → Historical process docs
└── results/             → Analysis outputs & rankings
```

## 🎯 Quick Commands

### View Top Stocks
```bash
cat results/strategy_analysis/optimized_strategy_metrics.csv
```

### Check Earnings Calendar
```bash
cat data/processed/earnings_final.csv
```

### Run Strategy Analysis
```bash
python scripts/analysis/three_step_earnings_strategy.py
```

### View Project Statistics
```bash
find scripts -name "*.py" -type f | wc -l  # Active scripts
find docs -name "*.md" -type f | wc -l     # Documentation files
du -sh data/ scripts/ docs/                 # Directory sizes
```

## 🏆 Top 20 Stocks (Quick View)

| Rank | Ticker | Score | Sector |
|------|--------|-------|--------|
| 1 | AIZ | 83.26 | Insurance |
| 2 | CVS | 83.13 | Healthcare |
| 3 | FE | 81.32 | Utilities |
| 4 | FFIV | 80.86 | Technology |
| 5 | OTEX | 80.81 | Technology |

*See PROJECT_SUMMARY.md for complete list*

## 📊 Key Metrics

- **Dataset**: 413 stocks, 373 with complete data
- **Timeframe**: Oct 14 - Nov 13, 2025 (4 weeks)
- **Capital**: $100,000 starting
- **Target**: 10-15% return (60-70% win rate)
- **Risk**: Max 5% per position, -10% max drawdown

## 📚 Documentation Map

| Need | File |
|------|------|
| Getting started | README.md |
| Full project details | PROJECT_SUMMARY.md |
| Strategy details | docs/strategy/FINAL_STRATEGY_COMPLETE.md |
| Competition guide | docs/WINNING_STRATEGY_GUIDE.md |
| Data verification | docs/reports/DATA_VERIFICATION_REPORT.md |
| What was optimized | OPTIMIZATION_COMPLETE.md |

## 🔧 Project Stats

- **Root files**: 4 essential files (down from 19)
- **Active scripts**: 16 (down from 28)
- **Empty directories**: 0 (cleaned 100%)
- **Project size**: 5.0 MB
- **Status**: ✅ Competition-Ready

---

**Last Updated**: October 15, 2025  
**Optimization**: Complete
