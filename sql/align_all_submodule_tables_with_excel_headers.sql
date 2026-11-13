-- ============================================================================
-- SRTPL ENERGY INTELLIGENCE — ALIGN ALL DATABASE SCHEMAS WITH EXCEL HEADERS
-- Target: Supabase (PostgreSQL) & Local Relational Storage
--
-- This script ensures all columns present in raw JUNO Excel/CSV log exports
-- across ALL submodules (Transformer, DG, UPS, EB, Solar) exist in the database:
--
-- 1. TRANSFORMER:
--    - KWH, KVAH (Cumulative energy)
--    - Interval KWH, Interval KVAH (Calculated interval deltas)
--    - FREQ (Frequency Hz)
--    - Primary & Secondary Voltages (RY, YB, BR) & Currents (R, Y, B)
--    - WTI (Winding Temperature), OTI (Oil Temperature), PF (Power Factor)
--
-- 2. DG (Diesel Generator):
--    - STATUS ON/OFF/RUN (Generator operational status)
--    - KVA, KW (Apparent & Active Power)
--    - VOLTAGE (RY, YB, BR), Load Current (R, Y, B), PF
--    - DIESEL LEVEL, Diesel Top-up, LOAD ٪, RPM
--    - KWH, Running Hours, Interval KWH, Interval Running Hours
--
-- 3. UPS (Battery System):
--    - MAIN(INPUT) VOLTAGE (R, Y, B) & CURRENT (R, Y, B)
--    - Main Input Rectifier Voltage
--    - BY PASS (Voltage, Current, Frequency)
--    - OUTPUT (Voltage, Current, Frequency)
--    - Battery (Temperature, Vdc, Current Ib)
--
-- 4. EB (Grid Supply):
--    - Cumulative & Interval kWh, kVAH, kVARh, MD, PF, Consumer No, Location, Category
--
-- 5. SOLAR (Rooftop Array):
--    - Cumulative & Interval kWh, Location, Remarks
-- ============================================================================

-- ============================================================================
-- PART 1: ALTER EXISTING TABLES TO ADD MISSING EXCEL COLUMNS
-- ============================================================================

-- 1.1 TRANSFORMER COLUMNS
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS cumulative_kwh NUMERIC(14, 4);
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS cumulative_kvah NUMERIC(14, 4);
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS interval_kwh NUMERIC(14, 4);
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS interval_kvah NUMERIC(14, 4);
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS frequency NUMERIC(6, 2);
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_readings.transformer ADD COLUMN IF NOT EXISTS location VARCHAR(256);

-- 1.2 DG (DIESEL GENERATOR) COLUMNS
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS status VARCHAR(32);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS kva NUMERIC(10, 2);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS kw NUMERIC(10, 2);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS voltage_ry NUMERIC(10, 2);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS voltage_yb NUMERIC(10, 2);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS voltage_br NUMERIC(10, 2);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS current_r NUMERIC(10, 2);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS current_y NUMERIC(10, 2);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS current_b NUMERIC(10, 2);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS diesel_level NUMERIC(10, 2);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS diesel_topup NUMERIC(10, 2);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS load_percentage NUMERIC(6, 2);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS rpm NUMERIC(8, 2);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_readings.dg ADD COLUMN IF NOT EXISTS location VARCHAR(256);

-- 1.3 UPS (UNINTERRUPTIBLE POWER SUPPLY) COLUMNS
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS input_voltage_r NUMERIC(10, 2);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS input_voltage_y NUMERIC(10, 2);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS input_voltage_b NUMERIC(10, 2);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS input_current_r NUMERIC(10, 2);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS input_current_y NUMERIC(10, 2);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS input_current_b NUMERIC(10, 2);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS rectifier_voltage NUMERIC(10, 2);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS bypass_voltage NUMERIC(10, 2);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS bypass_current NUMERIC(10, 2);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS bypass_frequency NUMERIC(6, 2);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS battery_current NUMERIC(10, 2);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_readings.ups ADD COLUMN IF NOT EXISTS location VARCHAR(256);

-- 1.4 EB & SOLAR AUDIT COLUMNS
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS maximum_demand NUMERIC(10, 2);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS consumer_number VARCHAR(64);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS location VARCHAR(256);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS category VARCHAR(64);

ALTER TABLE energy_readings.solar ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_readings.solar ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_readings.solar ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;
ALTER TABLE energy_readings.solar ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_readings.solar ADD COLUMN IF NOT EXISTS location VARCHAR(256);

-- Make foreign key asset_id nullable across all reading tables so FKs never block upload
DO $$
BEGIN
    ALTER TABLE energy_readings.eb ALTER COLUMN asset_id DROP NOT NULL;
    ALTER TABLE energy_readings.dg ALTER COLUMN asset_id DROP NOT NULL;
    ALTER TABLE energy_readings.solar ALTER COLUMN asset_id DROP NOT NULL;
    ALTER TABLE energy_readings.transformer ALTER COLUMN asset_id DROP NOT NULL;
    ALTER TABLE energy_readings.ups ALTER COLUMN asset_id DROP NOT NULL;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;


-- ============================================================================
-- PART 2: FULL REFERENCE DDL FOR FRESH CREATION (ALL 5 MODULES)
-- ============================================================================

