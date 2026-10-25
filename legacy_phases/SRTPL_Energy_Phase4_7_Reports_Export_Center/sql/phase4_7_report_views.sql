-- Report read-model foundation.
-- Final report-specific views should be connected to the Phase 3.3 KPI results
-- and Phase 4.x dashboard read models.

create or replace view energy_dashboard.vw_report_daily_energy as
select
    summary_date,
    plaza_id,
    solar_generation_kwh,
    dg_generation_kwh,
    eb_consumption_kwh,
    energy_cost,
    solar_savings
from energy_analytics.daily_summary;

create or replace view energy_dashboard.vw_report_monthly_energy as
select
    summary_month,
    plaza_id,
    solar_generation_kwh,
    dg_generation_kwh,
    eb_consumption_kwh,
    energy_cost,
    solar_savings
from energy_analytics.monthly_summary;
