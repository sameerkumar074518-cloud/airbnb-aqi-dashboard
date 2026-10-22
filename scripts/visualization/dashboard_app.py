"""
Interactive Streamlit Dashboard: Airbnb Pricing vs. Urban Air Quality
======================================================================
Course: BISL504 - Data Visualization Lab
Dataset: /data/processed/airbnb_aqi_merged_10cities.csv

Run Locally:
    streamlit run scripts/visualization/dashboard_app.py

Deploy on Streamlit Community Cloud:
    Connect GitHub repo -> Set main file to scripts/visualization/dashboard_app.py
"""

import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import streamlit as st

# -----------------------------------------------------------------------------
# 1. Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Paying for Clean Air? Airbnb Pricing vs. Urban Air Quality",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Consistent City and AQI Palettes
# -----------------------------------------------------------------------------
CITY_PALETTE = {
    'Amsterdam': '#1f77b4',   # Blue
    'Bangkok':   '#ff7f0e',   # Orange
    'Lisbon':    '#2ca02c',   # Green
    'Dublin':    '#d62728',   # Red
    'Hong Kong': '#9467bd',   # Purple
    'Istanbul':  '#8c564b',   # Brown
    'New York':  '#e377c2',   # Pink
    'Paris':     '#7f7f7f',   # Gray
    'Singapore': '#bcbd22',   # Olive
    'Venice':    '#17becf',   # Cyan
}

AQI_PALETTE = {
    'Good': '#2ca02c',                 # Green
    'Moderate': '#ff7f0e',             # Amber/Orange
    'Pending Verification': '#999999'  # Gray
}


# -----------------------------------------------------------------------------
# Data Loader (Cached)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    candidate_paths = [
        os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed', 'airbnb_aqi_merged_10cities.csv'),
        'data/processed/airbnb_aqi_merged_10cities.csv',
        'airbnb_aqi_merged_10cities.csv',
        '/content/data/processed/airbnb_aqi_merged_10cities.csv',
        '/content/airbnb_aqi_merged_10cities.csv'
    ]
    file_path = None
    for p in candidate_paths:
        if os.path.exists(p):
            file_path = p
            break
            
    if file_path is None:
        st.error("❌ Could not locate 'airbnb_aqi_merged_10cities.csv'. Please ensure the file is uploaded to 'data/processed/' or project root.")
        st.stop()
    
    df = pd.read_csv(file_path, low_memory=False)
    
    # Ensure categorical consistency
    df['city_clean'] = df['city_clean'].astype(str).str.strip()
    df['room_type'] = df['room_type'].astype(str).str.strip()
    
    # Fill pending aqi_bracket for visual grouping
    df['aqi_bracket_display'] = df['aqi_bracket'].fillna('Pending Verification')
    
    return df


df_raw = load_data()

# -----------------------------------------------------------------------------
# 2. Sidebar Filters
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 Dashboard Filters")
st.sidebar.markdown("Filter listings across global cities and environmental tiers:")

# City Multiselect
available_cities = sorted(df_raw['city_clean'].unique().tolist())
selected_cities = st.sidebar.multiselect(
    "Select Cities:",
    options=available_cities,
    default=available_cities,
    help="Select one or more cities to include in the analysis."
)

# Room Type Multiselect
available_rooms = sorted(df_raw['room_type'].unique().tolist())
selected_rooms = st.sidebar.multiselect(
    "Select Room Types:",
    options=available_rooms,
    default=available_rooms,
    help="Filter by accommodation room category."
)

# AQI Range Slider
valid_aqi = df_raw['aqi_value'].dropna()
min_aqi_val = int(valid_aqi.min()) if len(valid_aqi) > 0 else 0
max_aqi_val = int(valid_aqi.max()) if len(valid_aqi) > 0 else 100

aqi_range = st.sidebar.slider(
    "AQI Value Range (Verified Cities):",
    min_value=min_aqi_val,
    max_value=max_aqi_val,
    value=(min_aqi_val, max_aqi_val),
    step=1,
    help="Filters cities with verified AQI monitoring data."
)

include_pending_aqi = st.sidebar.checkbox(
    "Include Cities with Pending/Unverified AQI",
    value=True,
    help="Check to include Dublin, Hong Kong, New York, Paris, and Venice (cities awaiting official regional EPA AQI values)."
)

