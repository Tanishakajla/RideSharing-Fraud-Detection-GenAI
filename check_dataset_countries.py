import pandas as pd
import os
import sys
p = 'rideshare_fraud_data.csv'
if not os.path.exists(p):
    print('MISSING_FILE')
    sys.exit(1)
full = pd.read_csv(p)
print('rows,cols', full.shape)
print('\ncolumns:\n', list(full.columns))
# Detect likely country columns
candidates = [c for c in full.columns if 'country' in c.lower() or 'iso' in c.lower() or 'nation' in c.lower()]
print('\ncountry-like columns detected:', candidates)
for c in candidates:
    uniq = full[c].dropna().unique()
    print(f"\nColumn: {c}")
    print('unique_count:', len(uniq))
    print('sample_values:', list(uniq)[:20])
# If no explicit country column, try to infer from city/region or from location columns
if not candidates:
    city_cols = [c for c in full.columns if 'city' in c.lower() or 'region' in c.lower() or 'state' in c.lower()]
    print('\ncity/region-like columns found:', city_cols)
    if city_cols:
        for c in city_cols:
            print(f"unique {c}:", full[c].nunique())
    # Check for latitude/longitude
    latlon = [c for c in full.columns if c.lower() in ('latitude','longitude','lat','lon')]
    print('\nlat/lon columns:', latlon)
print('\nDone')
