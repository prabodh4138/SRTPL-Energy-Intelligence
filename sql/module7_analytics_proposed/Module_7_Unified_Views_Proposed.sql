-- Module 7 shared views across DG, EB, Solar, Transformer, and UPS.
-- Run after all five *_Module_7_Analytics_Proposed.sql files.
-- Adds new public.vw_m7_* views only; no schemas/tables/data are modified.

CREATE VIEW public.vw_m7_record_quality AS
SELECT
    'DG'::text AS source_type,
    q.reading_id, q.asset_id, q.asset_code, q.asset_name, q.plaza_id,
    COALESCE('ID:' || q.asset_id::text, 'CODE:' || q.asset_code, 'ROW:' || q.reading_id::text)
        AS asset_partition_key,
    q.operational_date, q.reading_datetime,
    q.total_records, q.valid_records, q.exception_records, q.reconciliation_difference,
    q.source_data_quality_status::text AS source_data_quality_status,
    q.analytics_quality_class::text AS analytics_quality_class,
    q.analytics_exception_reasons::text AS analytics_exception_reasons
FROM public.vw_dg71_record_quality AS q
UNION ALL
SELECT
    'EB'::text, q.reading_id, q.asset_id, q.asset_code, q.asset_name, q.plaza_id,
    COALESCE('ID:' || q.asset_id::text, 'CODE:' || q.asset_code, 'ROW:' || q.reading_id::text),
    q.operational_date, q.reading_datetime,
    q.total_records, q.valid_records, q.exception_records, q.reconciliation_difference,
    q.source_data_quality_status::text, q.analytics_quality_class::text,
    q.analytics_exception_reasons::text
FROM public.vw_eb71_record_quality AS q
UNION ALL
SELECT
    'SOLAR'::text, q.reading_id, q.asset_id, q.asset_code, q.asset_name, q.plaza_id,
    COALESCE('ID:' || q.asset_id::text, 'CODE:' || q.asset_code, 'ROW:' || q.reading_id::text),
    q.operational_date, q.reading_datetime,
    q.total_records, q.valid_records, q.exception_records, q.reconciliation_difference,
    q.source_data_quality_status::text, q.analytics_quality_class::text,
    q.analytics_exception_reasons::text
FROM public.vw_sol71_record_quality AS q
UNION ALL
SELECT
    'TRANSFORMER'::text, q.reading_id, q.asset_id, q.asset_code, q.asset_name, q.plaza_id,
    COALESCE('ID:' || q.asset_id::text, 'CODE:' || q.asset_code, 'ROW:' || q.reading_id::text),
    q.operational_date, q.reading_datetime,
    q.total_records, q.valid_records, q.exception_records, q.reconciliation_difference,
    q.source_data_quality_status::text, q.analytics_quality_class::text,
    q.analytics_exception_reasons::text
FROM public.vw_trf71_record_quality AS q
UNION ALL
SELECT
    'UPS'::text, q.reading_id, q.asset_id, q.asset_code, q.asset_name, q.plaza_id,
    COALESCE('ID:' || q.asset_id::text, 'CODE:' || q.asset_code, 'ROW:' || q.reading_id::text),
    q.operational_date, q.reading_datetime,
    q.total_records, q.valid_records, q.exception_records, q.reconciliation_difference,
    q.source_data_quality_status::text, q.analytics_quality_class::text,
    q.analytics_exception_reasons::text
FROM public.vw_ups71_record_quality AS q;

CREATE VIEW public.vw_m7_entry_audit AS
SELECT
    'DG'::text AS source_type, a.reading_id, a.asset_id, a.asset_code, a.asset_name, a.plaza_id,
    COALESCE('ID:' || a.asset_id::text, 'CODE:' || a.asset_code, 'ROW:' || a.reading_id::text)
        AS asset_partition_key,
    a.operational_date, a.reading_datetime, a.created_on, a.created_by,
    a.entry_delay, a.entry_delay_hours, a.negative_entry_delay_timestamp_anomaly,
    a.delayed_entry_24h_or_more, a.entry_within_24h,
    a.reading_datetime_night_indicator, a.created_on_night_indicator,
    a.analytics_quality_class::text AS analytics_quality_class
FROM public.vw_dg71_entry_audit AS a
UNION ALL
SELECT
    'EB'::text, a.reading_id, a.asset_id, a.asset_code, a.asset_name, a.plaza_id,
    COALESCE('ID:' || a.asset_id::text, 'CODE:' || a.asset_code, 'ROW:' || a.reading_id::text),
    a.operational_date, a.reading_datetime, a.created_on, a.created_by,
    a.entry_delay, a.entry_delay_hours, a.negative_entry_delay_timestamp_anomaly,
    a.delayed_entry_24h_or_more, a.entry_within_24h,
    a.reading_datetime_night_indicator, a.created_on_night_indicator,
    a.analytics_quality_class::text
