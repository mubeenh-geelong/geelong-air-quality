# Geelong air quality pipeline

Hourly air quality readings from EPA Victoria's monitoring sites around Geelong, landed as Parquet and summarised by suburb
with DuckDB. I ran it on an old laptop at home for about six months in 2025, mainly to get hands-on with Airflow outside work.

## How it works

1. `fetch_readings` (hourly) calls the EPA Victoria Environment Monitoring API for each site in `aq/sites.py` and writes one
   Parquet file per site per hour under `data/raw/date=YYYY-MM-DD/`.
2. `flag_dropouts` (hourly) marks a site as dropped out if it has no PM2.5 reading for 3 hours in a row. Dropouts were more
   common than I expected, usually overnight.
3. `daily_summary` (daily, 1am) runs `sql/daily_summary.sql` over the previous day's Parquet and writes one row per suburb
   per pollutant to `data/summary/`.

## Setup

You need a free API key from EPA Victoria's developer portal.

```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export EPA_API_KEY=...
export AIRFLOW_HOME=$(pwd)
airflow standalone
```

To look at the data without Airflow:

```
python -m aq.fetch --hours 24
duckdb -c "select * from read_parquet('data/raw/*/*.parquet') limit 20"
```

## Things I would change

- Parquet files per hour per site is far too many small files. Should have compacted daily.
- The API field names changed once while this was running. `aq/fetch.py` handles both, which is ugly.
- No backfill. If the laptop was off, that hour is just gone.
