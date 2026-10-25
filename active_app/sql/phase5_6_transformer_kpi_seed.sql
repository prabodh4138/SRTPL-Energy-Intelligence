-- Transformer Phase 5.6 KPI seed. Safe to run after phase3_3_kpi_analytics.sql.
-- Transformer loss and efficiency are intentionally disabled.
insert into energy_analytics.kpi_master
(kpi_code,kpi_name,source_type,unit,aggregation_method,formula_type,formula_definition)
values
('TR-VI-01','Transformer Primary Voltage Imbalance','TRANSFORMER','%','MAX','PHASE_IMBALANCE','{"side":"primary"}'),
('TR-CI-01','Transformer Primary Current Imbalance','TRANSFORMER','%','MAX','PHASE_IMBALANCE','{"side":"primary"}'),
('TRF-SV-IMB','Transformer Secondary Voltage Imbalance','TRANSFORMER','%','MAX','PHASE_IMBALANCE','{"side":"secondary"}'),
('TRF-SI-IMB','Transformer Secondary Current Imbalance','TRANSFORMER','%','MAX','PHASE_IMBALANCE','{"side":"secondary"}'),
('TRF-PF','Transformer Average Power Factor','TRANSFORMER','PF','AVG','AVERAGE','{"field":"pf"}'),
('TRF-MAX-OTI','Transformer Maximum Oil Temperature','TRANSFORMER','°C','MAX','MAXIMUM','{"field":"oti"}'),
('TRF-MAX-WTI','Transformer Maximum Winding Temperature','TRANSFORMER','°C','MAX','MAXIMUM','{"field":"wti"}')
on conflict(kpi_code,version) do nothing;
