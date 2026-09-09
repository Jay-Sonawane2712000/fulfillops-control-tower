select distinct
    warehouse_id,
    warehouse_name
from {{ source('bronze', 'raw_warehouse_assignments') }}
where warehouse_id is not null
