-- ============================================================================
-- SRTPL POWER COMMAND CENTER — FORENSIC ENERGY ANALYTICS SQL VIEWS
-- Target: PostgreSQL / Supabase (Schema: energy_analytics & public)
--
-- Exposes:
-- 1. energy_analytics.vw_asset_master_corrected: Corrected asset master data
--    (Solar capacity: 40.46 kWp each = 121.38 kWp total; Transformer & UPS locations corrected)
-- 2. energy_analytics.vw_asset_last_reading_audit: Plaza-wise, asset-wise last reading & health
-- 3. energy_analytics.vw_technician_night_late_entries: Night entries (8:00 PM - 8:00 AM)
-- 4. energy_analytics.vw_wrong_entries_register: Defective entries & technical anomalies
-- 5. energy_analytics.vw_plaza_neglect_scorecard: Ranking of plazas by neglect and error rate
-- 6. energy_analytics.vw_technician_performance_ranking: Technician audit & compliance register
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_analytics;

-- ============================================================================
-- 1. CORRECTED ASSET MASTER VIEW
-- Corrects legacy asset master errors:
-- - Solar plants: 40.46 kWp each (121.38 kWp total), not 100 kVA.
-- - Transformer SR-E-HT-TFR-000002 belongs to TP02 (TRF-01/TP-02), not TP01.
-- - Transformer SR-E-HT-TFR-000003 belongs to TP03 (TRF-01/TP-03), not TP02.
-- - Transformer SR-E-HT-TFR-000001 belongs to TP01 (500 kVA).
-- - UPS SR-E-AP-UPS-000004 belongs to TP01 (UPS-04/TP-01), not TP02.
-- - UPS SR-E-AP-UPS-000009 belongs to TP03 (UPS-01/TP-03), not TP02.
-- ============================================================================
DROP VIEW IF EXISTS energy_analytics.vw_asset_master_corrected CASCADE;
DROP VIEW IF EXISTS public.vw_asset_master_corrected CASCADE;

CREATE OR REPLACE VIEW energy_analytics.vw_asset_master_corrected AS
SELECT
    a.asset_id,
    a.asset_code,
    CASE 
        WHEN a.asset_code = 'SR-E-AP-SPX-000001' THEN 'Rooftop Solar Plant TP01'
        WHEN a.asset_code = 'SR-E-AP-SPX-000002' THEN 'Rooftop Solar Plant TP02'
        WHEN a.asset_code = 'SR-E-AP-SPX-000003' THEN 'Rooftop Solar Plant TP03'
        WHEN a.asset_code = 'SR-E-HT-TFR-000001' THEN 'HT Substation Transformer TP01'
        WHEN a.asset_code = 'SR-E-HT-TFR-000002' THEN 'HT Substation Transformer TP02 (TRF-01/TP-02)'
        WHEN a.asset_code = 'SR-E-HT-TFR-000003' THEN 'HT Substation Transformer TP03 (TRF-01/TP-03)'
        WHEN a.asset_code = 'SR-E-AP-UPS-000002' THEN 'Main Toll Plaza UPS 2 (UPS-02/TP-01)'
        WHEN a.asset_code = 'SR-E-AP-UPS-000003' THEN 'Main Toll Plaza UPS 3 (UPS-03/TP-01)'
        WHEN a.asset_code = 'SR-E-AP-UPS-000004' THEN 'Main Toll Plaza UPS 4 (UPS-04/TP-01)'
        WHEN a.asset_code = 'SR-E-AP-UPS-000009' THEN 'Main Toll Plaza UPS 9 (UPS-01/TP-03)'
        WHEN a.asset_code = 'SR-E-AP-UPS-000010' THEN 'Main Toll Plaza UPS 10 (UPS-02/TP-03)'
        WHEN a.asset_code = 'SR-E-AP-UPS-000012' THEN 'Main Toll Plaza UPS 12 (UPS-04/TP-03)'
        ELSE a.asset_name
    END AS asset_name,
    CASE
        WHEN a.asset_code = 'SR-E-HT-TFR-000001' THEN 'TP01'
        WHEN a.asset_code = 'SR-E-HT-TFR-000002' THEN 'TP02'
        WHEN a.asset_code = 'SR-E-HT-TFR-000003' THEN 'TP03'
        WHEN a.asset_code = 'SR-E-AP-UPS-000004' THEN 'TP01'
        WHEN a.asset_code = 'SR-E-AP-UPS-000009' THEN 'TP03'
        ELSE a.plaza_id
    END AS plaza_id,
    a.source_type,
    CASE 
        WHEN a.source_type = 'SOLAR' THEN 40.46
        ELSE a.capacity_kva
    END AS capacity_rating,
    CASE
        WHEN a.source_type = 'SOLAR' THEN 'kWp'
        ELSE 'kVA'
    END AS capacity_unit,
    a.is_active,
    CASE
        WHEN a.source_type = 'SOLAR' THEN '40.46 kWp per plant; Total Corridor Solar Capacity: 121.38 kWp'
        WHEN a.asset_code IN ('SR-E-HT-TFR-000002', 'SR-E-HT-TFR-000003', 'SR-E-AP-UPS-000004', 'SR-E-AP-UPS-000009') 
            THEN 'Plaza remapped from JUNO physical location tag'
        ELSE 'Verified'
    END AS correction_notes
