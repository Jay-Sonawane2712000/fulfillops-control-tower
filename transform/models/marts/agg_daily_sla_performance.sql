select
    order_purchase_date,
    warehouse_id,
    carrier_id,
    sla_tier,
    count(*) as shipment_count,
    sum(case when sla_breach_flag then 1 else 0 end) as sla_breach_count,
    sum(case when not sla_breach_flag then 1 else 0 end) as on_time_count,
    round(
        100.0 * sum(case when not sla_breach_flag then 1 else 0 end) / nullif(count(*), 0),
        2
    ) as sla_attainment_pct,
    round(avg(delay_days), 2) as avg_delay_days,
    sum(case when real_late_delivery_flag then 1 else 0 end) as real_late_delivery_count
from {{ ref('fct_shipments') }}
group by
    order_purchase_date,
    warehouse_id,
    carrier_id,
    sla_tier
