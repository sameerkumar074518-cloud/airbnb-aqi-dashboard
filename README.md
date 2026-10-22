# Clean Air, Higher Rent? Airbnb Pricing and Urban Air Quality

**Course:** BISL504 - Data Visualization Lab  
**Authors:** Research Team  
**Scope:** Phase 1 (10-City Demonstration) | Phase 2 (20-City Expansion)

---

## Overview
This project examines whether Airbnb nightly prices reflect a premium for cleaner urban environments by comparing listing prices against city-level Air Quality Index (AQI) scores across major global travel destinations.

### Phase 1 Cities (10 Cities)
- **Europe:** Amsterdam, Barcelona, Dublin, Paris, Venice
- **Asia:** Bangkok, Hong Kong, Istanbul, Singapore
- **North America:** New York

---

## Directory Layout
```text
Data Visualization/
├── data/
│   ├── raw/                  # Pristine untouched CSVs, one folder per city
│   │   ├── amsterdam/
│   │   ├── bangkok/
│   │   ├── barcelona/
│   │   ├── dublin/
│   │   ├── hong_kong/
│   │   ├── istanbul/
│   │   ├── new_york/
│   │   ├── paris/
│   │   ├── singapore/
│   │   ├── venice/
│   │   └── aqi/              # Kaggle Global Air Pollution CSV
│   └── processed/            # Cleaned, standardized, merged CSVs ready for BI
├── notebooks/                # Jupyter notebooks for exploratory data analysis
├── scripts/
│   ├── preprocessing/        # Loading, cleaning, name normalization, and merging
│   └── visualization/        # Individual chart generation scripts
├── outputs/
│   ├── figures/              # Exported publication-ready chart figures (PNG)
│   └── dashboards/           # Tableau (.twbx) and Power BI (.pbix) files
├── docs/
│   ├── proposal.md           # Research proposal, questions, and methodology
│   ├── data_dictionary.md    # Field definitions and data types
│   └── decisions_log.md      # Running audit trail of technical decisions
├── requirements.txt          # Python dependencies
├── AGENTS.md                 # Project rules and agent behavioral guidelines
└── README.md                 # Project documentation
```

---

## Setup & Installation

1. **Clone or Navigate to the Workspace:**
   ```bash
   cd "d:/Projects/Data Visualization"
   ```

2. **Set up a Virtual Environment (Optional but Recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## How to Run Preprocessing & Visualization

1. **Preprocessing Pipeline (Data Cleaning & Merging):**
   ```bash
   python scripts/preprocessing/clean_and_merge.py --save
   ```
   - Standardizes local currencies to USD (`price_local`, `price_currency`, `price_usd`).
   - Flags upper 99th-percentile price outliers (`price_outlier_flag`, `price_usd_capped`).
   - Applies exact-country verification to reject cross-country AQI collisions.
   - Saves final merged dataset to `data/processed/airbnb_aqi_merged_10cities.csv`.

2. **Generate Core Visualizations & Dashboard:**
   ```bash
   python scripts/visualization/generate_dashboard.py
   ```
   Outputs created in `outputs/figures/`:
   - `dashboard_overview.png`: High-resolution 2x2 combined overview.
   - `chart1_price_vs_aqi_scatter.png`: Panel 1 scatter plot with OLS regression trendline.
   - `chart2_city_ranking.png`: Panel 2 sorted between-city price and AQI ranking.
   - `chart3_geographic_proxy.png`: Panel 3 latitude/longitude price proxy map.
   - `chart4_room_type_segmentation.png`: Panel 4 room type price boxplots across AQI brackets.

3. **Launch the Interactive Plotly/Streamlit Dashboard:**
   ```bash
   streamlit run scripts/visualization/dashboard_app.py
   ```
   *(or `python -m streamlit run scripts/visualization/dashboard_app.py`)*

   - **Features:** Live cross-filtering via point/box selections on Chart 1, hover tooltips, zoom/pan, city & room-type multiselects, AQI range slider, outlier exclusion toggle, and collapsible raw data table.

---

## Free Permanent Deployment via Streamlit Community Cloud

To deploy the dashboard publicly with a permanent URL (no temporary Colab/ngrok tunnels needed):

1. **Initialize and Push this Repository to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Add interactive Streamlit dashboard"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Community Cloud:**
   - Navigate to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
   - Click **"New app"** (or "Create app").
   - Select your repository: `<your-username>/<your-repo-name>`.
   - Set **Branch:** `main`
   - Set **Main file path:** `scripts/visualization/dashboard_app.py`
   - Click **"Deploy!"**

3. **Automatic Dependency Detection:**
   - Streamlit Community Cloud automatically reads `requirements.txt` (`streamlit`, `pandas`, `plotly`, `statsmodels`, etc.) and provisions the environment.
   - Once deployed, your dashboard remains accessible 24/7 at a shareable `.streamlit.app` public link.
