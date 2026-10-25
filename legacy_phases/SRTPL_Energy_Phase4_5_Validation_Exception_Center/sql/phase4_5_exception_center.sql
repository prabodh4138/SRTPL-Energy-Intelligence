-- Phase 4.5 read model and operational indexes.
create index if not exists idx_exception_status_severity
on energy_validation.exception_master(status, severity);

create index if not exists idx_exception_source_asset
on energy_validation.exception_master(source_type, asset_id);

create index if not exists idx_exception_batch
on energy_validation.exception_master(batch_id);

create index if not exists idx_exception_rule
on energy_validation.exception_master(rule_id);

create or replace view energy_dashboard.vw_exception_center as
select
    e.exception_id,
    e.batch_id,
    e.import_row_id,
    e.source_type,
    e.plaza_id,
    e.asset_id,
    e.rule_id,
    e.severity,
    e.status,
    e.parameter,
    e.source_value,
    e.expected_value,
    e.message,
    e.created_at,
    e.resolved_at,
    e.resolved_by,
    e.resolution_note
from energy_validation.exception_master e;
