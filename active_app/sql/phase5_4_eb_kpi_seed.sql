-- EB Phase 5.4 KPI seed. Safe to run after phase3_3_kpi_analytics.sql.
insert into energy_analytics.kpi_master
(kpi_code,kpi_name,source_type,unit,aggregation_method,formula_type,formula_definition)
values
('EB-CONS-D','EB Consumption','EB','kWh','SUM_DELTA','CUMULATIVE_DELTA','{"field":"interval_kwh"}'),
('EB-KVAH-D','EB KVAH Consumption','EB','kVAh','SUM_DELTA','CUMULATIVE_DELTA','{"field":"interval_kvah"}'),
('EB-PF-D','EB Average PF','EB','PF','AVG','AVERAGE','{"field":"pf"}'),
('EB-KWH-KVAH','EB kWh/kVAh Ratio','EB','ratio','RATIO','RATIO','{"numerator":"EB-CONS-D","denominator":"EB-KVAH-D"}')
on conflict(kpi_code,version) do nothing;
