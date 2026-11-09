"""Load the data files exported by src/export_app_data.py.

Every function is cached: Streamlit reruns the whole script at each
interaction, and the cache keeps the files in memory instead of reading
them from disk every time.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_races() -> pd.DataFrame:
    """One row per race, ordered by date, with a label for menus."""
    races = pd.read_parquet(DATA_DIR / "races.parquet")
    races["label"] = races["season"].astype(str) + " " + races["circuit_name"]
    return races


@st.cache_data
def load_laps() -> pd.DataFrame:
    """One row per driver per lap, for all races."""
    return pd.read_parquet(DATA_DIR / "laps.parquet")


@st.cache_data
def load_degradation() -> pd.DataFrame:
    """Degradation per compound per race, estimated in notebook 03."""
    return pd.read_parquet(DATA_DIR / "tyre_degradation_by_race.parquet")


@st.cache_data
def load_undercut_attempts() -> pd.DataFrame:
    """Measured undercut attempts, from notebook 04."""
    return pd.read_parquet(DATA_DIR / "undercut_attempts.parquet")


@st.cache_data
def load_undercut_model() -> dict:
    """Coefficients of the logistic model of undercut success, from notebook 04."""
    return json.loads((DATA_DIR / "undercut_model.json").read_text())