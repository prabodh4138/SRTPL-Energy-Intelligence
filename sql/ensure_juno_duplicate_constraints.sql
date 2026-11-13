-- ============================================================================
-- SRTPL POWER INTELLIGENCE — JUNO DUPLICATE PREVENTION CONSTRAINTS
-- Target: Supabase / PostgreSQL SQL Editor
-- 
-- Enforces:
-- 1. LEVEL 1 DEDUPLICATION (File Level):
--    UNIQUE constraint on energy_import.import_file(sha256_hash)
-- 2. LEVEL 2 DEDUPLICATION (Telemetry Row Level):
--    UNIQUE constraints on (asset_id, reading_datetime) across:
--    - energy_readings.eb
--    - energy_readings.dg
--    - energy_readings.solar
--    - energy_readings.transformer
--    - energy_readings.ups
-- ============================================================================

DO $$
BEGIN
    -- 1. Ensure energy_import schema and tables exist
    CREATE SCHEMA IF NOT EXISTS energy_import;
    CREATE SCHEMA IF NOT EXISTS energy_readings;
    CREATE SCHEMA IF NOT EXISTS energy_validation;

    -- Level 1: Import File SHA-256 Uniqueness
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'energy_import' AND table_name = 'import_file') THEN
        -- Add unique constraint if not already present
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE n.nspname = 'energy_import' AND c.conname = 'uq_import_file_sha256'
        ) THEN
            BEGIN
                ALTER TABLE energy_import.import_file ADD CONSTRAINT uq_import_file_sha256 UNIQUE (sha256_hash);
            EXCEPTION WHEN OTHERS THEN
                NULL;
            END;
        END IF;
    END IF;

    -- Level 2: EB Telemetry (asset_id, reading_datetime) Uniqueness
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'energy_readings' AND table_name = 'eb') THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE n.nspname = 'energy_readings' AND c.conname = 'uq_eb_asset_datetime'
        ) THEN
            BEGIN
                ALTER TABLE energy_readings.eb ADD CONSTRAINT uq_eb_asset_datetime UNIQUE (asset_id, reading_datetime);
            EXCEPTION WHEN OTHERS THEN
                NULL;
            END;
        END IF;
    END IF;

    -- Level 2: DG Telemetry (asset_id, reading_datetime) Uniqueness
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'energy_readings' AND table_name = 'dg') THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE n.nspname = 'energy_readings' AND c.conname = 'uq_dg_asset_datetime'
        ) THEN
            BEGIN
                ALTER TABLE energy_readings.dg ADD CONSTRAINT uq_dg_asset_datetime UNIQUE (asset_id, reading_datetime);
            EXCEPTION WHEN OTHERS THEN
                NULL;
            END;
        END IF;
    END IF;

    -- Level 2: Solar Telemetry (asset_id, reading_datetime) Uniqueness
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'energy_readings' AND table_name = 'solar') THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE n.nspname = 'energy_readings' AND c.conname = 'uq_solar_asset_datetime'
        ) THEN
            BEGIN
                ALTER TABLE energy_readings.solar ADD CONSTRAINT uq_solar_asset_datetime UNIQUE (asset_id, reading_datetime);
            EXCEPTION WHEN OTHERS THEN
                NULL;
            END;
        END IF;
    END IF;

    -- Level 2: Transformer Telemetry (asset_id, reading_datetime) Uniqueness
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'energy_readings' AND table_name = 'transformer') THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE n.nspname = 'energy_readings' AND c.conname = 'uq_transformer_asset_datetime'
        ) THEN
            BEGIN
                ALTER TABLE energy_readings.transformer ADD CONSTRAINT uq_transformer_asset_datetime UNIQUE (asset_id, reading_datetime);
            EXCEPTION WHEN OTHERS THEN
                NULL;
            END;
        END IF;
    END IF;

    -- Level 2: UPS Telemetry (asset_id, reading_datetime) Uniqueness
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'energy_readings' AND table_name = 'ups') THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE n.nspname = 'energy_readings' AND c.conname = 'uq_ups_asset_datetime'
        ) THEN
            BEGIN
                ALTER TABLE energy_readings.ups ADD CONSTRAINT uq_ups_asset_datetime UNIQUE (asset_id, reading_datetime);
            EXCEPTION WHEN OTHERS THEN
                NULL;
            END;
        END IF;
    END IF;
END $$;

-- Reload Supabase PostgREST schema cache
NOTIFY pgrst, 'reload schema';

-- Verification Query: Check active constraints on Juno tables
SELECT 
    n.nspname AS schema_name,
    t.relname AS table_name,
    c.conname AS constraint_name,
    c.contype AS constraint_type
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
JOIN pg_class t ON t.oid = c.conrelid
WHERE n.nspname IN ('energy_import', 'energy_readings')
ORDER BY schema_name, table_name, constraint_name;
