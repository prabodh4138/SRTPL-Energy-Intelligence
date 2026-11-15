-- ============================================================================
-- SRTPL POWER INTELLIGENCE — EQUIPMENT READING & KPI SQL VIEWS (CLOUD SUPABASE)
-- Aligned with: SRTPL Interactive Reading Dashboard Module Wise (EB, DG, Solar, Transformer, UPS)
-- Target: PostgreSQL / Supabase
--
-- Exposes:
-- 1. vw_<module>_asset_latest_reading: Exact latest reading for every inventoried asset
-- 2. vw_<module>_reading_kpis: Live KPI aggregates computed strictly inside PostgreSQL views
-- 3. vw_all_assets_latest_reading: Unified multi-module asset health & latest reading register
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_analytics;

-- 1. Master Asset Table
CREATE TABLE IF NOT EXISTS energy_master.asset (
    asset_id VARCHAR(64) PRIMARY KEY,
    asset_code VARCHAR(64) NOT NULL UNIQUE,
    asset_name VARCHAR(128) NOT NULL,
    plaza_id VARCHAR(16) REFERENCES energy_master.plaza(plaza_id) ON DELETE SET NULL,
    source_type VARCHAR(32) NOT NULL,
    capacity_kva NUMERIC(10, 2),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 2. EB (ELECTRICITY BOARD) SQL VIEWS
-- ============================================================================
DROP VIEW IF EXISTS public.vw_eb_asset_latest_reading CASCADE;
CREATE OR REPLACE VIEW public.vw_eb_asset_latest_reading AS
SELECT 
    a.asset_id,
    a.asset_code,
    a.asset_name,
    a.plaza_id,
    a.source_type,
    a.capacity_kva,
    r.reading_id,
    r.reading_datetime,
    r.cumulative_kwh AS latest_cumulative_kwh,
    r.interval_kwh AS latest_interval_kwh,
    r.cumulative_kvah AS latest_cumulative_kvah,
    r.interval_kvah AS latest_interval_kvah,
    r.cumulative_kvarh AS latest_cumulative_kvarh,
    r.interval_kvarh AS latest_interval_kvarh,
    r.pf AS latest_pf,
    r.maximum_demand AS latest_maximum_demand,
    r.data_quality_status,
    r.created_by,
    r.remarks
FROM energy_master.asset a
LEFT JOIN LATERAL (
    SELECT *
    FROM energy_readings.eb e
    WHERE e.asset_code = a.asset_code OR e.asset_id = a.asset_id
    ORDER BY e.reading_datetime DESC NULLS LAST
    LIMIT 1
) r ON true
WHERE a.source_type = 'EB'
ORDER BY a.plaza_id, a.asset_code;

DROP VIEW IF EXISTS public.vw_eb_reading_kpis CASCADE;
CREATE OR REPLACE VIEW public.vw_eb_reading_kpis AS
SELECT
    'EB' AS source_type,
    COUNT(DISTINCT r.asset_code) AS active_meters,
    COALESCE(SUM(r.cumulative_kwh), 0.0) AS total_cumulative_kwh,
    COALESCE(SUM(r.interval_kwh), 0.0) AS total_interval_kwh,
    COALESCE(SUM(r.cumulative_kvah), 0.0) AS total_cumulative_kvah,
    COALESCE(SUM(r.interval_kvah), 0.0) AS total_interval_kvah,
    COALESCE(AVG(CASE WHEN r.pf > 0 THEN r.pf ELSE NULL END), 0.98) AS avg_power_factor,
    COALESCE(MAX(r.maximum_demand), 0.0) AS peak_demand,
    COUNT(r.reading_id) AS total_reading_count,
    COALESCE(SUM(CASE WHEN r.data_quality_status = 'VALID' THEN 1 ELSE 0 END), 0) AS valid_count,
    COALESCE(SUM(CASE WHEN r.data_quality_status != 'VALID' THEN 1 ELSE 0 END), 0) AS exception_count
FROM energy_readings.eb r;

-- ============================================================================
-- 3. DG (DIESEL GENERATOR) SQL VIEWS
-- ============================================================================
DROP VIEW IF EXISTS public.vw_dg_asset_latest_reading CASCADE;
CREATE OR REPLACE VIEW public.vw_dg_asset_latest_reading AS
SELECT 
    a.asset_id,
    a.asset_code,
    a.asset_name,
    a.plaza_id,
    a.source_type,
    a.capacity_kva,
    r.reading_id,
    r.reading_datetime,
    r.cumulative_kwh AS latest_cumulative_kwh,
    r.interval_kwh AS latest_interval_kwh,
    r.cumulative_running_hours AS latest_run_hours,
    r.interval_running_hours AS latest_interval_run_hours,
    r.diesel_level AS latest_fuel_level,
    r.load_percentage AS latest_load_pct,
    r.pf AS latest_pf,
    r.status AS operational_status,
    r.data_quality_status,
    r.created_by,
    r.remarks
FROM energy_master.asset a
LEFT JOIN LATERAL (
    SELECT *
    FROM energy_readings.dg d
    WHERE d.asset_code = a.asset_code OR d.asset_id = a.asset_id
    ORDER BY d.reading_datetime DESC NULLS LAST
    LIMIT 1
) r ON true
WHERE a.source_type = 'DG'
ORDER BY a.plaza_id, a.asset_code;

DROP VIEW IF EXISTS public.vw_dg_reading_kpis CASCADE;
CREATE OR REPLACE VIEW public.vw_dg_reading_kpis AS
SELECT
    'DG' AS source_type,
    COUNT(DISTINCT r.asset_code) AS active_generators,
    COALESCE(SUM(r.cumulative_kwh), 0.0) AS total_cumulative_kwh,
    COALESCE(SUM(r.interval_kwh), 0.0) AS total_interval_kwh,
    COALESCE(SUM(r.cumulative_running_hours), 0.0) AS total_cumulative_run_hours,
    COALESCE(SUM(r.interval_running_hours), 0.0) AS total_interval_run_hours,
    COALESCE(SUM(r.diesel_level), 0.0) AS total_fuel_level,
    COALESCE(AVG(CASE WHEN r.pf > 0 THEN r.pf ELSE NULL END), 0.98) AS avg_power_factor,
    COUNT(r.reading_id) AS total_log_count,
    COALESCE(SUM(CASE WHEN r.data_quality_status = 'VALID' THEN 1 ELSE 0 END), 0) AS valid_count,
    COALESCE(SUM(CASE WHEN r.data_quality_status != 'VALID' THEN 1 ELSE 0 END), 0) AS exception_count
FROM energy_readings.dg r;

-- ============================================================================
-- 4. SOLAR SQL VIEWS
-- ============================================================================
DROP VIEW IF EXISTS public.vw_solar_asset_latest_reading CASCADE;
CREATE OR REPLACE VIEW public.vw_solar_asset_latest_reading AS
SELECT 
    a.asset_id,
    a.asset_code,
    a.asset_name,
    a.plaza_id,
    a.source_type,
    a.capacity_kva,
    r.reading_id,
    r.reading_datetime,
    r.cumulative_kwh AS latest_cumulative_kwh,
    r.interval_kwh AS latest_interval_kwh,
    r.data_quality_status,
    r.created_by,
    r.remarks
FROM energy_master.asset a
LEFT JOIN LATERAL (
    SELECT *
    FROM energy_readings.solar s
    WHERE s.asset_code = a.asset_code OR s.asset_id = a.asset_id
    ORDER BY s.reading_datetime DESC NULLS LAST
    LIMIT 1
) r ON true
WHERE a.source_type = 'SOLAR'
ORDER BY a.plaza_id, a.asset_code;

DROP VIEW IF EXISTS public.vw_solar_reading_kpis CASCADE;
CREATE OR REPLACE VIEW public.vw_solar_reading_kpis AS
SELECT
    'SOLAR' AS source_type,
    COUNT(DISTINCT r.asset_code) AS active_plants,
    COALESCE(SUM(r.cumulative_kwh), 0.0) AS total_cumulative_kwh,
    COALESCE(SUM(r.interval_kwh), 0.0) AS total_interval_kwh,
    COALESCE(SUM(r.interval_kwh) * 0.82, 0.0) AS co2_avoided_kg,
    COUNT(r.reading_id) AS total_log_count,
    COALESCE(SUM(CASE WHEN r.data_quality_status = 'VALID' THEN 1 ELSE 0 END), 0) AS valid_count,
    COALESCE(SUM(CASE WHEN r.data_quality_status != 'VALID' THEN 1 ELSE 0 END), 0) AS exception_count
FROM energy_readings.solar r;

-- ============================================================================
-- 5. TRANSFORMER SQL VIEWS
-- ============================================================================
DROP VIEW IF EXISTS public.vw_transformer_asset_latest_reading CASCADE;
CREATE OR REPLACE VIEW public.vw_transformer_asset_latest_reading AS
SELECT 
    a.asset_id,
    a.asset_code,
    a.asset_name,
    a.plaza_id,
    a.source_type,
    a.capacity_kva,
    r.reading_id,
    r.reading_datetime,
    r.cumulative_kwh AS latest_cumulative_kwh,
    r.interval_kwh AS latest_interval_kwh,
    r.primary_v_ry AS latest_primary_v_ry,
    r.primary_i_r AS latest_primary_i_r,
    r.oil_temperature AS latest_oil_temp,
    r.winding_temperature AS latest_winding_temp,
    r.pf AS latest_pf,
    r.data_quality_status,
    r.created_by,
    r.remarks
FROM energy_master.asset a
LEFT JOIN LATERAL (
    SELECT *
    FROM energy_readings.transformer t
    WHERE t.asset_code = a.asset_code OR t.asset_id = a.asset_id
    ORDER BY t.reading_datetime DESC NULLS LAST
    LIMIT 1
) r ON true
WHERE a.source_type = 'TRANSFORMER'
ORDER BY a.plaza_id, a.asset_code;

DROP VIEW IF EXISTS public.vw_transformer_reading_kpis CASCADE;
CREATE OR REPLACE VIEW public.vw_transformer_reading_kpis AS
SELECT
    'TRANSFORMER' AS source_type,
    COUNT(DISTINCT r.asset_code) AS active_transformers,
    COALESCE(SUM(r.cumulative_kwh), 0.0) AS total_cumulative_kwh,
    COALESCE(SUM(r.interval_kwh), 0.0) AS total_interval_kwh,
    COALESCE(AVG(r.oil_temperature), 0.0) AS avg_oil_temp,
    COALESCE(AVG(r.winding_temperature), 0.0) AS avg_winding_temp,
    COALESCE(AVG(CASE WHEN r.pf > 0 THEN r.pf ELSE NULL END), 0.98) AS avg_power_factor,
    COUNT(r.reading_id) AS total_log_count,
    COALESCE(SUM(CASE WHEN r.data_quality_status = 'VALID' THEN 1 ELSE 0 END), 0) AS valid_count,
    COALESCE(SUM(CASE WHEN r.data_quality_status != 'VALID' THEN 1 ELSE 0 END), 0) AS exception_count
FROM energy_readings.transformer r;

-- ============================================================================
-- 6. UPS SQL VIEWS
-- ============================================================================
DROP VIEW IF EXISTS public.vw_ups_asset_latest_reading CASCADE;
CREATE OR REPLACE VIEW public.vw_ups_asset_latest_reading AS
SELECT 
    a.asset_id,
    a.asset_code,
    a.asset_name,
    a.plaza_id,
    a.source_type,
    a.capacity_kva,
    r.reading_id,
    r.reading_datetime,
    r.output_voltage AS latest_output_voltage,
    r.output_current AS latest_output_current,
    r.output_frequency AS latest_output_frequency,
    r.battery_vdc AS latest_battery_vdc,
    r.battery_temperature AS latest_battery_temp,
    r.data_quality_status,
    r.created_by,
    r.remarks
FROM energy_master.asset a
LEFT JOIN LATERAL (
    SELECT *
    FROM energy_readings.ups u
    WHERE u.asset_code = a.asset_code OR u.asset_id = a.asset_id
    ORDER BY u.reading_datetime DESC NULLS LAST
    LIMIT 1
) r ON true
WHERE a.source_type = 'UPS'
ORDER BY a.plaza_id, a.asset_code;

DROP VIEW IF EXISTS public.vw_ups_reading_kpis CASCADE;
CREATE OR REPLACE VIEW public.vw_ups_reading_kpis AS
SELECT
    'UPS' AS source_type,
    COUNT(DISTINCT r.asset_code) AS active_systems,
    COALESCE(AVG(r.output_voltage), 230.0) AS avg_output_voltage,
    COALESCE(AVG(r.battery_vdc), 380.0) AS avg_battery_vdc,
    COALESCE(AVG(r.battery_temperature), 25.0) AS avg_battery_temp,
    COUNT(r.reading_id) AS total_log_count,
    COALESCE(SUM(CASE WHEN r.data_quality_status = 'VALID' THEN 1 ELSE 0 END), 0) AS valid_count,
    COALESCE(SUM(CASE WHEN r.data_quality_status != 'VALID' THEN 1 ELSE 0 END), 0) AS exception_count
FROM energy_readings.ups r;

-- ============================================================================
-- 7. UNIFIED ALL ASSETS LATEST READING VIEW
-- ============================================================================
DROP VIEW IF EXISTS public.vw_all_assets_latest_reading CASCADE;
CREATE OR REPLACE VIEW public.vw_all_assets_latest_reading AS
SELECT asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva, reading_id, reading_datetime, latest_cumulative_kwh, latest_interval_kwh, latest_pf, data_quality_status, created_by FROM public.vw_eb_asset_latest_reading
UNION ALL
SELECT asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva, reading_id, reading_datetime, latest_cumulative_kwh, latest_interval_kwh, latest_pf, data_quality_status, created_by FROM public.vw_dg_asset_latest_reading
UNION ALL
SELECT asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva, reading_id, reading_datetime, latest_cumulative_kwh, latest_interval_kwh, NULL as latest_pf, data_quality_status, created_by FROM public.vw_solar_asset_latest_reading
UNION ALL
SELECT asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva, reading_id, reading_datetime, latest_cumulative_kwh, latest_interval_kwh, latest_pf, data_quality_status, created_by FROM public.vw_transformer_asset_latest_reading
UNION ALL
SELECT asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva, reading_id, reading_datetime, NULL as latest_cumulative_kwh, NULL as latest_interval_kwh, NULL as latest_pf, data_quality_status, created_by FROM public.vw_ups_asset_latest_reading;

-- Grants for API access
GRANT USAGE ON SCHEMA energy_master, energy_readings, energy_analytics TO anon, authenticated, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public, energy_master, energy_readings, energy_analytics TO anon, authenticated, service_role;
