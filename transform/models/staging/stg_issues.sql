select
    order_id,
    issue_type,
    issue_source,
    cast(synthetic_issue_probability as decimal(6, 4)) as synthetic_issue_probability,
    anomaly_flag,
    case
        when issue_type in ('missing', 'damaged', 'wrong', 'failed', 'cancelled', 'refund')
            then true
        else false
    end as quality_issue_flag
from {{ source('bronze', 'raw_issue_flags') }}
