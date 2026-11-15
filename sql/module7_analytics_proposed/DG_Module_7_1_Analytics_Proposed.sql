-- SRTPL Energy Command Center - Module 7.1 DG Analytics
-- PROPOSAL ONLY. Nothing in this file has been executed against a database.
-- PostgreSQL / Supabase. Adds new, versioned views only; no DROP, REPLACE,
-- table writes, or changes to existing source objects are included.
-- Preflight the target schema, columns, and view-name collisions before use.

CREATE VIEW public.vw_dg71_interval_classification AS
WITH raw_readings AS (
    SELECT
        d.reading_id,
        d.asset_id,
        COALESCE(d.asset_code, a.asset_code) AS asset_code,
        a.asset_name,
        a.plaza_id,
        a.capacity_kva AS registered_capacity_kva,
        d.reading_datetime,
        (d.reading_datetime AT TIME ZONE 'Asia/Kolkata')::date AS operational_date,
        d.status AS operational_status,
        d.kva,
        d.kw,
        d.voltage_ry,
        d.voltage_yb,
        d.voltage_br,
        d.current_r,
        d.current_y,
        d.current_b,
        d.diesel_level AS diesel_level_l,
        d.diesel_topup AS diesel_topup_l,
        d.load_percentage,
        d.cumulative_kwh,
        d.cumulative_running_hours,
        d.interval_kwh AS source_interval_kwh,
        d.interval_running_hours AS source_interval_running_hours,
        d.rpm,
        d.pf,
        d.created_by,
        d.created_on,
        d.created_at,
        d.remarks,
        d.data_quality_status AS source_data_quality_status,
        CASE
            WHEN UPPER(BTRIM(COALESCE(d.data_quality_status, ''))) = 'VALID' THEN 'VALID'
            ELSE 'EXCEPTION'
        END AS source_quality_class
    FROM energy_readings.dg AS d
    LEFT JOIN energy_master.asset AS a
        ON a.asset_id = d.asset_id
),
sequenced_readings AS (
    SELECT
        r.*,
        COALESCE(
            'ID:' || r.asset_id,
            'CODE:' || r.asset_code,
            'ROW:' || r.reading_id::text
        ) AS asset_partition_key,
        ROW_NUMBER() OVER w AS reading_sequence,
        LAG(r.reading_id) OVER w AS previous_reading_id,
        LAG(r.reading_datetime) OVER w AS previous_reading_datetime,
        LAG(r.cumulative_kwh) OVER w AS previous_cumulative_kwh,
        LAG(r.cumulative_running_hours) OVER w AS previous_cumulative_running_hours,
        LAG(r.diesel_level_l) OVER w AS previous_diesel_level_l,
        LAG(r.diesel_topup_l) OVER w AS previous_diesel_topup_l,
        LAG(r.source_quality_class) OVER w AS previous_source_quality_class
    FROM raw_readings AS r
    WINDOW w AS (
        PARTITION BY COALESCE(
            'ID:' || r.asset_id,
            'CODE:' || r.asset_code,
            'ROW:' || r.reading_id::text
        )
        ORDER BY r.reading_datetime, r.reading_id
    )
),
runtime_values AS (
    SELECT
        s.*,
        CASE
            WHEN s.cumulative_running_hours >= 0
             AND ROUND((s.cumulative_running_hours - TRUNC(s.cumulative_running_hours)) * 100)
                    BETWEEN 0 AND 59
            THEN (TRUNC(s.cumulative_running_hours) * 60
                 + ROUND((s.cumulative_running_hours - TRUNC(s.cumulative_running_hours)) * 100))::bigint
        END AS cumulative_runtime_minutes,
        CASE
            WHEN s.previous_cumulative_running_hours >= 0
             AND ROUND((s.previous_cumulative_running_hours - TRUNC(s.previous_cumulative_running_hours)) * 100)
                    BETWEEN 0 AND 59
            THEN (TRUNC(s.previous_cumulative_running_hours) * 60
                 + ROUND((s.previous_cumulative_running_hours - TRUNC(s.previous_cumulative_running_hours)) * 100))::bigint
        END AS previous_cumulative_runtime_minutes
    FROM sequenced_readings AS s
),
interval_values AS (
    SELECT
        r.*,
        r.cumulative_kwh - r.previous_cumulative_kwh AS generation_delta_kwh,
        r.cumulative_runtime_minutes - r.previous_cumulative_runtime_minutes AS runtime_interval_minutes,
        r.previous_diesel_level_l
            + COALESCE(r.previous_diesel_topup_l, 0::numeric)
            - r.diesel_level_l AS fuel_reconciliation_l
    FROM runtime_values AS r
),
interval_flags AS (
    SELECT
        i.*,
        CASE
            WHEN i.runtime_interval_minutes IS NOT NULL
             AND i.runtime_interval_minutes >= 0
             AND i.source_quality_class = 'VALID'
             AND i.previous_source_quality_class = 'VALID'
            THEN TRUE ELSE FALSE
        END AS is_validated_runtime_interval,
        CASE
            WHEN i.runtime_interval_minutes > 0
             AND i.cumulative_runtime_minutes IS NOT NULL
             AND i.previous_cumulative_runtime_minutes IS NOT NULL
             AND i.source_quality_class = 'VALID'
             AND i.previous_source_quality_class = 'VALID'
            THEN TRUE ELSE FALSE
        END AS has_positive_validated_runtime,
        CASE
            WHEN i.generation_delta_kwh > 0
             AND i.runtime_interval_minutes > 0
             AND i.cumulative_runtime_minutes IS NOT NULL
             AND i.previous_cumulative_runtime_minutes IS NOT NULL
             AND i.source_quality_class = 'VALID'
             AND i.previous_source_quality_class = 'VALID'
            THEN TRUE ELSE FALSE
        END AS has_confirmed_generation,
        CASE
            WHEN i.fuel_reconciliation_l > 0
             AND NOT (
                 i.generation_delta_kwh > 0
                 AND i.runtime_interval_minutes > 0
                 AND i.cumulative_runtime_minutes IS NOT NULL
                 AND i.previous_cumulative_runtime_minutes IS NOT NULL
                 AND i.source_quality_class = 'VALID'
                 AND i.previous_source_quality_class = 'VALID'
             )
            THEN TRUE ELSE FALSE
        END AS positive_fuel_without_confirmed_generation_or_runtime,
        CASE
            WHEN i.cumulative_running_hours IS NOT NULL
             AND i.cumulative_runtime_minutes IS NULL
            THEN TRUE ELSE FALSE
        END AS current_runtime_encoding_invalid
    FROM interval_values AS i
),
classified_rows AS (
    SELECT
        f.*,
        CASE
            WHEN f.reading_sequence = 1 THEN 'FIRST_READING'
            WHEN f.generation_delta_kwh IS NULL THEN 'UNUSABLE_INTERVAL'
            WHEN f.generation_delta_kwh < 0 THEN 'NEGATIVE_GENERATION'
            WHEN f.generation_delta_kwh = 0 THEN 'ZERO_GENERATION'
            WHEN f.has_confirmed_generation THEN 'CONFIRMED_GENERATION'
            WHEN f.generation_delta_kwh > 0 THEN 'UNVERIFIED_GENERATION'
            ELSE 'UNUSABLE_INTERVAL'
        END AS generation_classification,
        CASE
            WHEN f.source_quality_class <> 'VALID'
              OR f.current_runtime_encoding_invalid
              OR f.generation_delta_kwh < 0
              OR f.runtime_interval_minutes < 0
              OR f.fuel_reconciliation_l < 0
              OR f.positive_fuel_without_confirmed_generation_or_runtime
            THEN 'EXCEPTION'
            ELSE 'VALID'
        END AS analytics_quality_class
    FROM interval_flags AS f
)
SELECT
    c.*,
    CASE
        WHEN c.analytics_quality_class = 'VALID' AND c.has_confirmed_generation
        THEN c.generation_delta_kwh
    END AS confirmed_generation_kwh,
    CASE
        WHEN c.analytics_quality_class = 'VALID' AND c.is_validated_runtime_interval
        THEN c.runtime_interval_minutes
    END AS validated_runtime_interval_minutes,
    CONCAT_WS(
        '; ',
        CASE WHEN c.source_quality_class <> 'VALID' THEN 'SOURCE_STATUS_EXCEPTION' END,
        CASE WHEN c.current_runtime_encoding_invalid THEN 'INVALID_HH_MM_RUNTIME_ENCODING' END,
        CASE WHEN c.generation_delta_kwh < 0 THEN 'NEGATIVE_GENERATION_DELTA' END,
        CASE WHEN c.runtime_interval_minutes < 0 THEN 'NEGATIVE_RUNTIME_DELTA' END,
        CASE WHEN c.fuel_reconciliation_l < 0 THEN 'NEGATIVE_FUEL_RECONCILIATION' END,
        CASE WHEN c.positive_fuel_without_confirmed_generation_or_runtime
             THEN 'FUEL_CONSUMPTION_WITHOUT_CONFIRMED_GENERATION_AND_RUNTIME' END
    ) AS analytics_exception_reasons