FROM public.vw_eb71_entry_audit AS a
UNION ALL
SELECT
    'SOLAR'::text, a.reading_id, a.asset_id, a.asset_code, a.asset_name, a.plaza_id,
    COALESCE('ID:' || a.asset_id::text, 'CODE:' || a.asset_code, 'ROW:' || a.reading_id::text),
    a.operational_date, a.reading_datetime, a.created_on, a.created_by,
    a.entry_delay, a.entry_delay_hours, a.negative_entry_delay_timestamp_anomaly,
    a.delayed_entry_24h_or_more, a.entry_within_24h,
    a.reading_datetime_night_indicator, a.created_on_night_indicator,
    a.analytics_quality_class::text
FROM public.vw_sol71_entry_audit AS a
UNION ALL
SELECT
    'TRANSFORMER'::text, a.reading_id, a.asset_id, a.asset_code, a.asset_name, a.plaza_id,
    COALESCE('ID:' || a.asset_id::text, 'CODE:' || a.asset_code, 'ROW:' || a.reading_id::text),
    a.operational_date, a.reading_datetime, a.created_on, a.created_by,
    a.entry_delay, a.entry_delay_hours, a.negative_entry_delay_timestamp_anomaly,
    a.delayed_entry_24h_or_more, a.entry_within_24h,
    a.reading_datetime_night_indicator, a.created_on_night_indicator,
    a.analytics_quality_class::text
FROM public.vw_trf71_entry_audit AS a
UNION ALL
SELECT
    'UPS'::text, a.reading_id, a.asset_id, a.asset_code, a.asset_name, a.plaza_id,
    COALESCE('ID:' || a.asset_id::text, 'CODE:' || a.asset_code, 'ROW:' || a.reading_id::text),
    a.operational_date, a.reading_datetime, a.created_on, a.created_by,
    a.entry_delay, a.entry_delay_hours, a.negative_entry_delay_timestamp_anomaly,
    a.delayed_entry_24h_or_more, a.entry_within_24h,
    a.reading_datetime_night_indicator, a.created_on_night_indicator,
    a.analytics_quality_class::text
FROM public.vw_ups71_entry_audit AS a;

CREATE VIEW public.vw_m7_exception_register AS
SELECT
    q.source_type, q.reading_id, q.asset_id, q.asset_code, q.asset_name, q.plaza_id,
    q.asset_partition_key, q.operational_date, q.reading_datetime,
    q.source_data_quality_status, q.analytics_quality_class,
    q.analytics_exception_reasons,
    e.created_on, e.created_by, e.entry_delay_hours,
    e.delayed_entry_24h_or_more, e.reading_datetime_night_indicator,
    e.created_on_night_indicator
FROM public.vw_m7_record_quality AS q
LEFT JOIN public.vw_m7_entry_audit AS e
    ON e.source_type = q.source_type AND e.reading_id = q.reading_id
WHERE q.analytics_quality_class = 'EXCEPTION';

CREATE VIEW public.vw_m7_night_entry_detail AS
SELECT *
FROM public.vw_m7_entry_audit
WHERE reading_datetime_night_indicator IS TRUE
   OR created_on_night_indicator IS TRUE;

CREATE VIEW public.vw_m7_module_daily_quality_summary AS
SELECT
    source_type, plaza_id, operational_date,
    DATE_TRUNC('month', operational_date::timestamp)::date AS operational_month,
    EXTRACT(YEAR FROM operational_date)::integer AS operational_year,
    COUNT(*)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(reconciliation_difference)::bigint AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(COUNT(*), 0) AS observed_record_availability_pct,
    COUNT(DISTINCT asset_partition_key)::bigint AS assets_reporting
FROM public.vw_m7_record_quality
GROUP BY source_type, plaza_id, operational_date;

CREATE VIEW public.vw_m7_module_monthly_quality_summary AS
SELECT
    source_type, plaza_id, operational_month,
    COUNT(DISTINCT operational_date)::bigint AS observed_days,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(reconciliation_difference)::bigint AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
    MAX(assets_reporting)::bigint AS maximum_assets_reporting_on_day
FROM public.vw_m7_module_daily_quality_summary
GROUP BY source_type, plaza_id, operational_month;

CREATE VIEW public.vw_m7_module_yearly_quality_summary AS
SELECT
    source_type, plaza_id, operational_year,
    COUNT(DISTINCT operational_date)::bigint AS observed_days,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(reconciliation_difference)::bigint AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
    MAX(assets_reporting)::bigint AS maximum_assets_reporting_on_day
