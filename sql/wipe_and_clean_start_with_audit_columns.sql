-- ============================================================================
-- SRTPL POWER INTELLIGENCE — TOTAL CLEAN WIPE & FRESH SCHEMA PREPARATION
-- Target Project: Srtpl_Project (Supabase)
--
-- RUN THIS ENTIRE SCRIPT IN SUPABASE SQL EDITOR
-- 
-- This script:
-- 1. Completely wipes all old readings, exceptions, and import hash records
-- 2. Ensures all technician accountability columns (created_by, created_on, remarks,
--    maximum_demand, asset_code, consumer_number, location, category) exist
-- 3. Drops and recreates all public convenience views to guarantee full column exposure
-- 4. Reloads PostgREST schema cache so fresh uploads inject without missing columns
-- ============================================================================

-- STEP 1: CLEAN WIPE OF OPERATIONAL READINGS & IMPORT DEDUPLICATION LOGS
TRUNCATE TABLE energy_readings.eb CASCADE;
TRUNCATE TABLE energy_readings.dg CASCADE;
TRUNCATE TABLE energy_readings.solar CASCADE;
TRUNCATE TABLE energy_readings.transformer CASCADE;
TRUNCATE TABLE energy_readings.ups CASCADE;
TRUNCATE TABLE energy_validation.exception_record CASCADE;
TRUNCATE TABLE energy_import.import_file CASCADE;
TRUNCATE TABLE energy_import.import_batch CASCADE;

-- STEP 2: ENSURE AUDIT & METER COLUMNS EXIST ON energy_readings.eb
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS maximum_demand NUMERIC(10, 2);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS consumer_number VARCHAR(64);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS location VARCHAR(256);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS category VARCHAR(64);

DO $$
BEGIN
    ALTER TABLE energy_readings.eb ALTER COLUMN asset_id DROP NOT NULL;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- STEP 3: ENSURE AUDIT & METER COLUMNS EXIST ON energy_readings.dg
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS location VARCHAR(256);

DO $$
BEGIN
    ALTER TABLE energy_readings.dg ALTER COLUMN asset_id DROP NOT NULL;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- STEP 4: ENSURE AUDIT & METER COLUMNS EXIST ON energy_readings.solar
ALTER TABLE energy_readings.solar ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_readings.solar ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_readings.solar ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;
ALTER TABLE energy_readings.solar ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_readings.solar ADD COLUMN IF NOT EXISTS location VARCHAR(256);

DO $$
BEGIN
    ALTER TABLE energy_readings.solar ALTER COLUMN asset_id DROP NOT NULL;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- STEP 5: ENSURE AUDIT & METER COLUMNS EXIST ON energy_readings.transformer
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS location VARCHAR(256);

DO $$
BEGIN
    ALTER TABLE energy_readings.transformer ALTER COLUMN asset_id DROP NOT NULL;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- STEP 6: ENSURE AUDIT & METER COLUMNS EXIST ON energy_readings.ups
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS location VARCHAR(256);

DO $$
BEGIN
    ALTER TABLE energy_readings.ups ALTER COLUMN asset_id DROP NOT NULL;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- STEP 7: ENSURE AUDIT COLUMNS EXIST ON energy_validation.exception_record
ALTER TABLE energy_validation.exception_record ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_validation.exception_record ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_validation.exception_record ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;

DO $$
BEGIN
    ALTER TABLE energy_validation.exception_record ALTER COLUMN asset_id DROP NOT NULL;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- STEP 8: DROP & RECREATE ALL CONVENIENCE VIEWS (Guarantees all new columns appear!)
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

-- STEP 9: ENSURE CORE ASSETS & PLAZAS EXIST
INSERT INTO energy_master.plaza (plaza_id, plaza_name, location) VALUES
    ('TP01', 'Toll Plaza 01 (Main / Barabati)', 'SRTPL Corridor Km 24+500'),
    ('TP02', 'Toll Plaza 02 (Kutra)', 'SRTPL Corridor Km 68+200'),
    ('TP03', 'Toll Plaza 03 (Garposh)', 'SRTPL Corridor Km 112+800')
ON CONFLICT (plaza_id) DO NOTHING;

INSERT INTO energy_master.asset (asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva) VALUES
    ('AST-EB-01', 'SR-E-EM-EB-000TP01', 'Main EB Incomer TP01', 'TP01', 'EB', 500.0),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', 'Main EB Incomer TP02 (Kutra)', 'TP02', 'EB', 500.0),
    ('AST-EB-03', 'SRTPL_Test_JUNO_EB', 'Main EB Incomer TP03', 'TP03', 'EB', 500.0)
ON CONFLICT (asset_id) DO NOTHING;

-- STEP 10: PERMISSIONS & POSTGREST SCHEMA CACHE RELOAD
GRANT USAGE ON SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics, energy_raw 
TO anon, authenticated, service_role, postgres, authenticator;

GRANT ALL ON ALL TABLES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

GRANT ALL ON ALL SEQUENCES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

ALTER DEFAULT PRIVILEGES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
GRANT ALL ON TABLES TO anon, authenticated, service_role, postgres, authenticator;

NOTIFY pgrst, 'reload config';
NOTIFY pgrst, 'reload schema';

-- STEP 11: VERIFICATION QUERY (CONFIRMS 0 ROWS REMAIN)
SELECT 'energy_readings.eb' AS table_name, count(*) AS row_count FROM energy_readings.eb
UNION ALL
SELECT 'energy_readings.dg', count(*) FROM energy_readings.dg
UNION ALL
SELECT 'energy_readings.solar', count(*) FROM energy_readings.solar
UNION ALL
SELECT 'energy_readings.transformer', count(*) FROM energy_readings.transformer
UNION ALL
SELECT 'energy_readings.ups', count(*) FROM energy_readings.ups
UNION ALL
SELECT 'energy_validation.exception_record', count(*) FROM energy_validation.exception_record
UNION ALL
SELECT 'energy_import.import_file', count(*) FROM energy_import.import_file;
