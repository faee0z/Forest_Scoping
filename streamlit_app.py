import random
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Forest Fire Risk Dashboard", layout="wide")

REGION_NAMES = ["North Ridge", "River Valley", "East Pine", "South Basin"]


def get_status(value: float, metric: str) -> str:
    """Return safe / warning / critical based on metric thresholds."""
    if metric == "temperature":
        if value >= 40:
            return "critical"
        if value >= 32:
            return "warning"
    elif metric == "humidity":
        if value <= 15:
            return "critical"
        if value <= 25:
            return "warning"
    elif metric == "soil_moisture":
        if value <= 10:
            return "critical"
        if value <= 20:
            return "warning"
    elif metric == "gas":
        if value >= 650:
            return "critical"
        if value >= 400:
            return "warning"
    elif metric == "flame":
        if value >= 75:
            return "critical"
        if value >= 45:
            return "warning"

    return "safe"


def overall_region_status(metrics: Dict[str, float]) -> str:
    """Region-level risk status based on the worst sensor condition."""
    statuses = [
        get_status(metrics["temperature"], "temperature"),
        get_status(metrics["humidity"], "humidity"),
        get_status(metrics["soil_moisture"], "soil_moisture"),
        get_status(metrics["gas"], "gas"),
        get_status(metrics["flame_avg"], "flame"),
    ]

    if "critical" in statuses:
        return "critical"
    if "warning" in statuses:
        return "warning"
    return "safe"


def status_color(status: str) -> str:
    palette = {
        "safe": "#22c55e",
        "warning": "#f59e0b",
        "critical": "#ef4444",
    }
    return palette.get(status, "#94a3b8")


def region_seed(region_name: str) -> Dict[str, float]:
    base_values = {
        "North Ridge": {
            "temperature": 34,
            "humidity": 18,
            "soil_moisture": 16,
            "gas": 480,
            "flame_avg": 58,
        },
        "River Valley": {
            "temperature": 29,
            "humidity": 42,
            "soil_moisture": 30,
            "gas": 210,
            "flame_avg": 12,
        },
        "East Pine": {
            "temperature": 36,
            "humidity": 20,
            "soil_moisture": 15,
            "gas": 540,
            "flame_avg": 68,
        },
        "South Basin": {
            "temperature": 31,
            "humidity": 28,
            "soil_moisture": 25,
            "gas": 260,
            "flame_avg": 30,
        },
    }
    return base_values[region_name]


def generate_region_data(region_name: str) -> Dict[str, object]:
    seed = region_seed(region_name)
    values = {}

    for metric, base in seed.items():
        noise = random.uniform(-0.08, 0.08)
        value = base * (1 + noise)
        values[metric] = round(value, 2)

    flame_sensors = [round(random.uniform(0, 100), 1) for _ in range(5)]
    values["flame_sensors"] = flame_sensors
    values["status"] = overall_region_status(values)
    values["flame_status"] = [get_status(s, "flame") for s in flame_sensors]
    return values


def build_region_rows() -> List[Dict[str, object]]:
    rows = []
    for region in REGION_NAMES:
        record = generate_region_data(region)
        rows.append(
            {
                "Region": region,
                "Temperature (°C)": record["temperature"],
                "Humidity (%)": record["humidity"],
                "Soil Moisture (%)": record["soil_moisture"],
                "Gas (ppm)": record["gas"],
                "Flame Avg": record["flame_avg"],
                "Status": record["status"],
            }
        )
    return rows


region_rows = build_region_rows()
df = pd.DataFrame(region_rows)

st.title("🌲 Forest Fire Risk Monitoring Dashboard")
st.caption("IoT forest monitoring for temperature, humidity, soil moisture, gas, and 5 flame sensors.")

with st.sidebar:
    st.header("Controls")
    region_filter = st.selectbox("Select forest region", ["All regions", *REGION_NAMES])
    auto_refresh = st.toggle("Auto-refresh simulation", value=True)
    refresh_interval = st.slider("Refresh interval (seconds)", 2, 20, 5)

if region_filter == "All regions":
    filtered_rows = df
else:
    filtered_rows = df[df["Region"] == region_filter]

