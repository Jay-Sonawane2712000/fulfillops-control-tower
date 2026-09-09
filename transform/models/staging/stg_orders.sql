with orders as (
    select
        order_id,
        customer_id,
        order_status,
        order_purchase_timestamp,
        order_approved_at,
        order_delivered_carrier_date,
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
        warehouse_id,
        warehouse_name
    from {{ source('bronze', 'raw_warehouse_assignments') }}
),

carrier_assignments as (
    select
        order_id,
        carrier_id,
        carrier_name
    from {{ source('bronze', 'raw_carrier_assignments') }}
)

select
    orders.order_id,
    orders.customer_id,
    customers.customer_state,
    orders.order_status,
    orders.order_purchase_timestamp,
    orders.order_approved_at,
    orders.order_delivered_carrier_date,
    orders.order_delivered_customer_date,
    orders.order_estimated_delivery_date,
    warehouse_assignments.warehouse_id,
    warehouse_assignments.warehouse_name,
    carrier_assignments.carrier_id,
    carrier_assignments.carrier_name
from orders
left join customers
    on orders.customer_id = customers.customer_id
left join warehouse_assignments
    on orders.order_id = warehouse_assignments.order_id
left join carrier_assignments
    on orders.order_id = carrier_assignments.order_id
