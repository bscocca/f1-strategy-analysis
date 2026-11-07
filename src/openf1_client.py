"""Client for the OpenF1 API (https://openf1.org).

Respects the API rate limit, retries on transient errors and stops with a
clear error when the API is locked during a live session.
"""

import logging
import time

import pandas as pd
import requests

BASE_URL = "https://api.openf1.org/v1"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

logger = logging.getLogger(__name__)


class LiveSessionLockError(Exception):
    """The API rejects requests because a live session is in progress."""


class OpenF1Client:
    def __init__(self, min_interval=2.1, timeout=30, max_retries=5):
        self.min_interval = min_interval
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self._last_request = 0.0

    def _wait_for_slot(self):
        """Sleep just enough to stay within the requests-per-minute limit."""
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request = time.monotonic()

    def get_json(self, endpoint, **params):
        """Query an endpoint and return the records exactly as sent by the API."""
        url = f"{BASE_URL}/{endpoint}"

        for attempt in range(1, self.max_retries + 1):
            self._wait_for_slot()

            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout) as exc:
                problem = f"network error ({exc.__class__.__name__})"
            else:
                if response.status_code == 200:
                    return response.json()
                if response.status_code == 404:
                    # No data for this query (e.g. a race without pit stops)
                    return []
                if response.status_code == 401:
                    raise LiveSessionLockError(
                        "OpenF1 is locked during a live session. "
                        "Retry from 30 minutes after the session ends."
                    )
                if response.status_code not in RETRYABLE_STATUS:
                    response.raise_for_status()
                problem = f"status {response.status_code}"

            # Exponential backoff: 2, 4, 8, 16, 32 seconds
            delay = 2**attempt
            logger.warning(
                "%s on /%s, attempt %d of %d, retrying in %d s",
                problem, endpoint, attempt, self.max_retries, delay,
            )
            time.sleep(delay)

        raise RuntimeError(f"/{endpoint} did not respond after {self.max_retries} attempts")

    def get(self, endpoint, **params):
        """Query an endpoint and return the result as a DataFrame."""
        return pd.DataFrame(self.get_json(endpoint, **params))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    client = OpenF1Client()
    races = client.get("sessions", year=2025, session_name="Race")

    print(f"Races in 2025: {len(races)}")
    print(races[["session_key", "circuit_short_name", "date_start"]].to_string(index=False))