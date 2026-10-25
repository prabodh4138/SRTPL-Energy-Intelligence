-- ============================================================================
-- SRTPL POWER CONSUMPTION ANALYTICS — RESET / WIPE ALL OPERATIONAL DATA
-- Run this in Supabase SQL Editor to wipe all operational data from the database
-- ============================================================================

-- 1. Truncate all telemetry readings, exceptions, import files, bills, and receipts
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

-- 2. Optional: To ALSO wipe Toll Plazas and Assets (100% empty master catalog):
-- TRUNCATE TABLE energy_master.asset, energy_master.plaza CASCADE;
