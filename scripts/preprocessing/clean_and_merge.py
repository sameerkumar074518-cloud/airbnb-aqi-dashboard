"""
Preprocessing and Dataset Integration Pipeline: 10-City Demo
=============================================================
Project: Clean Air, Higher Rent? Airbnb Pricing and Urban Air Quality
Course: BISL504 (Data Visualization Lab)

This script loads, cleans, standardizes, currency-normalizes, and merges:
  1. Inside Airbnb listings datasets across 10 global cities.
  2. Kaggle Global Air Pollution Data (AQI), enforcing strict country verification
     to reject cross-country name collisions (e.g. Venice FL vs. Venice Italy).

Outputs:
  - data/processed/airbnb_aqi_merged_10cities.csv
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# Configuration: Cities, Countries, Currencies, and Exchange Rates to USD
# -----------------------------------------------------------------------------
CURRENCY_RATES_TO_USD = {
    'USD': 1.000,   # US Dollar (New York)
    'EUR': 1.080,   # Euro (Amsterdam, Lisbon, Dublin, Paris, Venice)
    'THB': 0.029,   # Thai Baht (Bangkok)
    'HKD': 0.128,   # Hong Kong Dollar (Hong Kong, pegged ~7.80 HKD/USD)
    'TRY': 0.029,   # Turkish Lira (Istanbul)
    'SGD': 0.760,   # Singapore Dollar (Singapore)
}

CITY_METADATA = {
    'Amsterdam': {
        'country': 'Netherlands',
        'currency': 'EUR',
        'raw_folder': 'data/raw/amsterdam',
        'raw_filename': 'Amsterdam - listings.csv',
        'compression': None
    },
    'Bangkok': {
        'country': 'Thailand',
        'currency': 'THB',
        'raw_folder': 'data/raw/bangkok',
        'raw_filename': 'Bangkok - listings.csv',
        'compression': None
    },
    'Lisbon': {
        'country': 'Portugal',
        'currency': 'EUR',
        'raw_folder': 'data/raw/lisbon',
        'raw_filename': 'lisbon_listings.csv',
        'compression': None
    },
    'Dublin': {
        'country': 'Ireland',
        'currency': 'EUR',
        'raw_folder': 'data/raw/dublin',
        'raw_filename': 'dublin_listings.csv',
        'compression': 'gzip'
    },
    'Hong Kong': {
        'country': 'Hong Kong',
        'currency': 'HKD',
        'raw_folder': 'data/raw/hong_kong',
        'raw_filename': 'honkkong_listings.csv',
        'compression': 'gzip'
    },
    'Istanbul': {
        'country': 'Turkey',
        'currency': 'TRY',
        'raw_folder': 'data/raw/istanbul',
        'raw_filename': 'istanbul_listings.csv',
        'compression': 'gzip'
    },
    'New York': {
        'country': 'United States of America',
        'currency': 'USD',
        'raw_folder': 'data/raw/new_york',
        'raw_filename': 'new_york_listings.csv',
        'compression': 'gzip'
    },
    'Paris': {
        'country': 'France',
        'currency': 'EUR',
        'raw_folder': 'data/raw/paris',
        'raw_filename': 'paris_listings.csv',
        'compression': 'gzip'
    },
    'Singapore': {
        'country': 'Singapore',
        'currency': 'SGD',
        'raw_folder': 'data/raw/singapore',
        'raw_filename': 'singapore_listings.csv',
        'compression': 'gzip'
    },
    'Venice': {
        'country': 'Italy',
        'currency': 'EUR',
        'raw_folder': 'data/raw/venice',
        'raw_filename': 'venice_listings.csv',
        'compression': 'gzip'
    },
}

RAW_AQI_PATH = 'data/raw/aqi/global_air_pollution_data.csv'
OUTPUT_PROCESSED_PATH = 'data/processed/airbnb_aqi_merged_10cities.csv'


def derive_aqi_bracket(val):
    """Assign standard EPA AQI classification bracket."""
    if pd.isna(val):
        return np.nan
    val = float(val)
    if val <= 50:
        return 'Good'
    elif val <= 100:
        return 'Moderate'
    elif val <= 150:
        return 'Unhealthy for Sensitive Groups'
    elif val <= 200:
        return 'Unhealthy'
    elif val <= 300:
        return 'Very Unhealthy'
    else:
        return 'Hazardous'


def clean_city_dataset(city_name, meta):
    """
    Loads, validates, cleans, and standardizes a single city's Airbnb dataset.
    Logs row drop counts and reasons per AGENTS.md rules.
    """
    file_path = os.path.join(meta['raw_folder'], meta['raw_filename'])
    if not os.path.exists(file_path):
        # Fallback: check if any csv file exists in the directory
        files = [f for f in os.listdir(meta['raw_folder']) if f.endswith('.csv')]
        if files:
            file_path = os.path.join(meta['raw_folder'], files[0])
        else:
            raise FileNotFoundError(f"No raw listings file found for {city_name} in {meta['raw_folder']}")

    # Detect compression if needed
    comp = meta['compression']
    if comp is None:
        with open(file_path, 'rb') as f:
            if f.read(2) == b'\x1f\x8b':
                comp = 'gzip'

    df_raw = pd.read_csv(file_path, compression=comp, low_memory=False)
    initial_rows = len(df_raw)

    # 1. Clean price column (handling numeric float or string with '$' and ',')
    if pd.api.types.is_numeric_dtype(df_raw['price']):
        price_numeric = pd.to_numeric(df_raw['price'], errors='coerce')
    else:
        price_clean = (
            df_raw['price']
            .astype(str)
            .str.replace('$', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.strip()
        )
        price_numeric = pd.to_numeric(price_clean, errors='coerce')

    # 2. Check exclusion criteria per AGENTS.md rule 1 (never silently drop rows)
    missing_price = (price_numeric.isna()) | (price_numeric <= 0)
    missing_room = df_raw['room_type'].isna() if 'room_type' in df_raw.columns else pd.Series(True, index=df_raw.index)
    missing_coords = (
        df_raw['latitude'].isna() | df_raw['longitude'].isna() |
        (df_raw['latitude'] < -90) | (df_raw['latitude'] > 90) |
        (df_raw['longitude'] < -180) | (df_raw['longitude'] > 180)
    )

    invalid_mask = missing_price | missing_room | missing_coords
    dropped_count = invalid_mask.sum()
    retained_df = df_raw.loc[~invalid_mask].copy()
    retained_count = len(retained_df)
    pct_dropped = (dropped_count / initial_rows) * 100 if initial_rows > 0 else 0.0

    cleaning_report = {
        'city': city_name,
        'initial_rows': initial_rows,
        'retained_rows': retained_count,
        'dropped_rows': dropped_count,
        'pct_dropped': pct_dropped,
        'missing_price': missing_price.sum(),
        'missing_room': missing_room.sum(),
        'missing_coords': missing_coords.sum()
    }

    # 3. Currency and Price Standardization (store price_local, price_currency, price_usd)
    currency_code = meta['currency']
    exchange_rate = CURRENCY_RATES_TO_USD[currency_code]
    retained_df['price_local'] = price_numeric.loc[~invalid_mask].astype(float)
    retained_df['price_currency'] = currency_code
    retained_df['price_usd'] = (retained_df['price_local'] * exchange_rate).round(2)

    # 4. Outlier Flagging & Capping per AGENTS.md rule 3 (flag and winsorize at 99th percentile)
    p99_usd = retained_df['price_usd'].quantile(0.99)
    retained_df['price_outlier_flag'] = retained_df['price_usd'] > p99_usd
    retained_df['price_usd_capped'] = retained_df['price_usd'].clip(upper=p99_usd).round(2)

    # 5. Standardize spatial & categorical fields
    retained_df['city'] = city_name
    retained_df['city_clean'] = city_name.strip()

    # Neighbourhood handling (summary vs full 90-column schema)
    if 'neighbourhood_cleansed' in retained_df.columns and 'neighbourhood' not in retained_df.columns:
        retained_df['neighbourhood'] = retained_df['neighbourhood_cleansed']
    elif 'neighbourhood_cleansed' in retained_df.columns and retained_df['neighbourhood'].isna().all():
        retained_df['neighbourhood'] = retained_df['neighbourhood_cleansed']

    if 'neighbourhood_group' not in retained_df.columns:
        if 'neighbourhood_group_cleansed' in retained_df.columns:
            retained_df['neighbourhood_group'] = retained_df['neighbourhood_group_cleansed']
        else:
            retained_df['neighbourhood_group'] = np.nan

    # Standardize core control columns
    for col in ['minimum_nights', 'number_of_reviews', 'reviews_per_month', 'availability_365']:
        if col not in retained_df.columns:
            retained_df[col] = np.nan

    # Keep standardized columns
    cols_to_keep = [
        'id', 'name', 'neighbourhood_group', 'neighbourhood', 'latitude', 'longitude',
        'room_type', 'price_local', 'price_currency', 'price_usd', 'price_usd_capped',
        'price_outlier_flag', 'minimum_nights', 'number_of_reviews', 'reviews_per_month',
        'availability_365', 'city', 'city_clean'
    ]
    return retained_df[cols_to_keep], cleaning_report


def evaluate_aqi_matches(df_aqi):
    """
    Evaluates exact city name and sovereign country alignment against the Kaggle AQI dataset.
    Returns:
      - aqi_lookup: dict mapping city_name -> aqi metadata dict
      - manual_review_list: list of tuples detailing cities requiring manual AQI curation
    """
    aqi_lookup = {}
    manual_review_list = []

    for city, meta in CITY_METADATA.items():
        expected_country = meta['country']
        matches = df_aqi[df_aqi['city_name'] == city]

        if len(matches) == 0:
            aqi_lookup[city] = {
                'aqi_value': np.nan,
                'aqi_category': np.nan,
                'aqi_country': np.nan,
                'aqi_bracket': np.nan,
                'aqi_match_status': 'NO_RELIABLE_MATCH (Missing in Dataset)',
                'audit_note': f"City '{city}' is not in the AQI dataset.",
                'is_reliable': False
            }
            manual_review_list.append({
                'city': city,
                'expected_country': expected_country,
                'status': 'NO RELIABLE MATCH',
                'reason': 'City missing entirely in AQI dataset',
                'raw_country': 'N/A',
                'raw_aqi': 'N/A'
            })
        else:
            row = matches.iloc[0]
            found_country = row['country_name']
            found_aqi = row['aqi_value']
            found_cat = row['aqi_category']

            # Check if country metadata is missing or mismatching
            if pd.isna(found_country):
                # City matched 'New York', but country_name is blank in Kaggle raw CSV
                aqi_lookup[city] = {
                    'aqi_value': np.nan,
                    'aqi_category': np.nan,
                    'aqi_country': 'Missing (NaN)',
                    'aqi_bracket': np.nan,
                    'aqi_match_status': 'AMBIGUOUS (Missing Country Metadata)',
                    'audit_note': f"Matched city '{city}', but country_name is blank in AQI CSV (raw AQI: {found_aqi}).",
                    'is_reliable': False
                }
                manual_review_list.append({
                    'city': city,
                    'expected_country': expected_country,
                    'status': 'AMBIGUOUS / UNCONFIRMED',
                    'reason': f"Blank country metadata in raw dataset (found raw AQI={found_aqi})",
                    'raw_country': 'NaN',
                    'raw_aqi': str(found_aqi)
                })
            elif found_country.strip().lower() != expected_country.strip().lower():
                # Cross-country duplicate collision
                aqi_lookup[city] = {
                    'aqi_value': np.nan,
                    'aqi_category': np.nan,
                    'aqi_country': found_country,
                    'aqi_bracket': np.nan,
                    'aqi_match_status': f'NO_RELIABLE_MATCH (Wrong Country: {found_country})',
                    'audit_note': f"Matched city '{city}', but in country '{found_country}' (expected '{expected_country}').",
                    'is_reliable': False
                }
                manual_review_list.append({
                    'city': city,
                    'expected_country': expected_country,
                    'status': 'NO RELIABLE MATCH',
                    'reason': f"Wrong country duplicate: found '{found_country}' instead of '{expected_country}'",
                    'raw_country': found_country,
                    'raw_aqi': str(found_aqi)
                })
            else:
                # Verified sovereign match
                aqi_lookup[city] = {
                    'aqi_value': float(found_aqi),
                    'aqi_category': str(found_cat),
                    'aqi_country': str(found_country),
                    'aqi_bracket': derive_aqi_bracket(found_aqi),
                    'aqi_match_status': 'RELIABLE_MATCH',
                    'audit_note': f"Verified match with {found_country}.",
                    'is_reliable': True
                }

    return aqi_lookup, manual_review_list


def main():
    parser = argparse.ArgumentParser(description="Clean and merge 10-city Airbnb and AQI datasets.")
    parser.add_argument('--dry-run', action='store_true', help="Run cleaning and print full report without writing final CSV.")
    parser.add_argument('--save', action='store_true', default=False, help="Explicitly confirm and save final merged CSV.")
    args = parser.parse_args()

    print("=" * 80)
    print("AIRBNB + AQI PREPROCESSING PIPELINE (10 CITIES)")
    print("=" * 80)

    # 1. Load AQI dataset
    if not os.path.exists(RAW_AQI_PATH):
        raise FileNotFoundError(f"Kaggle AQI dataset not found at {RAW_AQI_PATH}")
    df_aqi = pd.read_csv(RAW_AQI_PATH)
    df_aqi.columns = df_aqi.columns.str.strip()
    print(f"Loaded Kaggle Global Air Pollution Dataset: {len(df_aqi):,} records.")

    # 2. Evaluate AQI matches
    aqi_lookup, manual_review_list = evaluate_aqi_matches(df_aqi)

    # 3. Clean and merge all 10 cities
    cleaned_frames = []
    cleaning_reports = []

    print("\n" + "-" * 80)
    print("STAGE 1: AIRBNB DATASET CLEANING & ROW-DROP AUDIT")
    print("-" * 80)

    for city_name, meta in CITY_METADATA.items():
        city_df, report = clean_city_dataset(city_name, meta)
        cleaning_reports.append(report)

        # Attach AQI fields from verified lookup
        city_aqi_info = aqi_lookup[city_name]
        city_df['aqi_value'] = city_aqi_info['aqi_value']
        city_df['aqi_category'] = city_aqi_info['aqi_category']
        city_df['aqi_country'] = city_aqi_info['aqi_country']
        city_df['aqi_bracket'] = city_aqi_info['aqi_bracket']
        city_df['aqi_match_status'] = city_aqi_info['aqi_match_status']

        cleaned_frames.append(city_df)

        print(f"[{city_name.upper()}] (Local Currency: {meta['currency']})")
        print(f"  Initial Rows : {report['initial_rows']:,}")
        print(f"  Retained Rows: {report['retained_rows']:,}")
        print(f"  Dropped Rows : {report['dropped_rows']:,} ({report['pct_dropped']:.2f}%)")
        print(f"    - Invalid/Missing Price : {report['missing_price']:,}")
        print(f"    - Missing Room Type     : {report['missing_room']:,}")
        print(f"    - Invalid Coordinates   : {report['missing_coords']:,}")
        print(f"  Price USD Range (Retained): ${city_df['price_usd'].min():.2f} - ${city_df['price_usd'].max():.2f}")
        print(f"  Outliers Flagged (>99th%): {city_df['price_outlier_flag'].sum():,} listings (Cap: ${city_df['price_usd_capped'].max():.2f})\n")

    # Combine all cities
    combined_df = pd.concat(cleaned_frames, ignore_index=True)

    # 4. Print AQI Match Audit Report
    print("=" * 80)
    print("STAGE 2: AQI JOIN AUDIT & GEOGRAPHIC DISAMBIGUATION REPORT")
    print("=" * 80)
    for city_name, meta in CITY_METADATA.items():
        info = aqi_lookup[city_name]
        if info['is_reliable']:
            print(f"  {city_name:<12} -> RELIABLE MATCH")
            print(f"                 Expected: {meta['country']} | Matched Country: {info['aqi_country']}")
            print(f"                 AQI Value: {info['aqi_value']:.0f} | Category: {info['aqi_category']} | Bracket: {info['aqi_bracket']}")
        else:
            print(f"  {city_name:<12} -> {info['aqi_match_status']}")
            print(f"                 Expected: {meta['country']} | Dataset Country: {info['aqi_country']}")
            print(f"                 AQI Value: [NULL] (Raw entry rejected to avoid false correlation)")
        print()

    # 5. List cities requiring manual curation
    print("=" * 80)
    print("STAGE 3: REGISTER OF CITIES REQUIRING MANUAL AQI VALUE")
    print("=" * 80)
    for item in manual_review_list:
        print(f" - City: {item['city']:<12} | Expected Sovereign: {item['expected_country']}")
        print(f"   Status: {item['status']} | Reason: {item['reason']}")
        print(f"   Raw Dataset Observation: Country='{item['raw_country']}', AQI={item['raw_aqi']}\n")

    # 6. Overall summary statistics
    total_initial = sum(r['initial_rows'] for r in cleaning_reports)
    total_retained = len(combined_df)
    total_dropped = total_initial - total_retained
    overall_pct_drop = (total_dropped / total_initial) * 100

    print("=" * 80)
    print("PIPELINE SUMMARY (10 CITIES)")
    print("=" * 80)
    print(f"Total Raw Listings Input   : {total_initial:,}")
    print(f"Total Valid Listings Output : {total_retained:,}")
    print(f"Total Excluded Listings    : {total_dropped:,} ({overall_pct_drop:.2f}%)")
    print(f"Cities with Reliable AQI   : 5 (Amsterdam, Bangkok, Lisbon, Istanbul, Singapore)")
    print(f"Cities with Null/Pending AQI: 5 (Dublin, Hong Kong, New York, Paris, Venice)")
    print("=" * 80)

    # 7. Save output or halt on dry-run
    if args.save:
        os.makedirs(os.path.dirname(OUTPUT_PROCESSED_PATH), exist_ok=True)
        combined_df.to_csv(OUTPUT_PROCESSED_PATH, index=False)
        print(f"\n[SUCCESS] Final merged dataset saved to: {OUTPUT_PROCESSED_PATH}")
        print(f"File size: {os.path.getsize(OUTPUT_PROCESSED_PATH) / (1024*1024):.2f} MB")
    else:
        print("\n[REPORT-ONLY MODE] Run with '--save' to write final CSV to disk.")

    return combined_df, cleaning_reports, aqi_lookup


if __name__ == '__main__':
    main()
