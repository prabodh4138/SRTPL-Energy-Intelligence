create schema if not exists energy_dashboard;

create or replace view energy_dashboard.vw_data_quality_summary as
select
    count(*) as records_received,
    count(*) filter (where status = 'IMPORTED') as records_imported,
    count(*) filter (where status = 'INVALID') as records_invalid,
    count(*) filter (where status = 'DUPLICATE') as records_duplicate
from energy_import.import_row;

create or replace view energy_dashboard.vw_import_health as
select
    date(created_at) as import_date,
    count(*) as batches_received,
    count(*) filter (where status = 'COMPLETED') as batches_completed,
    count(*) filter (where status = 'FAILED') as batches_failed,
    count(*) filter (where status = 'PARTIAL') as batches_partial
from energy_import.import_batch
group by date(created_at);

create or replace view energy_dashboard.vw_exception_ageing as
select
    case
        when now() - created_at < interval '1 day' then '<1 day'
        when now() - created_at < interval '3 days' then '1-3 days'
        when now() - created_at < interval '7 days' then '3-7 days'
        when now() - created_at < interval '30 days' then '7-30 days'
        else '30+ days'
    end as age_bucket,
    severity,
    count(*) as exception_count
from energy_validation.exception_master
where status not in ('RESOLVED', 'ACCEPTED_EXCEPTION')
group by 1, 2;

create or replace view energy_dashboard.vw_audit_traceability as
select
    count(*) as total_import_rows,
    count(*) filter (
        where import_row_id is not null
    ) as traceable_rows
from energy_import.import_row;