CREATE TABLE IF NOT EXISTS energy_readings.transformer (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    asset_code VARCHAR(64),
    reading_datetime TIMESTAMPTZ NOT NULL,
    primary_v_ry NUMERIC(10, 2), primary_v_yb NUMERIC(10, 2), primary_v_br NUMERIC(10, 2),
    secondary_v_ry NUMERIC(10, 2), secondary_v_yb NUMERIC(10, 2), secondary_v_br NUMERIC(10, 2),
    primary_i_r NUMERIC(10, 3), primary_i_y NUMERIC(10, 3), primary_i_b NUMERIC(10, 3),
    secondary_i_r NUMERIC(10, 3), secondary_i_y NUMERIC(10, 3), secondary_i_b NUMERIC(10, 3),
    cumulative_kwh NUMERIC(14, 4),
    cumulative_kvah NUMERIC(14, 4),
    interval_kwh NUMERIC(14, 4),
    interval_kvah NUMERIC(14, 4),
    frequency NUMERIC(6, 2),
    oil_temperature NUMERIC(6, 2),
    winding_temperature NUMERIC(6, 2),
    pf NUMERIC(5, 4),
    created_by VARCHAR(128),
    created_on TIMESTAMPTZ,
    remarks TEXT,
    location VARCHAR(256),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_transformer_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.dg (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    asset_code VARCHAR(64),
    reading_datetime TIMESTAMPTZ NOT NULL,
    status VARCHAR(32),
    kva NUMERIC(10, 2),
    kw NUMERIC(10, 2),
    voltage_ry NUMERIC(10, 2),
    voltage_yb NUMERIC(10, 2),
    voltage_br NUMERIC(10, 2),
    current_r NUMERIC(10, 2),
    current_y NUMERIC(10, 2),
    current_b NUMERIC(10, 2),
    diesel_level NUMERIC(10, 2),
    diesel_topup NUMERIC(10, 2),
    load_percentage NUMERIC(6, 2),
    cumulative_kwh NUMERIC(14, 4),
    cumulative_running_hours NUMERIC(10, 4),
    interval_kwh NUMERIC(14, 4),
    interval_running_hours NUMERIC(10, 4),
    rpm NUMERIC(8, 2),
    pf NUMERIC(5, 4),
    created_by VARCHAR(128),
    created_on TIMESTAMPTZ,
    remarks TEXT,
    location VARCHAR(256),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dg_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.ups (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    asset_code VARCHAR(64),
    reading_datetime TIMESTAMPTZ NOT NULL,
    input_voltage_r NUMERIC(10, 2),
    input_voltage_y NUMERIC(10, 2),
    input_voltage_b NUMERIC(10, 2),
    input_current_r NUMERIC(10, 2),
    input_current_y NUMERIC(10, 2),
    input_current_b NUMERIC(10, 2),
    rectifier_voltage NUMERIC(10, 2),
    bypass_voltage NUMERIC(10, 2),
    bypass_current NUMERIC(10, 2),
    bypass_frequency NUMERIC(6, 2),
    output_voltage NUMERIC(10, 2),
    output_current NUMERIC(10, 2),
    output_frequency NUMERIC(6, 2),
    battery_temperature NUMERIC(6, 2),
    battery_vdc NUMERIC(10, 2),
    battery_current NUMERIC(10, 2),
    created_by VARCHAR(128),
    created_on TIMESTAMPTZ,
    remarks TEXT,
    location VARCHAR(256),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ups_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.eb (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    asset_code VARCHAR(64),
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 4),
    cumulative_kvah NUMERIC(14, 4),
    cumulative_kvarh NUMERIC(14, 4),
    interval_kwh NUMERIC(14, 4),
    interval_kvah NUMERIC(14, 4),
    interval_kvarh NUMERIC(14, 4),
    pf NUMERIC(5, 4),
    maximum_demand NUMERIC(10, 2),
    created_by VARCHAR(128),
    created_on TIMESTAMPTZ,
    remarks TEXT,
    consumer_number VARCHAR(64),
    location VARCHAR(256),
    category VARCHAR(64),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_eb_asset_datetime UNIQUE (asset_id, reading_datetime)
);

CREATE TABLE IF NOT EXISTS energy_readings.solar (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE CASCADE,
    asset_code VARCHAR(64),
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 4),
    interval_kwh NUMERIC(14, 4),
    created_by VARCHAR(128),
    created_on TIMESTAMPTZ,
    remarks TEXT,
    location VARCHAR(256),
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_solar_asset_datetime UNIQUE (asset_id, reading_datetime)
);


-- ============================================================================
-- PART 3: RECREATE PUBLIC SCHEMA COMPATIBILITY VIEWS
-- ============================================================================

DROP VIEW IF EXISTS public.reading_eb CASCADE;
CREATE VIEW public.reading_eb AS SELECT * FROM energy_readings.eb;

DROP VIEW IF EXISTS public.reading_dg CASCADE;
CREATE VIEW public.reading_dg AS SELECT * FROM energy_readings.dg;

DROP VIEW IF EXISTS public.reading_solar CASCADE;
CREATE VIEW public.reading_solar AS SELECT * FROM energy_readings.solar;

DROP VIEW IF EXISTS public.reading_transformer CASCADE;
CREATE VIEW public.reading_transformer AS SELECT * FROM energy_readings.transformer;

DROP VIEW IF EXISTS public.reading_ups CASCADE;
CREATE VIEW public.reading_ups AS SELECT * FROM energy_readings.ups;


-- ============================================================================
-- PART 4: GRANT PERMISSIONS & RELOAD POSTGREST CACHE
-- ============================================================================

GRANT ALL ON ALL TABLES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

NOTIFY pgrst, 'reload config';
NOTIFY pgrst, 'reload schema';
