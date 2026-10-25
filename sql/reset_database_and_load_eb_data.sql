-- ============================================================================
-- SRTPL POWER INTELLIGENCE — COMPLETE DATABASE RESET & IMMEDIATE LIVE DATA LOAD
-- Target Project: Srtpl_Project (Supabase)
-- Source File: EBDailyLogReport_25thSep2026_2143_EB Log - Copy.csv (Meter SR-E-EM-EB-130-000)
--
-- RUN THIS ENTIRE SCRIPT IN SUPABASE SQL EDITOR TO:
-- 1. Wipe all old readings and deduplication hashes cleanly.
-- 2. Ensure all 8 audit columns exist on energy_readings.eb and views.
-- 3. Register Plaza TP02 (Kutra) and Asset AST-EB-02 (SR-E-EM-EB-130-000).
-- 4. Load all 23 actual validated records from the untouched JUNO CSV with:
--    - Technician names (created_by: Srikant Sunani, Pritam Mahapatra, etc.)
--    - Entry timestamps (created_on)
--    - Maximum Demand (maximum_demand)
--    - Meter ID (asset_code: SR-E-EM-EB-130-000)
--    - Consumer Number (consumer_number: 813001070057)
--    - Location (location: Kutra EB METER)
--    - Category (category: Public Light)
-- 5. Drop and recreate public.reading_eb view to expose all columns cleanly.
-- 6. Reload schema cache and execute the verification query.
-- ============================================================================

-- STEP 1: CLEAN WIPE OF OLD READINGS & AUDIT RECORDS
TRUNCATE TABLE energy_readings.eb CASCADE;
TRUNCATE TABLE energy_readings.dg CASCADE;
TRUNCATE TABLE energy_readings.solar CASCADE;
TRUNCATE TABLE energy_readings.transformer CASCADE;
TRUNCATE TABLE energy_readings.ups CASCADE;
TRUNCATE TABLE energy_validation.exception_record CASCADE;
TRUNCATE TABLE energy_import.import_file CASCADE;
TRUNCATE TABLE energy_import.import_batch CASCADE;

-- STEP 2: ENSURE TABLE SCHEMA & ALL 8 AUDIT COLUMNS EXIST
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

DO $$
BEGIN
    ALTER TABLE energy_readings.eb DROP CONSTRAINT IF EXISTS uq_eb_asset_datetime;
    ALTER TABLE energy_readings.eb ADD CONSTRAINT uq_eb_asset_datetime UNIQUE (asset_id, reading_datetime);
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- STEP 3: ENSURE PLAZAS AND ASSETS ARE REGISTERED
INSERT INTO energy_master.plaza (plaza_id, plaza_name, location) VALUES
    ('TP01', 'Toll Plaza 01 (Main / Barabati)', 'SRTPL Corridor Km 24+500'),
    ('TP02', 'Toll Plaza 02 (Kutra)', 'SRTPL Corridor Km 68+200'),
    ('TP03', 'Toll Plaza 03 (Garposh)', 'SRTPL Corridor Km 112+800')
ON CONFLICT (plaza_id) DO NOTHING;

INSERT INTO energy_master.asset (asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva) VALUES
    ('AST-EB-01', 'SR-E-EM-EB-000TP01', 'Main EB Incomer TP01', 'TP01', 'EB', 500.0),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', 'Main EB Incomer TP02 (Kutra)', 'TP02', 'EB', 500.0),
    ('AST-EB-03', 'SRTPL_Test_JUNO_EB', 'Main EB Incomer TP03', 'TP03', 'EB', 500.0)
ON CONFLICT (asset_id) DO UPDATE SET
    asset_code = EXCLUDED.asset_code,
    asset_name = EXCLUDED.asset_name,
    plaza_id = EXCLUDED.plaza_id;

