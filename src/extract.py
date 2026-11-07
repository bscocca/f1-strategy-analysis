"""Download raw OpenF1 data for Formula 1 races.

Raw files are stored exactly as returned by the API:
- data/raw/sessions/<year>.json: the races of a season
- data/raw/<endpoint>/<session_key>.json: one file per endpoint and race

Usage:
    python src/extract.py                       # all default seasons
    python src/extract.py --seasons 2025 2026   # selected seasons
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from openf1_client import LiveSessionLockError, OpenF1Client

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

# OpenF1 historical data starts in 2023
DEFAULT_SEASONS = [2023, 2024, 2025, 2026]

# Endpoints downloaded for every race
RACE_ENDPOINTS = [
    "laps",
    "stints",
    "pit",
    "race_control",
    "drivers",
    "weather",
    "session_result",
]

# OpenF1 treats data as live until 30 minutes after a session ends
LIVE_WINDOW = timedelta(minutes=30)

logger = logging.getLogger(__name__)


def raw_path(endpoint, key):
    return RAW_DIR / endpoint / f"{key}.json"


def write_json(path, records):
    """Write to a temporary file first, then rename it: an interrupted
    download never leaves a half-written file that looks complete."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(records))
    tmp_path.replace(path)


def list_races(client, year):
    """Return the finished, non-cancelled races of a season in date order."""
    sessions = client.get_json("sessions", year=year, session_name="Race")
    write_json(raw_path("sessions", year), sessions)

    now = datetime.now(timezone.utc)
    races = [
        session
        for session in sessions
        if not session.get("is_cancelled")
        and datetime.fromisoformat(session["date_end"]) + LIVE_WINDOW < now
    ]
    # ISO 8601 dates in the same time zone sort correctly as text
    return sorted(races, key=lambda session: session["date_start"])


def extract_race(client, session_key):
    """Download every endpoint of one race, skipping files already saved."""
    for endpoint in RACE_ENDPOINTS:
        path = raw_path(endpoint, session_key)
        if path.exists():
            logger.info("%s/%s already downloaded, skipping", endpoint, session_key)
            continue

        records = client.get_json(endpoint, session_key=session_key)
        write_json(path, records)
        logger.info("%s/%s: %d records", endpoint, session_key, len(records))


def main():
    parser = argparse.ArgumentParser(description="Download raw OpenF1 race data.")
    parser.add_argument(
        "--seasons", nargs="+", type=int, default=DEFAULT_SEASONS,
        help="seasons to download (default: %(default)s)",
    )
    args = parser.parse_args()

    client = OpenF1Client()
    try:
        for year in args.seasons:
            races = list_races(client, year)
            logger.info("Season %d: %d finished races", year, len(races))

            for i, race in enumerate(races, start=1):
                logger.info("[%d, %d/%d] %s", year, i, len(races), race["circuit_short_name"])
                extract_race(client, race["session_key"])
    except LiveSessionLockError as exc:
        logger.error("%s Files already downloaded are kept.", exc)
        sys.exit(1)

    logger.info("Done")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()