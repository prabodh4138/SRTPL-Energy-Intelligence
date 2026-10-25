-- UPS Phase 5.7 KPI seed. Safe to run after phase3_3_kpi_analytics.sql.
insert into energy_analytics.kpi_master
(kpi_code,kpi_name,source_type,unit,aggregation_method,formula_type,formula_definition)
values
('UPS-AV-01','UPS Availability','UPS','%','RATIO','AVAILABILITY','{}'),
('UPS-V-OUT-AVG','UPS Average Output Voltage','UPS','V','AVG','AVERAGE','{"field":"output_voltage"}'),
('UPS-I-OUT-AVG','UPS Average Output Current','UPS','A','AVG','AVERAGE','{"field":"output_current"}'),
('UPS-F-OUT-AVG','UPS Average Output Frequency','UPS','Hz','AVG','AVERAGE','{"field":"output_frequency"}'),
('UPS-BATT-V-AVG','UPS Average Battery Voltage','UPS','V','AVG','AVERAGE','{"field":"battery_vdc"}'),
('UPS-BATT-T-MAX','UPS Maximum Battery Temperature','UPS','°C','MAX','MAXIMUM','{"field":"battery_temperature"}'),
('UPS-RECT-V-AVG','UPS Average Rectifier Voltage','UPS','V','AVG','AVERAGE','{"field":"rectifier_voltage"}')
on conflict(kpi_code,version) do nothing;
