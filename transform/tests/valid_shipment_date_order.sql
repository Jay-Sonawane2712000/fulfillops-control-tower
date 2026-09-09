select
    shipment_id,
    order_id,
    order_purchase_date,
    delivered_customer_date,
    estimated_delivery_date
from {{ ref('stg_shipments') }}
where (
    delivered_customer_date is not null
    and delivered_customer_date < order_purchase_date
)
or estimated_delivery_date < order_purchase_date