FROM public.vw_m7_module_daily_quality_summary
GROUP BY source_type, plaza_id, operational_year;

CREATE VIEW public.vw_m7_plaza_summary AS
WITH combined AS (
    SELECT
        q.source_type, q.reading_id, q.asset_partition_key, q.plaza_id,
        q.total_records, q.valid_records, q.exception_records,
        q.analytics_quality_class,
        e.created_on, e.created_by, e.entry_delay, e.delayed_entry_24h_or_more,
        e.negative_entry_delay_timestamp_anomaly,
        e.reading_datetime_night_indicator, e.created_on_night_indicator
    FROM public.vw_m7_record_quality AS q
    LEFT JOIN public.vw_m7_entry_audit AS e
        ON e.source_type = q.source_type AND e.reading_id = q.reading_id
)
SELECT
    source_type, plaza_id,
    COUNT(*)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    COUNT(*) - SUM(valid_records) - SUM(exception_records) AS reconciliation_difference,
    100.0 * SUM(exception_records) / NULLIF(COUNT(*), 0) AS exception_percentage,
    COUNT(DISTINCT asset_partition_key)::bigint AS assets_monitored,
    COUNT(*) FILTER (WHERE delayed_entry_24h_or_more IS TRUE)::bigint AS delayed_entry_count,
    COUNT(*) FILTER (WHERE entry_delay >= INTERVAL '0 seconds')::bigint AS entry_delay_eligible_count,
    COUNT(*) FILTER (WHERE negative_entry_delay_timestamp_anomaly IS TRUE)::bigint
        AS negative_entry_delay_timestamp_anomaly_count,
    COUNT(*) FILTER (WHERE reading_datetime_night_indicator IS TRUE)::bigint AS night_reading_count,
    COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE)::bigint AS night_entry_count,
    100.0 * COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE)
        / NULLIF(COUNT(*) FILTER (WHERE created_on IS NOT NULL), 0) AS night_entry_percentage,
    COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE AND analytics_quality_class = 'VALID')::bigint
        AS valid_night_entry_count,
    COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE AND analytics_quality_class = 'EXCEPTION')::bigint
        AS exception_night_entry_count
FROM combined
GROUP BY source_type, plaza_id;

CREATE VIEW public.vw_m7_technician_summary AS
SELECT
    e.source_type,
    e.plaza_id,
    COALESCE(NULLIF(BTRIM(e.created_by), ''), 'Unassigned') AS technician_name,
    COUNT(*)::bigint AS total_records,
    COUNT(*) FILTER (WHERE e.created_on_night_indicator IS TRUE)::bigint AS night_entries_count,
    100.0 * COUNT(*) FILTER (WHERE e.created_on_night_indicator IS TRUE)
        / NULLIF(COUNT(*) FILTER (WHERE e.created_on IS NOT NULL), 0) AS night_entry_percentage,
    COUNT(*) FILTER (WHERE e.delayed_entry_24h_or_more IS TRUE)::bigint AS delayed_entry_count,
    COUNT(*) FILTER (WHERE e.negative_entry_delay_timestamp_anomaly IS TRUE)::bigint
        AS negative_entry_delay_timestamp_anomaly_count,
    COUNT(*) FILTER (WHERE e.analytics_quality_class = 'VALID')::bigint AS valid_records,
    COUNT(*) FILTER (WHERE e.analytics_quality_class = 'EXCEPTION')::bigint AS exception_records,
    AVG(e.entry_delay_hours) FILTER (WHERE e.entry_delay >= INTERVAL '0 seconds') AS average_entry_delay_hours,
    MAX(e.entry_delay_hours) FILTER (WHERE e.entry_delay >= INTERVAL '0 seconds') AS maximum_entry_delay_hours
FROM public.vw_m7_entry_audit AS e
GROUP BY e.source_type, e.plaza_id, COALESCE(NULLIF(BTRIM(e.created_by), ''), 'Unassigned');

