-- one row per suburb and pollutant for the given day
-- $day is replaced by the DAG, e.g. 2025-06-14
copy (
    select
        suburb,
        pollutant,
        date_trunc('day', cast(since as timestamp)) as day,
        count(*)                        as n_readings,
        round(avg(value), 2)            as mean_value,
        round(max(value), 2)            as max_value,
        round(quantile_cont(value, 0.9), 2) as p90_value,
        any_value(unit)                 as unit
    from read_parquet('data/raw/date=$day/*.parquet')
    where value is not null
    group by all
    order by suburb, pollutant
) to 'data/summary/$day.parquet' (format parquet);
