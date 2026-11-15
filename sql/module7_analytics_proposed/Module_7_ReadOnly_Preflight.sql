-- Module 7 read-only preflight and post-deployment validation.
-- This file contains SELECTs only; no schema/view/data changes.

-- 1. Verify new public view names are available before deployment.
WITH expected(view_name) AS (
    VALUES
        ('vw_dg71_interval_classification'), ('vw_dg71_runtime_interval'),
        ('vw_dg71_diesel_interval'), ('vw_dg71_electrical_reading'),
        ('vw_dg71_entry_audit'), ('vw_dg71_record_quality'),
        ('vw_dg71_daily_summary'), ('vw_dg71_monthly_summary'),
        ('vw_dg71_yearly_summary'), ('vw_dg71_analytics_summary'),
        ('vw_eb71_interval_detail'), ('vw_eb71_record_quality'),
        ('vw_eb71_entry_audit'), ('vw_eb71_daily_summary'),
        ('vw_eb71_monthly_summary'), ('vw_eb71_yearly_summary'),
        ('vw_eb71_analytics_summary'), ('vw_eb71_asset_latest_reading'),
        ('vw_sol71_reading_detail'), ('vw_sol71_interval_reading'),
        ('vw_sol71_record_quality'), ('vw_sol71_entry_audit'),
        ('vw_sol71_daily_summary'), ('vw_sol71_monthly_summary'),
        ('vw_sol71_yearly_summary'), ('vw_sol71_analytics_summary'),
        ('vw_sol71_asset_latest_reading'),
        ('vw_trf71_reading_detail'), ('vw_trf71_electrical_reading'),
        ('vw_trf71_record_quality'), ('vw_trf71_entry_audit'),
        ('vw_trf71_daily_summary'), ('vw_trf71_monthly_summary'),
        ('vw_trf71_yearly_summary'), ('vw_trf71_analytics_summary'),
        ('vw_trf71_asset_latest_reading'),
        ('vw_ups71_reading_detail'), ('vw_ups71_record_quality'),
        ('vw_ups71_entry_audit'), ('vw_ups71_daily_summary'),
        ('vw_ups71_monthly_summary'), ('vw_ups71_yearly_summary'),
        ('vw_ups71_analytics_summary'), ('vw_ups71_asset_latest_reading'),
        ('vw_m7_record_quality'), ('vw_m7_entry_audit'),
        ('vw_m7_exception_register'), ('vw_m7_night_entry_detail'),
        ('vw_m7_module_daily_quality_summary'),
        ('vw_m7_module_monthly_quality_summary'),
        ('vw_m7_module_yearly_quality_summary'), ('vw_m7_plaza_summary'),
        ('vw_m7_technician_summary'), ('vw_m7_asset_latest_reading'),
        ('vw_m7_submodule_summary')
)
SELECT e.view_name, n.nspname IS NOT NULL AS public_schema_exists, c.relkind AS existing_relation_kind
FROM expected AS e
LEFT JOIN pg_namespace AS n ON n.nspname = 'public'
LEFT JOIN pg_class AS c ON c.relnamespace = n.oid AND c.relname = e.view_name
ORDER BY e.view_name;

