"""Load the raw OpenF1 JSON files into a DuckDB database.

Creates one table per endpoint, prefixed with raw_, holding the data exactly
as downloaded. Cleaning happens in a separate step.

Usage:
    python src/load.py
"""

import logging

import duckdb

from extract import RACE_ENDPOINTS, RAW_DIR, ROOT

DB_PATH = ROOT / "data" / "f1.duckdb"
ENDPOINTS = ["sessions"] + RACE_ENDPOINTS

logger = logging.getLogger(__name__)


def load_endpoint(con, endpoint):
    """Create (or replace) the raw table of one endpoint from all its files."""
    pattern = (RAW_DIR / endpoint / "*.json").as_posix()
    con.execute(
        f"""
        CREATE OR REPLACE TABLE raw_{endpoint} AS
        SELECT *
        FROM read_json(
            '{pattern}',
            format = 'array',
            union_by_name = true,
            sample_size = -1
        )
        """
    )
    rows = con.execute(f"SELECT count(*) FROM raw_{endpoint}").fetchone()[0]
    logger.info("raw_%s: %d rows", endpoint, rows)


def main():
    con = duckdb.connect(str(DB_PATH))
    try:
        for endpoint in ENDPOINTS:
            load_endpoint(con, endpoint)
    finally:
        con.close()
    logger.info("Database saved to %s", DB_PATH)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()