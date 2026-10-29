
import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, dash_table

# --------------------------------------------------
# 1. Load the existing project dataset
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "processed" / "airbnb_aqi_merged_10cities.csv"

if not DATA_FILE.exists():
    # Try to locate the processed CSV elsewhere in the repo.
    matches = list(BASE_DIR.glob("**/airbnb_aqi_merged_10cities.csv"))
    if matches:
        DATA_FILE = matches[0]

if not DATA_FILE.exists():
    raise FileNotFoundError(
        "Dataset not found. Upload "
        "airbnb_aqi_merged_10cities.csv to data/processed/ "
        "in your GitHub repository."
    )

df = pd.read_csv(DATA_FILE, low_memory=False)

required = ["city_clean", "room_type", "price_usd", "aqi_value"]
missing = [column for column in required if column not in df.columns]
if missing:
    raise ValueError(f"Dataset is missing required columns: {missing}")

df["city_clean"] = df["city_clean"].fillna("Unknown").astype(str).str.strip()
df["room_type"] = df["room_type"].fillna("Unknown").astype(str).str.strip()
df["price_usd"] = pd.to_numeric(df["price_usd"], errors="coerce")
df["aqi_value"] = pd.to_numeric(df["aqi_value"], errors="coerce")

if "price_outlier_flag" not in df.columns:
    df["price_outlier_flag"] = False

df["price_outlier_flag"] = (
    df["price_outlier_flag"].fillna(False).astype(bool)
)

cities = sorted(df["city_clean"].unique().tolist())
rooms = sorted(df["room_type"].unique().tolist())

valid_aqi = df["aqi_value"].dropna()
aqi_min = int(np.floor(valid_aqi.min())) if not valid_aqi.empty else 0
aqi_max = int(np.ceil(valid_aqi.max())) if not valid_aqi.empty else 100

if aqi_min == aqi_max:
    aqi_max = aqi_min + 1

# --------------------------------------------------
# 2. Dashboard styling
# --------------------------------------------------
app = Dash(__name__)
server = app.server

BACKGROUND = "#f4f7fb"
NAVY = "#172554"
BLUE = "#2563eb"
MUTED = "#64748b"

CARD_STYLE = {
    "backgroundColor": "white",
    "padding": "20px",
    "borderRadius": "14px",
    "boxShadow": "0 3px 14px rgba(15,23,42,0.06)",
    "minWidth": "180px",
    "flex": "1",
}

def metric_card(title, element_id):
    return html.Div(
        [
            html.Div(title, style={"color": MUTED, "fontSize": "14px"}),
            html.H2("—", id=element_id, style={"color": NAVY, "margin": "10px 0"}),
        ],
        style=CARD_STYLE,
    )

def chart_card(title, graph_id):
    return html.Div(
        [
            html.H3(title, style={"color": NAVY, "fontSize": "17px"}),
            dcc.Graph(id=graph_id, config={"displaylogo": False}),
        ],
        style={**CARD_STYLE, "minWidth": "0"},
    )

