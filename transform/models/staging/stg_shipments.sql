with orders as (
    select
        order_id,
        customer_id,
        order_purchase_timestamp,
        order_delivered_customer_date,
        order_estimated_delivery_date
    from {{ source('bronze', 'raw_orders') }}
),

customers as (
    select
        customer_id,
        customer_state
    from {{ source('bronze', 'raw_customers') }}
),

warehouse_assignments as (
    select
        order_id,
        warehouse_id
    from {{ source('bronze', 'raw_warehouse_assignments') }}
),

carrier_assignments as (
    select
        order_id,
        carrier_id
    from {{ source('bronze', 'raw_carrier_assignments') }}
),

sla_targets as (
    select
        order_id,
        sla_target_days
    from {{ source('bronze', 'raw_sla_targets') }}
)

select
    'ship_' || orders.order_id as shipment_id,
    orders.order_id,
    warehouse_assignments.warehouse_id,
    carrier_assignments.carrier_id,
    customers.customer_state,
    cast(orders.order_purchase_timestamp as date) as order_purchase_date,
    cast(orders.order_delivered_customer_date as date) as delivered_customer_date,
    cast(orders.order_estimated_delivery_date as date) as estimated_delivery_date,
    datediff(
        'day',
        cast(orders.order_purchase_timestamp as date),
        cast(orders.order_delivered_customer_date as date)
    ) as actual_delivery_days,
    datediff(
        'day',
        cast(orders.order_purchase_timestamp as date),
        cast(orders.order_estimated_delivery_date as date)
    ) as estimated_delivery_days,
    cast(sla_targets.sla_target_days as integer) as sla_target_days,
    greatest(
        datediff(
            'day',
            cast(orders.order_estimated_delivery_date as date),
            cast(orders.order_delivered_customer_date as date)
        ),
        0
    ) as delay_days,
    case
        when datediff(
            'day',
            cast(orders.order_purchase_timestamp as date),
            cast(orders.order_delivered_customer_date as date)
        ) > cast(sla_targets.sla_target_days as integer)
            then true
        else false
    end as sla_breach_flag,
    case
        when cast(orders.order_delivered_customer_date as date)
            > cast(orders.order_estimated_delivery_date as date)
            then true
        else false
    end as real_late_delivery_flag
from orders
left join customers
    on orders.customer_id = customers.customer_id
inner join warehouse_assignments
    on orders.order_id = warehouse_assignments.order_id
inner join carrier_assignments
    on orders.order_id = carrier_assignments.order_id
inner join sla_targets
    on orders.order_id = sla_targets.order_id
where orders.order_purchase_timestamp is not null
    and orders.order_delivered_customer_date is not null
    and orders.order_estimated_delivery_date is not null
