
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd

app = Dash(__name__)

app.layout = html.Div(
    style={"fontFamily": "Arial", "padding": "30px"},
    children=[
        html.H1("Airbnb + AQI Dashboard"),
        html.P("Airbnb listings and air quality analysis"),
        html.Hr(),
        html.H2("Dashboard Deployment Test"),
        html.P(
            "If you can see this page, your Dash application "
            "is running successfully on Render!"
        ),
    ],
)

server = app.server

if __name__ == "__main__":
    app.run(debug=True)

