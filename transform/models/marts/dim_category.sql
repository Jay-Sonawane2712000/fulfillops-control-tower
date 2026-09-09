select
    category_name,
    sla_tier,
    cast(sla_target_days as integer) as sla_target_days
from {{ source('bronze', 'raw_sla_targets') }}
where category_name is not null
group by
    category_name,
    sla_tier,
    cast(sla_target_days as integer)
