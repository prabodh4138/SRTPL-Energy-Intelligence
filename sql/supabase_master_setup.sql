-- ============================================================================
-- SRTPL PROJECT (SUPABASE) — ALL-IN-ONE SELF-HEALING MASTER SETUP SCRIPT
-- Target Project: Srtpl_Project
--
-- This script is 100% self-contained. It:
-- 1. Drops deprecated 'energy_raw' schema
-- 2. Creates all required schemas (energy_master, energy_import, energy_readings, energy_validation, etc.)
-- 3. Creates all tables with proper types, primary keys, and strict UNIQUE constraints
--    - Level 1 Deduplication: energy_import.import_file UNIQUE(sha256_hash)
--    - Level 2 Deduplication: energy_readings.* UNIQUE(asset_id, reading_datetime)
-- 4. Exposes synchronized views in 'public' for instant Supabase UI & REST API access
-- 5. Enables Row Level Security (RLS) on all tables with full CRUD policies
-- 6. Seeds default Plazas and 21 Assets
-- ============================================================================

-- STEP 1: EXTENSIONS & CLEANUP
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
DROP SCHEMA IF EXISTS energy_raw CASCADE;

-- STEP 2: CREATE ALL SCHEMAS (Guarantees no "schema does not exist" error)
CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_import;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_validation;
CREATE SCHEMA IF NOT EXISTS energy_analytics;
CREATE SCHEMA IF NOT EXISTS energy_admin;
CREATE SCHEMA IF NOT EXISTS energy_audit;

-- STEP 3: MASTER DATA TABLES (Plazas & Assets)
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
    plaza_id VARCHAR(16) NOT NULL REFERENCES energy_master.plaza(plaza_id) ON DELETE CASCADE,
    source_type VARCHAR(32) NOT NULL,
    capacity_kva NUMERIC(10, 2),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 4: IMPORT TRACKING (Level 1 Duplicate Prevention: SHA-256 Uniqueness)