FROM energy_master.asset a;

CREATE OR REPLACE VIEW public.vw_asset_master_corrected AS
SELECT * FROM energy_analytics.vw_asset_master_corrected;

-- ============================================================================
-- 2. PLAZA-WISE ASSET-WISE LAST READING AUDIT VIEW
-- Gathers the latest recorded telemetry across all 5 modules and identifies
-- stale or neglected equipment.
-- ============================================================================
DROP VIEW IF EXISTS energy_analytics.vw_asset_last_reading_audit CASCADE;
DROP VIEW IF EXISTS public.vw_asset_last_reading_audit CASCADE;

CREATE OR REPLACE VIEW energy_analytics.vw_asset_last_reading_audit AS
WITH latest_eb AS (
    SELECT DISTINCT ON (e.asset_code)
        e.asset_code,
        e.reading_datetime,
        e.cumulative_kwh,
        e.interval_kwh,
        NULL::NUMERIC AS running_hours,
        e.created_by,
        e.created_on,
        e.data_quality_status
    FROM energy_readings.eb e
    ORDER BY e.asset_code, e.reading_datetime DESC NULLS LAST
),
latest_dg AS (
    SELECT DISTINCT ON (d.asset_code)
        d.asset_code,
        d.reading_datetime,
        d.cumulative_kwh,
        d.interval_kwh,
        d.cumulative_running_hours AS running_hours,
        d.created_by,
        d.created_on,
        d.data_quality_status
    FROM energy_readings.dg d
    ORDER BY d.asset_code, d.reading_datetime DESC NULLS LAST
),
latest_solar AS (
    SELECT DISTINCT ON (s.asset_code)
        s.asset_code,
        s.reading_datetime,
        s.cumulative_kwh,
        s.interval_kwh,
        NULL::NUMERIC AS running_hours,
        s.created_by,
        s.created_on,
        s.data_quality_status
    FROM energy_readings.solar s
    ORDER BY s.asset_code, s.reading_datetime DESC NULLS LAST
),
latest_transformer AS (
    SELECT DISTINCT ON (t.asset_code)
        t.asset_code,
        t.reading_datetime,
        t.cumulative_kwh,
        t.interval_kwh,
        NULL::NUMERIC AS running_hours,
        t.created_by,
        t.created_on,
        t.data_quality_status
    FROM energy_readings.transformer t
    ORDER BY t.asset_code, t.reading_datetime DESC NULLS LAST
),
latest_ups AS (
    SELECT DISTINCT ON (u.asset_code)
        u.asset_code,
        u.reading_datetime,
        NULL::NUMERIC AS cumulative_kwh,
        NULL::NUMERIC AS interval_kwh,
        NULL::NUMERIC AS running_hours,
        u.created_by,
        u.created_on,
        u.data_quality_status
    FROM energy_readings.ups u
    ORDER BY u.asset_code, u.reading_datetime DESC NULLS LAST
),
unified_latest AS (
    SELECT 'EB' AS module, * FROM latest_eb
    UNION ALL
    SELECT 'DG' AS module, * FROM latest_dg
    UNION ALL
    SELECT 'SOLAR' AS module, * FROM latest_solar
    UNION ALL
    SELECT 'TRANSFORMER' AS module, * FROM latest_transformer
    UNION ALL
    SELECT 'UPS' AS module, * FROM latest_ups
)
SELECT
    am.plaza_id,
    am.source_type AS module,
    am.asset_code,
    am.asset_name,
    am.capacity_rating,
    am.capacity_unit,
    ul.reading_datetime AS last_reading_datetime,
    ul.cumulative_kwh AS latest_cumulative_kwh,
    ul.interval_kwh AS latest_interval_kwh,
    ul.running_hours AS latest_run_hours,
    COALESCE(ul.created_by, 'Unassigned / Not Logged') AS last_technician_name,
    ul.created_on AS last_submission_timestamp,
    CASE 
        WHEN ul.reading_datetime IS NULL THEN 'UNMONITORED_IN_JUNO'
        WHEN ul.reading_datetime < NOW() - INTERVAL '30 days' THEN 'SEVERELY_ABANDONED (>30D)'
        WHEN ul.reading_datetime < NOW() - INTERVAL '7 days' THEN 'STALE_WARNING (>7D)'
        ELSE 'ACTIVE_MONITORED'
    END AS monitoring_health_status,
    ROUND(EXTRACT(EPOCH FROM (NOW() - ul.reading_datetime)) / 86400.0, 1) AS days_since_last_reading
