-- Phase 4.1 dashboard read models.
-- These views intentionally read analytics/validation/master data and do not
-- duplicate source readings.

create schema if not exists energy_dashboard;

create or replace view energy_dashboard.vw_kpi_latest as
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
    kr.calculation_version,
    kr.source_reading_count,
    kr.calculated_at
from energy_analytics.kpi_result kr;

-- Future production views should join plaza/asset master tables by UUID.
-- Do not hard-code TP01/TP02/TP03 relationships inside application code.

create index if not exists idx_dashboard_kpi_period
on energy_analytics.kpi_result(period_start, period_end);