# --------------------------------------------------
# 3. Layout and filters
# --------------------------------------------------
app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": BACKGROUND,
        "minHeight": "100vh",
        "padding": "24px",
        "color": NAVY,
    },
    children=[
        html.Div(
            [
                html.H1(
                    "Airbnb + AQI Explorer",
                    style={"marginBottom": "8px", "fontSize": "32px"},
                ),
                html.P(
                    "Explore how nightly accommodation prices compare "
                    "with urban air quality across global destinations.",
                    style={"color": MUTED},
                ),
                html.P(
                    "Air quality and prices are observational data; "
                    "the charts do not establish causation.",
                    style={"color": MUTED, "fontSize": "13px"},
                ),
            ],
            style={**CARD_STYLE, "marginBottom": "20px"},
        ),

        html.Div(
            [
                html.Div(
                    [
                        html.H3("Dashboard Filters"),
                        html.Label("Cities"),
                        dcc.Dropdown(
                            id="city-filter",
                            options=[{"label": c, "value": c} for c in cities],
                            value=cities,
                            multi=True,
                            placeholder="Select cities",
                        ),

                        html.Br(),
                        html.Label("Room types"),
                        dcc.Dropdown(
                            id="room-filter",
                            options=[{"label": r, "value": r} for r in rooms],
                            value=rooms,
                            multi=True,
                            placeholder="Select room types",
                        ),

                        html.Br(),
                        html.Label("AQI range"),
                        dcc.RangeSlider(
                            id="aqi-filter",
                            min=aqi_min,
                            max=aqi_max,
                            value=[aqi_min, aqi_max],
                            step=1,
                            marks={
                                aqi_min: str(aqi_min),
                                aqi_max: str(aqi_max),
                            },
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),

                        html.Br(),
                        dcc.Checklist(
                            id="pending-filter",
                            options=[
                                {
                                    "label": " Include listings with unverified AQI",
                                    "value": "include",
                                }
                            ],
                            value=["include"],
                        ),

                        html.Br(),
                        dcc.Checklist(
                            id="outlier-filter",
                            options=[
                                {
                                    "label": " Exclude price outliers",
                                    "value": "exclude",
                                }
                            ],
                            value=[],
                        ),
                    ],
                    style={**CARD_STYLE, "flex": "0 0 250px"},
                ),

                html.Div(
                    [
                        html.Div(
                            [
                                metric_card("Average nightly price (USD)", "kpi-price"),
                                metric_card("Average verified AQI", "kpi-aqi"),
                                metric_card("Listings displayed", "kpi-listings"),
                                metric_card("AQI-verified listings", "kpi-verified"),
                            ],
                            style={
                                "display": "flex",
                                "flexWrap": "wrap",
                                "gap": "16px",
                                "marginBottom": "20px",
                            },
                        ),

                        html.Div(
                            [
                                chart_card("Price vs. Air Quality", "scatter-chart"),
                                chart_card("Average Nightly Price by City", "city-chart"),
                            ],
                            style={
                                "display": "grid",
                                "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))",
                                "gap": "20px",
                                "marginBottom": "20px",
                            },
                        ),

                        html.Div(
                            [
                                chart_card("Price by Room Type and AQI Tier", "room-chart"),
                                chart_card("Global Listing Map", "map-chart"),
                            ],
                            style={
                                "display": "grid",
                                "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))",
                                "gap": "20px",
                            },
                        ),
                    ],
                    style={"flex": "1", "minWidth": "0"},
                ),
            ],
            style={
                "display": "flex",
                "flexWrap": "wrap",
                "alignItems": "flex-start",
                "gap": "20px",
            },
        ),

        html.Div(
            [
                html.H2("Filtered Listing Data"),
                html.P(
                    "The table shows up to 2,000 matching rows. "
                    "Use the button to download all matching records.",
                    style={"color": MUTED},
                ),
                html.Button(
                    "Download filtered CSV",
                    id="download-button",
                    n_clicks=0,
                    style={
                        "backgroundColor": BLUE,
                        "color": "white",
                        "border": "none",
                        "padding": "12px 18px",
                        "borderRadius": "8px",
                        "cursor": "pointer",
                        "marginBottom": "16px",
                    },
                ),
                dcc.Download(id="download-data"),
                html.Div(id="table-count", style={"marginBottom": "10px"}),
                dash_table.DataTable(
                    id="data-table",
                    page_size=10,
                    sort_action="native",
                    filter_action="native",
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "padding": "10px",
                        "textAlign": "left",
                        "minWidth": "100px",
                        "maxWidth": "240px",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                    },
                    style_header={
                        "backgroundColor": "#eaf0fb",
                        "fontWeight": "bold",
                    },
                    style_data={"backgroundColor": "white"},
                ),
            ],
            style={**CARD_STYLE, "marginTop": "20px"},
        ),

        html.P(
            "Airbnb + AQI Dashboard | Data visualization project",
            style={"textAlign": "center", "color": MUTED, "marginTop": "24px"},
        ),
    ],
)

# --------------------------------------------------
# 4. Shared filtering function
# --------------------------------------------------
def filter_data(selected_cities, selected_rooms, aqi_range, pending, outliers):
    result = df[
        df["city_clean"].isin(selected_cities or [])
        & df["room_type"].isin(selected_rooms or [])
    ].copy()

    if "exclude" in (outliers or []):
        result = result[~result["price_outlier_flag"]]

    low, high = aqi_range or [aqi_min, aqi_max]
    if "include" in (pending or []):
        result = result[
            result["aqi_value"].isna()
            | result["aqi_value"].between(low, high)
        ]
    else:
        result = result[result["aqi_value"].between(low, high)]

    return result

def empty_figure(message):
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
    )
    fig.update_layout(template="plotly_white", height=390)
    return fig

