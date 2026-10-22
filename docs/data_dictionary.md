# Data Dictionary

This document provides schema definitions, descriptions, types, and constraints for raw inputs and processed outputs.

---

## 1. Raw Data: Inside Airbnb (`listings.csv`)

| Column Name | Data Type | Description | Cleaning / Validation Rules |
| :--- | :--- | :--- | :--- |
| `id` | Integer / String | Unique identifier for the listing | Primary key, must not be null |
| `name` | String | Listing title / description | Text |
| `host_id` | Integer / String | Unique identifier for host | Categorical identifier |
| `neighbourhood_group` | String | Broad region/borough within city (if available) | Categorical; may be empty in some cities |
| `neighbourhood` | String | Specific neighborhood name | Categorical; taken from `neighbourhood` or `neighbourhood_cleansed` |
| `latitude` | Float | Geographic latitude coordinate | Valid range: [-90.0, 90.0], must not be null |
| `longitude` | Float | Geographic longitude coordinate | Valid range: [-180.0, 180.0], must not be null |
| `room_type` | String | Type of accommodation (`Entire home/apt`, `Private room`, `Shared room`, `Hotel room`) | Categorical, must not be null |
| `price` | String / Float | Stated nightly rate in local currency | Stripped of `$`, `,`, cast to numeric float; strictly positive |
| `minimum_nights` | Integer | Minimum booking duration in nights | Non-negative integer |
| `number_of_reviews`| Integer | Total review count | Non-negative integer |
| `reviews_per_month`| Float | Average reviews per month | Float |
| `availability_365` | Integer | Days available within a 365-day calendar | Range: [0, 365] |

> **Note on Ratings:** Inside Airbnb summary listings files do not include `review_scores_rating`. Only `number_of_reviews` and `reviews_per_month` are available as review controls.

---

## 2. Raw Data: Global Air Pollution Dataset (`global_air_pollution_data.csv`)

| Column Name | Data Type | Description | Cleaning / Validation Rules |
| :--- | :--- | :--- | :--- |
| `country_name` | String | Country name | Standardize casing and whitespace; used to verify city-country alignment |
| `city_name` | String | Metropolitan area or city name | Standardize casing, trim spaces; requires exact match with target city |
| `aqi_value` | Integer / Float | Overall calculated Air Quality Index score | Lower indicates cleaner air; >100 is unhealthy for sensitive groups |
| `aqi_category` | String | EPA air quality band (e.g., `Good`, `Moderate`, `Unhealthy`) | Categorical classification |
| `co_aqi_value` | Float | Carbon Monoxide sub-index | Numeric |
| `co_aqi_category` | String | Carbon Monoxide category | Categorical |
| `ozone_aqi_value` | Float | Ground-level Ozone sub-index | Numeric |
| `ozone_aqi_category`| String | Ground-level Ozone category | Categorical |
| `no2_aqi_value` | Float | Nitrogen Dioxide sub-index | Numeric |
| `no2_aqi_category` | String | Nitrogen Dioxide category | Categorical |
| `pm2.5_aqi_value` | Float | Particulate Matter (PM2.5) sub-index | Numeric |
| `pm2.5_aqi_category`| String | Particulate Matter (PM2.5) category | Categorical |

---

## 3. Processed Data: `airbnb_aqi_merged_10cities.csv`

Output file created in `/data/processed/` ready for ingestion into Tableau and Power BI.

| Column Name | Data Type | Description | Source / Derivation |
| :--- | :--- | :--- | :--- |
| `id` | String / Int | Unique listing identifier | Raw Airbnb `id` |
| `name` | String | Listing name / description | Raw Airbnb `name` |
| `neighbourhood_group`| String | Broad regional group / borough | Raw `neighbourhood_group` or `neighbourhood_group_cleansed` |
| `neighbourhood` | String | Specific neighborhood name | Raw `neighbourhood` or `neighbourhood_cleansed` |
| `latitude` | Float | Listing latitude coordinate | Cleaned raw latitude |
| `longitude` | Float | Listing longitude coordinate | Cleaned raw longitude |
| `room_type` | String | Accommodation type (`Entire home/apt`, `Private room`, etc.) | Cleaned raw `room_type` |
| `price_local` | Float | Stated nightly price in city's local currency | Cleaned numeric price (untransformed) |
| `price_currency`| String | Three-letter ISO currency code (`EUR`, `THB`, `HKD`, `TRY`, `USD`, `SGD`) | City metadata assignment |
| `price_usd` | Float | Converted nightly price in US Dollars | `price_local * exchange_rate_to_usd` |
| `price_usd_capped`| Float | Price in USD winsorized at 99th percentile within city | Outlier-resistant pricing metric |
| `price_outlier_flag`| Boolean | True if listing `price_usd` exceeds the city's 99th percentile | Outlier flag (retains all records per rule) |
| `minimum_nights` | Integer | Minimum nights booking requirement | Cleaned raw `minimum_nights` |
| `number_of_reviews`| Integer | Cumulative review count | Cleaned raw `number_of_reviews` |
| `reviews_per_month`| Float | Average monthly review velocity | Cleaned raw `reviews_per_month` |
| `availability_365` | Integer | Days available in upcoming 365 days | Cleaned raw `availability_365` |
| `city` | String | Canonical city name (e.g., `Amsterdam`, `New York`) | Standardized city identifier |
| `city_clean` | String | Standardized lowercase / trimmed canonical key | Normalized join key |
| `aqi_value` | Float / Null | City-level Air Quality Index value | Merged from AQI dataset (`null` if unverified) |
| `aqi_category` | String / Null | Categorical AQI classification (`Good`, `Moderate`, etc.) | Merged from AQI dataset (`null` if unverified) |
| `aqi_country` | String / Null | Country name reported in the AQI dataset | Audit field for geographic verification |
| `aqi_bracket` | String / Null | Standardized EPA AQI bracket | Derived from `aqi_value` |
| `aqi_match_status` | String | Match validation audit outcome | Categorical: `RELIABLE_MATCH`, `WRONG_COUNTRY`, `MISSING_IN_DATASET` |

---

## 4. AQI Match-Confidence & Geographic Verification Approach

Due to widespread city-name collisions across distinct countries in global air quality registries (e.g. Venice, FL vs. Venice, Italy; Paris, TX vs. Paris, France; Dublin, OH vs. Dublin, Ireland), joins strictly enforce a two-tier verification:

1. **Exact City Name Matching:** Only exact string matches on `city_name` are evaluated (no fuzzy or substring joins).
2. **Geographic Country Verification:** The matched record's `country_name` is compared against the target city's expected sovereign country.
   - **`RELIABLE_MATCH`:** City name and sovereign country match exactly (e.g. `Amsterdam` in `Netherlands`). The AQI score is retained.
   - **`NO_RELIABLE_MATCH (Wrong Country)`:** City name matches a municipal duplicate in a different country (e.g. `Paris` in `United States of America`). The match is rejected, `aqi_value` is set to `null` (NaN), and the city is escalated to the "Needs Manual AQI Value" register.
   - **`NO_RELIABLE_MATCH (Missing in Dataset)`:** City name is entirely absent from the AQI registry (e.g. `Hong Kong`). `aqi_value` is set to `null` and escalated to manual curation.