FROM classified_rows AS c;

CREATE VIEW public.vw_dg71_runtime_interval AS
SELECT
    i.reading_id,
    i.asset_id,
    i.asset_code,
    i.asset_name,
    i.plaza_id,
    i.operational_date,
    i.reading_datetime,
    i.previous_reading_id,
    i.cumulative_running_hours AS source_cumulative_running_hours_hh_mm,
    i.cumulative_runtime_minutes,
    CASE WHEN i.cumulative_runtime_minutes IS NULL THEN NULL
         ELSE LPAD((i.cumulative_runtime_minutes / 60)::text, 2, '0')
              || ':' || LPAD((i.cumulative_runtime_minutes % 60)::text, 2, '0')
    END AS cumulative_runtime_hh_mm,
    i.runtime_interval_minutes,
    CASE
        WHEN i.runtime_interval_minutes IS NULL THEN NULL
        WHEN i.runtime_interval_minutes < 0 THEN '-'
             || LPAD((ABS(i.runtime_interval_minutes) / 60)::text, 2, '0')
             || ':' || LPAD((ABS(i.runtime_interval_minutes) % 60)::text, 2, '0')
        ELSE LPAD((i.runtime_interval_minutes / 60)::text, 2, '0')
             || ':' || LPAD((i.runtime_interval_minutes % 60)::text, 2, '0')
    END AS runtime_interval_hh_mm,
    i.validated_runtime_interval_minutes,
    CASE WHEN i.cumulative_running_hours IS NULL THEN TRUE ELSE FALSE END AS runtime_missing,
    i.current_runtime_encoding_invalid AS runtime_encoding_invalid,
    i.analytics_quality_class
