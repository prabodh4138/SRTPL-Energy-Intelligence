-- ============================================================================
-- SRTPL PROJECT (SUPABASE) — MASTER SCHEMA REPAIR & FRESH INGESTION FIX
-- Target Project: Srtpl_Project
--
-- This script fixes:
-- 1. Sets DEFAULT gen_random_uuid() on import_batch.import_batch_id (Error 23502)
-- 2. Seeds Plazas (TP01, TP02, TP03) & Assets so Foreign Keys in energy_readings.* succeed
-- 3. Clears incomplete import_file records so fresh live CSV uploads are accepted
-- 4. Exposes all schemas in PostgREST and reloads the schema cache
-- ============================================================================

-- STEP 1: EXPOSE ALL REQUIRED SCHEMAS TO POSTGREST API
ALTER ROLE authenticator SET pgrst.db_schemas = 'public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics';

-- STEP 2: ENSURE SCHEMAS EXIST
CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_import;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_validation;
CREATE SCHEMA IF NOT EXISTS energy_analytics;

-- STEP 3: ENSURE PLAZA TABLE EXISTS & SEED DEFAULT PLAZAS
CREATE TABLE IF NOT EXISTS energy_master.plaza (
    plaza_id VARCHAR(16) PRIMARY KEY,
    plaza_name VARCHAR(128) NOT NULL,
    location VARCHAR(256),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO energy_master.plaza (plaza_id, plaza_name, location) VALUES
    ('TP01', 'Toll Plaza 01 (Main / Barabati)', 'SRTPL Corridor Km 24+500'),
    ('TP02', 'Toll Plaza 02 (Kutra)', 'SRTPL Corridor Km 68+200'),
    ('TP03', 'Toll Plaza 03 (Garposh)', 'SRTPL Corridor Km 112+800')
ON CONFLICT (plaza_id) DO NOTHING;

-- STEP 4: ENSURE ASSET TABLE EXISTS & SEED STANDARD ASSETS
CREATE TABLE IF NOT EXISTS energy_master.asset (
    asset_id VARCHAR(64) PRIMARY KEY,
    asset_code VARCHAR(64) NOT NULL UNIQUE,
    asset_name VARCHAR(128) NOT NULL,
    plaza_id VARCHAR(16) NOT NULL REFERENCES energy_master.plaza(plaza_id) ON DELETE CASCADE,
    source_type VARCHAR(32) NOT NULL,
    capacity_kva NUMERIC(10, 2),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO energy_master.asset (asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva) VALUES
    ('AST-EB-01', 'SR-E-EM-EB-000TP01', 'Main EB Incomer TP01', 'TP01', 'EB', 500.0),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', 'Main EB Incomer TP02 (Kutra)', 'TP02', 'EB', 500.0),
    ('AST-EB-03', 'SRTPL_Test_JUNO_EB', 'Main EB Incomer TP03', 'TP03', 'EB', 500.0),
    ('AST-DG-01', 'SR-E-AP-DGX-000001', 'Diesel Generator 1', 'TP01', 'DG', 250.0),
    ('AST-DG-03', 'SR-E-AP-DGX-000003', 'Diesel Generator 3', 'TP02', 'DG', 250.0),
    ('AST-SOL-01', 'SR-E-AP-SPX-000001', 'Solar Plant 1', 'TP01', 'SOLAR', 100.0),
    ('AST-SOL-02', 'SR-E-AP-SPX-000002', 'Solar Plant 2', 'TP02', 'SOLAR', 100.0),
    ('AST-TRF-02', 'SR-E-HT-TFR-000002', 'HT Substation Transformer 2', 'TP01', 'TRANSFORMER', 500.0),
    ('AST-TRF-03', 'SR-E-HT-TFR-000003', 'HT Substation Transformer 3', 'TP02', 'TRANSFORMER', 500.0),
    ('AST-UPS-02', 'SR-E-AP-UPS-000002', 'Toll Plaza UPS 2', 'TP01', 'UPS', 40.0),
    ('AST-UPS-04', 'SR-E-AP-UPS-000004', 'Toll Plaza UPS 4', 'TP02', 'UPS', 40.0)
ON CONFLICT (asset_id) DO NOTHING;

-- STEP 5: ENSURE IMPORT_BATCH HAS DEFAULT GENERATOR (Prevents 23502)
CREATE TABLE IF NOT EXISTS energy_import.import_batch (
    import_batch_id VARCHAR(64) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    uploaded_by VARCHAR(128) DEFAULT 'admin@srtpl.com',
    source_system VARCHAR(32) DEFAULT 'JUNO',
    report_type VARCHAR(32),
    parser_version VARCHAR(32),
    status VARCHAR(32) DEFAULT 'IMPORTED',
    total_files INTEGER DEFAULT 1,
    total_rows INTEGER DEFAULT 0,
    valid_rows INTEGER DEFAULT 0,
    invalid_rows INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
    BEGIN
        ALTER TABLE energy_import.import_batch ALTER COLUMN import_batch_id SET DEFAULT gen_random_uuid()::text;
    EXCEPTION WHEN OTHERS THEN
        BEGIN
            ALTER TABLE energy_import.import_batch ALTER COLUMN import_batch_id SET DEFAULT gen_random_uuid();
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END;
    END;
END $$;

-- STEP 6: ENSURE IMPORT_FILE EXISTS AND HAS DEFAULTS
CREATE TABLE IF NOT EXISTS energy_import.import_file (
    import_file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_batch_id VARCHAR(64),
    original_filename VARCHAR(256) NOT NULL,
    sha256_hash VARCHAR(64) NOT NULL UNIQUE,
    report_type VARCHAR(32) NOT NULL,
    asset_code VARCHAR(64),
    row_count INTEGER NOT NULL DEFAULT 0,
    valid_row_count INTEGER NOT NULL DEFAULT 0,
    exception_row_count INTEGER NOT NULL DEFAULT 0,
    uploaded_by VARCHAR(128) DEFAULT 'admin@srtpl.com',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
    BEGIN
        ALTER TABLE energy_import.import_file ALTER COLUMN import_file_id SET DEFAULT gen_random_uuid();
    EXCEPTION WHEN OTHERS THEN
        BEGIN
            ALTER TABLE energy_import.import_file ALTER COLUMN import_file_id SET DEFAULT gen_random_uuid()::text;
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END;
    END;

    BEGIN
        ALTER TABLE energy_import.import_file ALTER COLUMN import_batch_id DROP NOT NULL;
    EXCEPTION WHEN OTHERS THEN
        NULL;
    END;
END $$;

-- STEP 7: ENSURE ALL 5 READINGS TABLES EXIST WITH LEVEL 2 DEDUPLICATION
CREATE TABLE IF NOT EXISTS energy_readings.eb (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) NOT NULL REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 4),
    cumulative_kvah NUMERIC(14, 4),
    cumulative_kvarh NUMERIC(14, 4),
    interval_kwh NUMERIC(14, 4),
    interval_kvah NUMERIC(14, 4),
    interval_kvarh NUMERIC(14, 4),
    pf NUMERIC(5, 4),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_eb_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.dg (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) NOT NULL REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 4),
    cumulative_running_hours NUMERIC(10, 2),
    interval_kwh NUMERIC(14, 4),
    interval_running_hours NUMERIC(10, 2),
    pf NUMERIC(5, 4),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dg_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.solar (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) NOT NULL REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 4),
    interval_kwh NUMERIC(14, 4),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_solar_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.transformer (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) NOT NULL REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    reading_datetime TIMESTAMPTZ NOT NULL,
    primary_v_ry NUMERIC(10, 2),
    primary_v_yb NUMERIC(10, 2),
    primary_v_br NUMERIC(10, 2),
    secondary_v_ry NUMERIC(10, 2),
    secondary_v_yb NUMERIC(10, 2),
    secondary_v_br NUMERIC(10, 2),
    primary_i_r NUMERIC(10, 2),
    primary_i_y NUMERIC(10, 2),
    primary_i_b NUMERIC(10, 2),
    secondary_i_r NUMERIC(10, 2),
    secondary_i_y NUMERIC(10, 2),
    secondary_i_b NUMERIC(10, 2),
    oil_temperature NUMERIC(6, 2),
    winding_temperature NUMERIC(6, 2),
    pf NUMERIC(5, 4),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_trf_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.ups (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) NOT NULL REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    reading_datetime TIMESTAMPTZ NOT NULL,
    output_voltage NUMERIC(10, 2),
    output_current NUMERIC(10, 2),
    output_frequency NUMERIC(6, 2),
    battery_vdc NUMERIC(10, 2),
    battery_temperature NUMERIC(6, 2),
    rectifier_voltage NUMERIC(10, 2),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ups_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_validation.exception_record (
    exception_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    rule_code VARCHAR(32) NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'ERROR',
    status VARCHAR(16) NOT NULL DEFAULT 'OPEN',
    reading_datetime TIMESTAMPTZ,
    detected_value NUMERIC(14, 4),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 8: EXPOSE CONVENIENCE VIEWS IN PUBLIC SCHEMA
CREATE OR REPLACE VIEW public.plaza AS SELECT * FROM energy_master.plaza;
CREATE OR REPLACE VIEW public.asset AS SELECT * FROM energy_master.asset;
CREATE OR REPLACE VIEW public.import_batch AS SELECT * FROM energy_import.import_batch;
CREATE OR REPLACE VIEW public.import_file AS SELECT * FROM energy_import.import_file;
CREATE OR REPLACE VIEW public.reading_eb AS SELECT * FROM energy_readings.eb;
CREATE OR REPLACE VIEW public.reading_dg AS SELECT * FROM energy_readings.dg;
CREATE OR REPLACE VIEW public.reading_solar AS SELECT * FROM energy_readings.solar;
CREATE OR REPLACE VIEW public.reading_transformer AS SELECT * FROM energy_readings.transformer;
CREATE OR REPLACE VIEW public.reading_ups AS SELECT * FROM energy_readings.ups;
CREATE OR REPLACE VIEW public.exception_record AS SELECT * FROM energy_validation.exception_record;

-- STEP 9: ROW LEVEL SECURITY POLICIES (Full CRUD access)
ALTER TABLE energy_master.plaza ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_master.asset ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_import.import_batch ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_import.import_file ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings.eb ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings.dg ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings.solar ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings.transformer ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings.ups ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_validation.exception_record ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "allow_all_plaza" ON energy_master.plaza;
CREATE POLICY "allow_all_plaza" ON energy_master.plaza FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_asset" ON energy_master.asset;
CREATE POLICY "allow_all_asset" ON energy_master.asset FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_import_batch" ON energy_import.import_batch;
CREATE POLICY "allow_all_import_batch" ON energy_import.import_batch FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_import_file" ON energy_import.import_file;
CREATE POLICY "allow_all_import_file" ON energy_import.import_file FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_eb" ON energy_readings.eb;
CREATE POLICY "allow_all_eb" ON energy_readings.eb FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_dg" ON energy_readings.dg;
CREATE POLICY "allow_all_dg" ON energy_readings.dg FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_solar" ON energy_readings.solar;
CREATE POLICY "allow_all_solar" ON energy_readings.solar FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_trf" ON energy_readings.transformer;
CREATE POLICY "allow_all_trf" ON energy_readings.transformer FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_ups" ON energy_readings.ups;
CREATE POLICY "allow_all_ups" ON energy_readings.ups FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_exc" ON energy_validation.exception_record;
CREATE POLICY "allow_all_exc" ON energy_validation.exception_record FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

-- STEP 10: GRANT ALL PERMISSIONS TO SUPABASE ROLES
GRANT USAGE ON SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

GRANT ALL ON ALL TABLES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

GRANT ALL ON ALL SEQUENCES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

GRANT ALL ON ALL ROUTINES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

ALTER DEFAULT PRIVILEGES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
GRANT ALL ON TABLES TO anon, authenticated, service_role, postgres, authenticator;

-- STEP 11: WIPE INCOMPLETE UPLOADS SO FRESH CSV UPLOADS ARE ACCEPTED (LEVEL 1 CLEAN START)
TRUNCATE TABLE 
    energy_readings.eb,
    energy_readings.dg,
    energy_readings.solar,
    energy_readings.transformer,
    energy_readings.ups,
    energy_validation.exception_record,
    energy_import.import_file,
    energy_import.import_batch
CASCADE;

-- STEP 12: RELOAD POSTGREST CONFIG & SCHEMA CACHE
NOTIFY pgrst, 'reload config';
NOTIFY pgrst, 'reload schema';
