"""Live KPI ingestion from the Wikimedia Pageviews API.

This is the *operations* track of the project. It fetches real, public traffic data on a
schedule so the detector runs against data nobody controls.

It deliberately does NOT replace the synthetic track. Live data has no ground-truth
labels, so precision/recall/F1 cannot be computed from it. The synthetic track exists to
measure detector quality; this track exists to prove the detector runs unattended against
data that genuinely moves.

Source: https://wikimedia.org/api/rest_v1/ - public, no API key, no authentication.
Wikimedia's policy requires a descriptive User-Agent, which is set below.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yaml


API_ROOT = "https://wikimedia.org/api/rest_v1/metrics/pageviews/aggregate"

# Wikimedia asks for a contactable User-Agent. Requests without one are rejected.
USER_AGENT = (
    "kpi-reliability-engine/1.0 "
    "(https://github.com/Kartz82/data-reliability-kpi-monitoring)"
)

LIVE_KPI_NAME = "pageviews"

# Dimension set for the live track. Mirrors the shape of the synthetic track's dimension
# list (leading entry is always kpi_name) so the same KPIMonitor/AnomalyDetector code
# paths work unchanged.
LIVE_DIMENSIONS = ["kpi_name", "project", "access", "agent"]

# Contribution hierarchy for RCA on live data: each single dimension, then the full
# interaction, so a fault isolated to one project+access+agent combination is findable.
LIVE_DIMENSION_SPECS = [
    ("project", ["project"]),
    ("access", ["access"]),
    ("agent", ["agent"]),
    ("project_access", ["project", "access"]),
    ("full_segment", ["project", "access", "agent"]),
]


class WikimediaPageviewsIngestor:
    def __init__(
        self,
        config_path: str = "config/live_monitoring_config.yaml",
        request_delay_seconds: float = 0.2,
        max_retries: int = 3,
    ):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        source = self.config.get("live_source", {})
        self.projects = source.get("projects", [])
        self.access_types = source.get("access_types", [])
        self.agent_types = source.get("agent_types", [])
        self.lookback_days = int(source.get("lookback_days", 90))
        self.request_delay_seconds = request_delay_seconds
        self.max_retries = max_retries

        if not (self.projects and self.access_types and self.agent_types):
            raise ValueError(
                "live_source config must define projects, access_types and agent_types"
            )

    def fetch(
        self,
        end_date: str | date | None = None,
        lookback_days: int | None = None,
    ) -> pd.DataFrame:
        """Fetches one row per (date, project, access, agent).

        The API only returns complete days, so the window ends yesterday by default -
        requesting today would yield a partial count that reads as a traffic collapse.
        """
        lookback_days = int(lookback_days or self.lookback_days)
        if end_date is None:
            end = date.today() - timedelta(days=1)
        elif isinstance(end_date, str):
            end = pd.Timestamp(end_date).date()
        else:
            end = end_date

        start = end - timedelta(days=lookback_days - 1)

        frames = []
        failures = []
        for project in self.projects:
            for access in self.access_types:
                for agent in self.agent_types:
                    try:
                        frames.append(self._fetch_series(project, access, agent, start, end))
                    except LiveIngestionError as error:
                        # One dead series must not sink the whole run. Record it and carry
                        # on; the caller reports partial coverage rather than pretending
                        # the missing series was zero.
                        failures.append(
                            {
                                "project": project,
                                "access": access,
                                "agent": agent,
                                "error": str(error),
                            }
                        )
                    time.sleep(self.request_delay_seconds)

        if not frames:
            raise LiveIngestionError(
                f"No live series could be fetched. Failures: {failures}"
            )

        df = pd.concat(frames, ignore_index=True)
        df = df.sort_values(["date", *LIVE_DIMENSIONS]).reset_index(drop=True)
        self.last_failures = failures
        return df

    def _fetch_series(
        self,
        project: str,
        access: str,
        agent: str,
        start: date,
        end: date,
    ) -> pd.DataFrame:
        url = (
            f"{API_ROOT}/{project}/{access}/{agent}/daily/"
            f"{start.strftime('%Y%m%d')}00/{end.strftime('%Y%m%d')}00"
        )
        payload = self._get_json(url)
        items = payload.get("items", [])
        if not items:
            raise LiveIngestionError(f"Empty payload for {project}/{access}/{agent}")

        records = [
            {
                "date": pd.Timestamp(item["timestamp"][:8]),
                "kpi_name": LIVE_KPI_NAME,
                "project": item["project"],
                "access": item["access"],
                "agent": item["agent"],
                "kpi_value": float(item["views"]),
            }
            for item in items
        ]
        return pd.DataFrame.from_records(records)

    def _get_json(self, url: str) -> dict:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        last_error = None

        for attempt in range(self.max_retries):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                # 404 means this series genuinely has no data - retrying will not help.
                if error.code == 404:
                    raise LiveIngestionError(f"404 for {url}") from error
                last_error = error
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
                last_error = error

            time.sleep(2 ** attempt)

        raise LiveIngestionError(f"Failed after {self.max_retries} attempts: {last_error}")

    @staticmethod
    def write_raw(df: pd.DataFrame, output_path: str | Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        out = df.copy()
        out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
        out.to_csv(output_path, index=False)
        return output_path


class LiveIngestionError(RuntimeError):
    pass
