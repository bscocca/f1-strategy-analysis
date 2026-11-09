"""Undercut calculator, based on the logistic model estimated in notebook 04."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from data_loading import load_circuit_degradation, load_undercut_attempts, load_undercut_model

DEFAULT_CIRCUIT = "Sakhir"
DEFAULT_GAP_S = 1.5
MAX_GAP_S = 3.0


def success_probability(gap_s, degradation_cs, params):
    """Probability of success from the logistic model.

    gap_s: gap to the car ahead before the stop, in seconds (a number or an array).
    degradation_cs: degradation of the circuit, in hundredths of a second per lap.
    """
    log_odds = (
        params["Intercept"]
        + params["gap_before_s"] * gap_s
        + params["degradation_cs"] * degradation_cs
    )
    return 1 / (1 + np.exp(-log_odds))


circuit_degradation = load_circuit_degradation()
attempts = load_undercut_attempts()
model = load_undercut_model()
params = model["params"]

st.title("Undercut calculator")
st.write(
    "You are behind another car and thinking of pitting first. "
    "How likely is it that you come out ahead once both of you have stopped?"
)

circuits = sorted(circuit_degradation.index)
left, right = st.columns(2)

with left:
    circuit = st.selectbox(
        "Circuit",
        circuits,
        index=circuits.index(DEFAULT_CIRCUIT) if DEFAULT_CIRCUIT in circuits else 0,
    )
    gap = st.slider(
        "Gap to the car ahead before the stop (s)",
        min_value=0.1,
        max_value=MAX_GAP_S,
        value=DEFAULT_GAP_S,
        step=0.1,
    )

degradation_cs = circuit_degradation[circuit] * 100
probability = success_probability(gap, degradation_cs, params)

# Gap at which the probability is exactly 50%: where the log-odds are zero
even_gap = -(params["Intercept"] + params["degradation_cs"] * degradation_cs) / params["gap_before_s"]

with right:
    st.metric("Probability of success", f"{probability:.0%}")
    st.write(
        f"Tyres at {circuit} lose on average {degradation_cs / 100:.3f} s per lap of age."
    )
    if even_gap <= 0:
        st.write("The undercut has less than an even chance here at any gap.")
    elif even_gap >= MAX_GAP_S:
        st.write(f"The undercut has at least an even chance here at any gap up to {MAX_GAP_S:.0f} s.")
    else:
        st.write(
            f"The undercut has at least an even chance here when the gap is below {even_gap:.1f} s."
        )

# Probability as the gap changes, for the selected circuit
gaps = np.arange(0.1, MAX_GAP_S + 0.01, 0.05)
curve = pd.DataFrame(
    {"gap_before_s": gaps, "probability": success_probability(gaps, degradation_cs, params)}
)

chart = px.line(
    curve,
    x="gap_before_s",
    y="probability",
    labels={
        "gap_before_s": "Gap to the car ahead before the stop (s)",
        "probability": "Probability of success",
    },
    title=f"{circuit}: probability of success by gap",
)
chart.add_vline(x=gap, line_dash="dash", line_color="grey")
chart.add_hline(y=0.5, line_dash="dot", line_color="grey")
chart.update_yaxes(range=[0, 1], tickformat=".0%")
chart.update_traces(hovertemplate="Gap %{x:.2f} s: %{y:.0%}<extra></extra>")
st.plotly_chart(chart)

st.caption(
    f"Logistic model fitted on {model['n_attempts']} undercut attempts from 2023 to 2026, "
    "with the initial gap and the degradation of the race as inputs. "
    "Here the degradation is the average of the circuit over all its races. "
    "Success means the attacker is ahead two laps after the stop of the car in front."
)

# Real attempts measured at the selected circuit
st.subheader(f"Undercut attempts measured at {circuit}")
past = attempts[attempts["circuit_name"] == circuit].sort_values(["season", "attacker_pit_lap"])

if past.empty:
    st.write("No undercut attempts were measured at this circuit.")
else:
    table = pd.DataFrame(
        {
            "Season": past["season"].astype(str),
            "Attacker": past["attacker_code"],
            "Defender": past["defender_code"],
            "Attacker pit lap": past["attacker_pit_lap"],
            "Gap before (s)": past["gap_before_s"],
            "Gain (s)": past["gain_s"],
            "Success": past["success"].map({True: "Yes", False: "No"}),
        }
    )
    st.dataframe(
        table,
        hide_index=True,
        column_config={
            "Gap before (s)": st.column_config.NumberColumn(format="%.2f"),
            "Gain (s)": st.column_config.NumberColumn(format="%.2f"),
        },
    )