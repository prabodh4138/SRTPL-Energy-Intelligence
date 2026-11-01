-- ============================================================================
-- SRTPL POWER CONSUMPTION ANALYTICS — RESET / WIPE ALL OPERATIONAL DATA
-- Run this in Supabase SQL Editor to wipe all data from every table and drop all views
-- ============================================================================

-- 1. Drop all views
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT table_schema, table_name 
        FROM information_schema.views 
        WHERE table_schema IN (
            'public', 'energy_dashboard', 'energy_readings', 'energy_master', 
            'energy_validation', 'energy_import', 'energy_analytics', 
            'energy_audit', 'energy_admin', 'energy_raw', 'energy_billing'
        )
    ) LOOP
        EXECUTE format('DROP VIEW IF EXISTS %I.%I CASCADE;', r.table_schema, r.table_name);
    END LOOP;
END $$;

-- 2. Truncate all tables in all schemas (leaving empty tables & schemas intact)
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname IN (
            'public', 'energy_readings', 'energy_master', 'energy_validation', 
            'energy_import', 'energy_analytics', 'energy_audit', 'energy_admin', 
            'energy_raw', 'energy_billing'
        )
        AND tablename NOT LIKE 'pg_%'
        AND tablename NOT LIKE 'sql_%'
    ) LOOP
        BEGIN
            EXECUTE format('TRUNCATE TABLE %I.%I RESTART IDENTITY CASCADE;', r.schemaname, r.tablename);
        EXCEPTION WHEN OTHERS THEN
            EXECUTE format('DELETE FROM %I.%I;', r.schemaname, r.tablename);
        END;
    END LOOP;
END $$;

-- 3. Reload schema cache
NOTIFY pgrst, 'reload schema';