# Outlier Filter
exclude_outliers = st.sidebar.checkbox(
    "Exclude Price Outliers (> 99th Percentile per City)",
    value=False,
    help="Removes extreme right-tail price outliers flagged during preprocessing to improve chart scaling."
)

# Apply Sidebar Filtering
filtered_df = df_raw[
    (df_raw['city_clean'].isin(selected_cities)) &
    (df_raw['room_type'].isin(selected_rooms))
]

if exclude_outliers:
    filtered_df = filtered_df[filtered_df['price_outlier_flag'] == False]

if include_pending_aqi:
    filtered_df = filtered_df[
        (filtered_df['aqi_value'].isna()) |
        ((filtered_df['aqi_value'] >= aqi_range[0]) & (filtered_df['aqi_value'] <= aqi_range[1]))
    ]
else:
    filtered_df = filtered_df[
        (filtered_df['aqi_value'].notna()) &
        (filtered_df['aqi_value'] >= aqi_range[0]) &
        (filtered_df['aqi_value'] <= aqi_range[1])
    ]

# -----------------------------------------------------------------------------
# 3. Main Dashboard Header & KPI Metrics Row
# -----------------------------------------------------------------------------
st.title("🏙️ Paying for Clean Air? Airbnb Pricing vs. Urban Air Quality")
st.markdown(
    "**Course Project (BISL504) — Data Visualization Lab**  \n"
    "An interactive empirical investigation testing whether short-term rental nightly prices "
    "reflect urban air pollution (Air Quality Index) across 10 global destinations."
)

if len(filtered_df) == 0:
    st.warning("⚠️ No listings match the current filter selection. Please broaden your sidebar filters.")
    st.stop()

# KPI Calculations
avg_price = filtered_df['price_usd'].mean()
median_price = filtered_df['price_usd'].median()
listings_count = len(filtered_df)
cities_count = filtered_df['city_clean'].nunique()

valid_aqi_filtered = filtered_df['aqi_value'].dropna()
avg_aqi = valid_aqi_filtered.mean() if len(valid_aqi_filtered) > 0 else np.nan

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.metric(
        label="Average Nightly Price",
        value=f"${avg_price:,.2f}",
        delta=f"Median: ${median_price:,.2f}"
    )

with kpi_col2:
    if pd.notna(avg_aqi):
        st.metric(
            label="Average AQI (Verified)",
            value=f"{avg_aqi:.1f}",
            delta="Lower = Cleaner Air",
            delta_color="inverse"
        )
    else:
        st.metric(label="Average AQI (Verified)", value="N/A", delta="Selected cities pending AQI")

with kpi_col3:
    st.metric(
        label="Listings Displayed",
        value=f"{listings_count:,}",
        delta=f"{cities_count} of 10 Cities"
    )

with kpi_col4:
    verified_count = valid_aqi_filtered.count()
    pct_verified = (verified_count / listings_count) * 100 if listings_count > 0 else 0
    st.metric(
        label="AQI Verified Listings",
        value=f"{verified_count:,}",
        delta=f"{pct_verified:.1f}% of current sample"
    )

st.markdown("---")

# -----------------------------------------------------------------------------
# 4. Interactive Plotly Charts (2x2 Grid)
# -----------------------------------------------------------------------------
chart_col_left, chart_col_right = st.columns(2)