-- STEP 4: REGISTER IMPORT BATCH & FILE AUDIT (SHA-256 = 5ced4b47983bb03b...)
INSERT INTO energy_import.import_batch (
    import_batch_id,
    uploaded_by,
    source_system,
    report_type,
    status,
    total_files,
    total_rows,
    valid_rows,
    invalid_rows
) VALUES (
    'b1000000-0000-0000-0000-000000000001',
    'admin@srtpl.com',
    'JUNO',
    'EB',
    'IMPORTED',
    1,
    23,
    23,
    0
) ON CONFLICT (import_batch_id) DO UPDATE SET
    valid_rows = 23,
    total_rows = 23;

INSERT INTO energy_import.import_file (
    import_file_id,
    import_batch_id,
    original_filename,
    sha256_hash,
    report_type,
    asset_code,
    row_count,
    valid_row_count,
    exception_row_count,
    uploaded_by
) VALUES (
    'f1000000-0000-0000-0000-000000000001',
    'b1000000-0000-0000-0000-000000000001',
    'EBDailyLogReport_25thSep2026_2143_EB Log - Copy.csv',
    '5ced4b47983bb03b8e721a3297a7a195be5d6d8ec5a9e3e7f2252a16d8e0ce9a',
    'EB',
    'SR-E-EM-EB-130-000',
    23,
    23,
    0,
    'admin@srtpl.com'
) ON CONFLICT (sha256_hash) DO UPDATE SET
    valid_row_count = 23;

