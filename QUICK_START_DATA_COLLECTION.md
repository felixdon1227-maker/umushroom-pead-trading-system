# 🚀 QUICK START - TWS Data Collection

## Prerequisites

1. **TWS/IB Gateway Running**
   - Start TWS or IB Gateway
   - Enable API in settings (File → Global Configuration → API → Settings)
   - Set port to 4002
   - Allow connections from localhost

2. **Python Environment**
   ```bash
   pip install ibapi yfinance pandas numpy
   ```

## Quick Start

### Option 1: One-Command Collection
```bash
python run_tws_data_collection.py
```

### Option 2: Step-by-Step Collection
```bash
# 1. Check TWS connection
python -c "from ibapi.client import EClient; print('TWS API available')"

# 2. Run data collection
python scripts/data_collection/tws_comprehensive_data_collector.py

# 3. Verify data
python scripts/data_collection/data_verification_system.py
```

## What Gets Collected

### For Each of 413 Stocks:
- ✅ **10 years daily data** (via TWS API)
- ✅ **30-minute data** for 14 days around each earnings event
- ✅ **Current fundamentals** (via yfinance)
- ✅ **Historical earnings data** (via yfinance)

### Data Structure:
```
data/all_stocks_complete/
├── AAPL/
│   ├── AAPL_daily_10years_tws.csv
│   ├── AAPL_30min_earnings_tws.csv
│   ├── AAPL_fundamentals.json
│   └── AAPL_earnings_history.json
├── MSFT/
│   └── ...
└── ...
```

## Monitoring Progress

### Real-time Updates:
- Progress displayed in console
- Detailed logs in `logs/` directory
- Success/failure rates tracked

### Log Files:
- `logs/tws_orchestrator_*.log` - Master orchestrator
- `logs/tws_collector_*.log` - Individual collectors
- `logs/data_verification_*.log` - Data verification

## Expected Performance

- **Duration**: 2-4 hours for all 413 stocks
- **Success Rate**: 95%+ (TWS API is very reliable)
- **Data Points**: ~1.5M daily bars + ~500K intraday bars
- **Storage**: ~500MB total

## Troubleshooting

### TWS Connection Issues:
```bash
# Check if TWS is running
netstat -an | grep 4002

# Test connection
python -c "
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
client = EClient(EWrapper())
client.connect('127.0.0.1', 4002, 9999)
print('Connected successfully')
client.disconnect()
"
```

### Common Issues:
1. **"Cannot connect to TWS"**
   - Ensure TWS is running
   - Check API is enabled
   - Verify port 4002

2. **"No data received"**
   - Check market hours
   - Verify ticker symbols
   - Check TWS data subscriptions

3. **"Rate limit exceeded"**
   - Script includes rate limiting
   - TWS has built-in limits
   - Wait and retry

## Data Verification

After collection, verify data quality:
```bash
python scripts/data_collection/data_verification_system.py
```

This will:
- Check all files exist
- Validate data completeness
- Report missing data
- Generate quality metrics

## Next Steps

Once data collection is complete:

1. **Run Analysis**:
   ```bash
   python scripts/analysis/three_step_earnings_strategy.py
   ```

2. **Backtest Strategies**:
   ```bash
   python scripts/analysis/comprehensive_backtester.py
   ```

3. **Generate Rankings**:
   ```bash
   python scripts/analysis/final_comprehensive_analysis.py
   ```

## Support

- Check logs in `logs/` directory
- Review error messages in console
- Ensure TWS API is properly configured
- Verify all 413 stocks are in `data/processed/earnings_final.csv`

---

**Ready to collect data for all 413 stocks using TWS API! 🚀**
