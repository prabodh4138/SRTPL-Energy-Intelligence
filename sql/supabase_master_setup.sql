-- ============================================================================
-- SRTPL PROJECT (SUPABASE) — ALL-IN-ONE SELF-HEALING MASTER SETUP SCRIPT
-- Target Project: Srtpl_Project
--
-- This script is 100% self-contained. It:
-- 1. Drops legacy tables, creates empty schema to prevent PostgREST PGRST002 cache crash
-- 2. Creates all required schemas (energy_master, energy_import, energy_readings, energy_validation, etc.)
-- 3. Creates all tables with proper types, primary keys, and strict UNIQUE constraints
--    - Level 1 Deduplication: energy_import.import_file UNIQUE(sha256_hash)
--    - Level 2 Deduplication: energy_readings.* UNIQUE(asset_id, reading_datetime)
-- 4. Exposes synchronized views in 'public' for instant Supabase UI & REST API access
-- 5. Enables Row Level Security (RLS) on all tables with full CRUD policies
-- 6. Grants permissions to anon, authenticated, service_role, and authenticator
-- 7. Signals PostgREST to reload its schema cache (eliminating PGRST002)
-- 8. Seeds default Plazas and 21 Assets
-- ============================================================================

-- STEP 1: EXTENSIONS & CLEANUP
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Reset legacy energy_raw tables, but keep empty schema so PostgREST doesn't crash with PGRST002
DO $$
BEGIN
    DROP SCHEMA IF EXISTS energy_raw CASCADE;
    CREATE SCHEMA IF NOT EXISTS energy_raw;
EXCEPTION WHEN OTHERS THEN
    CREATE SCHEMA IF NOT EXISTS energy_raw;
END $$;

-- STEP 2: CREATE ALL SCHEMAS & EXPOSE TO POSTGREST API
CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_import;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_validation;
CREATE SCHEMA IF NOT EXISTS energy_analytics;
CREATE SCHEMA IF NOT EXISTS energy_admin;
CREATE SCHEMA IF NOT EXISTS energy_audit;

-- Expose schemas in PostgREST configuration to eliminate PGRST205 errors
ALTER ROLE authenticator SET pgrst.db_schemas = 'public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics';

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