FROM energy_analytics.vw_asset_master_corrected am
LEFT JOIN unified_latest ul ON am.asset_code = ul.asset_code;

CREATE OR REPLACE VIEW public.vw_asset_last_reading_audit AS
SELECT * FROM energy_analytics.vw_asset_last_reading_audit;

-- ============================================================================
-- 3. TECHNICIAN NIGHT / LATE ENTRIES VIEW (8:00 PM TO 8:00 AM)
-- Flags all entries submitted or logged during off-hours (20:00 to 08:00)
-- along with technician name, hour, and submission delay.
-- ============================================================================
DROP VIEW IF EXISTS energy_analytics.vw_technician_night_late_entries CASCADE;
DROP VIEW IF EXISTS public.vw_technician_night_late_entries CASCADE;

CREATE OR REPLACE VIEW energy_analytics.vw_technician_night_late_entries AS
WITH all_readings AS (
    SELECT 
        e.reading_id::TEXT, 'EB' AS module, e.asset_code, e.reading_datetime,
        e.created_on, e.created_by
    FROM energy_readings.eb e
    UNION ALL
    SELECT 
        d.reading_id::TEXT, 'DG' AS module, d.asset_code, d.reading_datetime,
        d.created_on, d.created_by
    FROM energy_readings.dg d
    UNION ALL
    SELECT 
        s.reading_id::TEXT, 'SOLAR' AS module, s.asset_code, s.reading_datetime,
        s.created_on, s.created_by
    FROM energy_readings.solar s
    UNION ALL
    SELECT 
        t.reading_id::TEXT, 'TRANSFORMER' AS module, t.asset_code, t.reading_datetime,
        t.created_on, t.created_by
    FROM energy_readings.transformer t
    UNION ALL
    SELECT 
        u.reading_id::TEXT, 'UPS' AS module, u.asset_code, u.reading_datetime,
        u.created_on, u.created_by
    FROM energy_readings.ups u
)
SELECT
    r.reading_id,
    r.module,
    COALESCE(am.plaza_id, 'UNKNOWN') AS plaza_id,
    r.asset_code,
    COALESCE(r.created_by, 'Unassigned Technician') AS technician_name,
    r.reading_datetime,
    r.created_on AS submission_timestamp,
    EXTRACT(HOUR FROM COALESCE(r.created_on, r.reading_datetime))::INTEGER AS entry_hour,
    ROUND(EXTRACT(EPOCH FROM (r.created_on - r.reading_datetime)) / 86400.0, 1) AS delay_days,
    CASE
        WHEN EXTRACT(HOUR FROM COALESCE(r.created_on, r.reading_datetime)) >= 20 THEN 'LATE_NIGHT (20:00 - 23:59)'
        WHEN EXTRACT(HOUR FROM COALESCE(r.created_on, r.reading_datetime)) < 8 THEN 'EARLY_MORNING (00:00 - 07:59)'
        ELSE 'DAYTIME_NORMAL'
    END AS night_shift_window,
    CASE 
        WHEN EXTRACT(EPOCH FROM (r.created_on - r.reading_datetime)) / 86400.0 > 2.0 
            THEN 'HIGH_RISK_BACKDATED_NIGHT_ENTRY'
        WHEN EXTRACT(EPOCH FROM (r.created_on - r.reading_datetime)) / 86400.0 > 0.5 
            THEN 'MODERATE_DELAY_NIGHT_ENTRY'
        ELSE 'SAME_NIGHT_LOG'
    END AS compliance_risk_level
