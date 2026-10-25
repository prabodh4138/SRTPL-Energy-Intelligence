-- SRTPL ENERGY INTELLIGENCE & POWER CONSUMPTION ANALYTICS
-- PHASE 2 CORE SUPABASE SCHEMA
-- Scope: SOLAR, DG, EB, TRANSFORMER, UPS
-- TPWODL BILL: FUTURE EXTENSION
-- POWER PANEL: OUT OF CURRENT SCOPE

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_import;
CREATE SCHEMA IF NOT EXISTS energy_raw;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_validation;
CREATE SCHEMA IF NOT EXISTS energy_analytics;
CREATE SCHEMA IF NOT EXISTS energy_audit;

DO $$ BEGIN
  CREATE TYPE energy_import.import_status AS ENUM
  ('RECEIVED','PARSING','VALIDATING','IMPORTED','PARTIAL','FAILED','REJECTED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE energy_validation.exception_severity AS ENUM
  ('INFO','WARNING','ERROR','CRITICAL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE energy_validation.exception_status AS ENUM
  ('OPEN','ACKNOWLEDGED','UNDER_REVIEW','RESOLVED','ACCEPTED_EXCEPTION');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- =========================
-- MASTER DATA
-- =========================

CREATE TABLE IF NOT EXISTS energy_master.plaza (
  plaza_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plaza_code TEXT NOT NULL UNIQUE,
  plaza_name TEXT NOT NULL,
  location TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS energy_master.asset (
  asset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plaza_id UUID REFERENCES energy_master.plaza(plaza_id),
  asset_code TEXT NOT NULL UNIQUE,
  asset_type TEXT NOT NULL,
  asset_name TEXT,
  location TEXT,
  manufacturer TEXT,
  model TEXT,
  rated_capacity NUMERIC,
  rated_capacity_unit TEXT,
  installation_date DATE,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_asset_type ON energy_master.asset(asset_type);
CREATE INDEX IF NOT EXISTS ix_asset_plaza ON energy_master.asset(plaza_id);

CREATE TABLE IF NOT EXISTS energy_master.parameter (
  parameter_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parameter_code TEXT NOT NULL UNIQUE,
  parameter_name TEXT NOT NULL,
  category TEXT,
  unit TEXT,
  data_type TEXT NOT NULL DEFAULT 'NUMERIC',
  description TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS energy_master.asset_parameter (
  asset_id UUID NOT NULL REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
  parameter_id UUID NOT NULL REFERENCES energy_master.parameter(parameter_id),
  source_parameter_name TEXT,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY(asset_id, parameter_id)
);

CREATE TABLE IF NOT EXISTS energy_master.threshold (
  threshold_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_type TEXT,
  asset_id UUID REFERENCES energy_master.asset(asset_id),
  parameter_code TEXT NOT NULL,
  warning_min NUMERIC,
  warning_max NUMERIC,
  critical_min NUMERIC,
  critical_max NUMERIC,
  expected_interval_minutes INTEGER,
  effective_from TIMESTAMPTZ NOT NULL DEFAULT now(),
  effective_to TIMESTAMPTZ,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  remarks TEXT
);

CREATE INDEX IF NOT EXISTS ix_threshold_parameter
ON energy_master.threshold(parameter_code, active);

-- Generic tariff master; TPWODL billing can be added later.
CREATE TABLE IF NOT EXISTS energy_master.tariff (
  tariff_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tariff_code TEXT NOT NULL UNIQUE,
  tariff_name TEXT NOT NULL,
  energy_rate NUMERIC,
  demand_rate NUMERIC,
  fixed_charge NUMERIC,
  currency TEXT NOT NULL DEFAULT 'INR',
  effective_from DATE,
  effective_to DATE,
  source TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  active BOOLEAN NOT NULL DEFAULT TRUE
);

-- =========================
-- IMPORT / PROVENANCE
-- =========================

CREATE TABLE IF NOT EXISTS energy_import.import_batch (
  import_batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  uploaded_by TEXT,
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  source_system TEXT NOT NULL DEFAULT 'JUNO',
  report_type TEXT,
  report_version TEXT,
  parser_version TEXT,
  status energy_import.import_status NOT NULL DEFAULT 'RECEIVED',
  total_files INTEGER NOT NULL DEFAULT 0,
  total_rows INTEGER NOT NULL DEFAULT 0,
  valid_rows INTEGER NOT NULL DEFAULT 0,
  invalid_rows INTEGER NOT NULL DEFAULT 0,
  duplicate_rows INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS energy_import.import_file (
  import_file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  import_batch_id UUID NOT NULL REFERENCES energy_import.import_batch(import_batch_id) ON DELETE CASCADE,
  original_filename TEXT NOT NULL,
  storage_bucket TEXT,
  storage_path TEXT,
  sha256_hash TEXT NOT NULL UNIQUE,
  file_size_bytes BIGINT,
  report_type TEXT,
  report_title TEXT,
  downloaded_by TEXT,
  source_from_date DATE,
  source_to_date DATE,
  source_organization TEXT,
  detected_asset_code TEXT,
  detected_location TEXT,
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  row_count INTEGER,
  parsed_row_count INTEGER,
  valid_row_count INTEGER,
  invalid_row_count INTEGER,
  duplicate_row_count INTEGER,
  parse_status TEXT,
  parser_message TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS energy_import.import_row (
  import_row_id BIGSERIAL PRIMARY KEY,
  import_file_id UUID NOT NULL REFERENCES energy_import.import_file(import_file_id) ON DELETE CASCADE,
  source_row_number INTEGER NOT NULL,
  source_record_hash TEXT,
  business_key TEXT,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  parse_status TEXT NOT NULL DEFAULT 'PENDING',
  validation_status TEXT NOT NULL DEFAULT 'PENDING',
  duplicate_flag BOOLEAN NOT NULL DEFAULT FALSE,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(import_file_id, source_row_number)
);

CREATE INDEX IF NOT EXISTS ix_import_row_business_key
ON energy_import.import_row(business_key);

-- =========================
-- RAW JUNO DATA
-- =========================

CREATE TABLE IF NOT EXISTS energy_raw.juno_solar (
  raw_solar_id BIGSERIAL PRIMARY KEY,
  import_row_id BIGINT NOT NULL UNIQUE REFERENCES energy_import.import_row(import_row_id),
  solar_plant_id TEXT,
  reading_datetime TIMESTAMPTZ,
  cumulative_kwh NUMERIC,
  remarks TEXT,
  created_by TEXT,
  source_created_on TIMESTAMPTZ,
  source_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS energy_raw.juno_dg (
  raw_dg_id BIGSERIAL PRIMARY KEY,
  import_row_id BIGINT NOT NULL UNIQUE REFERENCES energy_import.import_row(import_row_id),
  dg_id TEXT,
  reading_datetime TIMESTAMPTZ,
  status TEXT,
  kva NUMERIC, kw NUMERIC,
  voltage_ry NUMERIC, voltage_yb NUMERIC, voltage_br NUMERIC,
  current_r NUMERIC, current_y NUMERIC, current_b NUMERIC,
  pf NUMERIC,
  diesel_level NUMERIC, diesel_topup NUMERIC,
  load_percent NUMERIC,
  cumulative_kwh NUMERIC,
  cumulative_running_hours NUMERIC,
  rpm NUMERIC,
  remarks TEXT,
  created_by TEXT,
  source_created_on TIMESTAMPTZ,
  source_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS energy_raw.juno_eb (
  raw_eb_id BIGSERIAL PRIMARY KEY,
  import_row_id BIGINT NOT NULL UNIQUE REFERENCES energy_import.import_row(import_row_id),
  meter_id TEXT,
  consumer_number TEXT,
  location TEXT,
  category TEXT,
  reading_datetime TIMESTAMPTZ,
  kwh NUMERIC, kvah NUMERIC, kvarh NUMERIC, md NUMERIC, pf NUMERIC,
  remarks TEXT,
  created_by TEXT,
  source_created_on TIMESTAMPTZ,
  source_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS energy_raw.juno_transformer (
  raw_transformer_id BIGSERIAL PRIMARY KEY,
  import_row_id BIGINT NOT NULL UNIQUE REFERENCES energy_import.import_row(import_row_id),
  transformer_id TEXT,
  location TEXT,
  reading_datetime TIMESTAMPTZ,
  primary_v_ry NUMERIC, primary_v_yb NUMERIC, primary_v_br NUMERIC,
  primary_i_r NUMERIC, primary_i_y NUMERIC, primary_i_b NUMERIC,
  secondary_v_ry NUMERIC, secondary_v_yb NUMERIC, secondary_v_br NUMERIC,
  secondary_i_r NUMERIC, secondary_i_y NUMERIC, secondary_i_b NUMERIC,
  kwh NUMERIC, kvah NUMERIC, pf NUMERIC, frequency NUMERIC,
  wti NUMERIC, oti NUMERIC,
  created_by TEXT,
  source_created_on TIMESTAMPTZ,
  source_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS energy_raw.juno_ups (
  raw_ups_id BIGSERIAL PRIMARY KEY,
  import_row_id BIGINT NOT NULL UNIQUE REFERENCES energy_import.import_row(import_row_id),
  ups_id TEXT,
  location TEXT,
  reading_datetime TIMESTAMPTZ,
  main_input_v_r NUMERIC, main_input_v_y NUMERIC, main_input_v_b NUMERIC,
  main_input_i_r NUMERIC, main_input_i_y NUMERIC, main_input_i_b NUMERIC,
  rectifier_voltage NUMERIC,
  bypass_voltage NUMERIC, bypass_current NUMERIC, bypass_frequency NUMERIC,
  output_voltage NUMERIC, output_current NUMERIC, output_frequency NUMERIC,
  battery_temperature NUMERIC, battery_vdc NUMERIC, battery_ib NUMERIC,
  created_by TEXT,
  source_created_on TIMESTAMPTZ,
  source_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_raw_solar_asset_date
ON energy_raw.juno_solar(solar_plant_id, reading_datetime);
CREATE INDEX IF NOT EXISTS ix_raw_dg_asset_date
ON energy_raw.juno_dg(dg_id, reading_datetime);
CREATE INDEX IF NOT EXISTS ix_raw_eb_meter_date
ON energy_raw.juno_eb(meter_id, reading_datetime);
CREATE INDEX IF NOT EXISTS ix_raw_transformer_asset_date
ON energy_raw.juno_transformer(transformer_id, reading_datetime);
CREATE INDEX IF NOT EXISTS ix_raw_ups_asset_date
ON energy_raw.juno_ups(ups_id, reading_datetime);

-- =========================
-- NORMALIZED READINGS
-- =========================

CREATE TABLE IF NOT EXISTS energy_readings.solar (
  reading_id BIGSERIAL PRIMARY KEY,
  asset_id UUID REFERENCES energy_master.asset(asset_id),
  import_row_id BIGINT UNIQUE REFERENCES energy_import.import_row(import_row_id),
  reading_datetime TIMESTAMPTZ NOT NULL,
  cumulative_kwh NUMERIC,
  interval_kwh NUMERIC,
  anomaly_flag BOOLEAN NOT NULL DEFAULT FALSE,
  data_quality_status TEXT NOT NULL DEFAULT 'VALID',
  calculation_version TEXT,
  UNIQUE(asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.dg (
  reading_id BIGSERIAL PRIMARY KEY,
  asset_id UUID REFERENCES energy_master.asset(asset_id),
  import_row_id BIGINT UNIQUE REFERENCES energy_import.import_row(import_row_id),
  reading_datetime TIMESTAMPTZ NOT NULL,
  status TEXT,
  kva NUMERIC, kw NUMERIC,
  voltage_ry NUMERIC, voltage_yb NUMERIC, voltage_br NUMERIC,
  current_r NUMERIC, current_y NUMERIC, current_b NUMERIC,
  pf NUMERIC,
  diesel_level NUMERIC, diesel_topup NUMERIC, load_percent NUMERIC,
  cumulative_kwh NUMERIC, interval_kwh NUMERIC,
  cumulative_running_hours NUMERIC, interval_running_hours NUMERIC,
  rpm NUMERIC,
  anomaly_flag BOOLEAN NOT NULL DEFAULT FALSE,
  data_quality_status TEXT NOT NULL DEFAULT 'VALID',
  calculation_version TEXT,
  UNIQUE(asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.eb (
  reading_id BIGSERIAL PRIMARY KEY,
  asset_id UUID REFERENCES energy_master.asset(asset_id),
  import_row_id BIGINT UNIQUE REFERENCES energy_import.import_row(import_row_id),
  reading_datetime TIMESTAMPTZ NOT NULL,
  cumulative_kwh NUMERIC, interval_kwh NUMERIC,
  cumulative_kvah NUMERIC, interval_kvah NUMERIC,
  cumulative_kvarh NUMERIC, interval_kvarh NUMERIC,
  md NUMERIC, pf NUMERIC,
  anomaly_flag BOOLEAN NOT NULL DEFAULT FALSE,
  data_quality_status TEXT NOT NULL DEFAULT 'VALID',
  calculation_version TEXT,
  UNIQUE(asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.transformer (
  reading_id BIGSERIAL PRIMARY KEY,
  asset_id UUID REFERENCES energy_master.asset(asset_id),
  import_row_id BIGINT UNIQUE REFERENCES energy_import.import_row(import_row_id),
  reading_datetime TIMESTAMPTZ NOT NULL,
  primary_v_ry NUMERIC, primary_v_yb NUMERIC, primary_v_br NUMERIC,
  primary_i_r NUMERIC, primary_i_y NUMERIC, primary_i_b NUMERIC,
  secondary_v_ry NUMERIC, secondary_v_yb NUMERIC, secondary_v_br NUMERIC,
  secondary_i_r NUMERIC, secondary_i_y NUMERIC, secondary_i_b NUMERIC,
  kwh NUMERIC, kvah NUMERIC, pf NUMERIC, frequency NUMERIC,
  wti NUMERIC, oti NUMERIC,
  anomaly_flag BOOLEAN NOT NULL DEFAULT FALSE,
  data_quality_status TEXT NOT NULL DEFAULT 'VALID',
  UNIQUE(asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.ups (
  reading_id BIGSERIAL PRIMARY KEY,
  asset_id UUID REFERENCES energy_master.asset(asset_id),
  import_row_id BIGINT UNIQUE REFERENCES energy_import.import_row(import_row_id),
  reading_datetime TIMESTAMPTZ NOT NULL,
  main_input_v_r NUMERIC, main_input_v_y NUMERIC, main_input_v_b NUMERIC,
  main_input_i_r NUMERIC, main_input_i_y NUMERIC, main_input_i_b NUMERIC,
  rectifier_voltage NUMERIC,
  bypass_voltage NUMERIC, bypass_current NUMERIC, bypass_frequency NUMERIC,
  output_voltage NUMERIC, output_current NUMERIC, output_frequency NUMERIC,
  battery_temperature NUMERIC, battery_vdc NUMERIC, battery_ib NUMERIC,
  anomaly_flag BOOLEAN NOT NULL DEFAULT FALSE,
  data_quality_status TEXT NOT NULL DEFAULT 'VALID',
  UNIQUE(asset_id, reading_datetime)
);

-- =========================
-- VALIDATION
-- =========================

CREATE TABLE IF NOT EXISTS energy_validation.rule_master (
  rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rule_code TEXT NOT NULL UNIQUE,
  rule_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  parameter_code TEXT,
  severity energy_validation.exception_severity NOT NULL,
  rule_expression TEXT,
  description TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  rule_version TEXT NOT NULL DEFAULT '1.0',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS energy_validation.exception_master (
  exception_id BIGSERIAL PRIMARY KEY,
  import_batch_id UUID REFERENCES energy_import.import_batch(import_batch_id),
  import_row_id BIGINT REFERENCES energy_import.import_row(import_row_id),
  asset_id UUID REFERENCES energy_master.asset(asset_id),
  rule_id UUID REFERENCES energy_validation.rule_master(rule_id),
  exception_code TEXT,
  severity energy_validation.exception_severity NOT NULL,
  status energy_validation.exception_status NOT NULL DEFAULT 'OPEN',
  message TEXT NOT NULL,
  source_value TEXT,
  expected_value TEXT,
  detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ,
  resolved_by TEXT,
  resolution_note TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_exception_open
ON energy_validation.exception_master(status, severity, detected_at);

-- =========================
-- KPI ENGINE
-- =========================

CREATE TABLE IF NOT EXISTS energy_analytics.kpi_master (
  kpi_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kpi_code TEXT NOT NULL UNIQUE,
  kpi_name TEXT NOT NULL,
  source_type TEXT,
  category TEXT,
  formula_logic TEXT NOT NULL,
  unit TEXT,
  frequency TEXT,
  description TEXT,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  kpi_version TEXT NOT NULL DEFAULT '1.0',
  effective_from DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS energy_analytics.kpi_result (
  kpi_result_id BIGSERIAL PRIMARY KEY,
  kpi_id UUID NOT NULL REFERENCES energy_analytics.kpi_master(kpi_id),
  plaza_id UUID REFERENCES energy_master.plaza(plaza_id),
  asset_id UUID REFERENCES energy_master.asset(asset_id),
  period_start TIMESTAMPTZ NOT NULL,
  period_end TIMESTAMPTZ NOT NULL,
  value NUMERIC,
  unit TEXT,
  status TEXT DEFAULT 'CALCULATED',
  calculation_version TEXT,
  source_record_count INTEGER,
  calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  trace JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_kpi_result_lookup
ON energy_analytics.kpi_result(kpi_id, asset_id, period_start);

CREATE TABLE IF NOT EXISTS energy_analytics.daily_summary (
  summary_date DATE NOT NULL,
  plaza_id UUID NOT NULL REFERENCES energy_master.plaza(plaza_id),
  solar_kwh NUMERIC,
  dg_kwh NUMERIC,
  eb_kwh NUMERIC,
  total_generation_kwh NUMERIC,
  total_consumption_kwh NUMERIC,
  solar_contribution_pct NUMERIC,
  dg_contribution_pct NUMERIC,
  data_completeness_pct NUMERIC,
  exception_count INTEGER DEFAULT 0,
  calculation_version TEXT,
  calculated_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY(summary_date, plaza_id)
);

CREATE TABLE IF NOT EXISTS energy_analytics.monthly_summary (
  month_start DATE NOT NULL,
  plaza_id UUID NOT NULL REFERENCES energy_master.plaza(plaza_id),
  solar_kwh NUMERIC,
  dg_kwh NUMERIC,
  eb_kwh NUMERIC,
  total_generation_kwh NUMERIC,
  total_consumption_kwh NUMERIC,
  solar_contribution_pct NUMERIC,
  dg_contribution_pct NUMERIC,
  data_completeness_pct NUMERIC,
  exception_count INTEGER DEFAULT 0,
  calculation_version TEXT,
  calculated_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY(month_start, plaza_id)
);

-- =========================
-- AUDIT
-- =========================

CREATE TABLE IF NOT EXISTS energy_audit.audit_log (
  audit_id BIGSERIAL PRIMARY KEY,
  event_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor TEXT,
  action TEXT NOT NULL,
  schema_name TEXT,
  table_name TEXT,
  record_pk TEXT,
  old_data JSONB,
  new_data JSONB,
  reason TEXT,
  import_batch_id UUID REFERENCES energy_import.import_batch(import_batch_id),
  ip_address INET,
  user_agent TEXT
);

CREATE TABLE IF NOT EXISTS energy_audit.change_request (
  change_request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requested_by TEXT NOT NULL,
  requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  target_table TEXT NOT NULL,
  target_record_pk TEXT NOT NULL,
  old_value JSONB,
  proposed_value JSONB,
  reason TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  reviewed_by TEXT,
  reviewed_at TIMESTAMPTZ,
  review_note TEXT
);

CREATE TABLE IF NOT EXISTS energy_audit.approval_log (
  approval_id BIGSERIAL PRIMARY KEY,
  change_request_id UUID NOT NULL REFERENCES energy_audit.change_request(change_request_id),
  action TEXT NOT NULL,
  acted_by TEXT NOT NULL,
  acted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  comments TEXT
);

-- =========================
-- INITIAL KPI DEFINITIONS
-- =========================

INSERT INTO energy_analytics.kpi_master
(kpi_code,kpi_name,source_type,category,formula_logic,unit,frequency,description)
VALUES
('SOL-GEN-D','Daily Solar Generation','SOLAR','ENERGY','Current cumulative kWh - previous cumulative kWh','kWh','DAILY','Solar generation'),
('DG-GEN-D','Daily DG Generation','DG','ENERGY','Current cumulative kWh - previous cumulative kWh','kWh','DAILY','DG generation'),
('DG-RUN-D','DG Runtime','DG','OPERATIONS','Current cumulative running hours - previous cumulative running hours','hour','DAILY','DG runtime'),
('DG-KWH-HR','DG Energy per Runtime Hour','DG','EFFICIENCY','DG generation / DG runtime','kWh/hour','DAILY','Energy per running hour'),
('DG-FUEL-KWH','DG Fuel per kWh','DG','EFFICIENCY','Diesel consumption / DG generation','L/kWh','DAILY','Fuel intensity'),
('DG-KWH-L','DG kWh per Litre','DG','EFFICIENCY','DG generation / diesel consumption','kWh/L','DAILY','Energy per litre'),
('DG-COST-KWH','DG Cost per kWh','DG','COST','Fuel cost / DG generation','INR/kWh','DAILY','Requires configured fuel price'),
('DG-PF','DG Average Power Factor','DG','POWER_QUALITY','Average valid PF readings','PF','DAILY','Average DG PF'),
('DG-V-IMB','DG Voltage Imbalance','DG','POWER_QUALITY','Maximum phase deviation from average / average * 100','%','READING','Voltage imbalance'),
('DG-I-IMB','DG Current Imbalance','DG','POWER_QUALITY','Maximum phase deviation from average / average * 100','%','READING','Current imbalance'),
('EB-CONS-D','EB Consumption','EB','ENERGY','Current cumulative kWh - previous cumulative kWh','kWh','DAILY','EB consumption'),
('EB-KVAH-D','EB KVAH Consumption','EB','ENERGY','Current cumulative KVAH - previous cumulative KVAH','kVAh','DAILY','Apparent energy'),
('EB-PF','EB Average Power Factor','EB','POWER_QUALITY','Average valid PF readings','PF','DAILY','Average EB PF'),
('EB-MD','EB Maximum Demand','EB','DEMAND','Maximum valid MD in selected period','METER/BILL UNIT','MONTHLY','Exact MD unit to be confirmed from TPWODL'),
('TRF-P-V-AVG','Transformer Primary Average Voltage','TRANSFORMER','POWER_QUALITY','Average RY/YB/BR primary voltage','V','READING','Primary voltage'),
('TRF-S-V-AVG','Transformer Secondary Average Voltage','TRANSFORMER','POWER_QUALITY','Average RY/YB/BR secondary voltage','V','READING','Secondary voltage'),
('TRF-P-I-AVG','Transformer Primary Average Current','TRANSFORMER','LOADING','Average R/Y/B primary current','A','READING','Primary current'),
('TRF-S-I-AVG','Transformer Secondary Average Current','TRANSFORMER','LOADING','Average R/Y/B secondary current','A','READING','Secondary current'),
('TRF-PF','Transformer Power Factor','TRANSFORMER','POWER_QUALITY','Source PF','PF','READING','Transformer PF'),
('TRF-FREQ','Transformer Frequency','TRANSFORMER','POWER_QUALITY','Source frequency','Hz','READING','Frequency'),
('TRF-WTI','Transformer WTI','TRANSFORMER','TEMPERATURE','Source WTI','deg C','READING','Winding temperature'),
('TRF-OTI','Transformer OTI','TRANSFORMER','TEMPERATURE','Source OTI','deg C','READING','Oil temperature'),
('UPS-INPUT-V','UPS Input Voltage','UPS','POWER_QUALITY','Main input phase voltage','V','READING','UPS input voltage'),
('UPS-INPUT-I','UPS Input Current','UPS','LOADING','Main input phase current','A','READING','UPS input current'),
('UPS-BYPASS-V','UPS Bypass Voltage','UPS','POWER_QUALITY','Source bypass voltage','V','READING','Bypass voltage'),
('UPS-BYPASS-F','UPS Bypass Frequency','UPS','POWER_QUALITY','Source bypass frequency','Hz','READING','Bypass frequency'),
('UPS-OUTPUT-V','UPS Output Voltage','UPS','POWER_QUALITY','Source output voltage','V','READING','Output voltage'),
('UPS-OUTPUT-F','UPS Output Frequency','UPS','POWER_QUALITY','Source output frequency','Hz','READING','Output frequency'),
('UPS-BATT-T','UPS Battery Temperature','UPS','BATTERY','Source battery temperature','deg C','READING','Battery temperature'),
('UPS-BATT-V','UPS Battery Voltage','UPS','BATTERY','Source battery Vdc','Vdc','READING','Battery voltage'),
('UPS-BATT-I','UPS Battery Current','UPS','BATTERY','Source battery current','A','READING','Battery current')
ON CONFLICT (kpi_code) DO NOTHING;

-- =========================
-- INITIAL VALIDATION RULES
-- =========================

INSERT INTO energy_validation.rule_master
(rule_code,rule_name,source_type,severity,description)
VALUES
('VAL-SOL-001','Solar cumulative reading cannot decrease','SOLAR','ERROR','Current cumulative kWh must not be below previous valid reading'),
('VAL-SOL-002','Solar duplicate timestamp','SOLAR','ERROR','Duplicate plant and timestamp'),
('VAL-DG-001','DG cumulative kWh cannot decrease','DG','ERROR','Current cumulative DG kWh must not decrease'),
('VAL-DG-002','DG running hours cannot decrease','DG','ERROR','Current cumulative runtime must not decrease'),
('VAL-DG-003','DG kW cannot exceed kVA','DG','WARNING','Check physical consistency of kW and kVA'),
('VAL-DG-004','DG PF outside valid range','DG','ERROR','PF should normally be between 0 and 1'),
('VAL-EB-001','EB cumulative kWh cannot decrease','EB','ERROR','Current cumulative EB kWh must not decrease'),
('VAL-EB-002','EB cumulative KVAH cannot decrease','EB','ERROR','Current cumulative KVAH must not decrease'),
('VAL-EB-003','EB PF outside valid range','EB','ERROR','PF should normally be between 0 and 1'),
('VAL-TRF-001','Transformer PF outside valid range','TRANSFORMER','ERROR','PF should normally be between 0 and 1'),
('VAL-TRF-002','Transformer abnormal temperature','TRANSFORMER','WARNING','WTI/OTI evaluated against configurable thresholds'),
('VAL-UPS-001','UPS abnormal battery voltage','UPS','WARNING','Battery voltage evaluated against configured thresholds'),
('VAL-UPS-002','UPS abnormal battery temperature','UPS','WARNING','Battery temperature evaluated against configured thresholds')
ON CONFLICT (rule_code) DO NOTHING;

COMMIT;

-- IMPLEMENTATION RULES
-- 1. Store every original JUNO CSV unchanged in a PRIVATE Supabase Storage bucket.
-- 2. Calculate SHA-256 before accepting the file.
-- 3. Use import_batch -> import_file -> import_row for provenance.
-- 4. Keep raw JUNO values and source_payload untouched.
-- 5. Populate normalized readings only after parsing/validation.
-- 6. Preserve NULL; never convert blank JUNO cells to zero.
-- 7. Keep KPI formulas/versioning in the database.
-- 8. Keep thresholds configurable in the database.
-- 9. TPWODL billing will later add energy_billing.tpwodl_bill and reconciliation.
-- 10. Do not calculate transformer loss/efficiency until measurement boundaries
--     and CT/PT/meter definitions are confirmed.