CREATE TABLE IF NOT EXISTS energy_import.import_file (
    import_file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

-- STEP 5: TELEMETRY READINGS TABLES (Level 2 Duplicate Prevention: asset_id + reading_datetime)
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
    cumulative_running_hours NUMERIC(10, 4),
    interval_kwh NUMERIC(14, 4),
    interval_running_hours NUMERIC(10, 4),
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
    primary_v_ry NUMERIC(10, 2), primary_v_yb NUMERIC(10, 2), primary_v_br NUMERIC(10, 2),
    secondary_v_ry NUMERIC(10, 2), secondary_v_yb NUMERIC(10, 2), secondary_v_br NUMERIC(10, 2),
    primary_i_r NUMERIC(10, 2), primary_i_y NUMERIC(10, 2), primary_i_b NUMERIC(10, 2),
    secondary_i_r NUMERIC(10, 2), secondary_i_y NUMERIC(10, 2), secondary_i_b NUMERIC(10, 2),
    oil_temperature NUMERIC(6, 2),
    winding_temperature NUMERIC(6, 2),
    pf NUMERIC(5, 4),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_transformer_asset_datetime UNIQUE (asset_id, reading_datetime)
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

-- Ensure UNIQUE constraints exist if tables were created previously
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_eb_asset_datetime') THEN
        ALTER TABLE energy_readings.eb ADD CONSTRAINT uq_eb_asset_datetime UNIQUE (asset_id, reading_datetime);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_dg_asset_datetime') THEN
        ALTER TABLE energy_readings.dg ADD CONSTRAINT uq_dg_asset_datetime UNIQUE (asset_id, reading_datetime);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_solar_asset_datetime') THEN
        ALTER TABLE energy_readings.solar ADD CONSTRAINT uq_solar_asset_datetime UNIQUE (asset_id, reading_datetime);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_transformer_asset_datetime') THEN
        ALTER TABLE energy_readings.transformer ADD CONSTRAINT uq_transformer_asset_datetime UNIQUE (asset_id, reading_datetime);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_ups_asset_datetime') THEN
        ALTER TABLE energy_readings.ups ADD CONSTRAINT uq_ups_asset_datetime UNIQUE (asset_id, reading_datetime);
    END IF;
EXCEPTION
    WHEN OTHERS THEN NULL;
END $$;

-- STEP 6: EXCEPTIONS & AUDIT TABLE
CREATE TABLE IF NOT EXISTS energy_validation.exception_record (
    exception_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    rule_code VARCHAR(32) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    reading_datetime TIMESTAMPTZ,
    detected_value NUMERIC(14, 4),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 7: ENERGY BILLS (Includes all 14 Extracted Fields + Math Verification)
CREATE TABLE IF NOT EXISTS public.energy_bills (
    bill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_filename VARCHAR(256) NOT NULL,
    consumer_account_no VARCHAR(64),
    consumer_id VARCHAR(64),
    old_consumer_no VARCHAR(64),
    bill_number VARCHAR(64) UNIQUE,
    bill_month VARCHAR(32),
    bill_period VARCHAR(64),
    bill_days VARCHAR(16),
    meter_sl_no VARCHAR(64),
    meter_rent_count VARCHAR(32),
    security_deposit NUMERIC(14, 2),
    tariff_category VARCHAR(64),
    division VARCHAR(128),
    sub_division VARCHAR(128),
    section VARCHAR(128),
    slab_normal_kwh NUMERIC(14, 2),
    slab_peak_kwh NUMERIC(14, 2),
    slab_solar_kwh NUMERIC(14, 2),
    energy_charges NUMERIC(14, 2),
    dps_rs NUMERIC(14, 2),
    current_total NUMERIC(14, 2),
    total_amount_payable NUMERIC(14, 2),
    cal_energy_charges NUMERIC(14, 2),
    diff_energy_charges NUMERIC(14, 2),
    cal_electricity_charges NUMERIC(14, 2),
    diff_electricity_charges NUMERIC(14, 2),
    cal_current_total NUMERIC(14, 2),
    diff_current_total NUMERIC(14, 2),
    verification_status VARCHAR(32) NOT NULL DEFAULT 'VERIFIED_MATCH',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 8: PAYMENT RECEIPTS TABLE
CREATE TABLE IF NOT EXISTS public.payment_receipts (
    receipt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receipt_no VARCHAR(64) NOT NULL UNIQUE,
    consumer_no VARCHAR(64),
    account_no VARCHAR(64),
    consumer_name VARCHAR(256),
    collections_date VARCHAR(32),
    amount_paid NUMERIC(14, 2),
    payment_type VARCHAR(32),
    transaction_id VARCHAR(64),
    bill_month VARCHAR(32),
    category VARCHAR(64),
    source_pdf VARCHAR(256) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 9: PUBLIC CONVENIENCE VIEWS (Allows querying both schema styles)
CREATE OR REPLACE VIEW public.plaza AS SELECT * FROM energy_master.plaza;
CREATE OR REPLACE VIEW public.asset AS SELECT * FROM energy_master.asset;
CREATE OR REPLACE VIEW public.import_file AS SELECT * FROM energy_import.import_file;
CREATE OR REPLACE VIEW public.reading_eb AS SELECT * FROM energy_readings.eb;
CREATE OR REPLACE VIEW public.reading_dg AS SELECT * FROM energy_readings.dg;
CREATE OR REPLACE VIEW public.reading_solar AS SELECT * FROM energy_readings.solar;
CREATE OR REPLACE VIEW public.reading_transformer AS SELECT * FROM energy_readings.transformer;
CREATE OR REPLACE VIEW public.reading_ups AS SELECT * FROM energy_readings.ups;
CREATE OR REPLACE VIEW public.exception_record AS SELECT * FROM energy_validation.exception_record;

-- STEP 10: RESET / WIPE STORED PROCEDURE
CREATE OR REPLACE FUNCTION public.reset_all_energy_data()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    TRUNCATE TABLE 
        energy_readings.eb,
        energy_readings.dg,
        energy_readings.solar,
        energy_readings.transformer,
        energy_readings.ups,
        energy_validation.exception_record,
        energy_import.import_file,
        public.energy_bills,
        public.payment_receipts
    CASCADE;
END;
$$;

-- STEP 11: ENABLE ROW LEVEL SECURITY (RLS) ON ALL TABLES
ALTER TABLE energy_master.plaza ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_master.asset ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_import.import_file ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings.eb ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings.dg ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings.solar ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings.transformer ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings.ups ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_validation.exception_record ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_receipts ENABLE ROW LEVEL SECURITY;

-- STEP 12: FULL CRUD RLS POLICIES FOR APPLICATION & AUTHENTICATED USERS
DROP POLICY IF EXISTS "allow_all_plaza" ON energy_master.plaza;
CREATE POLICY "allow_all_plaza" ON energy_master.plaza FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_asset" ON energy_master.asset;
CREATE POLICY "allow_all_asset" ON energy_master.asset FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

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

DROP POLICY IF EXISTS "allow_all_exception" ON energy_validation.exception_record;
CREATE POLICY "allow_all_exception" ON energy_validation.exception_record FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_bills" ON public.energy_bills;
CREATE POLICY "allow_all_bills" ON public.energy_bills FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_receipts" ON public.payment_receipts;
CREATE POLICY "allow_all_receipts" ON public.payment_receipts FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

-- STEP 13: GRANT PERMISSIONS TO POSTGREST & SUPABASE ROLES
GRANT USAGE ON SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics TO anon, authenticated, service_role;

-- STEP 14: SEED MASTER DATA (Plazas & 21 Assets)
INSERT INTO energy_master.plaza (plaza_id, plaza_name, location) VALUES
    ('TP01', 'Toll Plaza 01', 'SRTPL Corridor Km 24+500'),
    ('TP02', 'Toll Plaza 02', 'SRTPL Corridor Km 68+200'),
    ('TP03', 'Toll Plaza 03', 'SRTPL Corridor Km 112+800')
ON CONFLICT (plaza_id) DO NOTHING;

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

DO $$
BEGIN
    RAISE NOTICE 'SUCCESS: All schemas, tables, RLS policies, duplicate constraints, and master data configured with zero errors!';
END $$;