FROM public.vw_dg71_interval_classification AS i;

CREATE VIEW public.vw_dg71_diesel_interval AS
SELECT
    i.reading_id,
    i.asset_id,
    i.asset_code,
    i.asset_name,
    i.plaza_id,
    i.operational_date,
    i.reading_datetime,
    i.previous_reading_id,
    i.diesel_level_l,
    i.diesel_topup_l AS topup_recorded_at_this_reading_l,
    i.previous_diesel_level_l,
    COALESCE(i.previous_diesel_topup_l, 0::numeric) AS previous_row_topup_l,
    i.fuel_reconciliation_l AS calculated_fuel_movement_l,
    CASE WHEN i.fuel_reconciliation_l < 0 THEN TRUE ELSE FALSE END AS negative_fuel_reconciliation_exception,
    CASE WHEN i.positive_fuel_without_confirmed_generation_or_runtime THEN TRUE ELSE FALSE END
        AS consumption_without_confirmed_generation_or_runtime_exception,
    CASE
        WHEN i.fuel_reconciliation_l > 0
         AND i.has_confirmed_generation
         AND i.analytics_quality_class = 'VALID'
        THEN i.fuel_reconciliation_l
    END AS confirmed_diesel_consumption_l,
    CASE
        WHEN i.fuel_reconciliation_l > 0
         AND i.has_confirmed_generation
         AND i.analytics_quality_class = 'VALID'
        THEN i.runtime_interval_minutes
    END AS efficiency_runtime_minutes,
    CASE
        WHEN i.fuel_reconciliation_l > 0
         AND i.has_confirmed_generation
         AND i.analytics_quality_class = 'VALID'
        THEN i.generation_delta_kwh
    END AS efficiency_generation_kwh,
    CASE
        WHEN i.fuel_reconciliation_l IS NULL THEN 'MISSING_CURRENT_OR_PREVIOUS_FUEL_LEVEL'
        WHEN i.fuel_reconciliation_l <= 0 THEN 'NO_POSITIVE_CONFIRMED_CONSUMPTION'
        WHEN NOT i.has_confirmed_generation THEN 'NO_CONFIRMED_POSITIVE_GENERATION_AND_RUNTIME'
        WHEN i.analytics_quality_class <> 'VALID' THEN 'ANALYTICS_EXCEPTION'
        ELSE NULL
    END AS fuel_efficiency_exclusion_reason,
    i.source_quality_class,
    i.analytics_quality_class
FROM public.vw_dg71_interval_classification AS i;

CREATE VIEW public.vw_dg71_electrical_reading AS
WITH phase_means AS (
    SELECT
        i.*,
        CASE WHEN i.voltage_ry IS NOT NULL AND i.voltage_yb IS NOT NULL AND i.voltage_br IS NOT NULL
             THEN (i.voltage_ry + i.voltage_yb + i.voltage_br) / 3.0 END AS voltage_phase_mean,
        CASE WHEN i.current_r IS NOT NULL AND i.current_y IS NOT NULL AND i.current_b IS NOT NULL
             THEN (i.current_r + i.current_y + i.current_b) / 3.0 END AS current_phase_mean,
        (CASE WHEN i.voltage_ry IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN i.voltage_yb IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN i.voltage_br IS NOT NULL THEN 1 ELSE 0 END) AS voltage_phase_count,
        (CASE WHEN i.current_r IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN i.current_y IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN i.current_b IS NOT NULL THEN 1 ELSE 0 END) AS current_phase_count
    FROM public.vw_dg71_interval_classification AS i
)
SELECT
    p.reading_id,
    p.asset_id,
    p.asset_code,
    p.asset_name,
    p.plaza_id,
    p.operational_date,
    p.reading_datetime,
    p.kva,
    p.kw,
    p.pf,
    p.voltage_ry,
    p.voltage_yb,
    p.voltage_br,
    p.current_r,
    p.current_y,
    p.current_b,
    p.load_percentage,
    p.rpm,
    p.voltage_phase_mean,
    p.current_phase_mean,
    p.voltage_phase_count,
    p.current_phase_count,
    p.voltage_phase_count = 3 AS voltage_triplet_complete,
    p.current_phase_count = 3 AS current_triplet_complete,
    CASE
        WHEN p.voltage_phase_count = 3 AND p.voltage_phase_mean > 0
        THEN GREATEST(
            ABS(p.voltage_ry - p.voltage_phase_mean),
            ABS(p.voltage_yb - p.voltage_phase_mean),
            ABS(p.voltage_br - p.voltage_phase_mean)
        ) / p.voltage_phase_mean * 100.0
    END AS voltage_imbalance_pct,
    CASE
        WHEN p.current_phase_count = 3 AND p.current_phase_mean > 0
        THEN GREATEST(
            ABS(p.current_r - p.current_phase_mean),
            ABS(p.current_y - p.current_phase_mean),
            ABS(p.current_b - p.current_phase_mean)
        ) / p.current_phase_mean * 100.0
    END AS current_imbalance_pct,
    p.analytics_quality_class,
    p.analytics_exception_reasons
