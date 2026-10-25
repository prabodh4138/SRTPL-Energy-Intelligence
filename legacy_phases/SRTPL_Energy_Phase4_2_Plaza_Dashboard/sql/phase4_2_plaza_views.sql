-- Phase 4.2 plaza read models.
create schema if not exists energy_dashboard;

create or replace view energy_dashboard.vw_plaza_kpi_results as
select
    kr.kpi_result_id,
    kr.kpi_code,
    kr.kpi_version,
    kr.plaza_id,
    kr.asset_id,
    kr.period_start,
    kr.period_end,
    kr.value,
    kr.unit,
    kr.status,
    kr.reason,
    kr.source_reading_count,
    kr.calculation_version
from energy_analytics.kpi_result kr;

-- The production repository should join plaza_id and asset_id to
-- energy_master tables. No TP-specific relationship should be hard-coded here.

create index if not exists idx_plaza_kpi_lookup
on energy_analytics.kpi_result(plaza_id, period_start, period_end);
