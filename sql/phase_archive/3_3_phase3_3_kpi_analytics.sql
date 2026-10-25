create schema if not exists energy_analytics;
create table if not exists energy_analytics.kpi_master (
 kpi_id uuid primary key default gen_random_uuid(),
 kpi_code text not null, kpi_name text not null, source_type text not null,
 asset_scope text, unit text not null, aggregation_method text not null,
 formula_type text not null, formula_definition jsonb not null default '{}'::jsonb,
 version text not null default '1.0', effective_from timestamptz not null default now(),
 effective_to timestamptz, is_active boolean not null default true,
 created_at timestamptz not null default now(), unique(kpi_code,version)
);
create table if not exists energy_analytics.kpi_result (
 kpi_result_id uuid primary key default gen_random_uuid(),
 kpi_id uuid references energy_analytics.kpi_master(kpi_id),
 kpi_code text not null, kpi_version text not null,
 plaza_id uuid, asset_id uuid, period_start timestamptz not null,
 period_end timestamptz not null, value numeric, unit text not null,
 status text not null default 'CALCULATED', reason text,
 calculation_version text not null default '3.3.0',
 source_reading_count integer not null default 0,
 source_reading_ids jsonb not null default '[]'::jsonb,
 calculated_at timestamptz not null default now(),
 unique(kpi_code,kpi_version,asset_id,plaza_id,period_start,period_end)
);
create index if not exists idx_kpi_result_period on energy_analytics.kpi_result(period_start,period_end);
create index if not exists idx_kpi_result_asset on energy_analytics.kpi_result(asset_id);

insert into energy_analytics.kpi_master
(kpi_code,kpi_name,source_type,unit,aggregation_method,formula_type,formula_definition)
values
('SOL-GEN-D','Solar Daily Generation','SOLAR','kWh','SUM_DELTA','CUMULATIVE_DELTA','{"field":"cumulative_kwh"}'),
('SOL-GEN-M','Solar Monthly Generation','SOLAR','kWh','SUM','DERIVED_DAILY_SUM','{"source":"SOL-GEN-D"}'),
('DG-GEN-D','DG Daily Generation','DG','kWh','SUM_DELTA','CUMULATIVE_DELTA','{"field":"cumulative_kwh"}'),
('DG-RUN-D','DG Runtime','DG','hr','SUM_DELTA','CUMULATIVE_DELTA','{"field":"running_hours"}'),
('DG-EFF-01','DG kWh per Hour','DG','kWh/hr','RATIO','RATIO','{"numerator":"DG-GEN-D","denominator":"DG-RUN-D"}'),
('DG-PF-01','DG Average PF','DG','PF','AVG','AVERAGE','{"field":"pf"}'),
('DG-VI-01','DG Voltage Imbalance','DG','%','MAX','PHASE_IMBALANCE','{"fields":["voltage_ry","voltage_yb","voltage_br"]}'),
('DG-CI-01','DG Current Imbalance','DG','%','MAX','PHASE_IMBALANCE','{"fields":["current_r","current_y","current_b"]}'),
('EB-CONS-D','EB Consumption','EB','kWh','SUM_DELTA','CUMULATIVE_DELTA','{"field":"kwh"}'),
('EB-KVAH-D','EB KVAH Consumption','EB','kVAh','SUM_DELTA','CUMULATIVE_DELTA','{"field":"kvah"}'),
('EB-PF-D','EB Average PF','EB','PF','AVG','AVERAGE','{"field":"pf"}'),
('EB-KWH-KVAH','EB kWh/kVAh Ratio','EB','ratio','RATIO','RATIO','{"numerator":"EB-CONS-D","denominator":"EB-KVAH-D"}'),
('TR-VI-01','Transformer Voltage Imbalance','TRANSFORMER','%','MAX','PHASE_IMBALANCE','{"side":"primary"}'),
('TR-CI-01','Transformer Current Imbalance','TRANSFORMER','%','MAX','PHASE_IMBALANCE','{"side":"primary"}'),
('UPS-AV-01','UPS Availability','UPS','%','RATIO','AVAILABILITY','{}')
on conflict(kpi_code,version) do nothing;
