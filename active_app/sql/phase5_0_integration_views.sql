create schema if not exists energy_dashboard;

create or replace view energy_dashboard.vw_system_import_pipeline as
select
    b.batch_id,
    b.created_at,
    b.status,
    f.filename,
    f.sha256,
    f.report_type,
    f.row_count,
    f.rows_imported,
    f.rows_invalid,
    f.rows_duplicate
from energy_import.import_batch b
left join energy_import.import_file f
    on f.batch_id = b.batch_id;

create or replace view energy_dashboard.vw_pipeline_readiness as
select
    count(*) as total_batches,
    count(*) filter (where status = 'COMPLETED') as completed_batches,
    count(*) filter (where status = 'FAILED') as failed_batches,
    count(*) filter (where status = 'PARTIAL') as partial_batches
from energy_import.import_batch;