FROM phase_means AS p;

CREATE VIEW public.vw_dg71_entry_audit AS
SELECT
    i.reading_id,
    i.asset_id,
    i.asset_code,
    i.asset_name,
    i.plaza_id,
    i.operational_date,
    i.reading_datetime,
    i.created_on,
    i.created_by,
    i.created_at AS database_inserted_at,
    i.created_on - i.reading_datetime AS entry_delay,
    EXTRACT(EPOCH FROM (i.created_on - i.reading_datetime)) / 3600.0 AS entry_delay_hours,
    CASE WHEN i.created_on IS NULL THEN NULL
         WHEN i.created_on - i.reading_datetime < INTERVAL '0 seconds' THEN TRUE ELSE FALSE
    END AS negative_entry_delay_timestamp_anomaly,
    CASE WHEN i.created_on IS NULL OR i.created_on < i.reading_datetime THEN NULL
         WHEN i.created_on - i.reading_datetime >= INTERVAL '24 hours' THEN TRUE ELSE FALSE
    END AS delayed_entry_24h_or_more,
    CASE WHEN i.created_on IS NULL OR i.created_on < i.reading_datetime THEN NULL
         WHEN i.created_on - i.reading_datetime < INTERVAL '24 hours' THEN TRUE ELSE FALSE
    END AS entry_within_24h,
    ((i.reading_datetime AT TIME ZONE 'Asia/Kolkata')::time >= TIME '22:00'
      OR (i.reading_datetime AT TIME ZONE 'Asia/Kolkata')::time < TIME '06:00')
        AS reading_datetime_night_indicator,
    CASE WHEN i.created_on IS NULL THEN NULL
         ELSE ((i.created_on AT TIME ZONE 'Asia/Kolkata')::time >= TIME '22:00'
                OR (i.created_on AT TIME ZONE 'Asia/Kolkata')::time < TIME '06:00')
    END AS created_on_night_indicator,
    i.analytics_quality_class
FROM public.vw_dg71_interval_classification AS i;

CREATE VIEW public.vw_dg71_record_quality AS
SELECT
    i.reading_id,
    i.asset_id,
    i.asset_code,
    i.asset_name,
    i.plaza_id,
    i.operational_date,
    i.reading_datetime,
    1::bigint AS total_records,
    CASE WHEN i.source_quality_class = 'VALID' THEN 1::bigint ELSE 0::bigint END AS source_valid_records,
    CASE WHEN i.source_quality_class = 'EXCEPTION' THEN 1::bigint ELSE 0::bigint END AS source_exception_records,
    CASE WHEN i.analytics_quality_class = 'VALID' THEN 1::bigint ELSE 0::bigint END AS valid_records,
    CASE WHEN i.analytics_quality_class = 'EXCEPTION' THEN 1::bigint ELSE 0::bigint END AS exception_records,
    1::bigint
      - CASE WHEN i.analytics_quality_class = 'VALID' THEN 1::bigint ELSE 0::bigint END
      - CASE WHEN i.analytics_quality_class = 'EXCEPTION' THEN 1::bigint ELSE 0::bigint END
        AS reconciliation_difference,
    i.source_data_quality_status,
    i.source_quality_class,
    i.analytics_quality_class,
    i.analytics_exception_reasons
FROM public.vw_dg71_interval_classification AS i;

