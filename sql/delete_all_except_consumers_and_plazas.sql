-- ============================================================================
-- SRTPL POWER INTELLIGENCE — DELETE ALL DATA EXCEPT CONSUMERS & PLAZAS
-- Target: Supabase / PostgreSQL SQL Editor
--
-- PRESERVED TABLES:
--   1. energy_master.consumer_account (60 master consumer accounts)
--   2. energy_master.plaza (3 plazas: TP01, TP02, TP03)
--
-- WIPED TABLES (0 rows):
--   - energy_master.asset (assets)
--   - public.energy_bills (13 bills)
--   - public.payment_receipts (5 receipts)
--   - public.receipt_allocations (allocations)
--   - public.monthly_budgets (budgets)
--   - public.bill_review_queue & public.bill_rejected_bucket
--   - public.audit_events
--   - energy_readings.* (eb, dg, solar, transformer, ups)
--   - energy_import.* (import_row, import_file, import_batch)
--   - energy_validation.exception_record
-- ============================================================================

TRUNCATE TABLE 
    -- 1. Financial, Bills, Receipts & Reconciliation
    public.receipt_allocations,
    public.monthly_budgets,
    public.bill_review_queue,
    public.bill_rejected_bucket,
    public.audit_events,
    public.payment_receipts,
    public.energy_bills_provisional,
    public.energy_bills,

    -- 2. Equipment Telemetry & Daily Readings
    energy_readings.eb,
    energy_readings.dg,
    energy_readings.solar,
    energy_readings.transformer,
    energy_readings.ups,

    -- 3. File Ingestion & DQ Validation
    energy_validation.exception_record,
    energy_import.import_row,
    energy_import.import_file,
    energy_import.import_batch,

    -- 4. Master Assets (23 Assets wiped)
    energy_master.asset
RESTART IDENTITY CASCADE;

-- Safely clear optional tables if they exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'merged_bill_receipt_reconciliation') THEN
        EXECUTE 'TRUNCATE TABLE public.merged_bill_receipt_reconciliation RESTART IDENTITY CASCADE';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'energy_analytics' AND table_name = 'daily_summary') THEN
        EXECUTE 'TRUNCATE TABLE energy_analytics.daily_summary RESTART IDENTITY CASCADE';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'energy_analytics' AND table_name = 'kpi_master') THEN
        EXECUTE 'TRUNCATE TABLE energy_analytics.kpi_master RESTART IDENTITY CASCADE';
    END IF;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

-- Reload PostgREST API schema cache
NOTIFY pgrst, 'reload schema';

-- Verification Query: Confirm only consumer_account (60) and plaza (3) remain
SELECT 
    schemaname, 
    tablename, 
    n_live_tup AS remaining_rows
FROM pg_stat_user_tables
WHERE schemaname IN ('public', 'energy_readings', 'energy_master', 'energy_import', 'energy_validation')
ORDER BY remaining_rows DESC, tablename;
