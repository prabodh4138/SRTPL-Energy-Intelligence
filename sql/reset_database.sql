-- ============================================================================
-- SRTPL POWER CONSUMPTION ANALYTICS — RESET / WIPE ALL OPERATIONAL DATA
-- Run this in Supabase SQL Editor to wipe all operational data from the database
-- ============================================================================

-- Truncate all telemetry readings, exceptions, bills, and receipts
TRUNCATE TABLE 
    energy_readings.eb,
    energy_readings.dg,
    energy_readings.solar,
    energy_readings.transformer,
    energy_readings.ups,
    energy_validation.exception_record,
    public.energy_bills,
    public.payment_receipts
CASCADE;

-- Optional: To also wipe Plazas and Assets (completely empty fresh start):
-- TRUNCATE TABLE energy_master.asset, energy_master.plaza CASCADE;