-- 2. Verify direct source columns used by the module views.
WITH required(table_schema, table_name, column_name) AS (
    VALUES
        ('energy_master', 'asset', 'asset_id'), ('energy_master', 'asset', 'asset_code'),
        ('energy_master', 'asset', 'asset_name'), ('energy_master', 'asset', 'plaza_id'),
        ('energy_master', 'asset', 'source_type'), ('energy_master', 'asset', 'capacity_kva'),
        ('energy_readings', 'dg', 'reading_id'), ('energy_readings', 'dg', 'asset_id'),
        ('energy_readings', 'dg', 'asset_code'), ('energy_readings', 'dg', 'reading_datetime'),
        ('energy_readings', 'dg', 'status'), ('energy_readings', 'dg', 'kva'),
        ('energy_readings', 'dg', 'kw'), ('energy_readings', 'dg', 'voltage_ry'),
        ('energy_readings', 'dg', 'voltage_yb'), ('energy_readings', 'dg', 'voltage_br'),
        ('energy_readings', 'dg', 'current_r'), ('energy_readings', 'dg', 'current_y'),
        ('energy_readings', 'dg', 'current_b'), ('energy_readings', 'dg', 'diesel_level'),
        ('energy_readings', 'dg', 'diesel_topup'), ('energy_readings', 'dg', 'load_percentage'),
        ('energy_readings', 'dg', 'cumulative_kwh'),
        ('energy_readings', 'dg', 'cumulative_running_hours'),
        ('energy_readings', 'dg', 'interval_kwh'),
        ('energy_readings', 'dg', 'interval_running_hours'),
        ('energy_readings', 'dg', 'rpm'), ('energy_readings', 'dg', 'pf'),
        ('energy_readings', 'dg', 'created_by'), ('energy_readings', 'dg', 'created_on'),
        ('energy_readings', 'dg', 'created_at'), ('energy_readings', 'dg', 'remarks'),
        ('energy_readings', 'dg', 'data_quality_status'),
        ('energy_readings', 'eb', 'reading_id'), ('energy_readings', 'eb', 'asset_id'),
        ('energy_readings', 'eb', 'asset_code'), ('energy_readings', 'eb', 'reading_datetime'),
        ('energy_readings', 'eb', 'cumulative_kwh'), ('energy_readings', 'eb', 'cumulative_kvah'),
        ('energy_readings', 'eb', 'interval_kwh'), ('energy_readings', 'eb', 'interval_kvah'),
        ('energy_readings', 'eb', 'pf'), ('energy_readings', 'eb', 'maximum_demand'),
        ('energy_readings', 'eb', 'created_by'), ('energy_readings', 'eb', 'created_on'),
        ('energy_readings', 'eb', 'created_at'), ('energy_readings', 'eb', 'remarks'),
        ('energy_readings', 'eb', 'location'), ('energy_readings', 'eb', 'data_quality_status'),
        ('energy_readings', 'solar', 'reading_id'), ('energy_readings', 'solar', 'asset_id'),
        ('energy_readings', 'solar', 'asset_code'), ('energy_readings', 'solar', 'reading_datetime'),
        ('energy_readings', 'solar', 'created_by'), ('energy_readings', 'solar', 'created_on'),
        ('energy_readings', 'solar', 'created_at'), ('energy_readings', 'solar', 'remarks'),
        ('energy_readings', 'solar', 'location'), ('energy_readings', 'solar', 'data_quality_status'),
        ('energy_readings', 'transformer', 'reading_id'),
        ('energy_readings', 'transformer', 'asset_id'), ('energy_readings', 'transformer', 'asset_code'),
        ('energy_readings', 'transformer', 'reading_datetime'),
        ('energy_readings', 'transformer', 'primary_v_ry'),
        ('energy_readings', 'transformer', 'primary_v_yb'),
        ('energy_readings', 'transformer', 'primary_v_br'),
        ('energy_readings', 'transformer', 'secondary_v_ry'),
        ('energy_readings', 'transformer', 'secondary_v_yb'),
        ('energy_readings', 'transformer', 'secondary_v_br'),
        ('energy_readings', 'transformer', 'primary_i_r'),
        ('energy_readings', 'transformer', 'primary_i_y'),
        ('energy_readings', 'transformer', 'primary_i_b'),
        ('energy_readings', 'transformer', 'secondary_i_r'),
        ('energy_readings', 'transformer', 'secondary_i_y'),
        ('energy_readings', 'transformer', 'secondary_i_b'),
        ('energy_readings', 'transformer', 'oil_temperature'),
        ('energy_readings', 'transformer', 'winding_temperature'),
        ('energy_readings', 'transformer', 'pf'), ('energy_readings', 'transformer', 'created_by'),
        ('energy_readings', 'transformer', 'created_on'), ('energy_readings', 'transformer', 'created_at'),
        ('energy_readings', 'transformer', 'remarks'), ('energy_readings', 'transformer', 'location'),
        ('energy_readings', 'transformer', 'data_quality_status'),
        ('energy_readings', 'ups', 'reading_id'), ('energy_readings', 'ups', 'asset_id'),
        ('energy_readings', 'ups', 'asset_code'), ('energy_readings', 'ups', 'reading_datetime'),
        ('energy_readings', 'ups', 'output_voltage'), ('energy_readings', 'ups', 'output_current'),
        ('energy_readings', 'ups', 'output_frequency'), ('energy_readings', 'ups', 'battery_vdc'),
        ('energy_readings', 'ups', 'battery_temperature'), ('energy_readings', 'ups', 'rectifier_voltage'),
        ('energy_readings', 'ups', 'created_by'), ('energy_readings', 'ups', 'created_on'),
        ('energy_readings', 'ups', 'created_at'), ('energy_readings', 'ups', 'remarks'),
        ('energy_readings', 'ups', 'location'), ('energy_readings', 'ups', 'data_quality_status')
)
SELECT r.table_schema, r.table_name, r.column_name
FROM required AS r
LEFT JOIN information_schema.columns AS c
    ON c.table_schema = r.table_schema AND c.table_name = r.table_name AND c.column_name = r.column_name