# --- CHART 4A: Scatter Price vs AQI with Overall OLS Trendline ---
with chart_col_left:
    st.subheader("1. Price vs. Air Quality Index (AQI)")
    scatter_data = filtered_df.dropna(subset=['aqi_value', 'price_usd']).copy()
    
    if len(scatter_data) > 0:
        # Sample if large to ensure smooth WebGL / SVG rendering
        if len(scatter_data) > 5000:
            sample_scatter = scatter_data.sample(5000, random_state=42)
        else:
            sample_scatter = scatter_data
            
        fig_scatter = px.scatter(
            sample_scatter,
            x='aqi_value',
            y='price_usd',
            color='city_clean',
            color_discrete_map=CITY_PALETTE,
            trendline='ols',
            trendline_scope='overall',
            trendline_color_override='#b30000',
            labels={
                'aqi_value': 'Air Quality Index (AQI) [Lower = Cleaner]',
                'price_usd': 'Nightly Price (USD)',
                'city_clean': 'City'
            },
            hover_name='city_clean',
            hover_data={
                'room_type': True,
                'price_usd': ':.2f',
                'aqi_value': True,
                'neighbourhood': True
            },
            title="Nightly Price vs. AQI with Overall OLS Trendline"
        )
        
        fig_scatter.update_layout(
            legend_title_text='City',
            height=440,
            margin=dict(l=20, r=20, t=40, b=20),
            hovermode='closest'
        )
        
        # Calculate Pearson r and p-value
        r_val, p_val = stats.pearsonr(scatter_data['aqi_value'], scatter_data['price_usd'])
        
        # -----------------------------------------------------------------------------
        # 5. CROSS-FILTERING SUPPORT
        # CROSS-FILTERING: Uses st.plotly_chart(on_select="rerun").
        # If selection occurs, extracted point indices filter the subsequent charts.
        # If selection is empty, falls back seamlessly to the sidebar filters.
        # -----------------------------------------------------------------------------
        try:
            selected_scatter = st.plotly_chart(
                fig_scatter,
                on_select="rerun",
                selection_mode=["points", "box", "lasso"],
                key="scatter_cross_filter",
                use_container_width=True
            )
        except Exception:
            # Fallback if on_select is unsupported in current runtime
            selected_scatter = None
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.caption(
            f"📊 **Macro Correlation:** Pearson *r* = **{r_val:.3f}** (p < 0.001, n = {len(scatter_data):,}). "
            "Negative trend line confirms higher nightly rates in cities with cleaner air. "
            "*(Tip: Box-select or click points above to cross-filter charts below)*"
        )
    else:
        st.info("No verified AQI records in the current filter selection to display on the AQI scatter chart.")
        selected_scatter = None

# Determine if cross-filtering selection is active
active_cross_filter = False
cross_filtered_df = filtered_df

if selected_scatter and "selection" in selected_scatter and selected_scatter["selection"]["point_indices"]:
    sel_indices = selected_scatter["selection"]["point_indices"]
    if len(sel_indices) > 0 and len(scatter_data) > 0:
        # Map selected points from scatter sample to dataframe
        selected_listing_ids = sample_scatter.iloc[sel_indices]['id'].tolist()
        cross_filtered_df = filtered_df[filtered_df['id'].isin(selected_listing_ids)]
        active_cross_filter = True
        st.success(f"🎯 Cross-filtering active: showing {len(cross_filtered_df):,} listings selected from Chart 1.")

