# Decisions Log

A running audit log documenting technical choices, architectural decisions, data adjustments, and resolution rationales.

---

## Decision 001: City Name Matching & Disambiguation Strategy
- **Date:** 2026-09-24
- **Context:** The Kaggle Global Air Pollution dataset has known naming discrepancies and collisions (e.g. duplicate city names across multiple countries like "Paris" in France vs. USA, or regional variations like "New York City" vs. "New York").
- **Decision:** Do not perform blind joins on `city` alone. Use a lookup mapping dictionary that pairs canonical city names with expected country keys (e.g., `('Paris', 'France')`, `('New York', 'United States of America')`). Standardize text casing and strip whitespace. Any unmatched city during the merge must be logged explicitly with unmatched counts.
- **Impact:** Prevents incorrect joins and guarantees data fidelity across all 10 Phase 1 cities.

---

## Decision 002: Price Outlier Treatment
- **Date:** 2026-09-24
- **Context:** Airbnb listings exhibit extreme right-skewed pricing (e.g., luxury estates, erroneous entries, or pricing placeholders at \$10,000+/night). Dropping these rows removes valid listings and alters sample sizes.
- **Decision:** Follow the rule in `AGENTS.md`: **Do not delete price outliers**. Instead:
  1. Flag listings with `is_price_outlier = True` (`price_outlier_flag`) if price exceeds the 99th percentile within its city.
  2. Provide a `price_usd_capped` column winsorized at the 99th percentile for robust visual regressions in Tableau/Power BI while preserving both `price_local` and original `price_usd` for transparency.
- **Impact:** Ensures unbiased sample sizes while giving analysts both raw and outlier-resistant metrics.

---

## Decision 003: AQI Granularity & Aggregation Level
- **Date:** 2026-09-24
- **Context:** Airbnb data is localized to specific coordinates, whereas public AQI datasets are recorded at city or regional monitoring stations.
- **Decision:** For Phase 1, treat AQI as a city-level macro indicator attached uniformly to listings within that metropolitan area. For Phase 2, explore station-level distance weighting or sensor interpolation where granular station data exists.
- **Impact:** Clearly sets analytical scope without introducing artificial micro-climate precision that the dataset does not support.

---

## Decision 004: Multi-Currency Normalization to USD
- **Date:** 2026-10-01
- **Context:** Inside Airbnb raw datasets report prices in local currency (EUR, THB, HKD, TRY, USD, SGD). Comparing raw numeric values across cities would severely distort cross-market economic modeling.
- **Decision:** Explicitly assign the correct local currency to each city and convert prices to USD using fixed mid-market exchange rates:
  - EUR (Amsterdam, Lisbon, Dublin, Paris, Venice): 1.08 USD
  - THB (Bangkok): 0.029 USD
  - HKD (Hong Kong): 0.128 USD
  - TRY (Istanbul): 0.029 USD
  - USD (New York): 1.00 USD
  - SGD (Singapore): 0.76 USD
  Retain three distinct columns: `price_local` (original), `price_currency` (ISO code), and `price_usd` (converted numeric value). Never overwrite original prices.
- **Impact:** Enables valid cross-city pricing comparisons without loss of raw financial fidelity.

---

## Decision 005: Audit of 10-City AQI Matches & "Needs Manual AQI Value" Register
- **Date:** 2026-10-01
- **Context:** An audit of the Kaggle Global Air Pollution dataset revealed severe cross-country name collisions and coverage voids across the 10 demo cities. Naive joins on `city_name` result in completely erroneous matches (e.g. matching European capitals to small American municipalities).
- **Decision:** Enforce strict exact name and country verification. If the AQI dataset has no match or matches a different country, leave `aqi_value` as `null` (NaN), set `aqi_match_status` accordingly, and register the city in the "Needs Manual AQI Value" list. Do not guess or impute synthetic values.

### Register: Cities Requiring Manual AQI Validation
| City | Expected Country | AQI Dataset Status | Raw Dataset Value | Resolution / Action Required |
| :--- | :--- | :--- | :--- | :--- |
| **Dublin** | Ireland | Country Mismatch | `country_name='United States of America'`, AQI=43 | REJECTED wrong-country match (Dublin, Ohio/CA). Needs official EPA Ireland / EEA urban AQI. |
| **Hong Kong** | Hong Kong (SAR) | Missing Entirely | None found in dataset | REJECTED (absent). Needs official HKEPD (Hong Kong Environmental Protection Dept) AQHI/AQI. |
| **New York** | United States of America | Missing Country Metadata | `country_name=NaN`, AQI=70, Category=`Moderate` | Exact city matches line 4031, but country string is blank in raw CSV. Flagged for manual confirmation before hardcoding. |
| **Paris** | France | Country Mismatch | `country_name='United States of America'`, AQI=72 | REJECTED wrong-country match (Paris, Texas, USA). Needs official Airparif / EEA France urban AQI. |
| **Venice** | Italy | Country Mismatch | `country_name='United States of America'`, AQI=55 | REJECTED wrong-country match (Venice, Florida, USA). Needs official ARPA Veneto / EEA Italy urban AQI. |

### Register: Validated Reliable Matches
- **Amsterdam** (Netherlands): Matched `Netherlands` | AQI: 38 (Good)
- **Bangkok** (Thailand): Matched `Thailand` | AQI: 69 (Moderate)
- **Lisbon** (Portugal): Matched `Portugal` | AQI: 41 (Good)
- **Istanbul** (Turkey): Matched `Turkey` | AQI: 59 (Moderate)
- **Singapore** (Singapore): Matched `Singapore` | AQI: 91 (Moderate)
