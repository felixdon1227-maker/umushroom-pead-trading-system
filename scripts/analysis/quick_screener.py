import pandas as pd
import yfinance as yf
from datetime import datetime

def quick_screen(csv_file, top_n=10):
    """Quick screening of earnings opportunities"""
    
    print("=" * 100)
    print("QUICK PEAD SCREENING - WEEK 1 EXTENDED")
    print("=" * 100)
    
    df = pd.read_csv(csv_file)
    
    # Focus on stocks with market cap > $1B for better liquidity
    df_filtered = df[df['market_cap_usd'] >= 1e9].copy()
    
    print(f"\nTotal stocks: {len(df)}")
    print(f"Stocks >$1B market cap: {len(df_filtered)}")
    
    # Priority stocks to analyze (large cap, high profile)
    priority_tickers = ['AXP', 'PG', 'HCA', 'GD', 'ITW', 'SLB', 'RF', 'FITB', 'TFC', 
                       'HBAN', 'STT', 'CMA', 'ALLY', 'BAH', 'NVT', 'IBKR', 'WEX', 'PIPR']
    
    results = []
    
    print(f"\n🔍 Analyzing {len(priority_tickers)} high-priority stocks...")
    print("-" * 100)
    
    for ticker in priority_tickers:
        stock_row = df_filtered[df_filtered['ticker'] == ticker]
        
        if stock_row.empty:
            continue
            
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            current_price = info.get('currentPrice', 0)
            beta = info.get('beta', 0)
            volume = info.get('averageVolume', 0)
            market_cap = info.get('marketCap', 0)
            target = info.get('targetMeanPrice', 0)
            analysts = info.get('numberOfAnalystOpinions', 0)
            
            upside = ((target - current_price) / current_price * 100) if target > 0 else 0
            
            # Quick score calculation
            score = 0
            
            # Liquidity (30 points)
            if volume > 5e6:
                score += 30
            elif volume > 2e6:
                score += 20
            elif volume > 1e6:
                score += 15
            
            # Volatility (25 points)
            if beta > 1.3:
                score += 25
            elif beta > 1.1:
                score += 20
            elif beta > 0.9:
                score += 15
            
            # Market cap (20 points)
            if 10e9 <= market_cap <= 100e9:
                score += 20
            elif 5e9 <= market_cap <= 200e9:
                score += 15
            elif market_cap > 1e9:
                score += 10
            
            # Analyst support (25 points)
            if analysts >= 10 and upside > 10:
                score += 25
            elif analysts >= 5 and upside > 5:
                score += 15
            elif analysts >= 3:
                score += 10
            
            row_data = stock_row.iloc[0]
            
            result = {
                'ticker': ticker,
                'company': row_data['company_name'],
                'earnings_date': row_data['date'],
                'time': row_data['time'],
                'sector': row_data['sector'],
                'score': score,
                'price': current_price,
                'market_cap_b': market_cap / 1e9,
                'beta': beta,
                'volume_m': volume / 1e6,
                'target': target,
                'upside': upside,
                'analysts': analysts
            }
            
            results.append(result)
            
            print(f"✓ {ticker:6s} | Score: {score:2.0f} | ${current_price:7.2f} | β:{beta:4.2f} | Vol:{volume/1e6:5.1f}M | Cap:${market_cap/1e9:5.1f}B | Up:{upside:5.1f}%")
            
        except Exception as e:
            print(f"✗ {ticker:6s} | Error: {str(e)[:50]}")
            continue
    
    # Sort by score
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values('score', ascending=False)
    
    print("\n" + "=" * 100)
    print(f"📊 TOP {top_n} PEAD OPPORTUNITIES")
    print("=" * 100)
    
    for idx, row in df_results.head(top_n).iterrows():
        print(f"\n{idx+1}. {row['ticker']} - {row['company']}")
        print(f"   📅 Earnings: {row['earnings_date']} at {row['time']}")
        print(f"   🎯 Score: {row['score']:.0f}/100")
        print(f"   💰 Price: ${row['price']:.2f} → Target: ${row['target']:.2f} ({row['upside']:.1f}% upside)")
        print(f"   📊 Market Cap: ${row['market_cap_b']:.2f}B | Beta: {row['beta']:.2f} | Volume: {row['volume_m']:.1f}M")
        print(f"   🏢 Sector: {row['sector']} | Analysts: {row['analysts']}")
        
        # Position sizing
        if row['market_cap_b'] > 50:
            pos_size = 3000
        elif row['market_cap_b'] > 10:
            pos_size = 2500
        else:
            pos_size = 2000
        
        shares = int(pos_size / row['price'])
        stop = row['price'] * 0.92
        target_price = row['price'] * 1.12
        
        print(f"   📈 TRADE PLAN:")
        print(f"      • Position: ${pos_size} (~{shares} shares)")
        print(f"      • Entry: After earnings if beat >5%")
        print(f"      • Stop Loss: ${stop:.2f} (-8%)")
        print(f"      • Target: ${target_price:.2f} (+12%)")
        print(f"      • Risk/Reward: 1:1.5")
    
    # Export
    df_results.to_csv('week1_quick_screen.csv', index=False)
    print(f"\n✓ Results exported to: week1_quick_screen.csv")
    
    # Summary by sector
    print("\n" + "=" * 100)
    print("📈 SECTOR BREAKDOWN")
    print("=" * 100)
    sector_summary = df_results.groupby('sector').agg({
        'score': ['count', 'mean'],
        'upside': 'mean',
        'beta': 'mean'
    }).round(2)
    print(sector_summary)
    
    return df_results

if __name__ == "__main__":
    results = quick_screen('week1_earnings_extended.csv', top_n=10)
    
    print("\n" + "=" * 100)
    print("✅ SCREENING COMPLETE")
    print("=" * 100)
    print("\nNEXT STEPS:")
    print("1. Monitor these stocks for earnings releases")
    print("2. Wait for >5% earnings beat confirmation")
    print("3. Enter positions day after earnings")
    print("4. Set stop losses immediately")
    print("5. Target 5-10 day hold for drift capture")
    print("\n" + "=" * 100)