CREATE VIEW public.vw_dg71_daily_summary AS
WITH reading_metrics AS (
    SELECT
        i.reading_id,
        i.asset_id,
        i.asset_code,
        i.asset_name,
        i.plaza_id,
        i.operational_date,
        i.analytics_quality_class,
        i.source_quality_class,
        i.generation_classification,
        i.confirmed_generation_kwh,
        i.generation_delta_kwh,
        i.runtime_interval_minutes,
        i.validated_runtime_interval_minutes,
        i.fuel_reconciliation_l,
        i.diesel_topup_l,
        q.valid_records,
        q.exception_records,
        q.source_valid_records,
        q.source_exception_records,
        e.entry_delay,
        e.delayed_entry_24h_or_more,
        e.negative_entry_delay_timestamp_anomaly,
        e.reading_datetime_night_indicator,
        e.created_on_night_indicator,
        x.confirmed_diesel_consumption_l,
        x.efficiency_runtime_minutes,
        x.efficiency_generation_kwh,
        x.negative_fuel_reconciliation_exception,
        x.consumption_without_confirmed_generation_or_runtime_exception,
        el.kva,
        el.kw,
        el.pf,
        el.voltage_ry,
        el.voltage_yb,
        el.voltage_br,
        el.current_r,
        el.current_y,
        el.current_b,
        el.load_percentage,
        el.rpm,
        el.voltage_phase_count,
        el.current_phase_count,
        el.voltage_imbalance_pct,
        el.current_imbalance_pct
    FROM public.vw_dg71_interval_classification AS i
    JOIN public.vw_dg71_record_quality AS q USING (reading_id)
    JOIN public.vw_dg71_entry_audit AS e USING (reading_id)
    JOIN public.vw_dg71_diesel_interval AS x USING (reading_id)
    JOIN public.vw_dg71_electrical_reading AS el USING (reading_id)
)
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    operational_date,
    DATE_TRUNC('month', operational_date::timestamp)::date AS operational_month,
    EXTRACT(YEAR FROM operational_date)::integer AS operational_year,
    COUNT(*)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(source_valid_records)::bigint AS source_valid_records,
    SUM(source_exception_records)::bigint AS source_exception_records,
    COUNT(*)::bigint - SUM(valid_records) - SUM(exception_records) AS reconciliation_difference,
    100.0 * SUM(exception_records) / NULLIF(COUNT(*), 0) AS exception_percentage,
    COUNT(*) FILTER (WHERE generation_classification = 'FIRST_READING')::bigint AS first_reading_count,
    COUNT(*) FILTER (WHERE generation_classification = 'CONFIRMED_GENERATION'
                       AND analytics_quality_class = 'VALID')::bigint AS confirmed_generation_interval_count,
    COALESCE(SUM(confirmed_generation_kwh), 0::numeric) AS confirmed_generation_kwh,
    COUNT(*) FILTER (WHERE generation_classification = 'UNVERIFIED_GENERATION')::bigint AS unverified_generation_interval_count,
    COUNT(*) FILTER (WHERE generation_classification = 'ZERO_GENERATION')::bigint AS zero_generation_interval_count,
    COUNT(*) FILTER (WHERE generation_classification = 'NEGATIVE_GENERATION')::bigint AS negative_generation_exception_count,
    COUNT(*) FILTER (WHERE generation_classification = 'UNUSABLE_INTERVAL')::bigint AS unusable_generation_interval_count,
    COALESCE(SUM(validated_runtime_interval_minutes), 0::numeric) AS validated_runtime_minutes,
    COALESCE(SUM(efficiency_runtime_minutes), 0::numeric) AS efficiency_runtime_minutes,
    COALESCE(SUM(efficiency_generation_kwh), 0::numeric) AS efficiency_generation_kwh,
    COUNT(*) FILTER (WHERE runtime_interval_minutes = 0)::bigint AS zero_runtime_interval_count,
    COUNT(*) FILTER (WHERE runtime_interval_minutes < 0)::bigint AS negative_runtime_exception_count,
    COUNT(*) FILTER (WHERE runtime_interval_minutes IS NULL)::bigint AS unavailable_runtime_interval_count,
    COUNT(*) FILTER (WHERE diesel_topup_l IS NOT NULL)::bigint AS topup_report_count,
    COALESCE(SUM(diesel_topup_l), 0::numeric) AS reported_diesel_topup_l,
    COALESCE(SUM(fuel_reconciliation_l), 0::numeric) AS net_calculated_fuel_movement_l,
    COALESCE(SUM(confirmed_diesel_consumption_l), 0::numeric) AS confirmed_diesel_consumption_l,
    COUNT(*) FILTER (WHERE negative_fuel_reconciliation_exception)::bigint AS negative_fuel_reconciliation_exception_count,
    COUNT(*) FILTER (WHERE consumption_without_confirmed_generation_or_runtime_exception)::bigint
        AS consumption_without_confirmed_generation_or_runtime_count,
    SUM(confirmed_diesel_consumption_l)
        / NULLIF(SUM(efficiency_runtime_minutes) / 60.0, 0) AS diesel_l_per_runtime_hour,
    SUM(confirmed_diesel_consumption_l)
        / NULLIF(SUM(efficiency_generation_kwh), 0) AS diesel_l_per_kwh,
    SUM(efficiency_generation_kwh)
        / NULLIF(SUM(confirmed_diesel_consumption_l), 0) AS generation_kwh_per_l,
    AVG(kva) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_kva,
    MIN(kva) FILTER (WHERE analytics_quality_class = 'VALID') AS min_kva,
    MAX(kva) FILTER (WHERE analytics_quality_class = 'VALID') AS max_kva,
    AVG(kw) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_kw,
    MIN(kw) FILTER (WHERE analytics_quality_class = 'VALID') AS min_kw,
    MAX(kw) FILTER (WHERE analytics_quality_class = 'VALID') AS max_kw,
    AVG(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_pf,
    SUM(pf) FILTER (WHERE analytics_quality_class = 'VALID' AND pf IS NOT NULL) AS valid_pf_sum,
    COUNT(pf) FILTER (WHERE analytics_quality_class = 'VALID')::bigint AS valid_pf_count,
    MIN(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS min_pf,
    MAX(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS max_pf,
    AVG(voltage_ry) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_voltage_ry,
    MIN(voltage_ry) FILTER (WHERE analytics_quality_class = 'VALID') AS min_voltage_ry,
    MAX(voltage_ry) FILTER (WHERE analytics_quality_class = 'VALID') AS max_voltage_ry,
    AVG(voltage_yb) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_voltage_yb,
    MIN(voltage_yb) FILTER (WHERE analytics_quality_class = 'VALID') AS min_voltage_yb,
    MAX(voltage_yb) FILTER (WHERE analytics_quality_class = 'VALID') AS max_voltage_yb,
    AVG(voltage_br) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_voltage_br,
    MIN(voltage_br) FILTER (WHERE analytics_quality_class = 'VALID') AS min_voltage_br,
    MAX(voltage_br) FILTER (WHERE analytics_quality_class = 'VALID') AS max_voltage_br,
    AVG(current_r) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_current_r,
    MIN(current_r) FILTER (WHERE analytics_quality_class = 'VALID') AS min_current_r,
    MAX(current_r) FILTER (WHERE analytics_quality_class = 'VALID') AS max_current_r,
    AVG(current_y) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_current_y,
    MIN(current_y) FILTER (WHERE analytics_quality_class = 'VALID') AS min_current_y,
    MAX(current_y) FILTER (WHERE analytics_quality_class = 'VALID') AS max_current_y,
    AVG(current_b) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_current_b,
    MIN(current_b) FILTER (WHERE analytics_quality_class = 'VALID') AS min_current_b,
    MAX(current_b) FILTER (WHERE analytics_quality_class = 'VALID') AS max_current_b,
    AVG(load_percentage) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_load_percentage,
    MIN(load_percentage) FILTER (WHERE analytics_quality_class = 'VALID') AS min_load_percentage,
    MAX(load_percentage) FILTER (WHERE analytics_quality_class = 'VALID') AS max_load_percentage,
    AVG(rpm) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_rpm,
    MIN(rpm) FILTER (WHERE analytics_quality_class = 'VALID') AS min_rpm,
    MAX(rpm) FILTER (WHERE analytics_quality_class = 'VALID') AS max_rpm,
    AVG(voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_voltage_imbalance_pct,
    SUM(voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID' AND voltage_imbalance_pct IS NOT NULL)
        AS valid_voltage_imbalance_sum,
    COUNT(voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')::bigint
        AS valid_voltage_imbalance_count,
    MAX(voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS max_voltage_imbalance_pct,
    AVG(current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_current_imbalance_pct,
    SUM(current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID' AND current_imbalance_pct IS NOT NULL)
        AS valid_current_imbalance_sum,
    COUNT(current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')::bigint
        AS valid_current_imbalance_count,
    MAX(current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS max_current_imbalance_pct,
    COUNT(*) FILTER (WHERE voltage_phase_count < 3)::bigint AS incomplete_voltage_triplet_count,
    COUNT(*) FILTER (WHERE current_phase_count < 3)::bigint AS incomplete_current_triplet_count,
    COUNT(*) FILTER (WHERE delayed_entry_24h_or_more IS TRUE)::bigint AS delayed_entry_count,
    COUNT(*) FILTER (WHERE entry_delay IS NOT NULL AND entry_delay >= INTERVAL '0 seconds')::bigint
        AS entry_delay_eligible_count,
    100.0 * COUNT(*) FILTER (WHERE delayed_entry_24h_or_more IS TRUE)
        / NULLIF(COUNT(*) FILTER (WHERE entry_delay IS NOT NULL AND entry_delay >= INTERVAL '0 seconds'), 0)
        AS delayed_entry_percentage,
    AVG(entry_delay) FILTER (WHERE entry_delay >= INTERVAL '0 seconds') AS average_entry_delay,
    SUM(EXTRACT(EPOCH FROM entry_delay)) FILTER (WHERE entry_delay >= INTERVAL '0 seconds')
        AS eligible_entry_delay_sum_seconds,
    MAX(entry_delay) FILTER (WHERE entry_delay >= INTERVAL '0 seconds') AS maximum_entry_delay,
    COUNT(*) FILTER (WHERE negative_entry_delay_timestamp_anomaly IS TRUE)::bigint
        AS negative_entry_delay_timestamp_anomaly_count,
    COUNT(*) FILTER (WHERE reading_datetime_night_indicator IS TRUE)::bigint AS night_reading_count,
    COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE)::bigint AS night_entry_count,
    COUNT(*) FILTER (WHERE reading_datetime_night_indicator IS TRUE
                       AND analytics_quality_class = 'VALID')::bigint AS valid_night_reading_count,
    COUNT(*) FILTER (WHERE reading_datetime_night_indicator IS TRUE
                       AND analytics_quality_class = 'EXCEPTION')::bigint AS exception_night_reading_count,
    COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE
                       AND analytics_quality_class = 'VALID')::bigint AS valid_night_entry_count,
    COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE
                       AND analytics_quality_class = 'EXCEPTION')::bigint AS exception_night_entry_count
FROM reading_metrics
GROUP BY asset_id, asset_code, asset_name, plaza_id, operational_date;

CREATE VIEW public.vw_dg71_monthly_summary AS
SELECT
    asset_id, asset_code, asset_name, plaza_id, operational_month,
    COUNT(*)::bigint AS observed_asset_days,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
    SUM(confirmed_generation_kwh) AS confirmed_generation_kwh,
    AVG(confirmed_generation_kwh) AS average_confirmed_generation_per_observed_day_kwh,
    MAX(confirmed_generation_kwh) AS maximum_daily_confirmed_generation_kwh,
    SUM(validated_runtime_minutes) AS validated_runtime_minutes,
    SUM(confirmed_diesel_consumption_l) AS confirmed_diesel_consumption_l,
    SUM(reported_diesel_topup_l) AS reported_diesel_topup_l,
    SUM(net_calculated_fuel_movement_l) AS net_calculated_fuel_movement_l,
    SUM(negative_fuel_reconciliation_exception_count)::bigint AS negative_fuel_reconciliation_exception_count,
    SUM(consumption_without_confirmed_generation_or_runtime_count)::bigint
        AS consumption_without_confirmed_generation_or_runtime_count,
    SUM(confirmed_diesel_consumption_l)
        / NULLIF(SUM(efficiency_runtime_minutes) / 60.0, 0) AS diesel_l_per_runtime_hour,
    SUM(confirmed_diesel_consumption_l)
        / NULLIF(SUM(efficiency_generation_kwh), 0) AS diesel_l_per_kwh,
    SUM(efficiency_generation_kwh)
        / NULLIF(SUM(confirmed_diesel_consumption_l), 0) AS generation_kwh_per_l,
    SUM(valid_pf_sum) / NULLIF(SUM(valid_pf_count), 0) AS average_pf,
    MIN(min_pf) AS minimum_pf,
    MAX(max_pf) AS maximum_pf,
    SUM(valid_voltage_imbalance_sum) / NULLIF(SUM(valid_voltage_imbalance_count), 0)
        AS average_voltage_imbalance_pct,
    MAX(max_voltage_imbalance_pct) AS maximum_voltage_imbalance_pct,
    SUM(valid_current_imbalance_sum) / NULLIF(SUM(valid_current_imbalance_count), 0)
        AS average_current_imbalance_pct,
    MAX(max_current_imbalance_pct) AS maximum_current_imbalance_pct,
    SUM(delayed_entry_count)::bigint AS delayed_entry_count,
    SUM(entry_delay_eligible_count)::bigint AS entry_delay_eligible_count,
    100.0 * SUM(delayed_entry_count) / NULLIF(SUM(entry_delay_eligible_count), 0)
        AS delayed_entry_percentage,
    SUM(eligible_entry_delay_sum_seconds) / 3600.0
        / NULLIF(SUM(entry_delay_eligible_count), 0) AS average_entry_delay_hours,
    MAX(maximum_entry_delay) AS maximum_entry_delay,
    SUM(negative_entry_delay_timestamp_anomaly_count)::bigint
        AS negative_entry_delay_timestamp_anomaly_count,
    SUM(night_reading_count)::bigint AS night_reading_count,
    SUM(night_entry_count)::bigint AS night_entry_count,
    SUM(valid_night_reading_count)::bigint AS valid_night_reading_count,
    SUM(exception_night_reading_count)::bigint AS exception_night_reading_count,
    SUM(valid_night_entry_count)::bigint AS valid_night_entry_count,
    SUM(exception_night_entry_count)::bigint AS exception_night_entry_count
FROM public.vw_dg71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, operational_month;

CREATE VIEW public.vw_dg71_yearly_summary AS
SELECT
    asset_id, asset_code, asset_name, plaza_id, operational_year,
    COUNT(*)::bigint AS observed_asset_days,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
    SUM(confirmed_generation_kwh) AS confirmed_generation_kwh,
    AVG(confirmed_generation_kwh) AS average_confirmed_generation_per_observed_day_kwh,
    MAX(confirmed_generation_kwh) AS maximum_daily_confirmed_generation_kwh,
    SUM(validated_runtime_minutes) AS validated_runtime_minutes,
    SUM(confirmed_diesel_consumption_l) AS confirmed_diesel_consumption_l,
    SUM(reported_diesel_topup_l) AS reported_diesel_topup_l,
    SUM(net_calculated_fuel_movement_l) AS net_calculated_fuel_movement_l,
    SUM(negative_fuel_reconciliation_exception_count)::bigint AS negative_fuel_reconciliation_exception_count,
    SUM(consumption_without_confirmed_generation_or_runtime_count)::bigint
        AS consumption_without_confirmed_generation_or_runtime_count,
    SUM(confirmed_diesel_consumption_l)
        / NULLIF(SUM(efficiency_runtime_minutes) / 60.0, 0) AS diesel_l_per_runtime_hour,
    SUM(confirmed_diesel_consumption_l)
        / NULLIF(SUM(efficiency_generation_kwh), 0) AS diesel_l_per_kwh,
    SUM(efficiency_generation_kwh)
        / NULLIF(SUM(confirmed_diesel_consumption_l), 0) AS generation_kwh_per_l,
    SUM(valid_pf_sum) / NULLIF(SUM(valid_pf_count), 0) AS average_pf,
    MIN(min_pf) AS minimum_pf,
    MAX(max_pf) AS maximum_pf,
    SUM(valid_voltage_imbalance_sum) / NULLIF(SUM(valid_voltage_imbalance_count), 0)
        AS average_voltage_imbalance_pct,
    MAX(max_voltage_imbalance_pct) AS maximum_voltage_imbalance_pct,
    SUM(valid_current_imbalance_sum) / NULLIF(SUM(valid_current_imbalance_count), 0)
        AS average_current_imbalance_pct,
    MAX(max_current_imbalance_pct) AS maximum_current_imbalance_pct,
    SUM(delayed_entry_count)::bigint AS delayed_entry_count,
    SUM(entry_delay_eligible_count)::bigint AS entry_delay_eligible_count,
    100.0 * SUM(delayed_entry_count) / NULLIF(SUM(entry_delay_eligible_count), 0)
        AS delayed_entry_percentage,
    SUM(eligible_entry_delay_sum_seconds) / 3600.0
        / NULLIF(SUM(entry_delay_eligible_count), 0) AS average_entry_delay_hours,
    MAX(maximum_entry_delay) AS maximum_entry_delay,
    SUM(negative_entry_delay_timestamp_anomaly_count)::bigint
        AS negative_entry_delay_timestamp_anomaly_count,
    SUM(night_reading_count)::bigint AS night_reading_count,
    SUM(night_entry_count)::bigint AS night_entry_count,
    SUM(valid_night_reading_count)::bigint AS valid_night_reading_count,
    SUM(exception_night_reading_count)::bigint AS exception_night_reading_count,
    SUM(valid_night_entry_count)::bigint AS valid_night_entry_count,
    SUM(exception_night_entry_count)::bigint AS exception_night_entry_count
FROM public.vw_dg71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, operational_year;

CREATE VIEW public.vw_dg71_analytics_summary AS
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    SUM(confirmed_generation_kwh) AS confirmed_generation_kwh,
    SUM(validated_runtime_minutes) AS validated_runtime_minutes,
    SUM(reported_diesel_topup_l) AS reported_diesel_topup_l,
    SUM(net_calculated_fuel_movement_l) AS net_calculated_fuel_movement_l,
    SUM(confirmed_diesel_consumption_l) AS confirmed_diesel_consumption_l,
    SUM(negative_fuel_reconciliation_exception_count)::bigint AS negative_fuel_reconciliation_exception_count,
    SUM(consumption_without_confirmed_generation_or_runtime_count)::bigint
        AS consumption_without_confirmed_generation_or_runtime_count,
    SUM(delayed_entry_count)::bigint AS delayed_entry_count,
    SUM(entry_delay_eligible_count)::bigint AS entry_delay_eligible_count,
    100.0 * SUM(delayed_entry_count) / NULLIF(SUM(entry_delay_eligible_count), 0)
        AS delayed_entry_percentage,
    SUM(night_reading_count)::bigint AS night_reading_count,
    SUM(night_entry_count)::bigint AS night_entry_count,
    SUM(valid_night_reading_count)::bigint AS valid_night_reading_count,
    SUM(exception_night_reading_count)::bigint AS exception_night_reading_count,
    SUM(valid_night_entry_count)::bigint AS valid_night_entry_count,
    SUM(exception_night_entry_count)::bigint AS exception_night_entry_count
FROM public.vw_dg71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id;
