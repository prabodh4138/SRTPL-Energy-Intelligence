-- ============================================================================
-- SRTPL Energy Intelligence — Complete Transformer Purge Script
-- Purpose: Deletes all operational meter readings, validation exceptions,
--          and import file/batch tracking records for Transformers across all plazas.
-- ============================================================================

BEGIN;

-- 1. DELETE ALL RAW TRANSFORMER METER READINGS
-- Clears primary/secondary voltages, currents, oil/winding temp, frequency, and kWh.
-- Since public.reading_transformer is a view on this table, it clears automatically.
TRUNCATE TABLE energy_readings.transformer CASCADE;
-- Fallback if TRUNCATE CASCADE is restricted by permissions:
-- DELETE FROM energy_readings.transformer;

-- 2. DELETE ALL TRANSFORMER VALIDATION EXCEPTIONS
DELETE FROM energy_validation.exception_record
WHERE rule_code LIKE 'VAL-XFR-%'
   OR rule_code LIKE 'VAL-TRA-%'
   OR asset_code LIKE '%TFR%'
   OR asset_id IN (
       SELECT asset_id FROM energy_master.asset WHERE source_type = 'TRANSFORMER'
   );

-- 3. DELETE TRANSFORMER IMPORT HISTORY & SHA-256 HASHES (resets duplicate protection)
DELETE FROM energy_import.import_file
WHERE report_type = 'TRANSFORMER' 
   OR asset_code LIKE '%TFR%';

DELETE FROM energy_import.import_batch
WHERE report_type = 'TRANSFORMER';

-- 4. VERIFY PURGE COUNTS (all should return 0)
SELECT 'energy_readings.transformer' AS table_name, count(*) AS remaining_count FROM energy_readings.transformer
UNION ALL
SELECT 'energy_validation.exception_record (Transformer)', count(*) 
FROM energy_validation.exception_record 
WHERE rule_code LIKE 'VAL-XFR-%' OR rule_code LIKE 'VAL-TRA-%' OR asset_code LIKE '%TFR%'
UNION ALL
SELECT 'energy_import.import_file (Transformer)', count(*) 
FROM energy_import.import_file 
WHERE report_type = 'TRANSFORMER' OR asset_code LIKE '%TFR%'
UNION ALL
SELECT 'energy_import.import_batch (Transformer)', count(*) 
FROM energy_import.import_batch 
WHERE report_type = 'TRANSFORMER';

COMMIT;

-- ============================================================================
-- OPTIONAL: If you also want to remove the 3 master Transformer asset definitions 
-- from energy_master.asset (NOT recommended if you plan to re-import):
-- ============================================================================
-- DELETE FROM energy_master.asset WHERE source_type = 'TRANSFORMER';
