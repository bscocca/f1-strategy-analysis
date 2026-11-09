"""Build the compact data files used by the Streamlit app.

The app is deployed without the DuckDB database and the raw data, which are
not in the repository. This script exports what the app needs to app/data:
the list of races and the laps from fct_laps, plus the results saved by the
analysis notebooks.

Run it after the dbt models and notebooks 03 and 04:
    python src/export_app_data.py
"""

import shutil
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "f1.duckdb"
PROCESSED_DIR = ROOT / "data" / "processed"
APP_DATA_DIR = ROOT / "app" / "data"

ANALYSIS_FILES = [
    "tyre_degradation_by_race.parquet",
    "undercut_attempts.parquet",
    "undercut_model.json",
]

QUERIES = {
    "races": """
        select distinct session_key, season, circuit_name, race_started_at
        from fct_laps
        order by race_started_at
    """,
    "laps": """
        select
            session_key,
            driver_code,
            driver_name,
            team_name,
            team_colour,
            lap_number,
            lap_time_s,
            stint_number,
            compound,
            tyre_age_laps,
            is_pit_in_lap,
            is_pit_out_lap,
            neutralisation,
            is_representative_lap
        from fct_laps
        order by session_key, driver_code, lap_number
    """,
}


def export_tables() -> None:
    """Export the race list and the laps from the DuckDB database."""
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        for name, query in QUERIES.items():
            path = APP_DATA_DIR / f"{name}.parquet"
            con.execute(f"copy ({query}) to '{path}' (format parquet, compression zstd)")
            rows = con.execute(f"select count(*) from '{path}'").fetchone()[0]
            print(f"{path.name}: {rows:,} rows, {path.stat().st_size / 1024:,.0f} KB")


def copy_analysis_results() -> None:
    """Copy the results saved by the analysis notebooks."""
    for name in ANALYSIS_FILES:
        source = PROCESSED_DIR / name
        if not source.exists():
            raise SystemExit(
                f"{source} not found: run notebooks 03 and 04 before this script."
            )
        shutil.copy2(source, APP_DATA_DIR / name)
        print(f"{name}: copied, {source.stat().st_size / 1024:,.0f} KB")


def main() -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    export_tables()
    copy_analysis_results()


if __name__ == "__main__":
    main()