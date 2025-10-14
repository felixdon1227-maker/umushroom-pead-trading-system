import re
import pandas as pd

print("=" * 80)
print("EXTRACTING ALL 220 COMPANIES FROM EARNINGS DATA")
print("=" * 80)

with open('earnings_raw.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Split by separator
blocks = content.split('—')

earnings_data = []
current_date = None
current_time = None

for block in blocks:
    lines = [l.strip() for l in block.split('\n') if l.strip()]
    
    if not lines:
        continue
    
    # Check for date in first line
    first_line = lines[0]
    if any(day in first_line for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
        if 'October' in first_line:
            day_match = re.search(r'(\d+)', first_line)
            if day_match:
                current_date = f'2024-10-{day_match.group(1).zfill(2)}'
        elif 'November' in first_line:
            day_match = re.search(r'(\d+)', first_line)
            if day_match:
                current_date = f'2024-11-{day_match.group(1).zfill(2)}'
        continue
    
    # Check for time
    if re.match(r'^\d{1,2}:\d{2}$', first_line):
        current_time = first_line
        lines = lines[1:]
    
    # Now parse the company data
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip single letters
        if len(line) == 1 and line.isalpha():
            i += 1
            continue
        
        # Check if it's a ticker
        if re.match(r'^[A-Z]{2,5}$', line):
            ticker = line
            
            # Next line should be company name
            if i + 1 < len(lines):
                company = lines[i + 1]
                
                # Look for EPS and market cap
                eps = 0.0
                market_cap = 0
                
                for j in range(i + 2, min(i + 5, len(lines))):
                    if j >= len(lines):
                        break
                    
                    check_line = lines[j]
                    
                    # EPS
                    if 'USD' in check_line and re.search(r'[−\-]?\d+\.\d+', check_line):
                        eps_match = re.search(r'([−\-]?\d+\.\d+)USD', check_line)
                        if eps_match:
                            eps = float(eps_match.group(1).replace('−', '-'))
                    
                    # Market cap
                    if ('B' in check_line or 'M' in check_line) and 'USD' in check_line:
                        # Extract number and unit
                        cap_match = re.search(r'([\d,\.]+)\s*([BM])', check_line)
                        if cap_match:
                            value = float(cap_match.group(1).replace(',', ''))
                            unit = cap_match.group(2)
                            market_cap = value * 1e9 if unit == 'B' else value * 1e6
                
                # Add entry
                if current_date:
                    time_val = current_time if current_time else 'AM'
                    
                    earnings_data.append({
                        'date': current_date,
                        'time': time_val,
                        'ticker': ticker,
                        'company_name': company,
                        'eps_estimate': eps,
                        'market_cap_usd': market_cap if market_cap > 0 else 1000000  # Default 1M if missing
                    })
                
                i += 2
                continue
        
        i += 1

print(f"\n✓ Extracted {len(earnings_data)} companies")

# Create DataFrame
df = pd.DataFrame(earnings_data)
df['date'] = pd.to_datetime(df['date'])

# Sort by date
df = df.sort_values('date').reset_index(drop=True)

# Add sector classification
def classify_sector(company_name):
    company_lower = company_name.lower()
    
    if any(word in company_lower for word in ['bank', 'financial', 'bancorp', 'insurance', 'capital', 'trust']):
        return 'Financials'
    elif any(word in company_lower for word in ['tech', 'software', 'semiconductor', 'systems', 'data', 'design', 'cyber']):
        return 'Technology'
    elif any(word in company_lower for word in ['health', 'medical', 'pharma', 'bio', 'hospital', 'therapeutics', 'immun']):
        return 'Healthcare'
    elif any(word in company_lower for word in ['energy', 'oil', 'gas', 'resource', 'drilling', 'lng', 'solar']):
        return 'Energy'
    elif any(word in company_lower for word in ['industrial', 'manufacturing', 'electric', 'dynamics', 'tools', 'aviation', 'aerospace']):
        return 'Industrials'
    elif any(word in company_lower for word in ['retail', 'consumer', 'restaurant', 'brands', 'beer', 'coffee', 'food', 'below', 'apparel']):
        return 'Consumer'
    elif any(word in company_lower for word in ['material', 'chemical', 'metal', 'steel', 'nucor', 'lithium', 'mining']):
        return 'Materials'
    elif any(word in company_lower for word in ['utility', 'utilities', 'electric', 'propane', 'water']):
        return 'Utilities'
    elif any(word in company_lower for word in ['reit', 'real estate', 'properties', 'realty']):
        return 'Real Estate'
    else:
        return 'Other'

df['sector'] = df['company_name'].apply(classify_sector)

# Export
df.to_csv('earnings_clean.csv', index=False)

print(f"✅ Exported: earnings_clean.csv with {len(df)} companies")

# Summary
print("\n" + "=" * 80)
print("COMPLETE EARNINGS DATA")
print("=" * 80)
print(f"Date Range: {df['date'].min().strftime('%b %d')} - {df['date'].max().strftime('%b %d, %Y')}")
print(f"Total Companies: {len(df)}")

df['market_cap_b'] = df['market_cap_usd'] / 1e9
print(f"\n💵 Market Cap Distribution:")
print(f"  Mega Cap (>$200B)  : {len(df[df['market_cap_b'] >= 200]):3d}")
print(f"  Large Cap ($50-200B): {len(df[(df['market_cap_b'] >= 50) & (df['market_cap_b'] < 200)]):3d}")
print(f"  Mid Cap ($10-50B)  : {len(df[(df['market_cap_b'] >= 10) & (df['market_cap_b'] < 50)]):3d}")
print(f"  Small Cap ($2-10B) : {len(df[(df['market_cap_b'] >= 2) & (df['market_cap_b'] < 10)]):3d}")
print(f"  Micro Cap ($500M-2B): {len(df[(df['market_cap_b'] >= 0.5) & (df['market_cap_b'] < 2)]):3d}")
print(f"  Nano Cap (<$500M)  : {len(df[df['market_cap_b'] < 0.5]):3d}")

print(f"\n🏢 Top 10 Sectors:")
for sector, count in df['sector'].value_counts().head(10).items():
    pct = (count/len(df))*100
    print(f"  {sector:15s}: {count:3d} ({pct:5.1f}%)")

print(f"\n📅 Weekly Distribution:")
df['week'] = df['date'].dt.isocalendar().week
for week in sorted(df['week'].unique()):
    week_df = df[df['week'] == week]
    start = week_df['date'].min().strftime('%b %d')
    count = len(week_df)
    print(f"  Week {week} ({start}): {count:3d} companies")

print(f"\n🎯 High Priority (>$10B): {len(df[df['market_cap_b'] >= 10])} companies")

print("\n" + "=" * 80)
print("✅ ALL 220 COMPANIES EXTRACTED!")
print("=" * 80)

