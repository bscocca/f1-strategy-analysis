"""Race explorer: lap times and tyre strategies of a single race."""

import plotly.express as px
import streamlit as st

from data_loading import load_laps, load_races

COMPOUND_COLOURS = {
    "SOFT": "#DA291C",
    "MEDIUM": "#FFD12E",
    "HARD": "#A0A0A0",
    "INTERMEDIATE": "#43B02A",
    "WET": "#0067AD",
    "UNKNOWN": "#555555",
}
COMPOUND_ORDER = list(COMPOUND_COLOURS)
DEFAULT_RACE = "2025 Monza"
DEFAULT_DRIVER_COUNT = 3

races = load_races().iloc[::-1]  # most recent race first in the menu
laps = load_laps()

st.title("Race explorer")
st.write("Lap times and tyre strategies of a single race.")

labels = races["label"].tolist()
race_label = st.selectbox(
    "Race",
    labels,
    index=labels.index(DEFAULT_RACE) if DEFAULT_RACE in labels else 0,
)
session_key = races.loc[races["label"] == race_label, "session_key"].iloc[0]

race_laps = (
    laps[laps["session_key"] == session_key]
    .sort_values(["driver_code", "lap_number"])
    .copy()
)
# Laps not covered by any OpenF1 stint (usually the last lap or the lap of a
# retirement) keep the compound of the driver's previous lap
race_laps["compound"] = (
    race_laps.groupby("driver_code")["compound"].ffill().fillna("UNKNOWN")
)

# Approximate finishing order: most laps completed first, then lowest total time
finish = (
    race_laps.groupby("driver_code")
    .agg(laps_completed=("lap_number", "max"), total_time_s=("lap_time_s", "sum"))
    .sort_values(["laps_completed", "total_time_s"], ascending=[False, True])
)
drivers = finish.index.tolist()

selected_drivers = st.multiselect(
    "Drivers",
    drivers,
    default=drivers[:DEFAULT_DRIVER_COUNT],
    help="Ordered by approximate finishing position.",
)

# Neutralised periods: consecutive laps with the same safety car, VSC or red flag
lap_status = (
    race_laps.dropna(subset=["neutralisation"]).groupby("lap_number")["neutralisation"].first()
)
periods = []
for lap, status in lap_status.items():
    if periods and periods[-1]["status"] == status and periods[-1]["end"] == lap - 1:
        periods[-1]["end"] = lap
    else:
        periods.append({"status": status, "start": lap, "end": lap})

# Lap times of the selected drivers
st.subheader("Lap times")
representative_only = st.checkbox(
    "Representative laps only",
    value=True,
    help="Hide lap 1, in-laps, out-laps and laps under safety car, VSC or red flag.",
)

shown = race_laps[race_laps["driver_code"].isin(selected_drivers)].copy()
if representative_only:
    # Blank the hidden laps instead of dropping them, so the line breaks there
    shown.loc[~shown["is_representative_lap"], "lap_time_s"] = None

if selected_drivers:
    lap_times = px.line(
        shown,
        x="lap_number",
        y="lap_time_s",
        color="driver_code",
        markers=True,
        category_orders={"driver_code": selected_drivers},
        hover_data={"compound": True, "tyre_age_laps": True},
        labels={
            "lap_number": "Lap",
            "lap_time_s": "Lap time (s)",
            "driver_code": "Driver",
            "compound": "Compound",
            "tyre_age_laps": "Tyre age (laps)",
        },
    )
    for period in periods:
        lap_times.add_vrect(
            x0=period["start"] - 0.5,
            x1=period["end"] + 0.5,
            fillcolor="grey",
            opacity=0.2,
            line_width=0,
            annotation_text=period["status"],
            annotation_position="top left",
        )
    st.plotly_chart(lap_times)
else:
    st.write("Select at least one driver to see the lap times.")

# Tyre strategies of the whole field.
# Stints are rebuilt from the compound alone: OpenF1's stint number and pit-out
# flag are inconsistent in some wet races (overlapping stints, pit-out laps
# shifted by one lap), while the compound of each lap is reliable.
st.subheader("Tyre strategies")
previous_compound = race_laps.groupby("driver_code")["compound"].shift()
starts_stint = race_laps["compound"] != previous_compound
race_laps["stint"] = starts_stint.groupby(race_laps["driver_code"]).cumsum()

stints = (
    race_laps.groupby(["driver_code", "stint"])
    .agg(
        compound=("compound", "first"),
        start_lap=("lap_number", "min"),
        end_lap=("lap_number", "max"),
    )
    .reset_index()
)
stints["laps"] = stints["end_lap"] - stints["start_lap"] + 1
stints["base"] = stints["start_lap"] - 1

# With category_orders, Plotly Express already draws the first driver at the top
strategy = px.bar(
    stints,
    x="laps",
    y="driver_code",
    base="base",
    orientation="h",
    color="compound",
    color_discrete_map=COMPOUND_COLOURS,
    category_orders={"driver_code": drivers, "compound": COMPOUND_ORDER},
    hover_data={"start_lap": True, "end_lap": True, "laps": True, "base": False},
    labels={
        "laps": "Laps",
        "driver_code": "",
        "compound": "Compound",
        "start_lap": "From lap",
        "end_lap": "To lap",
    },
    height=max(400, 28 * len(drivers)),
)
strategy.update_traces(marker_line_color="rgba(0, 0, 0, 0.6)", marker_line_width=1)
strategy.update_xaxes(title="Lap")
st.plotly_chart(strategy)

st.caption(
    "Drivers are ordered by approximate finishing position: laps completed, then total "
    "race time. Shaded areas mark laps under safety car (SC), virtual safety car (VSC) "
    "or red flag (RED). Consecutive stints on the same compound appear as a single bar."
)