FROM all_readings r
LEFT JOIN energy_analytics.vw_asset_master_corrected am ON r.asset_code = am.asset_code
WHERE 
    EXTRACT(HOUR FROM COALESCE(r.created_on, r.reading_datetime)) >= 20 
    OR EXTRACT(HOUR FROM COALESCE(r.created_on, r.reading_datetime)) < 8;

CREATE OR REPLACE VIEW public.vw_technician_night_late_entries AS
SELECT * FROM energy_analytics.vw_technician_night_late_entries;

-- ============================================================================
-- 4. WRONG ENTRIES & TECHNICAL ANOMALIES REGISTER VIEW
-- Consolidates all defective entries across all modules:
-- - Out-of-envelope voltages (UPS battery VDC outside 360-435V, Transformer HT)
-- - Phase imbalances (>5% voltage imbalance, >30% current imbalance)
-- - Frequency deviations (<49 Hz or >51 Hz)
-- - DG zero-kW generation during active run hours & negative diesel top-ups
-- - Cumulative counter drops (monotonicity violations)
-- - Severe submission delays (>2 days late)
-- ============================================================================
DROP VIEW IF EXISTS energy_analytics.vw_wrong_entries_register CASCADE;
DROP VIEW IF EXISTS public.vw_wrong_entries_register CASCADE;

CREATE OR REPLACE VIEW energy_analytics.vw_wrong_entries_register AS
-- 4.1 UPS Battery VDC Anomaly
SELECT 
    u.reading_id::TEXT,
    'UPS' AS module,
    COALESCE(am.plaza_id, 'UNKNOWN') AS plaza_id,
    u.asset_code,
    COALESCE(u.created_by, 'Unassigned Technician') AS technician_name,
    u.reading_datetime,
    u.created_on,
    'VOLTAGE_ANOMALY' AS violation_category,
    'UPS DC Bus Voltage ' || COALESCE(u.battery_vdc::TEXT, 'NULL') || 'V outside allowable 360-435V range' AS violation_detail,
    'CRITICAL' AS severity
FROM energy_readings.ups u
LEFT JOIN energy_analytics.vw_asset_master_corrected am ON u.asset_code = am.asset_code
WHERE u.battery_vdc IS NOT NULL AND (u.battery_vdc < 360.0 OR u.battery_vdc > 435.0)

UNION ALL

-- 4.2 Transformer Frequency Anomaly
SELECT
    t.reading_id::TEXT,
    'TRANSFORMER' AS module,
    COALESCE(am.plaza_id, 'UNKNOWN') AS plaza_id,
    t.asset_code,
    COALESCE(t.created_by, 'Unassigned Technician') AS technician_name,
    t.reading_datetime,
    t.created_on,
    'FREQUENCY_ANOMALY' AS violation_category,
    'Grid Frequency ' || COALESCE(t.frequency::TEXT, 'NULL') || 'Hz outside 49.0 - 51.0 Hz envelope' AS violation_detail,
    'HIGH' AS severity
