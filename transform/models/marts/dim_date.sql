with bounds as (
    select
        min(order_purchase_date) as start_date,
        max(order_purchase_date) as end_date
    from {{ ref('stg_shipments') }}
),

date_spine as (
    select
        cast(date_value as date) as date_day
    from bounds,
        generate_series(start_date, end_date, interval 1 day) as dates(date_value)
)

select
    date_day,
    extract(year from date_day) as year,
    extract(quarter from date_day) as quarter,
    extract(month from date_day) as month,
    strftime(date_day, '%Y-%m') as year_month,
    extract(day from date_day) as day_of_month,
    dayofweek(date_day) as day_of_week
from date_spine