# --------------------------------------------------
# 5. Update metrics, charts, and table
# --------------------------------------------------
@app.callback(
    Output("kpi-price", "children"),
    Output("kpi-aqi", "children"),
    Output("kpi-listings", "children"),
    Output("kpi-verified", "children"),
    Output("scatter-chart", "figure"),
    Output("city-chart", "figure"),
    Output("room-chart", "figure"),
    Output("map-chart", "figure"),
    Output("data-table", "data"),
    Output("data-table", "columns"),
    Output("table-count", "children"),
    Input("city-filter", "value"),
    Input("room-filter", "value"),
    Input("aqi-filter", "value"),
    Input("pending-filter", "value"),
    Input("outlier-filter", "value"),
)
def update_dashboard(selected_cities, selected_rooms, aqi_range, pending, outliers):
    data = filter_data(
        selected_cities, selected_rooms, aqi_range, pending, outliers
    )

    avg_price = data["price_usd"].mean()
    verified = data["aqi_value"].notna().sum()
    avg_aqi = data.loc[data["aqi_value"].notna(), "aqi_value"].mean()

    price_text = f"${avg_price:,.2f}" if pd.notna(avg_price) else "N/A"
    aqi_text = f"{avg_aqi:.1f}" if pd.notna(avg_aqi) else "N/A"

    # Scatter: use a sample for responsive plotting on large datasets.
    scatter_data = data.dropna(subset=["aqi_value", "price_usd"])
    if len(scatter_data) > 5000:
        scatter_data = scatter_data.sample(5000, random_state=42)

    if len(scatter_data) >= 2:
        scatter = px.scatter(
            scatter_data,
            x="aqi_value",
            y="price_usd",
            color="city_clean",
            hover_data=["room_type"],
            trendline="ols",
            labels={
                "aqi_value": "Air Quality Index (lower is cleaner)",
                "price_usd": "Nightly price (USD)",
                "city_clean": "City",
            },
            title="Nightly Price vs. AQI",
        )
        scatter.update_layout(template="plotly_white", height=390)
        scatter.update_yaxes(tickprefix="$")
    else:
        scatter = empty_figure("Not enough verified AQI data for this selection")

    city_data = (
        data.dropna(subset=["price_usd"])
        .groupby("city_clean", as_index=False)
        .agg(avg_price=("price_usd", "mean"), listings=("price_usd", "size"))
        .sort_values("avg_price")
    )

    if not city_data.empty:
        city_fig = px.bar(
            city_data,
            x="avg_price",
            y="city_clean",
            orientation="h",
            text="avg_price",
            hover_data=["listings"],
            labels={"avg_price": "Average nightly price (USD)", "city_clean": "City"},
            title="Average Price by City",
        )
        city_fig.update_traces(texttemplate="$%{x:,.0f}", textposition="outside")
        city_fig.update_layout(
            template="plotly_white",
            height=390,
            showlegend=False,
            xaxis_tickprefix="$",
        )
    else:
        city_fig = empty_figure("No priced listings for this selection")

    room_data = data.dropna(subset=["price_usd"]).copy()
    if "aqi_bracket" in room_data.columns:
        room_data["aqi_bracket"] = room_data["aqi_bracket"].fillna(
            "Pending Verification"
        )
        room_fig = px.box(
            room_data,
            x="room_type",
            y="price_usd",
            color="aqi_bracket",
            points=False,
            labels={
                "room_type": "Room type",
                "price_usd": "Nightly price (USD)",
                "aqi_bracket": "AQI tier",
            },
            title="Price Distribution by Room Type",
        )
    else:
        room_fig = px.box(
            room_data,
            x="room_type",
            y="price_usd",
            points=False,
            title="Price Distribution by Room Type",
        )

    room_fig.update_layout(template="plotly_white", height=390)
    room_fig.update_yaxes(tickprefix="$", range=[0, 600])

    map_columns = {"latitude", "longitude", "price_usd", "city_clean"}
    if map_columns.issubset(data.columns):
        map_data = data.dropna(subset=["latitude", "longitude", "price_usd"])
        if len(map_data) > 5000:
            map_data = map_data.sample(5000, random_state=42)

        if not map_data.empty:
            map_fig = px.scatter_geo(
                map_data,
                lat="latitude",
                lon="longitude",
                color="price_usd",
                hover_name="city_clean",
                hover_data=["room_type"],
                color_continuous_scale="Plasma",
                labels={"price_usd": "Nightly price (USD)"},
                title="Global Listing Locations",
            )
            map_fig.update_layout(
                template="plotly_white",
                height=390,
                geo={"showland": True, "landcolor": "#edf2f7"},
            )
        else:
            map_fig = empty_figure("No geographic data available")
    else:
        map_fig = empty_figure("Dataset does not contain latitude and longitude")

    # Display a manageable page of data while retaining the full filtered set.
    display_cols = [
        "id", "city_clean", "room_type", "price_usd",
        "aqi_value", "aqi_bracket", "neighbourhood",
        "number_of_reviews", "price_outlier_flag",
    ]
    available_cols = [c for c in display_cols if c in data.columns]
    table_data = (
        data[available_cols]
        .head(2000)
        .replace({np.nan: None})
        .to_dict("records")
    )
    table_columns = [
        {"name": c.replace("_", " ").title(), "id": c}
        for c in available_cols
    ]

    return (
        price_text,
        aqi_text,
        f"{len(data):,}",
        f"{verified:,}",
        scatter,
        city_fig,
        room_fig,
        map_fig,
        table_data,
        table_columns,
        f"Showing up to {min(len(data), 2000):,} of {len(data):,} matching listings.",
    )

# --------------------------------------------------
# 6. Download all filtered records
# --------------------------------------------------
@app.callback(
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    State("city-filter", "value"),
    State("room-filter", "value"),
    State("aqi-filter", "value"),
    State("pending-filter", "value"),
    State("outlier-filter", "value"),
    prevent_initial_call=True,
)
def download_filtered_data(clicks, selected_cities, selected_rooms,
                           aqi_range, pending, outliers):
    data = filter_data(
        selected_cities, selected_rooms, aqi_range, pending, outliers
    )
    return dcc.send_data_frame(
        data.to_csv,
        "airbnb_aqi_filtered.csv",
        index=False,
    )

if __name__ == "__main__":
    app.run(debug=False)
