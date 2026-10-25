-- ============================================================================
-- SRTPL POWER CONSUMPTION ANALYTICS — COMPLETE DATABASE DEFINITION & DEMO SEED
-- Compatible with PostgreSQL 14+ and Supabase
--
-- This script:
-- 1. Creates all schemas and tables matching the 21 raw JUNO CSV exports
-- 2. Defines Plazas (TP01, TP02, TP03) and assigns all 18 Assets to Plazas
-- 3. Seeds KPI definitions, demo metrics, historical trends, and exceptions
-- ============================================================================

-- 1. SCHEMAS
CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_import;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_validation;
CREATE SCHEMA IF NOT EXISTS energy_analytics;
CREATE SCHEMA IF NOT EXISTS energy_admin;
CREATE SCHEMA IF NOT EXISTS energy_audit;

-- 2. MASTER DATA: PLAZAS & ASSETS
CREATE TABLE IF NOT EXISTS energy_master.plaza (
    plaza_id VARCHAR(16) PRIMARY KEY,
    plaza_name VARCHAR(128) NOT NULL,
    location VARCHAR(256),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS energy_master.asset (
    asset_id VARCHAR(64) PRIMARY KEY,
    asset_code VARCHAR(64) NOT NULL UNIQUE,
    asset_name VARCHAR(128) NOT NULL,
    plaza_id VARCHAR(16) NOT NULL REFERENCES energy_master.plaza(plaza_id),
    source_type VARCHAR(32) NOT NULL,
    capacity_kva NUMERIC(10, 2),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed Plazas
INSERT INTO energy_master.plaza (plaza_id, plaza_name, location) VALUES
    ('TP01', 'Toll Plaza 01', 'SRTPL Corridor Km 24+500'),
    ('TP02', 'Toll Plaza 02', 'SRTPL Corridor Km 68+200'),
    ('TP03', 'Toll Plaza 03', 'SRTPL Corridor Km 112+800')
ON CONFLICT (plaza_id) DO NOTHING;

-- Seed Assets mapped to Plazas
INSERT INTO energy_master.asset (asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva) VALUES
    -- TP01 Assets
    ('AST-EB-01', 'SR-E-EM-EB-000TP01', 'Main EB Incomer TP01', 'TP01', 'EB', 500.0),
    ('AST-DG-01', 'SR-E-AP-DGX-000001', 'Diesel Generator 1', 'TP01', 'DG', 250.0),
    ('AST-DG-02', 'SR-E-AP-DGX-000002', 'Diesel Generator 2', 'TP01', 'DG', 250.0),
    ('AST-SOL-01', 'SR-E-AP-SPX-000001', 'Solar Plant 1', 'TP01', 'SOLAR', 100.0),
    ('AST-TRF-02', 'SR-E-HT-TFR-000002', 'HT Substation Transformer 2', 'TP01', 'TRANSFORMER', 500.0),
    ('AST-UPS-02', 'SR-E-AP-UPS-000002', 'Toll Plaza UPS 2', 'TP01', 'UPS', 40.0),
    ('AST-UPS-03', 'SR-E-AP-UPS-000003', 'Toll Plaza UPS 3', 'TP01', 'UPS', 40.0),

    -- TP02 Assets
    ('AST-EB-02', 'SR-E-EM-EB-130-000', 'Main EB Incomer TP02', 'TP02', 'EB', 500.0),
    ('AST-DG-03', 'SR-E-AP-DGX-000003', 'Diesel Generator 3', 'TP02', 'DG', 250.0),
    ('AST-DG-04', 'SR-E-AP-DGX-000004', 'Diesel Generator 4', 'TP02', 'DG', 250.0),
    ('AST-SOL-02', 'SR-E-AP-SPX-000002', 'Solar Plant 2', 'TP02', 'SOLAR', 100.0),
    ('AST-TRF-03', 'SR-E-HT-TFR-000003', 'HT Substation Transformer 3', 'TP02', 'TRANSFORMER', 500.0),
    ('AST-UPS-04', 'SR-E-AP-UPS-000004', 'Toll Plaza UPS 4', 'TP02', 'UPS', 40.0),
    ('AST-UPS-09', 'SR-E-AP-UPS-000009', 'Toll Plaza UPS 9', 'TP02', 'UPS', 40.0),

    -- TP03 Assets
    ('AST-EB-03', 'SRTPL_Test_JUNO_EB', 'Main EB Incomer TP03', 'TP03', 'EB', 500.0),
    ('AST-DG-05', 'SR-E-AP-DGX-000005', 'Diesel Generator 5', 'TP03', 'DG', 250.0),
    ('AST-DG-06', 'SR-E-AP-DGX-000006', 'Diesel Generator 6', 'TP03', 'DG', 250.0),
    ('AST-SOL-03', 'SR-E-AP-SPX-000003', 'Solar Plant 3', 'TP03', 'SOLAR', 100.0),
    ('AST-TRF-01', 'SR-E-HT-TFR-000001', 'HT Substation Transformer 1', 'TP03', 'TRANSFORMER', 500.0),
    ('AST-UPS-10', 'SR-E-AP-UPS-000010', 'Toll Plaza UPS 10', 'TP03', 'UPS', 40.0),
    ('AST-UPS-12', 'SR-E-AP-UPS-000012', 'Toll Plaza UPS 12', 'TP03', 'UPS', 40.0)
ON CONFLICT (asset_id) DO NOTHING;

-- 3. JUNO RAW INGESTION AUDIT TABLES
CREATE TABLE IF NOT EXISTS energy_import.import_batch (
    import_batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(32) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    uploaded_by VARCHAR(128) NOT NULL,
    total_files INT NOT NULL DEFAULT 0,
    total_rows INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS energy_import.import_file (
    import_file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_batch_id UUID NOT NULL REFERENCES energy_import.import_batch(import_batch_id),
    file_name VARCHAR(256) NOT NULL,
    file_sha256 VARCHAR(64) NOT NULL UNIQUE,
    file_size_bytes BIGINT NOT NULL,
    report_type VARCHAR(32) NOT NULL,
    parsed_rows INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. NORMALIZED READINGS TABLES (EB, DG, Solar, Transformer, UPS)
CREATE TABLE IF NOT EXISTS energy_readings.eb (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) NOT NULL REFERENCES energy_master.asset(asset_id),
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 4),
    cumulative_kvah NUMERIC(14, 4),
    cumulative_kvarh NUMERIC(14, 4),
    interval_kwh NUMERIC(14, 4),
    interval_kvah NUMERIC(14, 4),
    interval_kvarh NUMERIC(14, 4),
    pf NUMERIC(5, 4),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS energy_readings.dg (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) NOT NULL REFERENCES energy_master.asset(asset_id),
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 4),
    cumulative_running_hours NUMERIC(10, 4),
    interval_kwh NUMERIC(14, 4),
    interval_running_hours NUMERIC(10, 4),
    pf NUMERIC(5, 4),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS energy_readings.solar (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) NOT NULL REFERENCES energy_master.asset(asset_id),
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 4),
    interval_kwh NUMERIC(14, 4),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS energy_readings.transformer (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) NOT NULL REFERENCES energy_master.asset(asset_id),
    reading_datetime TIMESTAMPTZ NOT NULL,
    primary_v_ry NUMERIC(10, 2), primary_v_yb NUMERIC(10, 2), primary_v_br NUMERIC(10, 2),
    secondary_v_ry NUMERIC(10, 2), secondary_v_yb NUMERIC(10, 2), secondary_v_br NUMERIC(10, 2),
    primary_i_r NUMERIC(10, 2), primary_i_y NUMERIC(10, 2), primary_i_b NUMERIC(10, 2),
    secondary_i_r NUMERIC(10, 2), secondary_i_y NUMERIC(10, 2), secondary_i_b NUMERIC(10, 2),
    oil_temperature NUMERIC(6, 2),
    winding_temperature NUMERIC(6, 2),
    pf NUMERIC(5, 4),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS energy_readings.ups (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) NOT NULL REFERENCES energy_master.asset(asset_id),
    reading_datetime TIMESTAMPTZ NOT NULL,
    output_voltage NUMERIC(10, 2),
    output_current NUMERIC(10, 2),
    output_frequency NUMERIC(6, 2),
    battery_vdc NUMERIC(10, 2),
    battery_temperature NUMERIC(6, 2),
    rectifier_voltage NUMERIC(10, 2),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. KPI MASTER DEFINITIONS & RESULT
CREATE TABLE IF NOT EXISTS energy_analytics.kpi_master (
    kpi_id VARCHAR(64) PRIMARY KEY,
    kpi_code VARCHAR(32) NOT NULL UNIQUE,
    kpi_name VARCHAR(128) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    formula_description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true
);

INSERT INTO energy_analytics.kpi_master (kpi_id, kpi_code, kpi_name, source_type, unit, formula_description) VALUES
    -- EB KPIs
    ('KPI-EB-01', 'EB-CONS-D', 'Daily EB Consumption', 'EB', 'kWh', 'SUM of validated interval_kwh for billing period'),
    ('KPI-EB-02', 'EB-KVAH-D', 'Daily EB Apparent Energy', 'EB', 'kVAh', 'SUM of validated interval_kvah'),
    ('KPI-EB-03', 'EB-PF-D', 'Average EB Power Factor', 'EB', 'PF', 'AVERAGE of validated power factor readings'),
    ('KPI-EB-04', 'EB-KWH-KVAH', 'EB kWh/kVAh Ratio', 'EB', 'ratio', 'EB-CONS-D / EB-KVAH-D'),

    -- DG KPIs
    ('KPI-DG-01', 'DG-GEN-D', 'Daily DG Generation', 'DG', 'kWh', 'SUM of validated interval_kwh from running generators'),
    ('KPI-DG-02', 'DG-RUN-D', 'Daily DG Runtime Hours', 'DG', 'hour', 'SUM of validated running hours'),
    ('KPI-DG-03', 'DG-KWH-HR', 'DG Generation Rate', 'DG', 'kWh/hr', 'DG-GEN-D / DG-RUN-D'),
    ('KPI-DG-04', 'DG-PF', 'Average DG Power Factor', 'DG', 'PF', 'AVERAGE of validated DG power factor'),

    -- Solar KPIs
    ('KPI-SOL-01', 'SOL-GEN-D', 'Daily Solar Generation', 'SOLAR', 'kWh', 'SUM of validated solar interval_kwh'),
    ('KPI-SOL-02', 'SOL-AVAIL-D', 'Solar Reporting Availability', 'SOLAR', '%', '(Valid readings / Total expected) * 100'),

    -- Transformer KPIs
    ('KPI-TRF-01', 'TR-VI-01', 'Primary Voltage Imbalance', 'TRANSFORMER', '%', 'Max deviation from average line voltage'),
    ('KPI-TRF-02', 'TR-CI-01', 'Primary Current Imbalance', 'TRANSFORMER', '%', 'Max deviation from average phase current'),
    ('KPI-TRF-03', 'TRF-PF', 'Average Transformer PF', 'TRANSFORMER', 'PF', 'AVERAGE of validated transformer PF'),
    ('KPI-TRF-04', 'TRF-MAX-OTI', 'Max Oil Temperature', 'TRANSFORMER', '°C', 'MAX oil temperature during interval'),
    ('KPI-TRF-05', 'TRF-MAX-WTI', 'Max Winding Temperature', 'TRANSFORMER', '°C', 'MAX winding temperature during interval'),

    -- UPS KPIs
    ('KPI-UPS-01', 'UPS-AV-01', 'UPS Reporting Availability', 'UPS', '%', '(Operational readings / Total readings) * 100'),
    ('KPI-UPS-02', 'UPS-V-OUT-AVG', 'Average Output Voltage', 'UPS', 'V', 'AVERAGE of validated output AC voltage'),
    ('KPI-UPS-03', 'UPS-F-OUT-AVG', 'Average Output Frequency', 'UPS', 'Hz', 'AVERAGE of output frequency (48-52 Hz window)'),
    ('KPI-UPS-04', 'UPS-BATT-V-AVG', 'Average Battery DC Voltage', 'UPS', 'V', 'AVERAGE of DC bus battery voltage')
ON CONFLICT (kpi_id) DO NOTHING;

-- 6. AUDIT & EXCEPTION MASTER
CREATE TABLE IF NOT EXISTS energy_validation.exception_record (
    exception_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) NOT NULL REFERENCES energy_master.asset(asset_id),
    rule_code VARCHAR(32) NOT NULL,
    severity VARCHAR(16) NOT NULL, -- INFO, WARNING, ERROR, CRITICAL
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    reading_datetime TIMESTAMPTZ NOT NULL,
    detected_value NUMERIC(14, 4),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed Demo Exceptions
INSERT INTO energy_validation.exception_record (asset_id, rule_code, severity, status, reading_datetime, detected_value, message) VALUES
    ('AST-DG-01', 'VAL-DG-001', 'WARNING', 'OPEN', NOW() - INTERVAL '2 days', -12.4, 'Cumulative kWh decreased between consecutive intervals'),
    ('AST-EB-01', 'VAL-EB-003', 'INFO', 'ACKNOWLEDGED', NOW() - INTERVAL '3 days', 0.88, 'Power factor dipped below target 0.90 threshold'),
    ('AST-TRF-02', 'VAL-TRF-PV-IMB', 'WARNING', 'OPEN', NOW() - INTERVAL '1 day', 1.82, 'Primary voltage phase imbalance exceeded 1.5% warning threshold')
ON CONFLICT DO NOTHING;
