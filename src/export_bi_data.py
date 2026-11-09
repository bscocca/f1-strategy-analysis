"""Build the data files for the BI dashboards.

- bi/f1_strategy.xlsx, for Tableau Public: tyre degradation and undercut
  attempts, from the results saved by notebooks 03 and 04.
- bi/f1_pit_stops.xlsx, for Looker Studio: one row per pit stop, from the
  DuckDB database built by the pipeline.

Excel is used instead of CSV because it stores numbers as numbers whatever
the language settings of the computer: in a CSV, a decimal point can be
misread in locales that use a decimal comma, such as Italian.

Run it after the dbt models and notebooks 03 and 04:
    python src/export_bi_data.py
"""

from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "f1.duckdb"
PROCESSED_DIR = ROOT / "data" / "processed"
BI_DIR = ROOT / "bi"

STRATEGY_PATH = BI_DIR / "f1_strategy.xlsx"
PIT_STOPS_PATH = BI_DIR / "f1_pit_stops.xlsx"

STRATEGY_SHEETS = {
    "degradation": "tyre_degradation_by_race.parquet",
    "undercut_attempts": "undercut_attempts.parquet",
}

# Same threshold as notebook 04: a green-flag stop more than 5 s slower than
# the race median is a penalty, a mistake or a repair, not a normal stop
SLOW_STOP_MARGIN_S = 5.0

PIT_STOPS_QUERY = f"""
    with race_drivers as (
        select distinct
            session_key,
            driver_number,
            season,
            circuit_name,
            cast(race_started_at as date) as race_date,
            driver_code,
            team_name
        from fct_laps
    ),

    -- Track status of each lap: safety car, VSC, red flag or green (null)
    lap_status as (
        select session_key, driver_number, lap_number, neutralisation
        from fct_laps
    ),

    stops as (
        select
            p.session_key,
            d.season,
            d.circuit_name,
            d.race_date,
            d.team_name,
            d.driver_code,
            p.lap_number,
            p.pit_lane_time_s,
            -- Condition on the lap the driver entered the pit lane
            case l.neutralisation
                when 'RED' then 'Red flag'
                when 'SC' then 'Safety car'
                when 'VSC' then 'Virtual safety car'
                else 'Green flag'
            end as stop_condition
        from stg_openf1__pit_stops as p
        inner join race_drivers as d
            on p.session_key = d.session_key
            and p.driver_number = d.driver_number
        left join lap_status as l
            on p.session_key = l.session_key
            and p.driver_number = l.driver_number
            and p.lap_number = l.lap_number
        where p.pit_lane_time_s is not null
    ),

    -- Typical pit lane time of each race, from green-flag stops only: under a
    -- red flag cars wait in the pit lane for the whole suspension
    green_medians as (
        select session_key, median(pit_lane_time_s) as green_median_s
        from stops
        where stop_condition = 'Green flag'
        group by session_key
    )

    select
        s.season,
        s.circuit_name,
        s.race_date,
        s.team_name,
        s.driver_code,
        s.lap_number,
        s.stop_condition,
        s.pit_lane_time_s,
        s.pit_lane_time_s - g.green_median_s as time_vs_green_median_s,
        s.stop_condition = 'Green flag'
            and s.pit_lane_time_s > g.green_median_s + {SLOW_STOP_MARGIN_S} as is_slow_stop
    from stops as s
    left join green_medians as g
        on s.session_key = g.session_key
    order by s.race_date, s.lap_number, s.driver_code
"""


def export_strategy() -> None:
    """Degradation and undercut attempts, for Tableau."""
    tables = {}
    for sheet, file_name in STRATEGY_SHEETS.items():
        source = PROCESSED_DIR / file_name
        if not source.exists():
            raise SystemExit(
                f"{source} not found: run notebooks 03 and 04 before this script."
            )
        tables[sheet] = pd.read_parquet(source)

    with pd.ExcelWriter(STRATEGY_PATH) as writer:
        for sheet, table in tables.items():
            table.to_excel(writer, sheet_name=sheet, index=False)
            print(f"{sheet}: {len(table):,} rows, columns: {', '.join(table.columns)}")
    print(f"Saved {STRATEGY_PATH.relative_to(ROOT)}")


def export_pit_stops() -> None:
    """One row per pit stop, for Looker Studio."""
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        pit_stops = con.sql(PIT_STOPS_QUERY).df()

    pit_stops.to_excel(PIT_STOPS_PATH, sheet_name="pit_stops", index=False)
    print(f"pit_stops: {len(pit_stops):,} rows, columns: {', '.join(pit_stops.columns)}")
    print(pit_stops["stop_condition"].value_counts().to_string())
    print(f"Slow green-flag stops: {int(pit_stops['is_slow_stop'].sum())}")
    print(f"Saved {PIT_STOPS_PATH.relative_to(ROOT)}")


def main() -> None:
    BI_DIR.mkdir(parents=True, exist_ok=True)
    export_strategy()
    export_pit_stops()


if __name__ == "__main__":
    main()