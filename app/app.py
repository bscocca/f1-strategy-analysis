"""F1 Strategy Explorer: tyre degradation and undercut analysis, 2023-2026."""

import streamlit as st

st.set_page_config(page_title="F1 Strategy Explorer", layout="wide")

st.title("F1 Strategy Explorer")
st.write(
    "How much do tyres degrade on each circuit, and when does pitting before "
    "the car ahead pay off? An analysis of every Formula 1 race from 2023 to 2026."
)

st.subheader("What you can explore")
st.markdown(
    """
    - **Tyre degradation**: how much time each compound loses per lap of age, by circuit and season.
    - **Undercut calculator**: the probability that an undercut succeeds, given the gap to the car ahead and the circuit.
    - **Race explorer**: lap times and tyre strategies of any race, driver by driver.
    """
)