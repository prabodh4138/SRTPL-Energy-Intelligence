-- ============================================================================
-- SRTPL POWER INTELLIGENCE — BULLETPROOF DELETE ALL TEST & OPERATIONAL DATA
-- Target: Supabase / PostgreSQL SQL Editor
--
-- PRESERVED 100% INTACT:
--   1. energy_master.consumer_account (All 60 master consumers PRESERVED)
--   2. energy_master.plaza (All 3 plazas: TP01, TP02, TP03 PRESERVED)
--
-- WIPED CLEAN (0 rows):
--   - energy_bills & energy_bills_provisional
--   - payment_receipts & receipt_allocations
--   - monthly_budgets, bill_review_queue, bill_rejected_bucket, audit_events
--   - equipment telemetry (eb, dg, solar, transformer, ups)
--   - import tables (import_row, import_file, import_batch, exception_record)
--   - energy_master.asset
-- ============================================================================

DO $$
DECLARE
    tbl text;
    tables_to_truncate text[] := ARRAY[
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
        'energy_analytics.kpi_master',
        'energy_master.asset'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables_to_truncate
    LOOP
        BEGIN
            EXECUTE 'TRUNCATE TABLE ' || tbl || ' RESTART IDENTITY CASCADE';
        EXCEPTION 
            WHEN undefined_table THEN
                NULL; -- Table does not exist in schema, safely skip
            WHEN OTHERS THEN
                NULL;
        END;
    END LOOP;
END $$;

-- Reload Supabase PostgREST API cache so UI sees changes immediately
NOTIFY pgrst, 'reload schema';

-- Verification: Check live counts of key tables
SELECT 'energy_master.consumer_account' AS table_name, count(*)::text AS current_rows FROM energy_master.consumer_account
UNION ALL
SELECT 'energy_master.plaza', count(*)::text FROM energy_master.plaza
UNION ALL
SELECT 'energy_master.asset', count(*)::text FROM energy_master.asset
UNION ALL
SELECT 'public.energy_bills', count(*)::text FROM public.energy_bills
UNION ALL
SELECT 'public.payment_receipts', count(*)::text FROM public.payment_receipts
UNION ALL
SELECT 'public.receipt_allocations', count(*)::text FROM public.receipt_allocations
UNION ALL
SELECT 'public.monthly_budgets', count(*)::text FROM public.monthly_budgets;
