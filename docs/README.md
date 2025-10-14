# UMushroom Investment Challenge - PEAD Strategy System

## 🎯 Challenge Overview

**Goal:** Win UMushroom Investment Challenge Stage 1  
**Timeline:** October 14 - November 13, 2024 (4 weeks)  
**Starting Capital:** $100,000  
**Strategy:** Long-only Post-Earnings Announcement Drift (PEAD)

---

## 📊 Portfolio Structure

### **40% Stability Portfolio ($40,000)**
- **SPY:** $15,000 (S&P 500)
- **QQQ:** $10,000 (Nasdaq Tech)
- **IWM:** $8,000 (Small Cap)
- **VTI:** $4,000 (Total Market)
- **Sector ETF:** $3,000 (Rotation based on earnings themes)

**Strategy:** Buy and hold entire 4 weeks for stability

### **60% Active Trading ($60,000)**
- **Target:** 10 trades per week × 4 weeks = 40 total trades
- **Position Size:** $1,500-3,000 per trade
- **Hold Period:** 5-10 days
- **Strategy:** Long-only PEAD on earnings beats >5%

---

## 🔧 System Components

### **1. TWS API Connection** ✅
- **File:** `tws_connector.py`
- **Port:** 4002
- **Status:** Connected and tested
- **Features:** Market data, positions, account info

### **2. Earnings Calendar** ✅
- **Files:** 
  - `week1_earnings.csv` (Oct 16-17)
  - `week1_earnings_extended.csv` (Oct 16-24)
- **Total Stocks:** 72 companies
- **Focus:** NYSE/NASDAQ primary listings

### **3. PEAD Screening Engine** ✅
- **File:** `quick_screener.py`
- **Scoring:** 0-100 points based on:
  - Liquidity (30 points)
  - Volatility/Beta (25 points)
  - Market Cap (20 points)
  - Analyst Coverage (25 points)
- **Output:** Ranked opportunities with trade plans

### **4. Trading Plan** ✅
- **File:** `WEEK1_TRADING_PLAN.md`
- **Top 10 Opportunities:** Identified and ranked
- **Execution Calendar:** Day-by-day plan
- **Risk Management:** Stop losses, position sizing

---

## 🏆 Week 1 Top Opportunities

### **Tier 1 (Score 85-90):**
1. **HBAN** - Huntington Bancshares (90/100)
2. **SLB** - Schlumberger (90/100)
3. **FITB** - Fifth Third Bancorp (90/100)
4. **RF** - Regions Financial (90/100)
5. **ALLY** - Ally Financial (85/100)
6. **STT** - State Street (85/100)

### **Tier 2 (Score 70-80):**
7. **TFC** - Truist Financial (75/100)
8. **IBKR** - Interactive Brokers (75/100)
9. **HCA** - HCA Healthcare (70/100)
10. **NVT** - nVent Electric (70/100)

---

## 📅 Week 1 Execution Timeline

### **Wednesday, October 16 (Today)**
- ✅ System setup complete
- ✅ TWS connection tested
- ✅ Earnings calendar loaded
- ✅ Screening complete
- ✅ Trading plan finalized
- 🎯 **Tonight 9 PM:** IBKR earnings

### **Thursday, October 17 (Main Event)**
- **11:00 AM:** RF
- **11:30 AM:** FITB
- **12:00 PM:** AXP, SLB
- **12:30 PM:** ALLY, STT
- **2:30 PM:** HBAN, TFC

**Action:** Monitor earnings, prepare entries for Friday

### **Friday, October 18**
- **Execute:** 6-8 positions from Thursday's beats
- **Deploy:** ~$20,000 of trading capital

---

## 💰 Expected Performance

### **Week 1 Target:**
- Trades: 10
- Win Rate: 65-70%
- Weekly Return: 2-4%

### **4-Week Target:**
- Total Trades: 40
- Win Rate: 65%+
- Total Return: 15-25%
- **Goal:** Top 10 at your university

---

## ⚠️ Risk Management

### **Position Level:**
- Stop Loss: -8% (automatic)
- Target: +12%
- Max Hold: 10 days
- Position Size: 1.5-3% of capital

### **Portfolio Level:**
- Max Weekly Loss: 10% ($6,000)
- Max Concurrent Positions: 8
- Max Sector Exposure: 3 positions
- Circuit Breaker: 3 consecutive losses = reduce size 50%

---

## 📂 File Structure

```
UMushroom Investment challange/
├── README.md (this file)
├── WEEK1_TRADING_PLAN.md (detailed execution plan)
├── tws_connector.py (TWS API connection)
├── earnings_fetcher.py (earnings calendar scraper)
├── earnings_analyzer.py (comprehensive analysis)
├── quick_screener.py (fast PEAD screening)
├── ticker_list.py (comprehensive ticker database)
├── week1_earnings.csv (Oct 16-17 earnings)
├── week1_earnings_extended.csv (Oct 16-24 earnings)
└── week1_quick_screen.csv (screening results)
```

