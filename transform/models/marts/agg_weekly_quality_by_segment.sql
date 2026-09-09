with shipments as (
    select
        time_bucket(interval 1 week, order_purchase_date) as week_start_date,
        warehouse_id,
        carrier_id,
        category_name,
        issue_type,
        quality_issue_flag,
        anomaly_flag
    from {{ ref('fct_shipments') }}
),

quality_by_segment as (
    select
        week_start_date,
        warehouse_id,
        carrier_id,
        category_name,
        issue_type,
        count(*) as shipment_count,
        sum(case when quality_issue_flag then 1 else 0 end) as issue_count,
        round(
            100.0 * sum(case when quality_issue_flag then 1 else 0 end) / nullif(count(*), 0),
            2
        ) as issue_rate_pct,
        sum(case when anomaly_flag <> 'none' then 1 else 0 end) as anomaly_count
    from shipments
    group by
        week_start_date,
        warehouse_id,
        carrier_id,
        category_name,
        issue_type
),

anomaly_rank as (
    select
        week_start_date,
        warehouse_id,
        carrier_id,
        category_name,
        issue_type,
        anomaly_flag,
        count(*) as anomaly_flag_count,
        row_number() over (
            partition by
                week_start_date,
                warehouse_id,
                carrier_id,
                category_name,
                issue_type
            order by count(*) desc, anomaly_flag
        ) as anomaly_rank
    from shipments
    where anomaly_flag <> 'none'
    group by
        week_start_date,
        warehouse_id,
        carrier_id,
        category_name,
        issue_type,
        anomaly_flag
)

select
    quality_by_segment.week_start_date,
    quality_by_segment.warehouse_id,
    quality_by_segment.carrier_id,
    quality_by_segment.category_name,
    quality_by_segment.issue_type,
    quality_by_segment.shipment_count,
    quality_by_segment.issue_count,
    quality_by_segment.issue_rate_pct,
    quality_by_segment.anomaly_count,
    coalesce(anomaly_rank.anomaly_flag, 'none') as dominant_anomaly_flag
from quality_by_segment
left join anomaly_rank
    on quality_by_segment.week_start_date = anomaly_rank.week_start_date
    and quality_by_segment.warehouse_id = anomaly_rank.warehouse_id
    and quality_by_segment.carrier_id = anomaly_rank.carrier_id
    and quality_by_segment.category_name = anomaly_rank.category_name
    and quality_by_segment.issue_type = anomaly_rank.issue_type
    and anomaly_rank.anomaly_rank = 1