status_order = {"safe": 0, "warning": 1, "critical": 2}
filtered_rows = filtered_rows.sort_values("Status", key=lambda s: s.map(status_order), ascending=False)

st.subheader("Overall region status")
cols = st.columns(4)
for idx, region in enumerate(filtered_rows["Region"].tolist()[:4]):
    status = filtered_rows.iloc[idx]["Status"]
    with cols[idx]:
        st.markdown(
            f"""
            <div style="background-color: {status_color(status)}; border-radius: 12px; padding: 18px; color: white; text-align: center;">
                <div style="font-size: 0.85rem; opacity: 0.9;">{region}</div>
                <div style="font-size: 1.5rem; font-weight: bold; text-transform: capitalize;">{status}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

left_col, right_col = st.columns([1.6, 1])

with left_col:
    st.subheader("Sensor readings")
    metric_cols = st.columns(4)
    for i, metric in enumerate(["Temperature (°C)", "Humidity (%)", "Soil Moisture (%)", "Gas (ppm)"]):
        with metric_cols[i]:
            value = float(filtered_rows.iloc[0][metric]) if not filtered_rows.empty else 0.0
            label = metric
            if metric == "Temperature (°C)":
                status = get_status(value, "temperature")
            elif metric == "Humidity (%)":
                status = get_status(value, "humidity")
            elif metric == "Soil Moisture (%)":
                status = get_status(value, "soil_moisture")
            else:
                status = get_status(value, "gas")

            st.markdown(
                f"""
                <div style="background-color: #0f172a; border: 1px solid {status_color(status)}; border-radius: 12px; padding: 16px; margin-bottom: 10px;">
                    <div style="font-size: 0.75rem; color: #cbd5e1;">{label}</div>
                    <div style="font-size: 1.6rem; font-weight: bold; color: white;">{value}</div>
                    <div style="font-size: 0.8rem; color: {status_color(status)}; text-transform: capitalize;">{status}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.subheader("Regional sensor summary")
    st.dataframe(filtered_rows, use_container_width=True, hide_index=True)

with right_col:
    st.subheader("Forest map")

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#e0f2fe")

    positions = {
        "North Ridge": (2.4, 7.2),
        "River Valley": (6.3, 6.5),
        "East Pine": (8.0, 3.7),
        "South Basin": (3.0, 2.0),
    }

    for region in REGION_NAMES:
        if region_filter != "All regions" and region != region_filter:
            continue
        record = generate_region_data(region)
        x, y = positions[region]
        color = status_color(record["status"])
        ax.scatter(x, y, s=340, color=color, edgecolors="black", linewidths=1.2)
        ax.text(x, y + 0.35, region, ha="center", va="bottom", fontsize=9, weight="bold")

    forest_shape = plt.Circle((5, 5), 5, color="#166534", alpha=0.08)
    ax.add_patch(forest_shape)

    st.pyplot(fig)

    st.subheader("Flame sensor array")
    region_select = filtered_rows["Region"].iloc[0] if not filtered_rows.empty else REGION_NAMES[0]
    flame_data = generate_region_data(region_select)["flame_sensors"]
    flare_cols = st.columns(5)
    for i, flame in enumerate(flame_data):
        status = get_status(flame, "flame")
        with flare_cols[i]:
            st.markdown(
                f"""
                <div style="background-color: {status_color(status)}; border-radius: 10px; padding: 12px; color: white; text-align: center; min-height: 100px;">
                    <div style="font-size: 0.7rem; opacity: 0.9;">F{i + 1}</div>
                    <div style="font-size: 1.4rem; font-weight: bold;">{flame}</div>
                    <div style="font-size: 0.7rem; text-transform: capitalize;">{status}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.subheader("Status legend")
legend_cols = st.columns(3)
for col, status in zip(legend_cols, ["safe", "warning", "critical"]):
    with col:
        st.markdown(
            f"""
            <div style="background-color: {status_color(status)}; color: white; border-radius: 10px; padding: 12px; text-align: center; text-transform: capitalize;">
                {status}
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")
st.caption("This dashboard is designed for a Wokwi-based IoT forest monitoring project. Replace the simulated values with live sensor data from your board when connected.")
