-- ============================================================================
-- SRTPL PROJECT (SUPABASE) — COMPLETE CLEAN WIPE & FRESH START SCRIPT
-- Target Project: Srtpl_Project
-- 
-- This script:
-- 1. Drops all custom SRTPL schemas with CASCADE (energy_master, energy_readings, etc.)
-- 2. Dynamically drops ALL custom tables, views, and functions in the 'public' schema
-- 3. Safely preserves Supabase system schemas (auth, storage, extensions, realtime)
-- 4. Re-grants all permissions so you have a 100% pristine database ready for fresh setup
-- ============================================================================

-- STEP 1: DROP ALL CUSTOM ENERGY SCHEMAS AND ALL THEIR OBJECTS (INCLUDING energy_raw)
DROP SCHEMA IF EXISTS energy_raw CASCADE;
DROP SCHEMA IF EXISTS energy_master CASCADE;
DROP SCHEMA IF EXISTS energy_import CASCADE;
DROP SCHEMA IF EXISTS energy_readings CASCADE;
DROP SCHEMA IF EXISTS energy_validation CASCADE;
DROP SCHEMA IF EXISTS energy_analytics CASCADE;
DROP SCHEMA IF EXISTS energy_admin CASCADE;
DROP SCHEMA IF EXISTS energy_audit CASCADE;

-- STEP 2: DROP ALL VIEWS IN THE PUBLIC SCHEMA
DO $$ 
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT viewname FROM pg_views WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP VIEW IF EXISTS public.' || quote_ident(r.viewname) || ' CASCADE';
    END LOOP;
END $$;

-- STEP 3: DROP ALL TABLES IN THE PUBLIC SCHEMA
DO $$ 
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;

-- STEP 4: DROP ALL USER-DEFINED FUNCTIONS IN THE PUBLIC SCHEMA
DO $$ 
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT routine_name, specific_schema
        FROM information_schema.routines 
        WHERE routine_schema = 'public' 
          AND routine_type = 'FUNCTION'
    ) LOOP
        EXECUTE 'DROP FUNCTION IF EXISTS public.' || quote_ident(r.routine_name) || ' CASCADE';
    END LOOP;
END $$;

-- STEP 5: RE-GRANT ESSENTIAL SUPABASE PERMISSIONS ON PUBLIC SCHEMA
GRANT USAGE, CREATE ON SCHEMA public TO postgres, anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres, anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO postgres, anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres, anon, authenticated, service_role;

-- STEP 6: CONFIRMATION
DO $$
BEGIN
    RAISE NOTICE 'CLEAN SLATE COMPLETE: All schemas and tables have been successfully deleted from Srtpl_Project.';
END $$;
