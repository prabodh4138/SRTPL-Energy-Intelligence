-- Phase 4.4 import-center read model.
create schema if not exists energy_dashboard;

create or replace view energy_dashboard.vw_import_history as
select
    b.batch_id,
    b.created_at as imported_at,
    b.status,
    f.filename,
    f.sha256,
    f.report_type,
    f.row_count,
    f.rows_imported,
    f.rows_invalid,
    f.rows_duplicate
from energy_import.import_batch b
left join energy_import.import_file f on f.batch_id = b.batch_id;

create index if not exists idx_import_batch_status_date
on energy_import.import_batch(status, created_at);
