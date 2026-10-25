-- ============================================================================
-- SRTPL PROJECT (SUPABASE) — REVISE COLUMNS FOR TECHNICIAN AUDIT & METER TRACKING
-- Target Project: Srtpl_Project
--
-- Adds:
-- 1. `created_by`: Technician name who entered each reading (e.g. Srikant Sunani, Sunil Kullu)
-- 2. `created_on`: Date and time when the technician entered the reading in JUNO
-- 3. `remarks`: Technician notes and operational comments
-- 4. `asset_code`: Direct Meter / Equipment ID from the CSV (e.g. SR-E-EM-EB-130-000)
-- 5. `maximum_demand`: MD from the CSV
-- 6. `consumer_number`, `location`, `category`: Directly accessible on reading rows
-- 7. `asset_id`: Made optional (DROP NOT NULL) so foreign keys never block ingestion
-- ============================================================================

-- STEP 1: ADD AUDIT & METER COLUMNS TO energy_readings.eb
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

-- STEP 2: ADD AUDIT & METER COLUMNS TO energy_readings.dg
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

-- STEP 3: ADD AUDIT & METER COLUMNS TO energy_readings.solar
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

-- STEP 4: ADD AUDIT & METER COLUMNS TO energy_readings.transformer
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

-- STEP 5: ADD AUDIT & METER COLUMNS TO energy_readings.ups
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

-- STEP 6: ADD AUDIT COLUMNS TO energy_validation.exception_record
ALTER TABLE energy_validation.exception_record ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_validation.exception_record ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_validation.exception_record ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;

DO $$
BEGIN
    ALTER TABLE energy_validation.exception_record ALTER COLUMN asset_id DROP NOT NULL;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- STEP 7: RECREATE VIEWS IN PUBLIC SCHEMA TO EXPOSE AUDIT COLUMNS
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

-- STEP 8: ENSURE DEFAULT PLAZAS & ASSETS EXIST
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

-- STEP 9: GRANT ALL PERMISSIONS TO ROLES
GRANT ALL ON ALL TABLES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

-- STEP 10: RELOAD POSTGREST CONFIG & SCHEMA CACHE
NOTIFY pgrst, 'reload config';
NOTIFY pgrst, 'reload schema';