CREATE VIEW public.vw_m7_asset_latest_reading AS
WITH all_readings AS (
    SELECT
        'DG'::text AS source_type, d.reading_id, d.asset_id, d.asset_code, d.asset_name, d.plaza_id,
        d.asset_partition_key, d.reading_datetime, d.operational_date,
        d.cumulative_kwh::numeric AS cumulative_kwh, d.source_interval_kwh::numeric AS interval_kwh,
        d.pf::numeric AS power_factor, NULL::numeric AS output_voltage, NULL::numeric AS battery_vdc,
        rt.cumulative_runtime_hh_mm::text AS cumulative_running_hours_hh_mm,
        d.source_data_quality_status::text AS source_data_quality_status, d.created_by, d.created_on
    FROM public.vw_dg71_interval_classification AS d
    LEFT JOIN public.vw_dg71_runtime_interval AS rt USING (reading_id)
    UNION ALL
    SELECT
        'EB', e.reading_id, e.asset_id, e.asset_code, e.asset_name, e.plaza_id,
        e.asset_partition_key, e.reading_datetime, e.operational_date,
        e.cumulative_kwh::numeric, e.interval_kwh::numeric, e.pf::numeric,
        NULL::numeric, NULL::numeric, NULL::text, e.source_data_quality_status::text, e.created_by, e.created_on
    FROM public.vw_eb71_interval_detail AS e
    UNION ALL
    SELECT
        'SOLAR', s.reading_id, s.asset_id, s.asset_code, s.asset_name, s.plaza_id,
        s.asset_partition_key, s.reading_datetime, s.operational_date,
        s.cumulative_kwh::numeric, s.interval_kwh::numeric, NULL::numeric,
        NULL::numeric, NULL::numeric, NULL::text, s.source_data_quality_status::text, s.created_by, s.created_on
    FROM public.vw_sol71_reading_detail AS s
    UNION ALL
    SELECT
        'TRANSFORMER', t.reading_id, t.asset_id, t.asset_code, t.asset_name, t.plaza_id,
        t.asset_partition_key, t.reading_datetime, t.operational_date,
        t.cumulative_kwh_value::numeric, t.interval_kwh_value::numeric, t.pf::numeric,
        NULL::numeric, NULL::numeric, NULL::text, t.source_data_quality_status::text, t.created_by, t.created_on
    FROM public.vw_trf71_reading_detail AS t
    UNION ALL
    SELECT
        'UPS', u.reading_id, u.asset_id, u.asset_code, u.asset_name, u.plaza_id,
        u.asset_partition_key, u.reading_datetime, u.operational_date,
        NULL::numeric, NULL::numeric, NULL::numeric,
        u.output_voltage::numeric, u.battery_vdc::numeric, NULL::text,
        u.source_data_quality_status::text, u.created_by, u.created_on
    FROM public.vw_ups71_reading_detail AS u
), stats AS (
    SELECT
        r.source_type,
        r.asset_partition_key,
        MIN(r.reading_datetime) AS start_date,
        MAX(r.reading_datetime) AS last_date,
        COUNT(r.reading_id)::bigint AS total_readings
    FROM all_readings r
    GROUP BY r.source_type, r.asset_partition_key
), ranked AS (
    SELECT
        r.*,
        ROW_NUMBER() OVER (
            PARTITION BY r.source_type, r.asset_partition_key
            ORDER BY r.reading_datetime DESC NULLS LAST, r.reading_id DESC
        ) AS latest_rank
    FROM all_readings AS r
)
SELECT
    a.source_type,
    a.asset_id,
    a.asset_code,
    a.asset_name,
    a.plaza_id,
    a.capacity_kva,
    s.start_date,
    s.last_date,
    COALESCE(s.total_readings, 0)::bigint AS total_readings,
    r.reading_id,
    r.reading_datetime,
    r.operational_date,
    r.cumulative_kwh AS latest_cumulative_kwh,
    r.interval_kwh AS latest_interval_kwh,
    r.power_factor AS latest_power_factor,
    r.output_voltage AS latest_output_voltage,
    r.battery_vdc AS latest_battery_vdc,
    r.cumulative_running_hours_hh_mm,
    r.source_data_quality_status,
    r.created_by,
    r.created_on,
    r.reading_id IS NOT NULL AS has_reading
FROM energy_master.asset AS a
LEFT JOIN ranked AS r
    ON (r.asset_id = a.asset_id OR (r.asset_id IS NULL AND r.asset_code = a.asset_code))
   AND r.source_type = UPPER(a.source_type)
   AND r.latest_rank = 1
LEFT JOIN stats AS s
    ON (s.asset_partition_key = r.asset_partition_key OR s.asset_partition_key = COALESCE('ID:' || a.asset_id::text, 'CODE:' || a.asset_code))
   AND s.source_type = UPPER(a.source_type)
WHERE UPPER(a.source_type) IN ('DG', 'EB', 'SOLAR', 'TRANSFORMER', 'UPS');

CREATE VIEW public.vw_m7_submodule_summary AS
SELECT
    source_type,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(reconciliation_difference)::bigint AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
    COUNT(DISTINCT asset_partition_key)::bigint AS assets_with_records
FROM public.vw_m7_record_quality
GROUP BY source_type;
