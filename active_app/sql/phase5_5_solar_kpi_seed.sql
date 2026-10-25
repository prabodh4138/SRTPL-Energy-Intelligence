-- Solar Phase 5.5 KPI seed. Safe to run after phase3_3_kpi_analytics.sql.
insert into energy_analytics.kpi_master
(kpi_code,kpi_name,source_type,unit,aggregation_method,formula_type,formula_definition)
values
('SOL-GEN-D','Solar Daily Generation','SOLAR','kWh','SUM_DELTA','CUMULATIVE_DELTA','{"field":"cumulative_kwh"}'),
('SOL-AVAIL-D','Solar Reporting Availability','SOLAR','%','RATIO','AVAILABILITY','{}')
on conflict(kpi_code,version) do nothing;
