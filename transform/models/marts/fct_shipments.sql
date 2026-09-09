with shipments as (
    select
        shipment_id,
        order_id,
        warehouse_id,
        carrier_id,
        order_purchase_date,
        delivered_customer_date,
        estimated_delivery_date,
        actual_delivery_days,
        estimated_delivery_days,
        sla_target_days,
        delay_days,
        sla_breach_flag,
        real_late_delivery_flag
    from {{ ref('stg_shipments') }}
),

sla_targets as (
    select
        order_id,
        category_name,
        sla_tier
    from {{ source('bronze', 'raw_sla_targets') }}
),

issues as (
    select
        order_id,
        issue_type,
        quality_issue_flag,
        anomaly_flag
    from {{ ref('stg_issues') }}
)

select
    shipments.shipment_id,
    shipments.order_id,
    shipments.warehouse_id,
    shipments.carrier_id,
    sla_targets.category_name,
    sla_targets.sla_tier,
    shipments.order_purchase_date,
    shipments.delivered_customer_date,
    shipments.estimated_delivery_date,
    shipments.actual_delivery_days,
    shipments.estimated_delivery_days,
    shipments.sla_target_days,
    shipments.delay_days,
    shipments.sla_breach_flag,
    shipments.real_late_delivery_flag,
    issues.issue_type,
    issues.quality_issue_flag,
    issues.anomaly_flag
from shipments
left join sla_targets
    on shipments.order_id = sla_targets.order_id
left join issues
    on shipments.order_id = issues.order_id
