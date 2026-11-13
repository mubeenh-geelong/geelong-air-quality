import os
from pathlib import Path

import duckdb

DATA = Path(os.environ.get("AQ_DATA", "data"))


def flag(gap_hours=3):
    con = duckdb.connect()
    df = con.execute(f"""
        with pm as (
            select suburb, max(cast(until as timestamp)) as last_seen
            from read_parquet('{DATA}/raw/*/*.parquet', hive_partitioning = true)
            where pollutant = 'PM2.5' and value is not null
            group by suburb
        )
        select suburb, last_seen
        from pm
        where last_seen < now() - interval {int(gap_hours)} hour
    """).fetchdf()
    for row in df.itertuples():
        print(f"DROPOUT {row.suburb}: no PM2.5 since {row.last_seen}")
    return len(df)