WHERE c.column_name IS NULL
ORDER BY r.table_schema, r.table_name, r.column_name;

-- 3. Inspect timestamp types and optional energy-field aliases.
SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE (table_schema = 'energy_readings' AND table_name IN ('dg', 'eb', 'solar', 'transformer', 'ups')
       AND column_name IN ('reading_datetime', 'created_on', 'cumulative_kwh', 'unit_generated_in_kwh',
                           'interval_kwh', 'diesel_topup', 'diesel_top_up'))
ORDER BY table_schema, table_name, column_name;

-- 4. Optional audit source check. A missing schema/table returns NULL.
SELECT to_regclass('energy_audit.audit_log') AS audit_log_relation;

-- 5. HH.MM runtime check: 16.45 means 16 hours 45 minutes = 1005 minutes.
WITH sample(value_hh_mm) AS (VALUES (16.45::numeric))
SELECT
    TRUNC(value_hh_mm)::integer AS hours_part,
    ROUND((value_hh_mm - TRUNC(value_hh_mm)) * 100)::integer AS minutes_part,
    (TRUNC(value_hh_mm) * 60 + ROUND((value_hh_mm - TRUNC(value_hh_mm)) * 100))::integer
        AS total_minutes
FROM sample;

-- 6. Night window edge check in IST: 22:00 inclusive and 06:00 exclusive.
WITH samples(local_timestamp, expected_night) AS (
    VALUES ('2026-10-01 21:59:59+05:30'::timestamptz, FALSE),
           ('2026-10-01 22:00:00+05:30'::timestamptz, TRUE),
           ('2026-10-02 05:59:59+05:30'::timestamptz, TRUE),
           ('2026-10-02 06:00:00+05:30'::timestamptz, FALSE)
)
SELECT local_timestamp, expected_night,
       ((local_timestamp AT TIME ZONE 'Asia/Kolkata')::time >= TIME '22:00'
        OR (local_timestamp AT TIME ZONE 'Asia/Kolkata')::time < TIME '06:00') AS actual_night
FROM samples;

-- 7. Post-deployment universal reconciliation checks.
SELECT source_type,
       SUM(total_records) AS total_records,
       SUM(valid_records) AS valid_records,
       SUM(exception_records) AS exception_records,
       SUM(total_records) - SUM(valid_records) - SUM(exception_records) AS reconciliation_difference
FROM public.vw_m7_record_quality
GROUP BY source_type
ORDER BY source_type;

SELECT * FROM public.vw_m7_record_quality
WHERE total_records <> valid_records + exception_records OR reconciliation_difference <> 0;

SELECT * FROM public.vw_m7_module_daily_quality_summary
WHERE total_records <> valid_records + exception_records OR reconciliation_difference <> 0;

SELECT * FROM public.vw_m7_module_monthly_quality_summary
WHERE total_records <> valid_records + exception_records OR reconciliation_difference <> 0;

SELECT * FROM public.vw_m7_module_yearly_quality_summary
WHERE total_records <> valid_records + exception_records OR reconciliation_difference <> 0;
