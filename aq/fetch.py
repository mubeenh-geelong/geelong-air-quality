import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import requests

from .sites import POLLUTANTS, SITES

BASE = "https://gateway.api.epa.vic.gov.au/environmentMonitoring/v1"
OUT = Path(os.environ.get("AQ_DATA", "data")) / "raw"


def get_site(site_id, key):
    r = requests.get(f"{BASE}/sites/{site_id}/parameters", headers={"X-API-Key": key}, timeout=30)
    r.raise_for_status()
    return r.json()


def readings_from(payload, suburb):
    rows = []
    for p in payload.get("parameters", []):
        name = p.get("name")
        if name not in POLLUTANTS:
            continue
        # the API renamed timeSeriesReadings -> readings at some point in 2025
        for series in p.get("timeSeriesReadings", p.get("readings", [])):
            for r in series.get("readings", [series]):
                value = r.get("averageValue", r.get("value"))
                rows.append({
                    "suburb": suburb,
                    "pollutant": name,
                    "value": float(value) if value is not None else None,
                    "unit": r.get("unit"),
                    "since": r.get("since"),
                    "until": r.get("until"),
                })
    return rows


def run(hours_label=None):
    key = os.environ["EPA_API_KEY"]
    now = datetime.now(timezone.utc)
    part = OUT / f"date={now:%Y-%m-%d}"
    part.mkdir(parents=True, exist_ok=True)
    written = 0
    for suburb, site_id in SITES.items():
        try:
            rows = readings_from(get_site(site_id, key), suburb)
        except requests.RequestException as e:
            print(f"{suburb}: {e}")
            continue
        if rows:
            pq.write_table(pa.Table.from_pylist(rows), part / f"{site_id}_{now:%H}.parquet")
            written += len(rows)
    print(f"wrote {written} readings to {part}")
    return written


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=1, help="unused for now, the API returns the latest window")
    run(ap.parse_args().hours)
