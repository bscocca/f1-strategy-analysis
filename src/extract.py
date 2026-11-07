"""Download raw OpenF1 data for Formula 1 races.

Raw files are stored exactly as returned by the API, one JSON file per
endpoint and race: data/raw/<endpoint>/<session_key>.json
"""

import json
import logging
from pathlib import Path

from openf1_client import OpenF1Client

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

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

logger = logging.getLogger(__name__)


def raw_path(endpoint, session_key):
    return RAW_DIR / endpoint / f"{session_key}.json"


def extract_race(client, session_key):
    """Download every endpoint of one race, skipping files already saved."""
    for endpoint in RACE_ENDPOINTS:
        path = raw_path(endpoint, session_key)
        if path.exists():
            logger.info("%s/%s already downloaded, skipping", endpoint, session_key)
            continue

        records = client.get_json(endpoint, session_key=session_key)

        # Write to a temporary file first, then rename it: an interrupted
        # download never leaves a half-written file that looks complete
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(records))
        tmp_path.replace(path)

        logger.info("%s/%s: %d records", endpoint, session_key, len(records))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    extract_race(OpenF1Client(), session_key=9912)