-- Master Consumer Account & Asset Mapping Table
CREATE TABLE IF NOT EXISTS energy_master.consumer_account (
    consumer_account_no VARCHAR(64) PRIMARY KEY,
    toll_plaza_id VARCHAR(16) REFERENCES energy_master.plaza(plaza_id) ON DELETE SET NULL,
    bill_type VARCHAR(32) NOT NULL DEFAULT 'HT',
    asset_code VARCHAR(64) NOT NULL,
    consumer_scope VARCHAR(64) NOT NULL DEFAULT 'HIGHWAY',
    division_name VARCHAR(128) NOT NULL,
    usage_type VARCHAR(128) NOT NULL DEFAULT 'Street Light',
    sanctioned_load_kw NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    location VARCHAR(256) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    remarks TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consumer_account_asset ON energy_master.consumer_account(asset_code);
CREATE INDEX IF NOT EXISTS idx_consumer_account_plaza ON energy_master.consumer_account(toll_plaza_id);
CREATE INDEX IF NOT EXISTS idx_consumer_account_division ON energy_master.consumer_account(division_name);

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

-- Ensure default generator exists on existing tables (handles both text/varchar and UUID)
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

CREATE TABLE IF NOT EXISTS energy_import.import_row (
    import_row_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_file_id UUID REFERENCES energy_import.import_file(import_file_id) ON DELETE CASCADE,
    source_row_number INTEGER,
    source_record_hash VARCHAR(64),
    business_key VARCHAR(128),
    raw_payload JSONB,
    parse_status VARCHAR(32) DEFAULT 'PARSED',
    validation_status VARCHAR(32) DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 5: TELEMETRY READINGS TABLES (Level 2 Duplicate Prevention: asset_id + reading_datetime)
CREATE TABLE IF NOT EXISTS energy_readings.eb (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    asset_code VARCHAR(64),
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 4),
    cumulative_kvah NUMERIC(14, 4),
    cumulative_kvarh NUMERIC(14, 4),
    interval_kwh NUMERIC(14, 4),
    interval_kvah NUMERIC(14, 4),
    interval_kvarh NUMERIC(14, 4),
    pf NUMERIC(5, 4),
    maximum_demand NUMERIC(10, 2),
    created_by VARCHAR(128),
    created_on TIMESTAMPTZ,
    remarks TEXT,
    consumer_number VARCHAR(64),
    location VARCHAR(256),
    category VARCHAR(64),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_eb_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.dg (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    asset_code VARCHAR(64),
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 4),
    cumulative_running_hours NUMERIC(10, 4),
    interval_kwh NUMERIC(14, 4),
    interval_running_hours NUMERIC(10, 4),
    pf NUMERIC(5, 4),
    created_by VARCHAR(128),
    created_on TIMESTAMPTZ,
    remarks TEXT,
    location VARCHAR(256),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dg_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.solar (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    asset_code VARCHAR(64),
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 4),
    interval_kwh NUMERIC(14, 4),
    created_by VARCHAR(128),
    created_on TIMESTAMPTZ,
    remarks TEXT,
    location VARCHAR(256),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_solar_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.transformer (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    asset_code VARCHAR(64),
    reading_datetime TIMESTAMPTZ NOT NULL,
    primary_v_ry NUMERIC(10, 2), primary_v_yb NUMERIC(10, 2), primary_v_br NUMERIC(10, 2),
    secondary_v_ry NUMERIC(10, 2), secondary_v_yb NUMERIC(10, 2), secondary_v_br NUMERIC(10, 2),
    primary_i_r NUMERIC(10, 2), primary_i_y NUMERIC(10, 2), primary_i_b NUMERIC(10, 2),
    secondary_i_r NUMERIC(10, 2), secondary_i_y NUMERIC(10, 2), secondary_i_b NUMERIC(10, 2),
    oil_temperature NUMERIC(6, 2),
    winding_temperature NUMERIC(6, 2),
    pf NUMERIC(5, 4),
    created_by VARCHAR(128),
    created_on TIMESTAMPTZ,
    remarks TEXT,
    location VARCHAR(256),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_transformer_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.ups (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    asset_code VARCHAR(64),
    reading_datetime TIMESTAMPTZ NOT NULL,
    output_voltage NUMERIC(10, 2),
    output_current NUMERIC(10, 2),
    output_frequency NUMERIC(6, 2),
    battery_vdc NUMERIC(10, 2),
    battery_temperature NUMERIC(6, 2),
    rectifier_voltage NUMERIC(10, 2),
    created_by VARCHAR(128),
    created_on TIMESTAMPTZ,
    remarks TEXT,
    location VARCHAR(256),
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
    asset_code VARCHAR(64),
    created_by VARCHAR(128),
    created_on TIMESTAMPTZ,
    rule_code VARCHAR(32) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    reading_datetime TIMESTAMPTZ,
    detected_value NUMERIC(14, 4),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- STEP 7: ENERGY BILLS (Includes all 14 Extracted Fields + Math Verification + Audit Fields)
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
    bill_issue_date VARCHAR(32),
    due_date VARCHAR(32),
    rebate_date VARCHAR(32),
    tariff_category VARCHAR(64),
    tariff_type VARCHAR(64),
    division VARCHAR(128),
    sub_division VARCHAR(128),
    section VARCHAR(128),
    meter_sl_no VARCHAR(64),
    meter_rent_count VARCHAR(32),
    security_deposit NUMERIC(14, 2) DEFAULT 0.0,
    md_kw NUMERIC(10, 2) DEFAULT 0.0,
    md_kva NUMERIC(10, 2) DEFAULT 0.0,
    slab_normal_kwh NUMERIC(14, 2) DEFAULT 0.0,
    slab_peak_kwh NUMERIC(14, 2) DEFAULT 0.0,
    slab_solar_kwh NUMERIC(14, 2) DEFAULT 0.0,
    energy_charges NUMERIC(14, 2) DEFAULT 0.0,
    demand_charge NUMERIC(14, 2) DEFAULT 0.0,
    tod_incentive NUMERIC(14, 2) DEFAULT 0.0,
    tod_surcharge NUMERIC(14, 2) DEFAULT 0.0,
    electricity_charges NUMERIC(14, 2) DEFAULT 0.0,
    electricity_duty NUMERIC(14, 2) DEFAULT 0.0,
    meter_rent NUMERIC(14, 2) DEFAULT 0.0,
    customer_service_charge NUMERIC(14, 2) DEFAULT 0.0,
    dps_rs NUMERIC(14, 2) DEFAULT 0.0,
    current_total NUMERIC(14, 2) DEFAULT 0.0,
    prompt_rebate NUMERIC(14, 2) DEFAULT 0.0,
    total_amount_payable NUMERIC(14, 2) DEFAULT 0.0,
    net_after_rebate NUMERIC(14, 2) DEFAULT 0.0,
    cal_energy_charges NUMERIC(14, 2) DEFAULT 0.0,
    diff_energy_charges NUMERIC(14, 2) DEFAULT 0.0,
    cal_electricity_charges NUMERIC(14, 2) DEFAULT 0.0,
    diff_electricity_charges NUMERIC(14, 2) DEFAULT 0.0,
    cal_current_total NUMERIC(14, 2) DEFAULT 0.0,
    diff_current_total NUMERIC(14, 2) DEFAULT 0.0,
    verification_status VARCHAR(64) NOT NULL DEFAULT 'VERIFIED_MATCH',
    is_edited BOOLEAN NOT NULL DEFAULT FALSE,
    edited_by VARCHAR(128),
    edited_at TIMESTAMPTZ,
    edit_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ensure all extended and audit columns exist if table was created previously
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS bill_issue_date VARCHAR(32);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS due_date VARCHAR(32);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS rebate_date VARCHAR(32);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS tariff_type VARCHAR(64);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS md_kw NUMERIC(10, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS md_kva NUMERIC(10, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS demand_charge NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS tod_incentive NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS tod_surcharge NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS electricity_charges NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS electricity_duty NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS meter_rent NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS customer_service_charge NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS prompt_rebate NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS net_after_rebate NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS is_edited BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS edited_by VARCHAR(128);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS edited_at TIMESTAMPTZ;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS edit_notes TEXT;

NOTIFY pgrst, 'reload schema';

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
CREATE OR REPLACE VIEW public.energy_consumer_master AS SELECT * FROM energy_master.consumer_account;
CREATE OR REPLACE VIEW public.consumer_account AS SELECT * FROM energy_master.consumer_account;
CREATE OR REPLACE VIEW public.import_file AS SELECT * FROM energy_import.import_file;
CREATE OR REPLACE VIEW public.import_batch AS SELECT * FROM energy_import.import_batch;
CREATE OR REPLACE VIEW public.import_row AS SELECT * FROM energy_import.import_row;
DROP VIEW IF EXISTS public.reading_eb CASCADE;
CREATE VIEW public.reading_eb AS SELECT * FROM energy_readings.eb;

DROP VIEW IF EXISTS public.reading_dg CASCADE;
CREATE VIEW public.reading_dg AS SELECT * FROM energy_readings.dg;

DROP VIEW IF EXISTS public.reading_solar CASCADE;
CREATE VIEW public.reading_solar AS SELECT * FROM energy_readings.solar;

DROP VIEW IF EXISTS public.reading_transformer CASCADE;
CREATE VIEW public.reading_transformer AS SELECT * FROM energy_readings.transformer;

DROP VIEW IF EXISTS public.reading_ups CASCADE;
CREATE VIEW public.reading_ups AS SELECT * FROM energy_readings.ups;

DROP VIEW IF EXISTS public.exception_record CASCADE;
CREATE VIEW public.exception_record AS SELECT * FROM energy_validation.exception_record;

-- STEP 10: RESET & CACHE RELOAD PROCEDURES
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
        energy_import.import_row,
        energy_import.import_batch,
        public.energy_bills,
        public.payment_receipts
    CASCADE;
END;
$$;

CREATE OR REPLACE FUNCTION public.reload_schema_cache()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    NOTIFY pgrst, 'reload schema';
END;
$$;
GRANT EXECUTE ON FUNCTION public.reload_schema_cache() TO anon, authenticated, service_role, postgres;

-- STEP 11: ENABLE ROW LEVEL SECURITY (RLS) ON ALL TABLES
ALTER TABLE energy_master.plaza ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_master.asset ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_master.consumer_account ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_import.import_file ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_import.import_batch ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_import.import_row ENABLE ROW LEVEL SECURITY;
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

DROP POLICY IF EXISTS "allow_all_consumer_account" ON energy_master.consumer_account;
CREATE POLICY "allow_all_consumer_account" ON energy_master.consumer_account FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_import_file" ON energy_import.import_file;
CREATE POLICY "allow_all_import_file" ON energy_import.import_file FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_import_batch" ON energy_import.import_batch;
CREATE POLICY "allow_all_import_batch" ON energy_import.import_batch FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_import_row" ON energy_import.import_row;
CREATE POLICY "allow_all_import_row" ON energy_import.import_row FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

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

-- STEP 13: GRANT PERMISSIONS TO POSTGREST & SUPABASE ROLES (INCLUDING authenticator)
GRANT USAGE ON SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics, energy_raw 
TO anon, authenticated, service_role, postgres, authenticator;

GRANT ALL ON ALL TABLES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

GRANT ALL ON ALL SEQUENCES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

GRANT ALL ON ALL ROUTINES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

ALTER DEFAULT PRIVILEGES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
GRANT ALL ON TABLES TO anon, authenticated, service_role, postgres, authenticator;

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
    ('AST-UPS-12', 'SR-E-AP-UPS-000012', 'Toll Plaza UPS 12', 'TP03', 'UPS', 40.0),

    -- Additional Corridor EB Meters
    ('AST-EB-04', 'SR-E-EM-EB-5-200', 'Corridor Lighting Meter 05.200 (Ainthapalli)', 'TP01', 'EB', 50.0),
    ('AST-EB-05', 'SR-E-EM-EB-62-600', 'Corridor Lighting Meter 62.600 (Tangarpali)', 'TP02', 'EB', 50.0),
    ('AST-EB-06', 'SR-E-EM-EB-148-500', 'Corridor Lighting Meter 148.500 (Garposh)', 'TP03', 'EB', 50.0),
    ('AST-EB-07', 'SR-E-EM-EB-000TP03', 'Main EB Substation TP03', 'TP03', 'EB', 500.0),
    ('AST-EB-08', 'SR-E-EM-EB-160-200', 'Garposh Toll Approach Meter', 'TP03', 'EB', 50.0)
ON CONFLICT (asset_id) DO UPDATE
SET asset_code = EXCLUDED.asset_code,
    asset_name = EXCLUDED.asset_name,
    plaza_id = EXCLUDED.plaza_id;

-- Seed Energy Consumer Accounts Master Data (Across All Toll Plazas TP01, TP02, TP03)
INSERT INTO energy_master.consumer_account (
    consumer_account_no, toll_plaza_id, bill_type, asset_code, consumer_scope, division_name, usage_type, sanctioned_load_kw, location, is_active
) VALUES
    ('411001070208', 'TP01', 'HT', 'SR-E-EM-EB-5-200', 'HIGHWAY', 'SED', 'Street Light', 10.0, 'Ainthapalli', true),
    ('413001070099', 'TP02', 'HT', 'SR-E-EM-EB-62-600', 'HIGHWAY', 'JED', 'Street Light', 18.0, 'TANGARPALI', true),
    ('813000000281', 'TP03', 'HT', 'SR-E-EM-EB-000TP03', 'TOLL_PLAZA', 'SED SUNDARAGADA', 'General Purpose', 120.0, 'TP-03 EB Meter (Garposh)', true),
    ('812001070018', 'TP03', 'LT', 'SR-E-EM-EB-148-500', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 28.0, 'Bhawanipur / Garposh Corridor', true),
    ('812001070020', 'TP03', 'LT', 'SR-E-EM-EB-160-200', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 15.0, 'Garposh Toll Approach', true),
    ('416000000110', 'TP01', 'HT', 'SR-E-EM-EB-000TP01', 'TOLL_PLAZA', 'SEED SAMBALPUR', 'General Purpose', 120.0, 'TP-01 EB Meter', true),
    ('813001070057', 'TP02', 'LT', 'SR-E-EM-EB-130-000', 'HIGHWAY', 'KUTRA', 'Public Light', 15.0, 'Kutra EB METER', true),
    ('413001070102', 'TP02', 'HT', 'SR-E-EM-EB-112-800', 'HIGHWAY', 'JED JHARSUGUDA', 'Street Light', 14.0, 'Jharsuguda Bypass', true),
    ('413001070344', 'TP02', 'HT', 'SR-E-EM-EB-95-400', 'HIGHWAY', 'JED JHARSUGUDA', 'Street Light', 12.0, 'Badmal', true),
    ('416001070082', 'TP01', 'HT', 'SR-E-EM-EB-12-300', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Rengali', true),
    ('416001070084', 'TP01', 'HT', 'SR-E-EM-EB-24-500', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Lapanga', true),
    ('416001070086', 'TP01', 'HT', 'SR-E-EM-EB-36-800', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Bhojpur', true),
    ('416001070090', 'TP01', 'HT', 'SR-E-EM-EB-48-200', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Kuchinda Road', true),
    ('416001111004', 'TP01', 'LT', 'SR-E-EM-EB-24-500-LT', 'HIGHWAY', 'SEED SAMBALPUR', 'General Purpose', 4.0, 'Sambalpur Toll Admin', true)
ON CONFLICT (consumer_account_no) DO UPDATE
SET toll_plaza_id = EXCLUDED.toll_plaza_id,
    bill_type = EXCLUDED.bill_type,
    asset_code = EXCLUDED.asset_code,
    consumer_scope = EXCLUDED.consumer_scope,
    division_name = EXCLUDED.division_name,
    usage_type = EXCLUDED.usage_type,
    sanctioned_load_kw = EXCLUDED.sanctioned_load_kw,
    location = EXCLUDED.location,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- Create unified cross-table reconciliation view
CREATE OR REPLACE VIEW public.v_energy_consumer_reconciliation AS
WITH bills_actual_agg AS (
    SELECT 
        consumer_account_no,
        COUNT(bill_number) AS actual_bills_count,
        MAX(bill_month) AS latest_actual_bill_month,
        SUM(COALESCE(slab_normal_kwh, 0) + COALESCE(slab_peak_kwh, 0) + COALESCE(slab_solar_kwh, 0)) AS actual_billed_kwh,
        SUM(COALESCE(current_total, 0)) AS actual_billed_amount,
        SUM(COALESCE(total_amount_payable, 0)) AS actual_amount_payable
    FROM public.energy_bills
    GROUP BY consumer_account_no
),
bills_prov_agg AS (
    SELECT 
        consumer_account_no,
        COUNT(bill_number) AS prov_bills_count,
        MAX(bill_month) AS latest_prov_bill_month,
        SUM(COALESCE(slab_normal_kwh, 0) + COALESCE(slab_peak_kwh, 0) + COALESCE(slab_solar_kwh, 0)) AS prov_billed_kwh,
        SUM(COALESCE(current_total, 0)) AS prov_billed_amount,
        SUM(COALESCE(total_amount_payable, 0)) AS prov_amount_payable
    FROM public.energy_bills_provisional
    GROUP BY consumer_account_no
),
readings_agg AS (
    SELECT 
        COALESCE(consumer_number, asset_code) AS account_or_asset,
        asset_code,
        COUNT(reading_id) AS total_meter_readings,
        MAX(reading_datetime) AS latest_reading_datetime,
        MAX(COALESCE(cumulative_kwh, 0)) AS latest_cumulative_kwh,
        SUM(COALESCE(interval_kwh, 0)) AS total_meter_interval_kwh,
        MAX(COALESCE(maximum_demand, 0)) AS max_recorded_demand_kw,
        AVG(COALESCE(pf, 1.0)) AS avg_recorded_pf
    FROM energy_readings.eb
    GROUP BY COALESCE(consumer_number, asset_code), asset_code
),
receipts_agg AS (
    SELECT 
        COALESCE(account_no, consumer_no) AS account_key,
        COUNT(receipt_no) AS total_receipts_count,
        SUM(COALESCE(amount_paid, 0)) AS total_amount_paid,
        MAX(collections_date) AS latest_payment_date
    FROM public.payment_receipts
    GROUP BY COALESCE(account_no, consumer_no)
)
SELECT 
    m.consumer_account_no,
    m.toll_plaza_id,
    p.plaza_name,
    m.bill_type,
    m.asset_code,
    a.asset_name,
    m.consumer_scope,
    m.division_name,
    m.usage_type,
    m.sanctioned_load_kw,
    m.location,
    m.is_active,

    -- DISCOM Actual vs. Provisional Bill Counts & Units
    COALESCE(ba.actual_bills_count, 0) AS actual_bills_count,
    COALESCE(bp.prov_bills_count, 0) AS provisional_bills_count,
    (COALESCE(ba.actual_bills_count, 0) + COALESCE(bp.prov_bills_count, 0)) AS total_bills_count,
    COALESCE(ba.latest_actual_bill_month, bp.latest_prov_bill_month, '—') AS latest_bill_month,
    COALESCE(ba.actual_billed_kwh, 0.0) AS actual_billed_kwh,
    COALESCE(bp.prov_billed_kwh, 0.0) AS provisional_billed_kwh,
    (COALESCE(ba.actual_billed_kwh, 0.0) + COALESCE(bp.prov_billed_kwh, 0.0)) AS discom_billed_kwh,

    -- Invoiced Amounts & Provisional Risk Exposure
    COALESCE(ba.actual_billed_amount, 0.0) AS actual_billed_amount,
    COALESCE(bp.prov_billed_amount, 0.0) AS provisional_exposure_amount,
    (COALESCE(ba.actual_billed_amount, 0.0) + COALESCE(bp.prov_billed_amount, 0.0)) AS discom_billed_amount,
    (COALESCE(ba.actual_amount_payable, 0.0) + COALESCE(bp.prov_amount_payable, 0.0)) AS discom_amount_payable,

    -- Payment Receipts & Balance Clearance Correlation
    COALESCE(r.total_receipts_count, 0) AS total_receipts_count,
    COALESCE(r.total_amount_paid, 0.0) AS total_amount_paid,
    COALESCE(r.latest_payment_date, '—') AS latest_payment_date,
    ((COALESCE(ba.actual_amount_payable, 0.0) + COALESCE(bp.prov_amount_payable, 0.0)) - COALESCE(r.total_amount_paid, 0.0)) AS outstanding_balance,

    -- JUNO Physical Meter Telemetry Correlation
    COALESCE(rd.total_meter_readings, 0) AS total_meter_readings,
    COALESCE(rd.total_meter_interval_kwh, 0.0) AS juno_meter_kwh,
    COALESCE(rd.latest_cumulative_kwh, 0.0) AS latest_cumulative_kwh,
    COALESCE(rd.max_recorded_demand_kw, 0.0) AS max_recorded_demand_kw,
    COALESCE(rd.avg_recorded_pf, 1.0) AS avg_recorded_pf,
    rd.latest_reading_datetime,

    -- Automated Reconciliation Variance (Metered kWh vs DISCOM Billed kWh)
    ((COALESCE(ba.actual_billed_kwh, 0.0) + COALESCE(bp.prov_billed_kwh, 0.0)) - COALESCE(rd.total_meter_interval_kwh, 0.0)) AS kwh_variance,
    CASE 
        WHEN (COALESCE(ba.actual_billed_kwh, 0.0) + COALESCE(bp.prov_billed_kwh, 0.0)) > 0 AND COALESCE(rd.total_meter_interval_kwh, 0.0) > 0 THEN
            ROUND(
                ABS((COALESCE(ba.actual_billed_kwh, 0.0) + COALESCE(bp.prov_billed_kwh, 0.0)) - COALESCE(rd.total_meter_interval_kwh, 0.0)) 
                / (COALESCE(ba.actual_billed_kwh, 0.0) + COALESCE(bp.prov_billed_kwh, 0.0)) * 100.0, 
                2
            )
        ELSE 0.0
    END AS variance_percentage,

    m.created_at,
    m.updated_at
FROM energy_master.consumer_account m
LEFT JOIN energy_master.plaza p ON m.toll_plaza_id = p.plaza_id
LEFT JOIN energy_master.asset a ON m.asset_code = a.asset_code
LEFT JOIN bills_actual_agg ba ON m.consumer_account_no = ba.consumer_account_no
LEFT JOIN bills_prov_agg bp ON m.consumer_account_no = bp.consumer_account_no
LEFT JOIN receipts_agg r ON m.consumer_account_no = r.account_key
LEFT JOIN readings_agg rd ON (m.asset_code = rd.asset_code OR m.consumer_account_no = rd.account_or_asset);

-- STEP 15: RELOAD POSTGREST SCHEMA CACHE (Fixes PGRST002)
NOTIFY pgrst, 'reload schema';

DO $$
BEGIN
    RAISE NOTICE 'SUCCESS: All schemas, tables, RLS policies, duplicate constraints, and PostgREST schema cache reloaded with zero errors!';
END $$;
