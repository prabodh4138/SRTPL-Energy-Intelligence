-- Phase 4.3 equipment read models.

create schema if not exists energy_dashboard;

create or replace view energy_dashboard.vw_equipment_kpi as
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
    kr.source_reading_ids,
    kr.calculation_version,
    kr.calculated_at
from energy_analytics.kpi_result kr;

-- Asset/parameter master joins must use UUID relationships.
-- The application must not infer an asset from its name or location.
create index if not exists idx_equipment_kpi_asset_period
on energy_analytics.kpi_result(asset_id, period_start, period_end);