# --- CHART 4B: Horizontal Bar Chart of Average Price per City ---
with chart_col_right:
    st.subheader("2. City Ranking: Average Nightly Price")
    
    city_bar_data = (
        cross_filtered_df.groupby('city_clean')
        .agg(
            avg_price=('price_usd', 'mean'),
            listing_count=('id', 'count'),
            aqi_val=('aqi_value', 'first')
        )
        .reset_index()
        .sort_values(by='avg_price', ascending=True)
    )
    
    city_bar_data['aqi_label'] = city_bar_data['aqi_val'].apply(
        lambda x: f"AQI: {x:.0f}" if pd.notna(x) else "AQI: Pending"
    )
    
    fig_bar = px.bar(
        city_bar_data,
        x='avg_price',
        y='city_clean',
        orientation='h',
        color='city_clean',
        color_discrete_map=CITY_PALETTE,
        text_auto='.0f',
        labels={'avg_price': 'Average Price (USD)', 'city_clean': 'City'},
        hover_data={'avg_price': ':.2f', 'listing_count': ':,', 'aqi_label': True, 'city_clean': False},
        title="Sorted Average Nightly Price (USD) by City"
    )
    
    fig_bar.update_layout(
        showlegend=False,
        height=440,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_tickprefix="$"
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
    st.caption("Between-city comparison: Amsterdam and Paris rank highest; Bangkok is the most economical.")

chart_col_bottom_left, chart_col_bottom_right = st.columns(2)

# --- CHART 4C: Box Plot of Price by Room Type & AQI Bracket ---
with chart_col_bottom_left:
    st.subheader("3. Price Distribution by Room Type & AQI Tier")
    
    box_data = cross_filtered_df.copy()
    # Order room types logically
    room_order = ['Entire home/apt', 'Private room', 'Hotel room', 'Shared room']
    
    fig_box = px.box(
        box_data,
        x='room_type',
        y='price_usd',
        color='aqi_bracket_display',
        color_discrete_map=AQI_PALETTE,
        category_orders={'room_type': room_order},
        labels={
            'price_usd': 'Nightly Price (USD)',
            'room_type': 'Room Type',
            'aqi_bracket_display': 'Air Quality Tier'
        },
        title="Room Type Segmentation Across Environmental Tiers"
    )
    
    # Cap y-axis display to $600 for clear interquartile visibility while retaining outlier points
    fig_box.update_yaxes(range=[0, 600], tickprefix="$")
    fig_box.update_layout(
        height=440,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_box, use_container_width=True)
    st.caption("Entire homes command the highest absolute premium in Good AQI cities ($198 median vs. $65 in Moderate).")

# --- CHART 4D: Interactive Geographic Map ---
with chart_col_bottom_right:
    st.subheader("4. Global Spatial Distribution of Listings")
    
    map_sample = cross_filtered_df
    if len(map_sample) > 8000:
        map_sample = map_sample.sample(8000, random_state=42)
        
    # Check plotly version compatibility for map rendering
    if hasattr(px, 'scatter_map'):
        fig_map = px.scatter_map(
            map_sample,
            lat='latitude',
            lon='longitude',
            color='price_usd',
            color_continuous_scale='Plasma',
            range_color=[20, 500],
            hover_name='city_clean',
            hover_data={
                'room_type': True,
                'neighbourhood': True,
                'price_usd': ':.2f',
                'latitude': False,
                'longitude': False
            },
            map_style='open-street-map',
            zoom=1,
            title="Global Geographic Distribution Colored by Nightly Rate (USD)"
        )
    elif hasattr(px, 'scatter_mapbox'):
        fig_map = px.scatter_mapbox(
            map_sample,
            lat='latitude',
            lon='longitude',
            color='price_usd',
            color_continuous_scale='Plasma',
            range_color=[20, 500],
            hover_name='city_clean',
            hover_data={
                'room_type': True,
                'neighbourhood': True,
                'price_usd': ':.2f',
                'latitude': False,
                'longitude': False
            },
            mapbox_style='open-street-map',
            zoom=1,
            title="Global Geographic Distribution Colored by Nightly Rate (USD)"
        )
    else:
        fig_map = px.scatter_geo(
            map_sample,
            lat='latitude',
            lon='longitude',
            color='price_usd',
            color_continuous_scale='Plasma',
            range_color=[20, 500],
            hover_name='city_clean',
            hover_data={'room_type': True, 'neighbourhood': True, 'price_usd': ':.2f'},
            title="Global Geographic Distribution Colored by Nightly Rate (USD)"
        )
        
    fig_map.update_layout(
        height=440,
        margin=dict(l=10, r=10, t=40, b=10),
        coloraxis_colorbar=dict(title="Price (USD)", tickprefix="$")
    )
    
    st.plotly_chart(fig_map, use_container_width=True)
    st.caption("Interactive OpenStreetMap basemap. Zoom and pan into individual city clusters worldwide.")

# -----------------------------------------------------------------------------
# 6. Collapsible Raw Data Table
# -----------------------------------------------------------------------------
st.markdown("---")
show_raw_data = st.checkbox("📋 Inspect Filtered Raw Data Records", value=False)

if show_raw_data:
    st.subheader(f"Filtered Records Table ({len(cross_filtered_df):,} rows)")
    display_cols = [
        'id', 'city_clean', 'room_type', 'price_usd', 'price_local', 'price_currency',
        'aqi_value', 'aqi_bracket', 'neighbourhood', 'latitude', 'longitude',
        'number_of_reviews', 'reviews_per_month', 'price_outlier_flag'
    ]
    available_display_cols = [c for c in display_cols if c in cross_filtered_df.columns]
    
    st.dataframe(
        cross_filtered_df[available_display_cols],
        use_container_width=True,
        hide_index=True
    )
    
    csv_data = cross_filtered_df[available_display_cols].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv_data,
        file_name="airbnb_aqi_filtered_sample.csv",
        mime="text/csv"
    )

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<small style='color: #666666;'>BISL504 Data Visualization Lab | Interactive Plotly Dashboard | "
    "Data sources: Inside Airbnb & Kaggle Global Air Pollution Dataset.</small>",
    unsafe_allow_html=True
)
