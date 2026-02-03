# app.py
# Electricity Consumption Dashboard (Updated for Dash 2.15+)

import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output
import os

# -------------------------------
# 1️⃣ Load CSV
CSV_FILE = "electricity_data.csv"

if not os.path.exists(CSV_FILE):
    raise FileNotFoundError(f"⚠️ CSV file '{CSV_FILE}' not found in current folder.")

df = pd.read_csv(CSV_FILE)

# -------------------------------
# 2️⃣ Detect or rename columns
# Lowercase mapping
col_map = {}
for col in df.columns:
    cname = col.lower()
    if "date" in cname or "day" in cname:
        col_map["Date"] = col
    elif "device" in cname or "appliance" in cname:
        col_map["Device"] = col
    elif "power" in cname or "watt" in cname:
        col_map["Power_Watts"] = col
    elif "hour" in cname or "usage" in cname:
        col_map["Hours_Used"] = col

# Required columns
required_cols = ["Date", "Device", "Power_Watts", "Hours_Used"]
missing = [c for c in required_cols if c not in col_map]
if missing:
    raise ValueError(f"⚠️ Could not detect columns in CSV: {missing}")

df = df.rename(columns={v: k for k, v in col_map.items()})

# -------------------------------
# 3️⃣ Prepare data
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
COST_PER_KWH = 0.15  # Adjust your local rate
df["Energy_kWh"] = (df["Power_Watts"] * df["Hours_Used"]) / 1000
df["Cost"] = df["Energy_kWh"] * COST_PER_KWH

# -------------------------------
# 4️⃣ Initialize Dash app
app = Dash(__name__)
app.title = "Electricity Consumption Dashboard"

# -------------------------------
# 5️⃣ Layout
app.layout = html.Div([
    html.H1("⚡ Electricity Consumption Dashboard", style={"textAlign": "center"}),

    html.Div([
        html.Label("Select Device:"),
        dcc.Dropdown(
            id="device-filter",
            options=[{"label": "All Devices", "value": "All"}] +
                    [{"label": d, "value": d} for d in sorted(df["Device"].unique())],
            value="All",
            clearable=False
        )
    ], style={"width": "40%", "margin": "auto"}),

    html.Br(),
    dcc.Graph(id="daily-consumption-graph"),
    dcc.Graph(id="device-comparison-graph"),
    dcc.Graph(id="cost-trend-graph"),

    html.Hr(),
    html.Div(id="summary", style={"textAlign": "center", "fontSize": 18, "fontWeight": "bold"})
])

# -------------------------------
# 6️⃣ Callback
@app.callback(
    [Output("daily-consumption-graph", "figure"),
     Output("device-comparison-graph", "figure"),
     Output("cost-trend-graph", "figure"),
     Output("summary", "children")],
    Input("device-filter", "value")
)
def update_dashboard(selected_device):
    filtered_df = df if selected_device == "All" else df[df["Device"] == selected_device]

    # Daily energy consumption
    daily = filtered_df.groupby("Date", as_index=False)["Energy_kWh"].sum()
    fig1 = px.line(daily, x="Date", y="Energy_kWh",
                   title="Daily Energy Consumption (kWh)", markers=True, color_discrete_sequence=["#1f77b4"])

    # Total energy by device
    device_sum = df.groupby("Device", as_index=False)["Energy_kWh"].sum()
    fig2 = px.bar(device_sum, x="Device", y="Energy_kWh",
                  title="Total Energy by Device", color="Device", color_discrete_sequence=px.colors.qualitative.Set2)

    # Daily cost trend
    daily_cost = filtered_df.groupby("Date", as_index=False)["Cost"].sum()
    fig3 = px.area(daily_cost, x="Date", y="Cost", title="Daily Cost Trend", color_discrete_sequence=["#FF8800"])

    # Summary
    total_energy = filtered_df["Energy_kWh"].sum()
    total_cost = filtered_df["Cost"].sum()
    summary = f"🔋 Total Energy Used: {total_energy:.2f} kWh | 💰 Total Cost: ${total_cost:.2f}"

    return fig1, fig2, fig3, summary

# -------------------------------
# 7️⃣ Run app (Dash 2.15+)
if __name__ == "__main__":
    app.run(debug=True)
