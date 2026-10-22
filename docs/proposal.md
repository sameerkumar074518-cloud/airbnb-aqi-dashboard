# Project Proposal: Clean Air, Higher Rent? Airbnb Pricing and Urban Air Quality

**Course:** BISL504 - Data Visualization Lab  
**Project Title:** Clean Air, Higher Rent? Airbnb Pricing and Urban Air Quality  
**Status:** In Progress (Phase 1)

---

## 1. Abstract
This project investigates the empirical relationship between short-term accommodation pricing (Airbnb nightly rates) and urban environmental quality, specifically ambient Air Quality Index (AQI). As eco-conscious travel gains traction and urban density heightens health awareness, we test whether markets reflect a "clean air premium" or if tourist destination centrality dominates price determination regardless of pollution levels. The analysis combines Python for data wrangling and econometric modeling with Tableau and Power BI for interactive multi-city dashboards.

## 2. Research Questions & Hypotheses
- **Primary Question:** Does a lower AQI (cleaner air) correlate with higher nightly Airbnb prices across major global tourist destinations?
- **Secondary Questions:**
  - How does room type (entire home vs. private room) moderate the price-AQI relationship?
  - Does spatial variance within dense cities reflect localized environmental gradients, or is AQI predominantly a macro-city-level indicator?
  - What proportion of price variance is explained by location/amenities versus environmental health indicators?
- **Working Hypothesis:** While baseline location and listing amenities account for the majority of price variance, cities with consistently superior air quality demonstrate a positive price premium when controlling for room type and listing capacity.

## 3. Project Scope & Phased Implementation

### Phase 1: 10-City Global Demonstration (Current)
A representative set of 10 diverse global metropolitan markets covering Europe, Asia, and North America:
1. **Amsterdam** (Netherlands)
2. **Bangkok** (Thailand)
3. **Barcelona** (Spain)
4. **Dublin** (Ireland)
5. **Hong Kong** (Hong Kong SAR)
6. **Istanbul** (Turkey)
7. **New York** (United States)
8. **Paris** (France)
9. **Singapore** (Singapore)
10. **Venice** (Italy)

### Phase 2: 20-City Expansion (Upcoming)
- Expansion to 20 cities globally.
- Integration of an India-specific regional market: **Goa, India**, leveraging a dedicated Indian Airbnb dataset and sub-regional AQI monitoring.

## 4. Data Sources

1. **Inside Airbnb (`listings.csv` per city):**
   - Granular snapshot data per city including listing ID, geographical coordinates (`latitude`, `longitude`), `room_type`, `price`, `accommodates`, `minimum_nights`, and review metrics.
2. **Kaggle Global Air Pollution Dataset:**
   - City-level and country-level air quality observations detailing overall `AQI Value`, `AQI Category`, as well as specific pollutant sub-indices (`CO`, `Ozone`, `NO2`, `PM2.5`).
   - *Data caveat:* Contains non-unique city names across different countries and naming discrepancies that require strict multi-key (City + Country) validation and canonical normalization.

## 5. Technology Stack & Deliverables
- **Data Engineering & Cleaning:** Python (`pandas`, `numpy`)
- **Statistical Analysis & Exploration:** Jupyter Notebooks (`notebooks/`)
- **Static Visualizations:** `matplotlib`, `seaborn` (saved to `outputs/figures/`)
- **Interactive Dashboards:** Tableau (`.twbx`) & Power BI (`.pbix`) (saved to `outputs/dashboards/`)
- **Documentation:** Data dictionary, decisions log, and reproducible project scripts
