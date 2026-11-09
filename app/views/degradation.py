"""Tyre degradation by circuit and season, estimated in notebook 03."""

import plotly.express as px
import streamlit as st

from data_loading import load_degradation

COMPOUND_COLOURS = {"SOFT": "#DA291C", "MEDIUM": "#FFD12E", "HARD": "#A0A0A0"}
COMPOUND_ORDER = ["SOFT", "MEDIUM", "HARD"]
DEFAULT_CIRCUIT = "Sakhir"

degradation = load_degradation()

st.title("Tyre degradation")
st.write(
    "How much lap time each compound loses per lap of tyre age, "
    "once fuel burn and the pace of each driver are accounted for."
)
st.caption(
    "Estimated race by race with a regression of lap time on driver, lap number "
    "(fuel burn) and tyre age by compound. Error bars are 95% confidence intervals. "
    "Compounds with fewer than 50 representative laps in a race are not estimated."
)

circuits = sorted(degradation["circuit_name"].unique())
circuit = st.selectbox(
    "Circuit",
    circuits,
    index=circuits.index(DEFAULT_CIRCUIT) if DEFAULT_CIRCUIT in circuits else 0,
)

# Degradation by compound and season for the selected circuit
selected = degradation[degradation["circuit_name"] == circuit].copy()
selected["season"] = selected["season"].astype(str)
selected["error_plus"] = selected["ci_high"] - selected["degradation_s_per_lap"]
selected["error_minus"] = selected["degradation_s_per_lap"] - selected["ci_low"]

by_season = px.scatter(
    selected,
    x="season",
    y="degradation_s_per_lap",
    color="compound",
    error_y="error_plus",
    error_y_minus="error_minus",
    color_discrete_map=COMPOUND_COLOURS,
    category_orders={
        "compound": COMPOUND_ORDER,
        "season": sorted(selected["season"].unique()),
    },
    hover_data={
        "degradation_s_per_lap": ":.3f",
        "laps": True,
        "error_plus": False,
        "error_minus": False,
    },
    labels={
        "season": "Season",
        "degradation_s_per_lap": "Degradation (s per lap of tyre age)",
        "compound": "Compound",
        "laps": "Laps",
    },
    title=f"{circuit}: degradation by season",
)
by_season.update_traces(marker_size=11)
# Seasons are categories: without this, Plotly converts "2023" back to a number
by_season.update_xaxes(type="category")
by_season.update_layout(scattermode="group")
by_season.add_hline(y=0, line_color="grey", line_width=1)
st.plotly_chart(by_season)

# All circuits, ranked by average degradation
st.subheader("How it compares with other circuits")
st.caption("Average over races of the mean degradation of the compounds estimated in each race.")

by_circuit = (
    degradation.groupby(["circuit_name", "session_key"])["degradation_s_per_lap"]
    .mean()
    .groupby("circuit_name")
    .mean()
    .sort_values()
    .reset_index()
)
by_circuit["selected"] = by_circuit["circuit_name"] == circuit

ranking = px.bar(
    by_circuit,
    x="degradation_s_per_lap",
    y="circuit_name",
    orientation="h",
    color="selected",
    color_discrete_map={True: "#4C72B0", False: "#B8C4D6"},
    hover_data={"degradation_s_per_lap": ":.3f", "selected": False},
    labels={
        "degradation_s_per_lap": "Average degradation (s per lap of tyre age)",
        "circuit_name": "",
    },
    height=max(400, 24 * len(by_circuit)),
)
ranking.update_layout(showlegend=False)
st.plotly_chart(ranking)