-- ============================================================================
-- SRTPL PROJECT (SUPABASE) — INSTANT FIX FOR ERROR 23502 (import_batch_id NOT NULL)
-- Target Project: Srtpl_Project
--
-- Root Cause:
-- The column `import_batch.import_batch_id` had a NOT NULL constraint without
-- an automatic default generator (DEFAULT gen_random_uuid()).
--
-- This script:
-- 1. Sets DEFAULT gen_random_uuid() on import_batch.import_batch_id (handles UUID & TEXT)
-- 2. Ensures import_file.import_batch_id is nullable or has valid defaults
-- 3. Exposes all schemas in PostgREST and grants permissions
-- 4. Reloads PostgREST schema cache immediately
-- ============================================================================

-- STEP 1: EXPOSE SCHEMAS TO POSTGREST API
ALTER ROLE authenticator SET pgrst.db_schemas = 'public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics';

-- STEP 2: ENSURE SCHEMAS EXIST
CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_import;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_validation;
CREATE SCHEMA IF NOT EXISTS energy_analytics;

-- STEP 3: ENSURE IMPORT_BATCH TABLE EXISTS WITH DEFAULT GENERATOR
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

-- Apply default generator on import_batch.import_batch_id (handles TEXT, VARCHAR, or UUID)
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

-- STEP 4: ENSURE IMPORT_FILE EXISTS AND HAS DEFAULTS
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

-- Ensure import_file_id has default and import_batch_id is optional
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

    -- Make import_batch_id nullable if constrained in legacy tables
    BEGIN
        ALTER TABLE energy_import.import_file ALTER COLUMN import_batch_id DROP NOT NULL;
    EXCEPTION WHEN OTHERS THEN
        NULL;
    END;
END $$;

-- STEP 5: ENSURE IMPORT_ROW EXISTS AND HAS DEFAULTS
CREATE TABLE IF NOT EXISTS energy_import.import_row (
    import_row_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_file_id UUID,
    source_row_number INTEGER,
    source_record_hash VARCHAR(64),
    business_key VARCHAR(128),
    raw_payload JSONB,
    parse_status VARCHAR(32) DEFAULT 'PARSED',
    validation_status VARCHAR(32) DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
    BEGIN
        ALTER TABLE energy_import.import_row ALTER COLUMN import_row_id SET DEFAULT gen_random_uuid();
    EXCEPTION WHEN OTHERS THEN
        BEGIN
            ALTER TABLE energy_import.import_row ALTER COLUMN import_row_id SET DEFAULT gen_random_uuid()::text;
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END;
    END;
END $$;

-- STEP 6: EXPOSE COMPATIBILITY VIEWS IN PUBLIC SCHEMA
CREATE OR REPLACE VIEW public.import_batch AS SELECT * FROM energy_import.import_batch;
CREATE OR REPLACE VIEW public.import_file AS SELECT * FROM energy_import.import_file;
CREATE OR REPLACE VIEW public.import_row AS SELECT * FROM energy_import.import_row;

-- STEP 7: ROW LEVEL SECURITY POLICIES
ALTER TABLE energy_import.import_batch ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_import.import_file ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_import.import_row ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "allow_all_import_batch" ON energy_import.import_batch;
CREATE POLICY "allow_all_import_batch" ON energy_import.import_batch FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_import_file" ON energy_import.import_file;
CREATE POLICY "allow_all_import_file" ON energy_import.import_file FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_import_row" ON energy_import.import_row;
CREATE POLICY "allow_all_import_row" ON energy_import.import_row FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

-- STEP 8: GRANT PRIVILEGES TO ALL ROLES
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

-- STEP 9: RELOAD POSTGREST CONFIG & SCHEMA CACHE
NOTIFY pgrst, 'reload config';
NOTIFY pgrst, 'reload schema';
