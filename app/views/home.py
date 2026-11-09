"""Home page: what the app is about and what data it uses."""

import streamlit as st

from data_loading import load_races

races = load_races()

st.title("F1 Strategy Explorer")
st.write(
    "How much do tyres degrade on each circuit, and when does pitting before "
    "the car ahead pay off? An analysis of every Formula 1 race from 2023 to 2026."
)
st.caption(
    f"Data: {len(races)} races from {races['season'].min()} to "
    f"{races['season'].max()}, from the OpenF1 API."
)

st.subheader("What you can explore")
st.markdown(
    """
    - **Tyre degradation**: how much time each compound loses per lap of age, by circuit and season.
    - **Undercut calculator**: the probability that an undercut succeeds, given the gap to the car ahead and the circuit.
    - **Race explorer**: lap times and tyre strategies of any race, driver by driver.
    """
)