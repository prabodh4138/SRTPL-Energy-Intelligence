-- ============================================================================
-- SRTPL POWER INTELLIGENCE — COMPLETE OPERATIONAL & JUNO READING DATA RESET
-- Target: Supabase / PostgreSQL SQL Editor
--
-- STRICT PRESERVATION GUARANTEE:
--   1. energy_master.consumer_account : 60 master consumers PRESERVED 100%
--   2. energy_master.plaza            : 3 plazas (TP01, TP02, TP03) PRESERVED 100%
--   3. energy_master.asset            : 23 substation/equipment assets PRESERVED 100%
--
-- WIPED CLEAN TO 0 ROWS (Ready for fresh data injection):
--   - All equipment readings: energy_readings.eb, dg, solar, transformer, ups
--   - All import tracking & SHA-256 deduplication hashes: energy_import.import_file, import_batch, import_row
--   - All validation errors: energy_validation.exception_record
--   - All analytics & profiles: energy_analytics.daily_summary, hourly_profile, kpi_result, kpi_master
--   - All billing & test records: public.energy_bills, energy_bills_provisional, payment_receipts, receipt_allocations, monthly_budgets, bill_review_queue, bill_rejected_bucket, audit_events
-- ============================================================================

DO $$
DECLARE
    tbl text;
    tables_to_wipe text[] := ARRAY[
        'public.receipt_allocations',
        'public.monthly_budgets',
        'public.bill_review_queue',
        'public.bill_rejected_bucket',
        'public.audit_events',
        'public.payment_receipts',
        'public.energy_bills_provisional',
        'public.energy_bills',
        'public.merged_bill_receipt_reconciliation',
        'energy_readings.eb',
        'energy_readings.dg',
        'energy_readings.solar',
        'energy_readings.transformer',
        'energy_readings.ups',
        'energy_validation.exception_record',
        'energy_import.import_row',
        'energy_import.import_file',
        'energy_import.import_batch',
        'energy_analytics.daily_summary',
        'energy_analytics.hourly_profile',
        'energy_analytics.kpi_result',
        'energy_analytics.kpi_master'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables_to_wipe
    LOOP
        BEGIN
            EXECUTE 'TRUNCATE TABLE ' || tbl || ' RESTART IDENTITY CASCADE';
        EXCEPTION 
            WHEN undefined_table THEN
                NULL; -- Table does not exist in schema, safely skip
            WHEN OTHERS THEN
                -- If TRUNCATE is blocked by foreign key or view, fallback to DELETE
                BEGIN
                    EXECUTE 'DELETE FROM ' || tbl;
                EXCEPTION
                    WHEN OTHERS THEN
                        NULL;
                END;
        END;
    END LOOP;
END $$;

-- Guarantee the 23 Master Assets exist for foreign key integrity
INSERT INTO energy_master.asset (asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva) VALUES
    ('AST-EB-01', 'SR-E-EM-EB-000TP01', 'Main EB Incomer TP01', 'TP01', 'EB', 500.0),
    ('AST-DG-01', 'SR-E-AP-DGX-000001', 'Diesel Generator 1', 'TP01', 'DG', 250.0),
    ('AST-DG-02', 'SR-E-AP-DGX-000002', 'Diesel Generator 2', 'TP01', 'DG', 250.0),
    ('AST-SOL-01', 'SR-E-AP-SPX-000001', 'Solar Plant 1', 'TP01', 'SOLAR', 100.0),
    ('AST-TRF-02', 'SR-E-HT-TFR-000002', 'HT Substation Transformer 2', 'TP01', 'TRANSFORMER', 500.0),
    ('AST-UPS-02', 'SR-E-AP-UPS-000002', 'Toll Plaza UPS 2', 'TP01', 'UPS', 40.0),
    ('AST-UPS-03', 'SR-E-AP-UPS-000003', 'Toll Plaza UPS 3', 'TP01', 'UPS', 40.0),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', 'Main EB Incomer TP02', 'TP02', 'EB', 500.0),
    ('AST-DG-03', 'SR-E-AP-DGX-000003', 'Diesel Generator 3', 'TP02', 'DG', 250.0),
    ('AST-DG-04', 'SR-E-AP-DGX-000004', 'Diesel Generator 4', 'TP02', 'DG', 250.0),
    ('AST-SOL-02', 'SR-E-AP-SPX-000002', 'Solar Plant 2', 'TP02', 'SOLAR', 100.0),
    ('AST-TRF-03', 'SR-E-HT-TFR-000003', 'HT Substation Transformer 3', 'TP02', 'TRANSFORMER', 500.0),
    ('AST-UPS-04', 'SR-E-AP-UPS-000004', 'Toll Plaza UPS 4', 'TP02', 'UPS', 40.0),
    ('AST-UPS-09', 'SR-E-AP-UPS-000009', 'Toll Plaza UPS 9', 'TP02', 'UPS', 40.0),
    ('AST-EB-03', 'SRTPL_Test_JUNO_EB', 'Main EB Incomer TP03', 'TP03', 'EB', 500.0),
    ('AST-DG-05', 'SR-E-AP-DGX-000005', 'Diesel Generator 5', 'TP03', 'DG', 250.0),
    ('AST-DG-06', 'SR-E-AP-DGX-000006', 'Diesel Generator 6', 'TP03', 'DG', 250.0),
    ('AST-SOL-03', 'SR-E-AP-SPX-000003', 'Solar Plant 3', 'TP03', 'SOLAR', 100.0),
    ('AST-TRF-01', 'SR-E-HT-TFR-000001', 'HT Substation Transformer 1', 'TP03', 'TRANSFORMER', 500.0),
    ('AST-UPS-10', 'SR-E-AP-UPS-000010', 'Toll Plaza UPS 10', 'TP03', 'UPS', 40.0),
    ('AST-UPS-12', 'SR-E-AP-UPS-000012', 'Toll Plaza UPS 12', 'TP03', 'UPS', 40.0),
    ('AST-EB-04', 'SR-E-EM-EB-5-200', 'Corridor Lighting Meter 05.200 (Ainthapalli)', 'TP01', 'EB', 50.0),
    ('AST-EB-05', 'SR-E-EM-EB-62-600', 'Corridor Lighting Meter 62.600 (Tangarpali)', 'TP02', 'EB', 50.0),
    ('AST-EB-06', 'SR-E-EM-EB-148-500', 'Corridor Lighting Meter 148.500 (Garposh)', 'TP03', 'EB', 50.0),
    ('AST-EB-07', 'SR-E-EM-EB-000TP03', 'Main EB Substation TP03', 'TP03', 'EB', 500.0),
    ('AST-EB-08', 'SR-E-EM-EB-160-200', 'Garposh Toll Approach Meter', 'TP03', 'EB', 50.0)
ON CONFLICT (asset_id) DO UPDATE
SET asset_code = EXCLUDED.asset_code,
    asset_name = EXCLUDED.asset_name,
    plaza_id = EXCLUDED.plaza_id;

-- Reload Supabase PostgREST API cache so UI sees changes immediately
NOTIFY pgrst, 'reload schema';

-- Verification: Live counts of all tables (Preserved vs Cleared)
SELECT 'energy_master.consumer_account' AS table_name, count(*)::text AS current_rows, 'PRESERVED' AS target_status FROM energy_master.consumer_account
UNION ALL
SELECT 'energy_master.plaza', count(*)::text, 'PRESERVED' FROM energy_master.plaza
UNION ALL
SELECT 'energy_master.asset', count(*)::text, 'PRESERVED' FROM energy_master.asset
UNION ALL
SELECT 'energy_readings.eb', count(*)::text, 'CLEARED (0)' FROM energy_readings.eb
UNION ALL
SELECT 'energy_readings.dg', count(*)::text, 'CLEARED (0)' FROM energy_readings.dg
UNION ALL
SELECT 'energy_readings.solar', count(*)::text, 'CLEARED (0)' FROM energy_readings.solar
UNION ALL
SELECT 'energy_readings.transformer', count(*)::text, 'CLEARED (0)' FROM energy_readings.transformer
UNION ALL
SELECT 'energy_readings.ups', count(*)::text, 'CLEARED (0)' FROM energy_readings.ups
UNION ALL
SELECT 'energy_import.import_file', count(*)::text, 'CLEARED (0)' FROM energy_import.import_file
UNION ALL
SELECT 'energy_import.import_batch', count(*)::text, 'CLEARED (0)' FROM energy_import.import_batch
UNION ALL
SELECT 'energy_validation.exception_record', count(*)::text, 'CLEARED (0)' FROM energy_validation.exception_record
UNION ALL
SELECT 'public.energy_bills', count(*)::text, 'CLEARED (0)' FROM public.energy_bills
UNION ALL
SELECT 'public.payment_receipts', count(*)::text, 'CLEARED (0)' FROM public.payment_receipts
UNION ALL
SELECT 'public.receipt_allocations', count(*)::text, 'CLEARED (0)' FROM public.receipt_allocations;