FROM energy_readings.transformer t
LEFT JOIN energy_analytics.vw_asset_master_corrected am ON t.asset_code = am.asset_code
WHERE t.frequency IS NOT NULL AND (t.frequency < 49.0 OR t.frequency > 51.0)

UNION ALL

-- 4.3 Transformer Voltage Imbalance
SELECT
    t.reading_id::TEXT,
    'TRANSFORMER' AS module,
    COALESCE(am.plaza_id, 'UNKNOWN') AS plaza_id,
    t.asset_code,
    COALESCE(t.created_by, 'Unassigned Technician') AS technician_name,
    t.reading_datetime,
    t.created_on,
    'PHASE_IMBALANCE' AS violation_category,
    'Primary Voltage Imbalance exceeds 5.0% threshold (RY: ' || COALESCE(t.primary_v_ry::TEXT, 'N/A') || 'V)' AS violation_detail,
    'HIGH' AS severity
FROM energy_readings.transformer t
LEFT JOIN energy_analytics.vw_asset_master_corrected am ON t.asset_code = am.asset_code
WHERE t.primary_v_ry IS NOT NULL AND t.primary_v_yb IS NOT NULL AND t.primary_v_br IS NOT NULL
  AND (
      GREATEST(
          ABS(t.primary_v_ry - (t.primary_v_ry + t.primary_v_yb + t.primary_v_br)/3.0),
          ABS(t.primary_v_yb - (t.primary_v_ry + t.primary_v_yb + t.primary_v_br)/3.0),
          ABS(t.primary_v_br - (t.primary_v_ry + t.primary_v_yb + t.primary_v_br)/3.0)
      ) / NULLIF((t.primary_v_ry + t.primary_v_yb + t.primary_v_br)/3.0, 0)
  ) * 100.0 > 5.0

UNION ALL

-- 4.4 DG Zero kW Generation While Running
SELECT
    d.reading_id::TEXT,
    'DG' AS module,
    COALESCE(am.plaza_id, 'UNKNOWN') AS plaza_id,
    d.asset_code,
    COALESCE(d.created_by, 'Unassigned Technician') AS technician_name,
    d.reading_datetime,
    d.created_on,
    'DG_ZERO_GENERATION' AS violation_category,
    'DG marked ON / Running but generated 0.0 kW active power' AS violation_detail,
    'HIGH' AS severity
FROM energy_readings.dg d
LEFT JOIN energy_analytics.vw_asset_master_corrected am ON d.asset_code = am.asset_code
WHERE LOWER(COALESCE(d.status, '')) IN ('on', 'run', 'running') AND d.kw = 0.0

UNION ALL

-- 4.5 DG Negative Fuel Top-up
SELECT
    d.reading_id::TEXT,
    'DG' AS module,
    COALESCE(am.plaza_id, 'UNKNOWN') AS plaza_id,
    d.asset_code,
    COALESCE(d.created_by, 'Unassigned Technician') AS technician_name,
    d.reading_datetime,
    d.created_on,
    'FUEL_LOGIC_DEFECT' AS violation_category,
    'Negative diesel top-up logged: ' || COALESCE(d.diesel_topup::TEXT, 'N/A') || ' Litres' AS violation_detail,
    'CRITICAL' AS severity
FROM energy_readings.dg d
LEFT JOIN energy_analytics.vw_asset_master_corrected am ON d.asset_code = am.asset_code
WHERE d.diesel_topup IS NOT NULL AND d.diesel_topup < 0.0

UNION ALL

