-- ============================================================================
-- SRTPL POWER PROJECT — PURGE / DELETE ALL SOLAR DATA IN SUPABASE
-- ============================================================================
-- Run this in the Supabase SQL Editor to cleanly wipe all solar readings,
-- import batches, file records, and validation exceptions.
-- Note: Does NOT delete the physical assets from energy_master.asset,
-- keeping plant inventory (40.46 kWp each) intact for fresh ingestion.
-- ============================================================================

BEGIN;

-- 1. Delete all raw and normalized solar readings
DELETE FROM energy_readings.solar;

-- 2. If public.reading_solar is a table rather than a view, purge it as well
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE schemaname = 'public' AND tablename = 'reading_solar'
    ) THEN
        DELETE FROM public.reading_solar;
    END IF;
END $$;

-- 3. Delete Solar validation exception records
DELETE FROM energy_validation.exception_record
WHERE rule_code LIKE 'VAL-SOL%'
   OR asset_code IN ('SR-E-AP-SPX-000001', 'SR-E-AP-SPX-000002', 'SR-E-AP-SPX-000003');

-- 4. Delete Solar import rows, files, and batches from the ingestion log
DELETE FROM energy_import.import_row
WHERE import_file_id IN (
    SELECT import_file_id FROM energy_import.import_file WHERE report_type = 'SOLAR'
);

DELETE FROM energy_import.import_file
WHERE report_type = 'SOLAR';

DELETE FROM energy_import.import_batch
WHERE report_type = 'SOLAR';

-- 5. Verification queries to confirm 0 records remain
SELECT 'energy_readings.solar' AS table_name, count(*) AS remaining_count FROM energy_readings.solar
UNION ALL
SELECT 'energy_validation.exception_record (SOLAR)' AS table_name, count(*) AS remaining_count 
FROM energy_validation.exception_record 
WHERE rule_code LIKE 'VAL-SOL%' OR asset_code IN ('SR-E-AP-SPX-000001', 'SR-E-AP-SPX-000002', 'SR-E-AP-SPX-000003')
UNION ALL
SELECT 'energy_import.import_file (SOLAR)' AS table_name, count(*) AS remaining_count 
FROM energy_import.import_file WHERE report_type = 'SOLAR';

COMMIT;
