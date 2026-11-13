from datetime import datetime, timedelta
from pathlib import Path

import duckdb
from airflow.decorators import dag, task

from aq import dropouts, fetch

SQL = Path(__file__).resolve().parents[1] / "sql" / "daily_summary.sql"

default_args = {"retries": 2, "retry_delay": timedelta(minutes=5)}


@dag(schedule="@hourly", start_date=datetime(2025, 3, 1), catchup=False, default_args=default_args, tags=["aq"])
def aq_hourly():
    @task
    def fetch_readings():
        return fetch.run()

    @task
    def flag_dropouts(_):
        return dropouts.flag()

    flag_dropouts(fetch_readings())


@dag(schedule="0 1 * * *", start_date=datetime(2025, 3, 1), catchup=False, default_args=default_args, tags=["aq"])
def aq_daily():
    @task
    def daily_summary(ds=None):
        Path("data/summary").mkdir(parents=True, exist_ok=True)
        # ds is the logical date, which for a daily run at 1am is the previous day
        duckdb.connect().execute(SQL.read_text().replace("$day", ds))

    daily_summary()


aq_hourly()
aq_daily()
