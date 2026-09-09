select distinct
    carrier_id,
    carrier_name
from {{ source('bronze', 'raw_carrier_assignments') }}
where carrier_id is not null
