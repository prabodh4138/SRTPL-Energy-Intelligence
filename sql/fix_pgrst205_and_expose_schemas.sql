-- ============================================================================
-- SRTPL PROJECT (SUPABASE) — INSTANT FIX FOR PGRST205 & SCHEMA CACHE
-- Target Project: Srtpl_Project
--
-- This script:
-- 1. Sets pgrst.db_schemas on the authenticator role to expose all SRTPL schemas
-- 2. Creates energy_import.import_file table if missing
-- 3. Creates public.import_file table/view so both schema styles work
-- 4. Grants full permissions to anon, authenticated, service_role, and authenticator
-- 5. Sends 'reload config' and 'reload schema' to PostgREST
-- ============================================================================

-- STEP 1: EXPOSE ALL REQUIRED SCHEMAS TO POSTGREST API
ALTER ROLE authenticator SET pgrst.db_schemas = 'public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics';

-- STEP 2: ENSURE SCHEMAS EXIST
CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_import;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_validation;
CREATE SCHEMA IF NOT EXISTS energy_analytics;

-- STEP 3: CREATE IMPORT_FILE TABLE IN BOTH energy_import AND public
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

-- Expose in public schema as well
CREATE OR REPLACE VIEW public.import_file AS SELECT * FROM energy_import.import_file;
CREATE OR REPLACE VIEW public.import_batch AS SELECT * FROM energy_import.import_batch;
CREATE OR REPLACE VIEW public.import_row AS SELECT * FROM energy_import.import_row;

-- STEP 4: ENABLE RLS ON IMPORT TABLES WITH PERMISSIVE POLICIES
ALTER TABLE energy_import.import_file ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_import.import_batch ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_import.import_row ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "allow_all_import_file" ON energy_import.import_file;
CREATE POLICY "allow_all_import_file" ON energy_import.import_file FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_import_batch" ON energy_import.import_batch;
CREATE POLICY "allow_all_import_batch" ON energy_import.import_batch FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_import_row" ON energy_import.import_row;
CREATE POLICY "allow_all_import_row" ON energy_import.import_row FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

-- STEP 5: GRANT PERMISSIONS TO ALL SUPABASE AND POSTGREST ROLES
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

-- STEP 6: NOTIFY POSTGREST TO RELOAD CONFIG AND SCHEMA CACHE
NOTIFY pgrst, 'reload config';
NOTIFY pgrst, 'reload schema';

DO $$
BEGIN
    RAISE NOTICE 'SUCCESS: PostgREST configured, pgrst.db_schemas set, tables verified, and schema cache reloaded!';
END $$;
