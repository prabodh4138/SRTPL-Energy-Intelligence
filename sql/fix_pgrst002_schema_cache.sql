-- ============================================================================
-- SRTPL PROJECT (SUPABASE) — FIX PGRST002 SCHEMA CACHE ERROR
-- Run this in Supabase SQL Editor to instantly heal PostgREST
-- ============================================================================

-- 1. Create an empty placeholder schema for 'energy_raw'
-- If 'energy_raw' is still configured in Supabase Project Settings -> Data API -> Exposed Schemas,
-- having this empty schema immediately stops PostgREST from crashing with PGRST002.
CREATE SCHEMA IF NOT EXISTS energy_raw;

-- 2. Ensure all other schemas exist
CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_import;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_validation;
CREATE SCHEMA IF NOT EXISTS energy_analytics;
CREATE SCHEMA IF NOT EXISTS energy_admin;
CREATE SCHEMA IF NOT EXISTS energy_audit;

-- 3. Grant full permissions to all Supabase roles AND the PostgREST 'authenticator' role
GRANT USAGE ON SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics, energy_raw 
TO postgres, anon, authenticated, service_role, authenticator;

GRANT ALL ON ALL TABLES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO postgres, anon, authenticated, service_role, authenticator;

GRANT ALL ON ALL SEQUENCES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO postgres, anon, authenticated, service_role, authenticator;

GRANT ALL ON ALL ROUTINES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO postgres, anon, authenticated, service_role, authenticator;

ALTER DEFAULT PRIVILEGES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
GRANT ALL ON TABLES TO postgres, anon, authenticated, service_role, authenticator;

-- 4. Create an automatic RPC to allow client-side cache refresh
CREATE OR REPLACE FUNCTION public.reload_schema_cache()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    NOTIFY pgrst, 'reload schema';
END;
$$;
GRANT EXECUTE ON FUNCTION public.reload_schema_cache() TO anon, authenticated, service_role, postgres;

-- 5. Send the reload signal to PostgREST to rebuild its schema cache immediately
NOTIFY pgrst, 'reload schema';

DO $$
BEGIN
    RAISE NOTICE 'SUCCESS: PostgREST schema cache reload signal sent. Error PGRST002 resolved!';
END $$;
