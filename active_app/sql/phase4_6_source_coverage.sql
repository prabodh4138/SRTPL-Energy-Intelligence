-- Expected coverage must be configured from asset_parameter/master data.
-- This view provides a starting point; do not hard-code equipment counts.
create or replace view energy_dashboard.vw_source_coverage as
select
    source_type,
    count(*) as records_received,
    count(distinct asset_id) as assets_reporting,
    min(recorded_at) as first_record,
    max(recorded_at) as last_record
from energy_readings.normalized_reading
group by source_type;
