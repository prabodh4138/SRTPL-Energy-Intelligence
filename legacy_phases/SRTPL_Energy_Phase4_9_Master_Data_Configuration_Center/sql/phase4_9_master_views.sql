create or replace view energy_dashboard.vw_active_asset_configuration as
select
    a.asset_id,
    a.asset_code,
    a.asset_type,
    a.plaza_id,
    a.location,
    a.active
from energy_master.asset a
where a.active = true;

create or replace view energy_dashboard.vw_active_asset_parameters as
select
    ap.asset_parameter_id,
    ap.asset_id,
    ap.parameter_id,
    ap.required,
    ap.collection_frequency,
    ap.active
from energy_master.asset_parameter ap
where ap.active = true;

create or replace view energy_dashboard.vw_active_thresholds as
select
    threshold_id,
    parameter_id,
    condition_code,
    warning_value,
    critical_value,
    unit
from energy_master.threshold
where active = true;

create or replace view energy_dashboard.vw_active_kpis as
select
    kpi_id,
    kpi_code,
    kpi_name,
    formula_code,
    unit,
    scope,
    version
from energy_analytics.kpi_master
where active = true;