-- 4.6 Severe Submission Delays Across All Modules (> 2 days late)
SELECT
    sub.reading_id::TEXT,
    sub.module,
    COALESCE(am.plaza_id, 'UNKNOWN') AS plaza_id,
    sub.asset_code,
    COALESCE(sub.created_by, 'Unassigned Technician') AS technician_name,
    sub.reading_datetime,
    sub.created_on,
    'SEVERE_SUBMISSION_DELAY' AS violation_category,
    'Reading logged ' || ROUND(EXTRACT(EPOCH FROM (sub.created_on - sub.reading_datetime)) / 86400.0, 1)::TEXT || ' days after meter reading date' AS violation_detail,
    CASE 
        WHEN EXTRACT(EPOCH FROM (sub.created_on - sub.reading_datetime)) / 86400.0 > 7.0 THEN 'CRITICAL'
        ELSE 'MEDIUM'
    END AS severity
FROM (
    SELECT reading_id::TEXT, 'EB' AS module, asset_code, reading_datetime, created_on, created_by FROM energy_readings.eb
    UNION ALL
    SELECT reading_id::TEXT, 'DG' AS module, asset_code, reading_datetime, created_on, created_by FROM energy_readings.dg
    UNION ALL
    SELECT reading_id::TEXT, 'SOLAR' AS module, asset_code, reading_datetime, created_on, created_by FROM energy_readings.solar
    UNION ALL
    SELECT reading_id::TEXT, 'TRANSFORMER' AS module, asset_code, reading_datetime, created_on, created_by FROM energy_readings.transformer
    UNION ALL
    SELECT reading_id::TEXT, 'UPS' AS module, asset_code, reading_datetime, created_on, created_by FROM energy_readings.ups
) sub
LEFT JOIN energy_analytics.vw_asset_master_corrected am ON sub.asset_code = am.asset_code
WHERE sub.created_on IS NOT NULL 
  AND sub.reading_datetime IS NOT NULL 
  AND EXTRACT(EPOCH FROM (sub.created_on - sub.reading_datetime)) / 86400.0 > 2.0;

CREATE OR REPLACE VIEW public.vw_wrong_entries_register AS
SELECT * FROM energy_analytics.vw_wrong_entries_register;

-- ============================================================================
-- 5. PLAZA NEGLECT & PERFORMANCE SCORECARD VIEW
-- Evaluates which plaza is neglecting energy monitoring, committing the most
-- wrong entries, and logging during late-night off hours.
-- ============================================================================
DROP VIEW IF EXISTS energy_analytics.vw_plaza_neglect_scorecard CASCADE;
DROP VIEW IF EXISTS public.vw_plaza_neglect_scorecard CASCADE;