---

## 🚀 Quick Start Guide

### **1. Verify TWS Connection:**
```bash
python3 tws_connector.py
```

### **2. Run Week 1 Screening:**
```bash
python3 quick_screener.py
```

### **3. Review Trading Plan:**
```bash
cat WEEK1_TRADING_PLAN.md
```

### **4. Monitor Earnings (Thursday):**
- Watch for >5% beats
- Check guidance
- Note after-hours gaps

### **5. Execute Trades (Friday):**
- Enter positions on confirmed beats
- Set stop losses immediately
- Target 6-8 positions

---

## 📈 Success Metrics

### **Activity Points:**
- ✅ 40 trades over 4 weeks
- ✅ Daily portfolio updates
- ✅ Learning modules completed
- ✅ Webinar attendance
- ✅ Community engagement

### **Performance Points:**
- 🎯 Target: 15-25% total return
- 🎯 Rank: Top 10 at university
- 🎯 Consistency: Positive returns 3/4 weeks

### **Bonus Points:**
- Complete all challenges
- Attend special events
- Share insights

---

## 🎯 Strategy Advantages

### **Why PEAD Works:**
1. ✅ **Academically Proven:** 40+ years of research
2. ✅ **Market Inefficiency:** Prices drift after earnings
3. ✅ **High Activity:** 40 trades = maximum engagement
4. ✅ **Risk Managed:** Clear stops, diversification
5. ✅ **Timely:** Peak earnings season (Oct-Nov)

### **Why Long-Only:**
1. ✅ **Simpler:** No inverse ETF complexity
2. ✅ **Better Odds:** More beats than misses
3. ✅ **Wider Universe:** 500+ stocks vs 10-15
4. ✅ **Lower Costs:** No inverse ETF fees
5. ✅ **Cleaner Story:** Positive momentum focus

---

## 📝 Daily Workflow

### **Pre-Market (6:00-9:30 AM):**
1. Check overnight earnings
2. Review pre-market gaps
3. Confirm beats >5%
4. Set entry orders
5. Review stop losses

### **Market Hours (9:30 AM-4:00 PM):**
1. Execute planned entries
2. Set stops immediately
3. Monitor positions
4. Take profits at targets
5. Adjust trailing stops

### **After-Hours (4:00-8:00 PM):**
1. Update trading journal
2. Review P&L
3. Check upcoming earnings
4. Plan tomorrow's trades
5. Complete activities

---

## 🏆 Challenge Milestones

- [x] **Oct 14:** System setup complete
- [x] **Oct 16:** Week 1 plan finalized
- [ ] **Oct 17:** First trades executed
- [ ] **Oct 24:** Week 1 complete (10 trades)
- [ ] **Oct 31:** Week 2 complete (20 trades total)
- [ ] **Nov 7:** Week 3 complete (30 trades total)
- [ ] **Nov 13:** Stage 1 complete (40 trades, Top 10 rank)
- [ ] **Nov 20:** Finalists announced
- [ ] **Dec 5:** Final presentation (if selected)

---

## 💡 Key Insights

### **Week 1 Focus:**
- **Sector:** Financials (bank earnings season)
- **Theme:** Regional banks reporting Q3
- **Opportunity:** 8/10 top picks are financial stocks
- **Strategy:** Capitalize on sector momentum

### **Weeks 2-4 Preview:**
- **Week 2:** Tech earnings (AAPL, MSFT, GOOGL, META, AMZN)
- **Week 3:** Industrials & Consumer (CAT, HON, WMT, TGT)
- **Week 4:** Final opportunities + position closing

---

## 📞 Support & Resources

### **Tools:**
- **TWS/IB Gateway:** Port 4002
- **yfinance:** Real-time data
- **pandas:** Data analysis
- **Python 3:** System automation

### **Data Sources:**
- Interactive Brokers API
- Yahoo Finance
- Earnings calendars
- Analyst estimates

---

## ✅ System Status

- ✅ TWS Connection: **ACTIVE**
- ✅ Earnings Calendar: **LOADED**
- ✅ Screening Engine: **OPERATIONAL**
- ✅ Trading Plan: **READY**
- ✅ Risk Management: **CONFIGURED**
- ✅ Week 1 Targets: **IDENTIFIED**

**STATUS: READY TO TRADE** 🚀

---

## 🎯 Remember

> "Discipline beats conviction. Consistency beats brilliance. Risk management beats everything."

**Win Rate Target:** 65%  
**Risk/Reward:** 1:1.5  
**Position Size:** 1.5-3% max  
**Stop Loss:** -8% always  

**LET'S WIN THIS! 🏆**

---

**Last Updated:** October 16, 2024  
**Next Update:** October 17, 2024 (after first trades)


