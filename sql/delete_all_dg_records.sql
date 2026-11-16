-- ============================================================================
-- SRTPL Energy Intelligence — Complete DG (Diesel Generator) Purge Script
-- Purpose: Deletes all operational meter readings, validation exceptions,
--          and import file/batch tracking records for DG across all plazas.
-- ============================================================================

BEGIN;

-- 1. DELETE ALL RAW DG METER READINGS (both schema and public view target)
TRUNCATE TABLE energy_readings.dg CASCADE;
-- Fallback if TRUNCATE CASCADE is restricted by permissions:
-- DELETE FROM energy_readings.dg;

-- 2. DELETE ALL DG VALIDATION EXCEPTIONS
DELETE FROM energy_validation.exception_record
WHERE rule_code LIKE 'VAL-DG-%'
   OR asset_code LIKE '%DGX%'
   OR asset_id IN (
       SELECT asset_id FROM energy_master.asset WHERE source_type = 'DG'
   );

-- 3. DELETE DG IMPORT HISTORY & SHA-256 HASHES (resets duplicate protection)
DELETE FROM energy_import.import_file
WHERE report_type = 'DG' 
   OR asset_code LIKE '%DGX%';

DELETE FROM energy_import.import_batch
WHERE report_type = 'DG';

-- 4. VERIFY PURGE COUNTS (all should return 0)
SELECT 'energy_readings.dg' AS table_name, count(*) AS remaining_count FROM energy_readings.dg
UNION ALL
SELECT 'energy_validation.exception_record (DG)', count(*) 
FROM energy_validation.exception_record 
WHERE rule_code LIKE 'VAL-DG-%' OR asset_code LIKE '%DGX%'
UNION ALL
SELECT 'energy_import.import_file (DG)', count(*) 
FROM energy_import.import_file 
WHERE report_type = 'DG' OR asset_code LIKE '%DGX%'
UNION ALL
SELECT 'energy_import.import_batch (DG)', count(*) 
FROM energy_import.import_batch 
WHERE report_type = 'DG';

COMMIT;

-- ============================================================================
-- OPTIONAL: If you also want to remove the 6 master DG asset definitions 
-- from energy_master.asset (NOT recommended if you plan to re-import):
-- ============================================================================
-- DELETE FROM energy_master.asset WHERE source_type = 'DG';