-- STEP 5: INSERT ALL 23 VERIFIED ROWS INTO energy_readings.eb
INSERT INTO energy_readings.eb (
    asset_id,
    asset_code,
    reading_datetime,
    cumulative_kwh,
    cumulative_kvah,
    cumulative_kvarh,
    interval_kwh,
    interval_kvah,
    interval_kvarh,
    pf,
    maximum_demand,
    created_by,
    created_on,
    remarks,
    consumer_number,
    location,
    category,
    data_quality_status
) VALUES
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-04-06 08:00:00+00', 208861.0, 208861.0, NULL, NULL, NULL, NULL, NULL, 16.78, 'Srikant Sunani', '2026-04-16 23:15:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-04-13 08:00:00+00', 210058.0, 210058.0, NULL, 1197.0, 1197.0, NULL, NULL, 16.78, 'Srikant Sunani', '2026-04-16 23:49:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-04-20 08:00:00+00', 211206.0, 211206.0, NULL, 1148.0, 1148.0, NULL, NULL, 16.78, 'Srikant Sunani', '2026-05-14 20:19:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-04-26 08:00:00+00', 212205.0, 212205.0, NULL, 999.0, 999.0, NULL, NULL, 16.78, 'Pritam Mahapatra', '2026-05-14 23:11:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-05-04 08:00:00+00', 213463.0, 213463.0, NULL, 1258.0, 1258.0, NULL, NULL, 16.66, 'Pritam Mahapatra', '2026-05-14 23:13:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-05-11 08:00:00+00', 214631.0, 214631.0, NULL, 1168.0, 1168.0, NULL, NULL, 16.72, 'Pritam Mahapatra', '2026-05-14 23:14:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-05-18 08:00:00+00', 216024.0, 216024.0, NULL, 1393.0, 1393.0, NULL, NULL, 16.72, 'Krishna Chandra  Patra', '2026-05-26 21:47:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-05-25 08:00:00+00', 216967.0, 216967.0, NULL, 943.0, 943.0, NULL, NULL, 16.72, 'Pritam Mahapatra', '2026-05-27 09:51:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-05-31 19:08:00+00', 217762.0, 217762.0, NULL, 795.0, 795.0, NULL, NULL, 16.72, 'Krishna Chandra  Patra', '2026-05-31 19:09:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-06-07 08:00:00+00', 219033.0, 219033.0, NULL, 1271.0, 1271.0, NULL, NULL, 16.65, 'Krishna Chandra  Patra', '2026-06-08 22:21:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-06-14 08:00:00+00', 220019.0, 220019.0, NULL, 986.0, 986.0, NULL, NULL, 16.65, 'Krishna Chandra  Patra', '2026-06-15 12:55:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-06-28 09:46:00+00', 222396.0, 222396.0, NULL, 2377.0, 2377.0, NULL, 1.0, 16.68, 'Krishna Chandra  Patra', '2026-07-10 09:46:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-07-06 08:01:00+00', 222925.0, 222925.0, NULL, 529.0, 529.0, NULL, 1.0, 16.71, 'Krishna Chandra  Patra', '2026-07-14 22:43:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-07-12 08:00:00+00', 223454.0, 223454.0, NULL, 529.0, 529.0, NULL, 1.0, 8.61, 'Krishna Chandra  Patra', '2026-07-14 22:44:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-07-20 08:00:00+00', 224289.0, 224289.0, NULL, 835.0, 835.0, NULL, 1.0, 8.61, 'Sanurjya Roudia', '2026-07-29 19:02:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-07-29 08:00:00+00', 225124.0, 225124.0, NULL, 835.0, 835.0, NULL, 1.0, 11.76, 'Sanurjya Roudia', '2026-07-29 19:03:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-08-03 08:00:00+00', 225700.0, 225700.0, NULL, 576.0, 576.0, NULL, 1.0, 12.96, 'Sanurjya Roudia', '2026-08-12 12:57:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-08-10 08:00:00+00', 226276.0, 226276.0, NULL, 576.0, 576.0, NULL, 0.999, 13.04, 'Sanurjya Roudia', '2026-08-12 13:00:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-08-16 08:00:00+00', 227221.0, 227221.0, NULL, 945.0, 945.0, NULL, 1.0, 13.02, 'Pritam Mahapatra', '2026-09-10 19:33:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-08-23 08:00:00+00', 228167.0, 228167.0, NULL, 946.0, 946.0, NULL, 1.0, 13.2, 'Pritam Mahapatra', '2026-09-10 19:34:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-08-30 08:00:00+00', 229113.0, 229113.0, NULL, 946.0, 946.0, NULL, 1.0, 13.25, 'Pritam Mahapatra', '2026-09-10 19:35:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-09-07 08:00:00+00', 230062.0, 230062.0, NULL, 949.0, 949.0, NULL, 1.0, 13.64, 'Pritam Mahapatra', '2026-09-10 19:36:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID'),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', '2026-09-14 08:00:00+00', 231891.0, 231891.0, NULL, 1829.0, 1829.0, NULL, 1.0, 8.72, 'Sanurjya Roudia', '2026-09-21 16:01:00+00', NULL, '813001070057', 'Kutra EB METER', 'Public Light', 'VALID')
ON CONFLICT (asset_id, reading_datetime) DO UPDATE SET
    asset_code = EXCLUDED.asset_code,
    cumulative_kwh = EXCLUDED.cumulative_kwh,
    cumulative_kvah = EXCLUDED.cumulative_kvah,
    cumulative_kvarh = EXCLUDED.cumulative_kvarh,
    interval_kwh = EXCLUDED.interval_kwh,
    interval_kvah = EXCLUDED.interval_kvah,
    interval_kvarh = EXCLUDED.interval_kvarh,
    pf = EXCLUDED.pf,
    maximum_demand = EXCLUDED.maximum_demand,
    created_by = EXCLUDED.created_by,
    created_on = EXCLUDED.created_on,
    remarks = EXCLUDED.remarks,
    consumer_number = EXCLUDED.consumer_number,
    location = EXCLUDED.location,
    category = EXCLUDED.category,
    data_quality_status = EXCLUDED.data_quality_status;

-- STEP 6: RECREATE ALL CONVENIENCE VIEWS (Fixes PostgreSQL Column Freezing)
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

-- STEP 7: PERMISSIONS & POSTGREST SCHEMA CACHE RELOAD
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

-- STEP 8: FINAL VERIFICATION QUERY (OUTPUTS THE EXACT 5 ROWS YOU REQUESTED)
SELECT 
    reading_datetime,
    cumulative_kwh,
    cumulative_kvah,
    interval_kwh,
    maximum_demand,
    pf,
    created_by,
    created_on,
    asset_code,
    consumer_number,
    location,
    category
FROM public.reading_eb
ORDER BY reading_datetime ASC
LIMIT 5;