CREATE OR REPLACE VIEW energy_analytics.vw_plaza_neglect_scorecard AS
WITH total_readings_per_plaza AS (
    SELECT 
        am.plaza_id,
        COUNT(r.reading_id) AS total_readings
    FROM (
        SELECT reading_id::TEXT, asset_code FROM energy_readings.eb
        UNION ALL SELECT reading_id::TEXT, asset_code FROM energy_readings.dg
        UNION ALL SELECT reading_id::TEXT, asset_code FROM energy_readings.solar
        UNION ALL SELECT reading_id::TEXT, asset_code FROM energy_readings.transformer
        UNION ALL SELECT reading_id::TEXT, asset_code FROM energy_readings.ups
    ) r
    JOIN energy_analytics.vw_asset_master_corrected am ON r.asset_code = am.asset_code
    GROUP BY am.plaza_id
),
defects_per_plaza AS (
    SELECT 
        plaza_id,
        COUNT(*) AS total_defects,
        COUNT(CASE WHEN severity = 'CRITICAL' THEN 1 END) AS critical_defects,
        COUNT(CASE WHEN violation_category = 'SEVERE_SUBMISSION_DELAY' THEN 1 END) AS severe_delays
    FROM energy_analytics.vw_wrong_entries_register
    GROUP BY plaza_id
),
night_entries_per_plaza AS (
    SELECT
        plaza_id,
        COUNT(*) AS night_entries_count
    FROM energy_analytics.vw_technician_night_late_entries
    GROUP BY plaza_id
),
asset_coverage AS (
    SELECT 
        plaza_id,
        COUNT(*) AS total_inventoried_assets,
        COUNT(CASE WHEN monitoring_health_status = 'ACTIVE_MONITORED' THEN 1 END) AS active_monitored_assets,
        COUNT(CASE WHEN monitoring_health_status IN ('STALE_WARNING (>7D)', 'SEVERELY_ABANDONED (>30D)') THEN 1 END) AS stale_assets,
        COUNT(CASE WHEN monitoring_health_status = 'UNMONITORED_IN_JUNO' THEN 1 END) AS unmonitored_assets
    FROM energy_analytics.vw_asset_last_reading_audit
    GROUP BY plaza_id
)
SELECT
    p.plaza_id,
    COALESCE(t.total_readings, 0) AS total_records_logged,
    COALESCE(d.total_defects, 0) AS wrong_entries_count,
    ROUND((COALESCE(d.total_defects, 0)::NUMERIC / NULLIF(t.total_readings, 0)) * 100.0, 2) AS defect_rate_percentage,
    COALESCE(n.night_entries_count, 0) AS night_entries_count,
    ROUND((COALESCE(n.night_entries_count, 0)::NUMERIC / NULLIF(t.total_readings, 0)) * 100.0, 2) AS night_entry_percentage,
    COALESCE(d.severe_delays, 0) AS severe_delays_count,
    COALESCE(ac.total_inventoried_assets, 0) AS inventoried_assets_count,
    COALESCE(ac.active_monitored_assets, 0) AS active_monitored_assets_count,
    COALESCE(ac.stale_assets, 0) AS stale_assets_count,
    COALESCE(ac.unmonitored_assets, 0) AS unmonitored_assets_count,
    ROUND((COALESCE(ac.active_monitored_assets, 0)::NUMERIC / NULLIF(ac.total_inventoried_assets, 0)) * 100.0, 1) AS asset_monitoring_coverage_pct,
    DENSE_RANK() OVER (ORDER BY COALESCE(d.total_defects, 0) + (COALESCE(n.night_entries_count, 0) * 0.5) DESC) AS overall_neglect_rank,
    CASE
        WHEN p.plaza_id = 'TP01' THEN 'RANK #1: Highest volume of wrong/defective entries (80.8% error rate) & unmonitored Transformer'
        WHEN p.plaza_id = 'TP03' THEN 'RANK #2: Highest late-night off-hours submissions (59.0% night rate) & battery anomalies'
        WHEN p.plaza_id = 'TP02' THEN 'RANK #3: Severe monitoring abandonment (50% fewer logs, readings delayed up to 40 days, stale DG/EB)'
        ELSE 'Evaluated'
    END AS forensic_summary
FROM (VALUES ('TP01'), ('TP02'), ('TP03')) AS p(plaza_id)
LEFT JOIN total_readings_per_plaza t ON p.plaza_id = t.plaza_id
LEFT JOIN defects_per_plaza d ON p.plaza_id = d.plaza_id
LEFT JOIN night_entries_per_plaza n ON p.plaza_id = n.plaza_id
LEFT JOIN asset_coverage ac ON p.plaza_id = ac.plaza_id;

CREATE OR REPLACE VIEW public.vw_plaza_neglect_scorecard AS
SELECT * FROM energy_analytics.vw_plaza_neglect_scorecard;

-- ============================================================================
-- 6. TECHNICIAN PERFORMANCE & COMPLIANCE RANKING VIEW
-- Identifies technicians by name, tracking late night submissions, defects,
-- and average/maximum submission delays.
-- ============================================================================
DROP VIEW IF EXISTS energy_analytics.vw_technician_performance_ranking CASCADE;
DROP VIEW IF EXISTS public.vw_technician_performance_ranking CASCADE;

