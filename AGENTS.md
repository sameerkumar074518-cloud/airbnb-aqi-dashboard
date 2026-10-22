# Project Rules & Agent Instructions

This document governs the engineering rules, data-handling policies, and analytical standards for the **"Clean Air, Higher Rent? Airbnb Pricing and Urban Air Quality"** lab project (BISL504). All agents and contributors must adhere to these directives.

---

## 1. Missing Data Handling
- **Never silently drop rows** with missing `price`, `room_type`, or `latitude`/`longitude` during cleaning.
- Log exact counts of dropped rows and the explicit reason for exclusion (e.g., missing price, coordinates out of range, missing room type) at each preprocessing stage.

## 2. City Name Standardization & Joins
- **Always standardize city names** (strip whitespace, normalize casing to title-case/lowercase canonical forms, resolve name aliases) prior to any dataset merge.
- The Kaggle Global Air Pollution dataset contains known coverage gaps, spelling variations, and cross-country duplicate city names (e.g., Paris, Texas vs. Paris, France). Never perform blind joins purely on raw city strings. Always verify country/region associations where possible.
- **Report match/mismatch statistics explicitly** after every join (total records input, successfully matched records, unmatched records, and distinct unmatched city keys). Never allow silent join failures.

## 3. Outlier Policy
- **Do not delete price outliers**.
- Extreme values should be flagged (e.g., `is_price_outlier` boolean or percentile thresholds like 99th percentile) and/or capped (winsorized).
- Document every outlier decision and threshold choice in [`docs/decisions_log.md`](file:///d:/Projects/Data%20Visualization/docs/decisions_log.md).

## 4. Visualizations & Outputs
- **Chart Persistence**: Every visualization script must save its output figure directly to `outputs/figures/` using a clear, descriptive filename (e.g., `chart1_price_vs_aqi_scatter.png`), rather than merely displaying it inline.
- Charts should use publication-ready formatting (consistent DPI, clear axis titles, legends, and readable fonts).

## 5. Raw Data Immutability
- **Keep `/data/raw` files strictly untouched**.
- Original downloaded CSVs from Inside Airbnb and Kaggle must remain in their pristine raw state.
- All filtering, cleaning, transformations, feature engineering, and joins must happen via scripts and write exclusively to `/data/processed/`.