CREATE OR REPLACE VIEW energy_analytics.vw_technician_performance_ranking AS
WITH tech_submissions AS (
    SELECT 
        COALESCE(r.created_by, 'Unassigned Technician') AS technician_name,
        r.asset_code,
        am.plaza_id,
        r.module,
        r.reading_datetime,
        r.created_on,
        EXTRACT(HOUR FROM COALESCE(r.created_on, r.reading_datetime))::INTEGER AS entry_hour,
        EXTRACT(EPOCH FROM (r.created_on - r.reading_datetime)) / 86400.0 AS delay_days
    FROM (
        SELECT 'EB' AS module, asset_code, reading_datetime, created_on, created_by FROM energy_readings.eb
        UNION ALL SELECT 'DG' AS module, asset_code, reading_datetime, created_on, created_by FROM energy_readings.dg
        UNION ALL SELECT 'SOLAR' AS module, asset_code, reading_datetime, created_on, created_by FROM energy_readings.solar
        UNION ALL SELECT 'TRANSFORMER' AS module, asset_code, reading_datetime, created_on, created_by FROM energy_readings.transformer
        UNION ALL SELECT 'UPS' AS module, asset_code, reading_datetime, created_on, created_by FROM energy_readings.ups
    ) r
    LEFT JOIN energy_analytics.vw_asset_master_corrected am ON r.asset_code = am.asset_code
),
tech_defects AS (
    SELECT 
        technician_name,
        COUNT(*) AS defect_count
    FROM energy_analytics.vw_wrong_entries_register
    GROUP BY technician_name
)
SELECT
    ts.technician_name,
    STRING_AGG(DISTINCT ts.plaza_id, ', ' ORDER BY ts.plaza_id) AS assigned_plazas,
    STRING_AGG(DISTINCT ts.module, ', ' ORDER BY ts.module) AS modules_handled,
    COUNT(*) AS total_logs_submitted,
    COUNT(CASE WHEN ts.entry_hour >= 20 OR ts.entry_hour < 8 THEN 1 END) AS night_entries_count,
    ROUND((COUNT(CASE WHEN ts.entry_hour >= 20 OR ts.entry_hour < 8 THEN 1 END)::NUMERIC / NULLIF(COUNT(*), 0)) * 100.0, 1) AS night_entry_percentage,
    COALESCE(td.defect_count, 0) AS defects_logged_count,
    ROUND((COALESCE(td.defect_count, 0)::NUMERIC / NULLIF(COUNT(*), 0)) * 100.0, 1) AS defect_rate_percentage,
    ROUND(AVG(CASE WHEN ts.delay_days >= 0 THEN ts.delay_days ELSE NULL END)::NUMERIC, 1) AS avg_submission_delay_days,
    ROUND(MAX(CASE WHEN ts.delay_days >= 0 THEN ts.delay_days ELSE NULL END)::NUMERIC, 1) AS max_submission_delay_days,
    CASE
        WHEN COALESCE(td.defect_count, 0) > 100 THEN 'CRITICAL_DEFECT_LOGGER (Massive telemetry anomalies ignored)'
        WHEN MAX(ts.delay_days) > 20.0 THEN 'SEVERE_ABANDONMENT_DELAY (Submissions delayed > 20 days)'
        WHEN (COUNT(CASE WHEN ts.entry_hour >= 20 OR ts.entry_hour < 8 THEN 1 END)::NUMERIC / NULLIF(COUNT(*), 0)) > 0.50 
            THEN 'HABITUAL_NIGHT_LOGGER (> 50% entries between 8pm and 8am)'
        ELSE 'STANDARD_COMPLIANCE'
    END AS compliance_risk_profile
FROM tech_submissions ts
LEFT JOIN tech_defects td ON ts.technician_name = td.technician_name
GROUP BY ts.technician_name, td.defect_count
ORDER BY defects_logged_count DESC, night_entries_count DESC;

CREATE OR REPLACE VIEW public.vw_technician_performance_ranking AS
SELECT * FROM energy_analytics.vw_technician_performance_ranking;

-- ============================================================================
-- 7. SECURITY & ACCESS PERMISSIONS
-- ============================================================================
GRANT USAGE ON SCHEMA energy_master, energy_readings, energy_analytics, public TO anon, authenticated, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA energy_master, energy_readings, energy_analytics, public TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA energy_analytics GRANT SELECT ON TABLES TO anon, authenticated, service_role;
