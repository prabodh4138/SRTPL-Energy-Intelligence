-- ============================================================================
-- SRTPL ENERGY COMMAND CENTER — MODULE 7 COMPLETE ANALYTICS VIEWS DEPLOYMENT
-- Target: PostgreSQL / Supabase
-- Updated with: Industrial EB Billing Basis on kVAh (not kWh) & Multiplying Factor (MF) = 200
-- Execution Order:
--   1. DG Submodule Views (including vw_dg71_daily_summary)
--   2. EB Submodule Views (including vw_eb71_daily_summary with kVAh MF:200)
--   3. Solar Submodule Views (including vw_sol71_daily_summary & asset latest)
--   4. Transformer Submodule Views (including vw_trf71_daily_summary)
--   5. UPS Submodule Views (including vw_ups71_daily_summary)
--   6. Unified Module 7 Views (vw_m7_record_quality, vw_m7_entry_audit,
--      vw_m7_exception_register, vw_m7_asset_latest_reading with kVAh & MF:200)
--   7. Optional Guarded Correction Audit View
-- ============================================================================


-- >>> START OF DG_Module_7_1_Analytics_Proposed.sql <<<

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


-- >>> END OF DG_Module_7_1_Analytics_Proposed.sql <<<


-- >>> START OF EB_Module_Analytics_Proposed.sql <<<

-- SRTPL Energy Command Center - EB Analytics
-- PROPOSAL ONLY. Nothing in this file has been executed against a database.
-- PostgreSQL / Supabase. Adds new public.vw_eb71_* views only; no DROP,
-- CREATE OR REPLACE, schema/table changes, or source-data writes are included.
-- Run the separate read-only preflight before using these definitions.

CREATE VIEW public.vw_eb71_interval_detail AS
WITH reading_source AS (
    SELECT
        d.reading_id,
        d.asset_id,
        COALESCE(d.asset_code, a.asset_code) AS asset_code,
        a.asset_name,
        a.plaza_id,
        d.consumer_number,
        d.reading_datetime,
        (d.reading_datetime AT TIME ZONE 'Asia/Kolkata')::date AS operational_date,
        d.cumulative_kwh,
        d.cumulative_kvah,
        d.cumulative_kvarh,
        d.interval_kwh,
        d.interval_kvah,
        d.interval_kvarh,
        d.pf,
        CASE
            WHEN to_jsonb(d)->>'maximum_demand' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (to_jsonb(d)->>'maximum_demand')::numeric
            WHEN to_jsonb(d)->>'md' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (to_jsonb(d)->>'md')::numeric
        END AS maximum_demand_value,
        d.created_by,
        d.created_on,
        d.created_at,
        d.remarks,
        d.location,
        d.category,
        d.data_quality_status AS source_data_quality_status,
        CASE
            WHEN UPPER(BTRIM(COALESCE(d.data_quality_status, ''))) = 'VALID' THEN 'VALID'
            ELSE 'EXCEPTION'
        END AS source_quality_class,
        COALESCE(
            'ID:' || d.asset_id,
            'CODE:' || COALESCE(d.asset_code, a.asset_code),
            'ROW:' || d.reading_id::text
        ) AS asset_partition_key
    FROM energy_readings.eb AS d
    LEFT JOIN energy_master.asset AS a
        ON (d.asset_id IS NOT NULL AND a.asset_id = d.asset_id)
        OR (d.asset_id IS NULL AND a.asset_code = d.asset_code AND a.source_type = 'EB')
),
sequenced_readings AS (
    SELECT
        r.*,
        ROW_NUMBER() OVER w AS reading_sequence,
        LAG(r.reading_id) OVER w AS previous_reading_id,
        LAG(r.reading_datetime) OVER w AS previous_reading_datetime,
        LAG(r.cumulative_kwh) OVER w AS previous_cumulative_kwh,
        LAG(r.cumulative_kvah) OVER w AS previous_cumulative_kvah,
        LAG(r.cumulative_kvarh) OVER w AS previous_cumulative_kvarh
    FROM reading_source AS r
    WINDOW w AS (
        PARTITION BY r.asset_partition_key
        ORDER BY r.reading_datetime, r.reading_id
    )
),
interval_values AS (
    SELECT
        s.*,
        s.cumulative_kwh - s.previous_cumulative_kwh AS cumulative_delta_kwh,
        s.cumulative_kvah - s.previous_cumulative_kvah AS cumulative_delta_kvah,
        s.cumulative_kvarh - s.previous_cumulative_kvarh AS cumulative_delta_kvarh,
        CASE
            WHEN s.interval_kwh IS NOT NULL THEN s.interval_kwh
            WHEN s.cumulative_kwh IS NOT NULL AND s.previous_cumulative_kwh IS NOT NULL
            THEN s.cumulative_kwh - s.previous_cumulative_kwh
        END AS normalized_interval_kwh,
        CASE
            WHEN s.interval_kvah IS NOT NULL THEN s.interval_kvah
            WHEN s.cumulative_kvah IS NOT NULL AND s.previous_cumulative_kvah IS NOT NULL
            THEN s.cumulative_kvah - s.previous_cumulative_kvah
        END AS normalized_interval_kvah,
        CASE
            WHEN s.interval_kvarh IS NOT NULL THEN s.interval_kvarh
            WHEN s.cumulative_kvarh IS NOT NULL AND s.previous_cumulative_kvarh IS NOT NULL
            THEN s.cumulative_kvarh - s.previous_cumulative_kvarh
        END AS normalized_interval_kvarh
    FROM sequenced_readings AS s
),
classified_readings AS (
    SELECT
        i.*,
        200::numeric AS multiplying_factor,
        (i.normalized_interval_kvah * 200)::numeric AS billed_interval_kvah,
        (i.normalized_interval_kwh * 200)::numeric AS billed_interval_kwh,
        (i.cumulative_kvah * 200)::numeric AS billed_cumulative_kvah,
        (i.cumulative_kwh * 200)::numeric AS billed_cumulative_kwh,
        (i.previous_cumulative_kvah * 200)::numeric AS billed_previous_cumulative_kvah,
        (i.previous_cumulative_kwh * 200)::numeric AS billed_previous_cumulative_kwh,
        CASE
            WHEN i.source_quality_class <> 'VALID'
              OR i.cumulative_delta_kwh < 0
              OR i.cumulative_delta_kvah < 0
              OR i.cumulative_delta_kvarh < 0
              OR i.pf < 0
              OR i.pf > 1
            THEN 'EXCEPTION'
            ELSE 'VALID'
        END AS analytics_quality_class,
        CONCAT_WS(
            '; ',
            CASE WHEN i.source_quality_class <> 'VALID' THEN 'SOURCE_STATUS_EXCEPTION' END,
            CASE WHEN i.cumulative_delta_kwh < 0 THEN 'DECREASING_CUMULATIVE_KWH' END,
            CASE WHEN i.cumulative_delta_kvah < 0 THEN 'DECREASING_CUMULATIVE_KVAH' END,
            CASE WHEN i.cumulative_delta_kvarh < 0 THEN 'DECREASING_CUMULATIVE_KVARH' END,
            CASE WHEN i.pf < 0 OR i.pf > 1 THEN 'POWER_FACTOR_OUTSIDE_0_TO_1' END
        ) AS analytics_exception_reasons
    FROM interval_values AS i
)
SELECT *
FROM classified_readings;

CREATE VIEW public.vw_eb71_record_quality AS
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
FROM public.vw_eb71_interval_detail AS i;

CREATE VIEW public.vw_eb71_entry_audit AS
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
         WHEN i.created_on < i.reading_datetime THEN TRUE ELSE FALSE
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
FROM public.vw_eb71_interval_detail AS i;

CREATE VIEW public.vw_eb71_daily_summary AS
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
        i.normalized_interval_kwh,
        i.normalized_interval_kvah,
        i.normalized_interval_kvarh,
        i.cumulative_delta_kwh,
        i.cumulative_delta_kvah,
        i.cumulative_delta_kvarh,
        i.pf,
        i.maximum_demand_value,
        q.valid_records,
        q.exception_records,
        q.source_valid_records,
        q.source_exception_records,
        e.entry_delay,
        e.delayed_entry_24h_or_more,
        e.negative_entry_delay_timestamp_anomaly,
        e.reading_datetime_night_indicator,
        e.created_on_night_indicator
    FROM public.vw_eb71_interval_detail AS i
    JOIN public.vw_eb71_record_quality AS q USING (reading_id)
    JOIN public.vw_eb71_entry_audit AS e USING (reading_id)
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
    200::numeric AS multiplying_factor,
    COALESCE(SUM(normalized_interval_kvah * 200) FILTER (WHERE analytics_quality_class = 'VALID'), 0::numeric)
        AS valid_billed_kvah,
    COALESCE(SUM(normalized_interval_kwh * 200) FILTER (WHERE analytics_quality_class = 'VALID'), 0::numeric)
        AS valid_billed_kwh,
    COALESCE(SUM(normalized_interval_kwh) FILTER (WHERE analytics_quality_class = 'VALID'), 0::numeric)
        AS valid_interval_kwh,
    COALESCE(SUM(normalized_interval_kvah) FILTER (WHERE analytics_quality_class = 'VALID'), 0::numeric)
        AS valid_interval_kvah,
    COALESCE(SUM(normalized_interval_kvarh) FILTER (WHERE analytics_quality_class = 'VALID'), 0::numeric)
        AS valid_interval_kvarh,
    COUNT(*) FILTER (WHERE normalized_interval_kwh IS NULL AND analytics_quality_class = 'VALID')::bigint
        AS valid_rows_missing_interval_kwh,
    COUNT(*) FILTER (WHERE normalized_interval_kvah IS NULL AND analytics_quality_class = 'VALID')::bigint
        AS valid_rows_missing_interval_kvah,
    COUNT(*) FILTER (WHERE normalized_interval_kvarh IS NULL AND analytics_quality_class = 'VALID')::bigint
        AS valid_rows_missing_interval_kvarh,
    SUM(pf) FILTER (WHERE analytics_quality_class = 'VALID' AND pf IS NOT NULL) AS valid_pf_sum,
    COUNT(pf) FILTER (WHERE analytics_quality_class = 'VALID')::bigint AS valid_pf_count,
    AVG(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS average_pf,
    MIN(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_pf,
    MAX(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_pf,
    MIN(maximum_demand_value) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_recorded_demand,
    AVG(maximum_demand_value) FILTER (WHERE analytics_quality_class = 'VALID') AS average_recorded_demand,
    MAX(maximum_demand_value) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_recorded_demand,
    SUM(normalized_interval_kwh) FILTER (WHERE analytics_quality_class = 'VALID')
        / NULLIF(SUM(normalized_interval_kvah) FILTER (WHERE analytics_quality_class = 'VALID'), 0)
        AS kwh_to_kvah_ratio,
    COUNT(*) FILTER (WHERE cumulative_delta_kwh < 0)::bigint AS decreasing_cumulative_kwh_count,
    COUNT(*) FILTER (WHERE cumulative_delta_kvah < 0)::bigint AS decreasing_cumulative_kvah_count,
    COUNT(*) FILTER (WHERE cumulative_delta_kvarh < 0)::bigint AS decreasing_cumulative_kvarh_count,
    COUNT(*) FILTER (WHERE pf < 0 OR pf > 1)::bigint AS out_of_range_pf_count,
    COUNT(*) FILTER (WHERE delayed_entry_24h_or_more IS TRUE)::bigint AS delayed_entry_count,
    COUNT(*) FILTER (WHERE entry_delay IS NOT NULL AND entry_delay >= INTERVAL '0 seconds')::bigint
        AS entry_delay_eligible_count,
    100.0 * COUNT(*) FILTER (WHERE delayed_entry_24h_or_more IS TRUE)
        / NULLIF(COUNT(*) FILTER (WHERE entry_delay IS NOT NULL AND entry_delay >= INTERVAL '0 seconds'), 0)
        AS delayed_entry_percentage,
    AVG(entry_delay) FILTER (WHERE entry_delay >= INTERVAL '0 seconds') AS average_entry_delay,
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

CREATE VIEW public.vw_eb71_monthly_summary AS
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    operational_month,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    200::numeric AS multiplying_factor,
    SUM(valid_billed_kvah) AS valid_billed_kvah,
    SUM(valid_billed_kwh) AS valid_billed_kwh,
    SUM(valid_interval_kwh) AS valid_interval_kwh,
    SUM(valid_interval_kvah) AS valid_interval_kvah,
    SUM(valid_interval_kvarh) AS valid_interval_kvarh,
    SUM(valid_interval_kwh) / NULLIF(SUM(valid_interval_kvah), 0) AS kwh_to_kvah_ratio,
    SUM(valid_pf_sum) / NULLIF(SUM(valid_pf_count), 0) AS average_pf,
    MIN(minimum_pf) AS minimum_pf,
    MAX(maximum_pf) AS maximum_pf,
    MAX(maximum_recorded_demand) AS peak_recorded_demand,
    SUM(decreasing_cumulative_kwh_count)::bigint AS decreasing_cumulative_kwh_count,
    SUM(decreasing_cumulative_kvah_count)::bigint AS decreasing_cumulative_kvah_count,
    SUM(decreasing_cumulative_kvarh_count)::bigint AS decreasing_cumulative_kvarh_count,
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
FROM public.vw_eb71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, operational_month;

CREATE VIEW public.vw_eb71_yearly_summary AS
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    operational_year,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    200::numeric AS multiplying_factor,
    SUM(valid_billed_kvah) AS valid_billed_kvah,
    SUM(valid_billed_kwh) AS valid_billed_kwh,
    SUM(valid_interval_kwh) AS valid_interval_kwh,
    SUM(valid_interval_kvah) AS valid_interval_kvah,
    SUM(valid_interval_kvarh) AS valid_interval_kvarh,
    SUM(valid_interval_kwh) / NULLIF(SUM(valid_interval_kvah), 0) AS kwh_to_kvah_ratio,
    SUM(valid_pf_sum) / NULLIF(SUM(valid_pf_count), 0) AS average_pf,
    MIN(minimum_pf) AS minimum_pf,
    MAX(maximum_pf) AS maximum_pf,
    MAX(maximum_recorded_demand) AS peak_recorded_demand,
    SUM(decreasing_cumulative_kwh_count)::bigint AS decreasing_cumulative_kwh_count,
    SUM(decreasing_cumulative_kvah_count)::bigint AS decreasing_cumulative_kvah_count,
    SUM(decreasing_cumulative_kvarh_count)::bigint AS decreasing_cumulative_kvarh_count,
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
FROM public.vw_eb71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, operational_year;

CREATE VIEW public.vw_eb71_analytics_summary AS
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    200::numeric AS multiplying_factor,
    SUM(valid_billed_kvah) AS valid_billed_kvah,
    SUM(valid_billed_kwh) AS valid_billed_kwh,
    SUM(valid_interval_kwh) AS valid_interval_kwh,
    SUM(valid_interval_kvah) AS valid_interval_kvah,
    SUM(valid_interval_kvarh) AS valid_interval_kvarh,
    SUM(valid_interval_kwh) / NULLIF(SUM(valid_interval_kvah), 0) AS kwh_to_kvah_ratio,
    SUM(valid_pf_sum) / NULLIF(SUM(valid_pf_count), 0) AS average_pf,
    MIN(minimum_pf) AS minimum_pf,
    MAX(maximum_pf) AS maximum_pf,
    MAX(maximum_recorded_demand) AS peak_recorded_demand,
    SUM(decreasing_cumulative_kwh_count)::bigint AS decreasing_cumulative_kwh_count,
    SUM(decreasing_cumulative_kvah_count)::bigint AS decreasing_cumulative_kvah_count,
    SUM(decreasing_cumulative_kvarh_count)::bigint AS decreasing_cumulative_kvarh_count,
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
FROM public.vw_eb71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id;

CREATE VIEW public.vw_eb71_asset_latest_reading AS
SELECT *
FROM (
    SELECT
        i.*,
        ROW_NUMBER() OVER (
            PARTITION BY i.asset_partition_key
            ORDER BY i.reading_datetime DESC, i.reading_id DESC
        ) AS asset_latest_rank
    FROM public.vw_eb71_interval_detail AS i
) AS ranked
WHERE asset_latest_rank = 1;


-- >>> END OF EB_Module_Analytics_Proposed.sql <<<


-- >>> START OF Solar_Module_Analytics_Proposed.sql <<<

-- SRTPL Energy Command Center - Solar Analytics Views
-- PROPOSAL ONLY. Do not run without first reviewing the separate preflight.
-- Adds new public.vw_sol71_* views only. No DROP/replace, schema/table changes,
-- or source-data writes are included.

CREATE VIEW public.vw_sol71_reading_detail AS
WITH reading_source AS (
    SELECT
        s.reading_id,
        s.asset_id,
        COALESCE(s.asset_code, a.asset_code) AS asset_code,
        a.asset_name,
        a.plaza_id,
        s.reading_datetime,
        (s.reading_datetime AT TIME ZONE 'Asia/Kolkata')::date AS operational_date,
        s.created_by,
        s.created_on,
        s.created_at,
        s.remarks,
        s.location,
        s.data_quality_status AS source_data_quality_status,
        CASE
            WHEN UPPER(BTRIM(COALESCE(s.data_quality_status, ''))) = 'VALID' THEN 'VALID'
            ELSE 'EXCEPTION'
        END AS source_quality_class,
        COALESCE(
            'ID:' || s.asset_id::text,
            'CODE:' || COALESCE(s.asset_code, a.asset_code),
            'ROW:' || s.reading_id::text
        ) AS asset_partition_key,
        to_jsonb(s) AS reading_payload
    FROM energy_readings.solar AS s
    LEFT JOIN energy_master.asset AS a
        ON (s.asset_id IS NOT NULL AND a.asset_id = s.asset_id)
        OR (s.asset_id IS NULL AND a.asset_code = s.asset_code AND a.source_type = 'SOLAR')
)
SELECT
    r.reading_id,
    r.asset_id,
    r.asset_code,
    r.asset_name,
    r.plaza_id,
    r.asset_partition_key,
    r.reading_datetime,
    r.operational_date,
    CASE
        WHEN r.reading_payload->>'cumulative_kwh' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'cumulative_kwh')::numeric
        WHEN r.reading_payload->>'unit_generated_in_kwh' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'unit_generated_in_kwh')::numeric
    END AS cumulative_kwh,
    CASE
        WHEN r.reading_payload->>'interval_kwh' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'interval_kwh')::numeric
    END AS interval_kwh,
    r.created_by,
    r.created_on,
    r.created_at,
    r.remarks,
    r.location,
    r.source_data_quality_status,
    r.source_quality_class
FROM reading_source AS r;

CREATE VIEW public.vw_sol71_interval_reading AS
WITH ordered_readings AS (
    SELECT
        d.*,
        LAG(d.reading_datetime) OVER (
            PARTITION BY d.asset_partition_key
            ORDER BY d.reading_datetime, d.reading_id
        ) AS previous_row_reading_datetime,
        LAG(d.cumulative_kwh) OVER (
            PARTITION BY d.asset_partition_key
            ORDER BY d.reading_datetime, d.reading_id
        ) AS previous_cumulative_kwh,
        LAG(d.reading_datetime) OVER (
            PARTITION BY d.asset_partition_key
            ORDER BY d.reading_datetime, d.reading_id
        ) AS previous_reading_datetime
    FROM public.vw_sol71_reading_detail AS d
), deltas AS (
    SELECT
        o.*,
        o.cumulative_kwh - o.previous_cumulative_kwh AS cumulative_delta_kwh,
        o.interval_kwh - (o.cumulative_kwh - o.previous_cumulative_kwh)
            AS reported_vs_cumulative_delta_kwh
    FROM ordered_readings AS o
)
SELECT
    d.*,
    CASE
        WHEN d.cumulative_kwh IS NULL THEN 'MISSING_CUMULATIVE_KWH'
        WHEN d.previous_row_reading_datetime IS NULL THEN 'FIRST_READING'
        WHEN d.previous_cumulative_kwh IS NULL THEN 'MISSING_PREVIOUS_CUMULATIVE_KWH'
        WHEN d.cumulative_delta_kwh < 0 THEN 'NEGATIVE_CUMULATIVE_DELTA'
        WHEN d.interval_kwh < 0 THEN 'NEGATIVE_INTERVAL_KWH'
        WHEN d.source_quality_class = 'EXCEPTION' THEN 'SOURCE_EXCEPTION'
        WHEN d.interval_kwh IS NULL THEN 'MISSING_INTERVAL_KWH'
        WHEN d.interval_kwh = 0 THEN 'ZERO_GENERATION'
        ELSE 'POSITIVE_GENERATION'
    END AS generation_interval_class
FROM deltas AS d;

CREATE VIEW public.vw_sol71_record_quality AS
SELECT
    i.reading_id,
    i.asset_id,
    i.asset_code,
    i.asset_name,
    i.plaza_id,
    i.asset_partition_key,
    i.operational_date,
    i.reading_datetime,
    1::bigint AS total_records,
    CASE WHEN i.source_quality_class = 'VALID' THEN 1::bigint ELSE 0::bigint END
        AS source_valid_records,
    CASE WHEN i.source_quality_class = 'EXCEPTION' THEN 1::bigint ELSE 0::bigint END
        AS source_exception_records,
    CASE
        WHEN i.source_quality_class = 'VALID'
         AND (i.cumulative_delta_kwh IS NULL OR i.cumulative_delta_kwh >= 0)
         AND (i.interval_kwh IS NULL OR i.interval_kwh >= 0)
            THEN 1::bigint ELSE 0::bigint
    END AS valid_records,
    CASE
        WHEN i.source_quality_class <> 'VALID'
          OR i.cumulative_delta_kwh < 0
          OR i.interval_kwh < 0
            THEN 1::bigint ELSE 0::bigint
    END AS exception_records,
    CASE
        WHEN i.source_quality_class = 'VALID'
         AND (i.cumulative_delta_kwh IS NULL OR i.cumulative_delta_kwh >= 0)
         AND (i.interval_kwh IS NULL OR i.interval_kwh >= 0)
            THEN 'VALID' ELSE 'EXCEPTION'
    END AS analytics_quality_class,
    1::bigint
      - CASE
            WHEN i.source_quality_class = 'VALID'
             AND (i.cumulative_delta_kwh IS NULL OR i.cumulative_delta_kwh >= 0)
             AND (i.interval_kwh IS NULL OR i.interval_kwh >= 0)
                THEN 1::bigint ELSE 0::bigint
        END
      - CASE
            WHEN i.source_quality_class <> 'VALID'
              OR i.cumulative_delta_kwh < 0
              OR i.interval_kwh < 0
                THEN 1::bigint ELSE 0::bigint
        END AS reconciliation_difference,
    i.source_data_quality_status,
    NULLIF(CONCAT_WS(', ',
        CASE WHEN i.source_quality_class <> 'VALID' THEN 'SOURCE_STATUS_EXCEPTION' END,
        CASE WHEN i.cumulative_delta_kwh < 0 THEN 'NEGATIVE_CUMULATIVE_DELTA' END,
        CASE WHEN i.interval_kwh < 0 THEN 'NEGATIVE_INTERVAL_KWH' END
    ), '') AS analytics_exception_reasons
FROM public.vw_sol71_interval_reading AS i;

CREATE VIEW public.vw_sol71_entry_audit AS
SELECT
    d.reading_id,
    d.asset_id,
    d.asset_code,
    d.asset_name,
    d.plaza_id,
    d.asset_partition_key,
    d.operational_date,
    d.reading_datetime,
    d.created_on,
    d.created_by,
    d.created_at AS database_inserted_at,
    d.created_on - d.reading_datetime AS entry_delay,
    EXTRACT(EPOCH FROM (d.created_on - d.reading_datetime)) / 3600.0 AS entry_delay_hours,
    CASE WHEN d.created_on IS NULL THEN NULL
         WHEN d.created_on < d.reading_datetime THEN TRUE ELSE FALSE
    END AS negative_entry_delay_timestamp_anomaly,
    CASE WHEN d.created_on IS NULL OR d.created_on < d.reading_datetime THEN NULL
         WHEN d.created_on - d.reading_datetime >= INTERVAL '24 hours' THEN TRUE ELSE FALSE
    END AS delayed_entry_24h_or_more,
    CASE WHEN d.created_on IS NULL OR d.created_on < d.reading_datetime THEN NULL
         WHEN d.created_on - d.reading_datetime < INTERVAL '24 hours' THEN TRUE ELSE FALSE
    END AS entry_within_24h,
    ((d.reading_datetime AT TIME ZONE 'Asia/Kolkata')::time >= TIME '22:00'
      OR (d.reading_datetime AT TIME ZONE 'Asia/Kolkata')::time < TIME '06:00')
        AS reading_datetime_night_indicator,
    CASE WHEN d.created_on IS NULL THEN NULL
         ELSE ((d.created_on AT TIME ZONE 'Asia/Kolkata')::time >= TIME '22:00'
                OR (d.created_on AT TIME ZONE 'Asia/Kolkata')::time < TIME '06:00')
    END AS created_on_night_indicator,
    q.analytics_quality_class
FROM public.vw_sol71_reading_detail AS d
JOIN public.vw_sol71_record_quality AS q USING (reading_id);

CREATE VIEW public.vw_sol71_daily_summary AS
WITH reading_metrics AS (
    SELECT
        d.reading_id,
        d.asset_id,
        d.asset_code,
        d.asset_name,
        d.plaza_id,
        d.asset_partition_key,
        d.operational_date,
        i.cumulative_kwh,
        i.previous_cumulative_kwh,
        i.cumulative_delta_kwh,
        i.interval_kwh,
        i.reported_vs_cumulative_delta_kwh,
        i.generation_interval_class,
        q.analytics_quality_class,
        q.valid_records,
        q.exception_records,
        q.source_valid_records,
        q.source_exception_records,
        a.entry_delay,
        a.entry_delay_hours,
        a.delayed_entry_24h_or_more,
        a.negative_entry_delay_timestamp_anomaly,
        a.reading_datetime_night_indicator,
        a.created_on_night_indicator,
        d.created_on
    FROM public.vw_sol71_reading_detail AS d
    JOIN public.vw_sol71_interval_reading AS i USING (reading_id)
    JOIN public.vw_sol71_record_quality AS q USING (reading_id)
    JOIN public.vw_sol71_entry_audit AS a USING (reading_id)
)
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    asset_partition_key,
    operational_date,
    DATE_TRUNC('month', operational_date::timestamp)::date AS operational_month,
    EXTRACT(YEAR FROM operational_date)::integer AS operational_year,
    COUNT(*)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(source_valid_records)::bigint AS source_valid_records,
    SUM(source_exception_records)::bigint AS source_exception_records,
    COUNT(*)::bigint - SUM(valid_records) - SUM(exception_records) AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(COUNT(*), 0) AS observed_record_availability_pct,
    SUM(interval_kwh) FILTER (
        WHERE analytics_quality_class = 'VALID' AND interval_kwh >= 0
    ) AS valid_generation_kwh,
    COUNT(interval_kwh) FILTER (
        WHERE analytics_quality_class = 'VALID' AND interval_kwh >= 0
    )::bigint AS valid_generation_interval_count,
    AVG(interval_kwh) FILTER (
        WHERE analytics_quality_class = 'VALID' AND interval_kwh >= 0
    ) AS average_generation_interval_kwh,
    MAX(interval_kwh) FILTER (
        WHERE analytics_quality_class = 'VALID' AND interval_kwh >= 0
    ) AS maximum_generation_interval_kwh,
    COUNT(*) FILTER (
        WHERE analytics_quality_class = 'VALID' AND interval_kwh = 0
    )::bigint AS zero_generation_interval_count,
    COUNT(*) FILTER (
        WHERE generation_interval_class = 'FIRST_READING'
    )::bigint AS first_reading_count,
    COUNT(*) FILTER (
        WHERE generation_interval_class = 'MISSING_PREVIOUS_CUMULATIVE_KWH'
    )::bigint AS missing_previous_cumulative_kwh_count,
    COUNT(*) FILTER (
        WHERE generation_interval_class = 'MISSING_CUMULATIVE_KWH'
    )::bigint AS missing_cumulative_kwh_count,
    COUNT(*) FILTER (
        WHERE analytics_quality_class = 'VALID' AND interval_kwh IS NULL
    )::bigint AS missing_interval_kwh_count,
    COUNT(*) FILTER (WHERE cumulative_delta_kwh < 0)::bigint
        AS negative_cumulative_delta_exception_count,
    COUNT(*) FILTER (WHERE interval_kwh < 0)::bigint
        AS negative_interval_exception_count,
    COUNT(*) FILTER (WHERE reported_vs_cumulative_delta_kwh IS NOT NULL)::bigint
        AS interval_reconciliation_comparable_count,
    SUM(reported_vs_cumulative_delta_kwh)
        FILTER (WHERE reported_vs_cumulative_delta_kwh IS NOT NULL)
        AS reported_vs_cumulative_delta_sum_kwh,
    MAX(ABS(reported_vs_cumulative_delta_kwh))
        AS maximum_absolute_interval_reconciliation_difference_kwh,
    COUNT(*) FILTER (WHERE delayed_entry_24h_or_more IS TRUE)::bigint AS delayed_entry_count,
    COUNT(*) FILTER (
        WHERE entry_delay IS NOT NULL AND entry_delay >= INTERVAL '0 seconds'
    )::bigint AS entry_delay_eligible_count,
    100.0 * COUNT(*) FILTER (WHERE delayed_entry_24h_or_more IS TRUE)
        / NULLIF(COUNT(*) FILTER (
            WHERE entry_delay IS NOT NULL AND entry_delay >= INTERVAL '0 seconds'
        ), 0) AS delayed_entry_percentage,
    SUM(entry_delay) FILTER (WHERE entry_delay >= INTERVAL '0 seconds')
        AS eligible_entry_delay_sum,
    AVG(entry_delay_hours) FILTER (WHERE entry_delay >= INTERVAL '0 seconds')
        AS average_entry_delay_hours,
    MAX(entry_delay_hours) FILTER (WHERE entry_delay >= INTERVAL '0 seconds')
        AS maximum_entry_delay_hours,
    COUNT(*) FILTER (WHERE negative_entry_delay_timestamp_anomaly IS TRUE)::bigint
        AS negative_entry_delay_timestamp_anomaly_count,
    COUNT(*) FILTER (WHERE created_on IS NOT NULL)::bigint AS created_on_timestamp_count,
    COUNT(*) FILTER (WHERE reading_datetime_night_indicator IS TRUE)::bigint AS night_reading_count,
    COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE)::bigint AS night_entry_count,
    100.0 * COUNT(*) FILTER (WHERE reading_datetime_night_indicator IS TRUE)
        / NULLIF(COUNT(*), 0) AS night_reading_percentage,
    100.0 * COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE)
        / NULLIF(COUNT(*) FILTER (WHERE created_on IS NOT NULL), 0) AS night_entry_percentage,
    COUNT(*) FILTER (WHERE reading_datetime_night_indicator IS TRUE
                       AND analytics_quality_class = 'VALID')::bigint AS valid_night_reading_count,
    COUNT(*) FILTER (WHERE reading_datetime_night_indicator IS TRUE
                       AND analytics_quality_class = 'EXCEPTION')::bigint AS exception_night_reading_count,
    COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE
                       AND analytics_quality_class = 'VALID')::bigint AS valid_night_entry_count,
    COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE
                       AND analytics_quality_class = 'EXCEPTION')::bigint AS exception_night_entry_count
FROM reading_metrics
GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_date;

CREATE VIEW public.vw_sol71_monthly_summary AS
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    asset_partition_key,
    operational_month,
    COUNT(*)::bigint AS observed_asset_days,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
    SUM(valid_generation_kwh) AS solar_generation_kwh,
    AVG(valid_generation_kwh) AS average_generation_per_observed_day_kwh,
    MAX(valid_generation_kwh) AS maximum_daily_generation_kwh,
    SUM(valid_generation_interval_count)::bigint AS valid_generation_interval_count,
    SUM(zero_generation_interval_count)::bigint AS zero_generation_interval_count,
    SUM(first_reading_count)::bigint AS first_reading_count,
    SUM(missing_previous_cumulative_kwh_count)::bigint AS missing_previous_cumulative_kwh_count,
    SUM(missing_cumulative_kwh_count)::bigint AS missing_cumulative_kwh_count,
    SUM(missing_interval_kwh_count)::bigint AS missing_interval_kwh_count,
    SUM(negative_cumulative_delta_exception_count)::bigint AS negative_cumulative_delta_exception_count,
    SUM(negative_interval_exception_count)::bigint AS negative_interval_exception_count,
    SUM(interval_reconciliation_comparable_count)::bigint AS interval_reconciliation_comparable_count,
    SUM(reported_vs_cumulative_delta_sum_kwh) AS reported_vs_cumulative_delta_sum_kwh,
    MAX(maximum_absolute_interval_reconciliation_difference_kwh)
        AS maximum_absolute_interval_reconciliation_difference_kwh,
    SUM(delayed_entry_count)::bigint AS delayed_entry_count,
    SUM(entry_delay_eligible_count)::bigint AS entry_delay_eligible_count,
    100.0 * SUM(delayed_entry_count) / NULLIF(SUM(entry_delay_eligible_count), 0)
        AS delayed_entry_percentage,
    SUM(EXTRACT(EPOCH FROM eligible_entry_delay_sum)) / 3600.0
        / NULLIF(SUM(entry_delay_eligible_count), 0) AS average_entry_delay_hours,
    MAX(maximum_entry_delay_hours) AS maximum_entry_delay_hours,
    SUM(negative_entry_delay_timestamp_anomaly_count)::bigint
        AS negative_entry_delay_timestamp_anomaly_count,
    SUM(created_on_timestamp_count)::bigint AS created_on_timestamp_count,
    SUM(night_reading_count)::bigint AS night_reading_count,
    SUM(night_entry_count)::bigint AS night_entry_count,
    100.0 * SUM(night_reading_count) / NULLIF(SUM(total_records), 0) AS night_reading_percentage,
    100.0 * SUM(night_entry_count) / NULLIF(SUM(created_on_timestamp_count), 0)
        AS night_entry_percentage,
    SUM(valid_night_reading_count)::bigint AS valid_night_reading_count,
    SUM(exception_night_reading_count)::bigint AS exception_night_reading_count,
    SUM(valid_night_entry_count)::bigint AS valid_night_entry_count,
    SUM(exception_night_entry_count)::bigint AS exception_night_entry_count
FROM public.vw_sol71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_month;

CREATE VIEW public.vw_sol71_yearly_summary AS
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    asset_partition_key,
    operational_year,
    COUNT(*)::bigint AS observed_asset_days,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
    SUM(valid_generation_kwh) AS solar_generation_kwh,
    AVG(valid_generation_kwh) AS average_generation_per_observed_day_kwh,
    MAX(valid_generation_kwh) AS maximum_daily_generation_kwh,
    SUM(valid_generation_interval_count)::bigint AS valid_generation_interval_count,
    SUM(zero_generation_interval_count)::bigint AS zero_generation_interval_count,
    SUM(first_reading_count)::bigint AS first_reading_count,
    SUM(missing_previous_cumulative_kwh_count)::bigint AS missing_previous_cumulative_kwh_count,
    SUM(missing_cumulative_kwh_count)::bigint AS missing_cumulative_kwh_count,
    SUM(missing_interval_kwh_count)::bigint AS missing_interval_kwh_count,
    SUM(negative_cumulative_delta_exception_count)::bigint AS negative_cumulative_delta_exception_count,
    SUM(negative_interval_exception_count)::bigint AS negative_interval_exception_count,
    SUM(interval_reconciliation_comparable_count)::bigint AS interval_reconciliation_comparable_count,
    SUM(reported_vs_cumulative_delta_sum_kwh) AS reported_vs_cumulative_delta_sum_kwh,
    MAX(maximum_absolute_interval_reconciliation_difference_kwh)
        AS maximum_absolute_interval_reconciliation_difference_kwh,
    SUM(delayed_entry_count)::bigint AS delayed_entry_count,
    SUM(entry_delay_eligible_count)::bigint AS entry_delay_eligible_count,
    100.0 * SUM(delayed_entry_count) / NULLIF(SUM(entry_delay_eligible_count), 0)
        AS delayed_entry_percentage,
    SUM(EXTRACT(EPOCH FROM eligible_entry_delay_sum)) / 3600.0
        / NULLIF(SUM(entry_delay_eligible_count), 0) AS average_entry_delay_hours,
    MAX(maximum_entry_delay_hours) AS maximum_entry_delay_hours,
    SUM(negative_entry_delay_timestamp_anomaly_count)::bigint
        AS negative_entry_delay_timestamp_anomaly_count,
    SUM(created_on_timestamp_count)::bigint AS created_on_timestamp_count,
    SUM(night_reading_count)::bigint AS night_reading_count,
    SUM(night_entry_count)::bigint AS night_entry_count,
    100.0 * SUM(night_reading_count) / NULLIF(SUM(total_records), 0) AS night_reading_percentage,
    100.0 * SUM(night_entry_count) / NULLIF(SUM(created_on_timestamp_count), 0)
        AS night_entry_percentage,
    SUM(valid_night_reading_count)::bigint AS valid_night_reading_count,
    SUM(exception_night_reading_count)::bigint AS exception_night_reading_count,
    SUM(valid_night_entry_count)::bigint AS valid_night_entry_count,
    SUM(exception_night_entry_count)::bigint AS exception_night_entry_count
FROM public.vw_sol71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_year;

CREATE VIEW public.vw_sol71_analytics_summary AS
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    asset_partition_key,
    COUNT(*)::bigint AS observed_asset_days,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
    SUM(valid_generation_kwh) AS solar_generation_kwh,
    AVG(valid_generation_kwh) AS average_generation_per_observed_day_kwh,
    MAX(valid_generation_kwh) AS maximum_daily_generation_kwh,
    SUM(valid_generation_interval_count)::bigint AS valid_generation_interval_count,
    SUM(zero_generation_interval_count)::bigint AS zero_generation_interval_count,
    SUM(first_reading_count)::bigint AS first_reading_count,
    SUM(missing_previous_cumulative_kwh_count)::bigint AS missing_previous_cumulative_kwh_count,
    SUM(missing_cumulative_kwh_count)::bigint AS missing_cumulative_kwh_count,
    SUM(missing_interval_kwh_count)::bigint AS missing_interval_kwh_count,
    SUM(negative_cumulative_delta_exception_count)::bigint AS negative_cumulative_delta_exception_count,
    SUM(negative_interval_exception_count)::bigint AS negative_interval_exception_count,
    SUM(interval_reconciliation_comparable_count)::bigint AS interval_reconciliation_comparable_count,
    SUM(reported_vs_cumulative_delta_sum_kwh) AS reported_vs_cumulative_delta_sum_kwh,
    MAX(maximum_absolute_interval_reconciliation_difference_kwh)
        AS maximum_absolute_interval_reconciliation_difference_kwh,
    SUM(delayed_entry_count)::bigint AS delayed_entry_count,
    SUM(entry_delay_eligible_count)::bigint AS entry_delay_eligible_count,
    100.0 * SUM(delayed_entry_count) / NULLIF(SUM(entry_delay_eligible_count), 0)
        AS delayed_entry_percentage,
    SUM(EXTRACT(EPOCH FROM eligible_entry_delay_sum)) / 3600.0
        / NULLIF(SUM(entry_delay_eligible_count), 0) AS average_entry_delay_hours,
    MAX(maximum_entry_delay_hours) AS maximum_entry_delay_hours,
    SUM(negative_entry_delay_timestamp_anomaly_count)::bigint
        AS negative_entry_delay_timestamp_anomaly_count,
    SUM(created_on_timestamp_count)::bigint AS created_on_timestamp_count,
    SUM(night_reading_count)::bigint AS night_reading_count,
    SUM(night_entry_count)::bigint AS night_entry_count,
    100.0 * SUM(night_reading_count) / NULLIF(SUM(total_records), 0) AS night_reading_percentage,
    100.0 * SUM(night_entry_count) / NULLIF(SUM(created_on_timestamp_count), 0)
        AS night_entry_percentage,
    SUM(valid_night_reading_count)::bigint AS valid_night_reading_count,
    SUM(exception_night_reading_count)::bigint AS exception_night_reading_count,
    SUM(valid_night_entry_count)::bigint AS valid_night_entry_count,
    SUM(exception_night_entry_count)::bigint AS exception_night_entry_count
FROM public.vw_sol71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key;

CREATE VIEW public.vw_sol71_asset_latest_reading AS
SELECT
    a.asset_id,
    a.asset_code,
    a.asset_name,
    a.plaza_id,
    a.source_type,
    a.capacity_kva,
    latest.reading_id,
    latest.reading_datetime,
    latest.cumulative_kwh AS latest_cumulative_kwh,
    latest.interval_kwh AS latest_interval_kwh,
    latest.source_data_quality_status,
    q.analytics_quality_class,
    latest.created_by,
    latest.created_on,
    latest.remarks
FROM energy_master.asset AS a
LEFT JOIN LATERAL (
    SELECT d.*
    FROM public.vw_sol71_reading_detail AS d
    WHERE d.asset_id = a.asset_id
       OR (d.asset_id IS NULL AND d.asset_code = a.asset_code)
    ORDER BY d.reading_datetime DESC NULLS LAST, d.reading_id DESC
    LIMIT 1
) AS latest ON TRUE
LEFT JOIN public.vw_sol71_record_quality AS q USING (reading_id)
WHERE a.source_type = 'SOLAR';


-- >>> END OF Solar_Module_Analytics_Proposed.sql <<<


-- >>> START OF Solar_Module_Fix_Asset_Latest_View.sql <<<

-- Safe recovery for the final Solar asset-latest view after a partial run.
-- Creates this new view only if it is absent; it never replaces or drops one.

DO $solar_asset_latest_recovery$
BEGIN
    IF to_regclass('public.vw_sol71_asset_latest_reading') IS NOT NULL THEN
        RAISE NOTICE 'Skipping: public.vw_sol71_asset_latest_reading already exists and was left unchanged.';
    ELSIF to_regclass('public.vw_sol71_reading_detail') IS NULL
       OR to_regclass('public.vw_sol71_record_quality') IS NULL THEN
        RAISE NOTICE 'Skipping: deploy the Solar reading-detail and record-quality views first.';
    ELSE
        EXECUTE $view$
            CREATE VIEW public.vw_sol71_asset_latest_reading AS
            SELECT
                a.asset_id,
                a.asset_code,
                a.asset_name,
                a.plaza_id,
                a.source_type,
                a.capacity_kva,
                latest.reading_id,
                latest.reading_datetime,
                latest.cumulative_kwh AS latest_cumulative_kwh,
                latest.interval_kwh AS latest_interval_kwh,
                latest.source_data_quality_status,
                q.analytics_quality_class,
                latest.created_by,
                latest.created_on,
                latest.remarks
            FROM energy_master.asset AS a
            LEFT JOIN LATERAL (
                SELECT d.*
                FROM public.vw_sol71_reading_detail AS d
                WHERE d.asset_id = a.asset_id
                   OR (d.asset_id IS NULL AND d.asset_code = a.asset_code)
                ORDER BY d.reading_datetime DESC NULLS LAST, d.reading_id DESC
                LIMIT 1
            ) AS latest ON TRUE
            LEFT JOIN public.vw_sol71_record_quality AS q USING (reading_id)
            WHERE a.source_type = 'SOLAR'
        $view$;
        RAISE NOTICE 'Created public.vw_sol71_asset_latest_reading.';
    END IF;
END
$solar_asset_latest_recovery$;


-- >>> END OF Solar_Module_Fix_Asset_Latest_View.sql <<<


-- >>> START OF Transformer_Module_Analytics_Proposed.sql <<<

-- SRTPL Energy Command Center - Transformer Analytics
-- PROPOSAL ONLY. Nothing in this file has been executed against a database.
-- PostgreSQL / Supabase. Adds new public.vw_trf71_* views only; no DROP,
-- CREATE OR REPLACE, schema/table changes, or source-data writes are included.
-- Run the separate read-only preflight before using these definitions.

CREATE VIEW public.vw_trf71_reading_detail AS
WITH reading_source AS (
    SELECT
        d.reading_id,
        d.asset_id,
        COALESCE(d.asset_code, a.asset_code) AS asset_code,
        a.asset_name,
        a.plaza_id,
        d.reading_datetime,
        CASE
            WHEN pg_typeof(d.reading_datetime) = 'timestamp without time zone'::regtype
                THEN d.reading_datetime::date
            ELSE (d.reading_datetime AT TIME ZONE 'Asia/Kolkata')::date
        END AS operational_date,
        d.primary_v_ry,
        d.primary_v_yb,
        d.primary_v_br,
        d.secondary_v_ry,
        d.secondary_v_yb,
        d.secondary_v_br,
        d.primary_i_r,
        d.primary_i_y,
        d.primary_i_b,
        d.secondary_i_r,
        d.secondary_i_y,
        d.secondary_i_b,
        d.pf,
        d.created_by,
        d.created_on,
        d.created_at,
        d.remarks,
        d.location,
        d.data_quality_status AS source_data_quality_status,
        CASE
            WHEN UPPER(BTRIM(COALESCE(d.data_quality_status, ''))) = 'VALID' THEN 'VALID'
            ELSE 'EXCEPTION'
        END AS source_quality_class,
        COALESCE(
            'ID:' || d.asset_id::text,
            'CODE:' || COALESCE(d.asset_code, a.asset_code),
            'ROW:' || d.reading_id::text
        ) AS asset_partition_key,
        to_jsonb(d) AS reading_payload
    FROM energy_readings.transformer AS d
    LEFT JOIN energy_master.asset AS a
        ON (d.asset_id IS NOT NULL AND a.asset_id = d.asset_id)
        OR (d.asset_id IS NULL AND a.asset_code = d.asset_code AND a.source_type = 'TRANSFORMER')
),
normalized_values AS (
    SELECT
        r.*,
        CASE
            WHEN r.reading_payload->>'cumulative_kwh' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'cumulative_kwh')::numeric
            WHEN r.reading_payload->>'kwh' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'kwh')::numeric
        END AS cumulative_kwh_value,
        CASE
            WHEN r.reading_payload->>'cumulative_kvah' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'cumulative_kvah')::numeric
            WHEN r.reading_payload->>'kvah' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'kvah')::numeric
        END AS cumulative_kvah_value,
        CASE
            WHEN r.reading_payload->>'interval_kwh' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'interval_kwh')::numeric
        END AS interval_kwh_value,
        CASE
            WHEN r.reading_payload->>'interval_kvah' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'interval_kvah')::numeric
        END AS interval_kvah_value,
        CASE
            WHEN r.reading_payload->>'frequency' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'frequency')::numeric
        END AS frequency_hz,
        CASE
            WHEN r.reading_payload->>'oil_temperature' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'oil_temperature')::numeric
            WHEN r.reading_payload->>'oti' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'oti')::numeric
            WHEN r.reading_payload->>'oil_temperature_c' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'oil_temperature_c')::numeric
        END AS oil_temperature_c,
        CASE
            WHEN r.reading_payload->>'winding_temperature' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'winding_temperature')::numeric
            WHEN r.reading_payload->>'wti' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'wti')::numeric
            WHEN r.reading_payload->>'winding_temperature_c' ~ '^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$'
            THEN (r.reading_payload->>'winding_temperature_c')::numeric
        END AS winding_temperature_c
    FROM reading_source AS r
)
SELECT
    n.reading_id,
    n.asset_id,
    n.asset_code,
    n.asset_name,
    n.plaza_id,
    n.asset_partition_key,
    n.reading_datetime,
    n.operational_date,
    n.primary_v_ry,
    n.primary_v_yb,
    n.primary_v_br,
    n.secondary_v_ry,
    n.secondary_v_yb,
    n.secondary_v_br,
    n.primary_i_r,
    n.primary_i_y,
    n.primary_i_b,
    n.secondary_i_r,
    n.secondary_i_y,
    n.secondary_i_b,
    n.cumulative_kwh_value,
    n.cumulative_kvah_value,
    n.interval_kwh_value,
    n.interval_kvah_value,
    n.frequency_hz,
    n.oil_temperature_c,
    n.winding_temperature_c,
    n.pf,
    n.created_by,
    n.created_on,
    n.created_at,
    n.remarks,
    n.location,
    n.source_data_quality_status,
    n.source_quality_class
FROM normalized_values AS n;

CREATE VIEW public.vw_trf71_electrical_reading AS
WITH phase_means AS (
    SELECT
        d.*,
        CASE WHEN d.primary_v_ry IS NOT NULL AND d.primary_v_yb IS NOT NULL AND d.primary_v_br IS NOT NULL
             THEN (d.primary_v_ry + d.primary_v_yb + d.primary_v_br) / 3.0 END AS primary_voltage_mean,
        CASE WHEN d.secondary_v_ry IS NOT NULL AND d.secondary_v_yb IS NOT NULL AND d.secondary_v_br IS NOT NULL
             THEN (d.secondary_v_ry + d.secondary_v_yb + d.secondary_v_br) / 3.0 END AS secondary_voltage_mean,
        CASE WHEN d.primary_i_r IS NOT NULL AND d.primary_i_y IS NOT NULL AND d.primary_i_b IS NOT NULL
             THEN (d.primary_i_r + d.primary_i_y + d.primary_i_b) / 3.0 END AS primary_current_mean,
        CASE WHEN d.secondary_i_r IS NOT NULL AND d.secondary_i_y IS NOT NULL AND d.secondary_i_b IS NOT NULL
             THEN (d.secondary_i_r + d.secondary_i_y + d.secondary_i_b) / 3.0 END AS secondary_current_mean,
        (CASE WHEN d.primary_v_ry IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN d.primary_v_yb IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN d.primary_v_br IS NOT NULL THEN 1 ELSE 0 END) AS primary_voltage_phase_count,
        (CASE WHEN d.secondary_v_ry IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN d.secondary_v_yb IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN d.secondary_v_br IS NOT NULL THEN 1 ELSE 0 END) AS secondary_voltage_phase_count,
        (CASE WHEN d.primary_i_r IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN d.primary_i_y IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN d.primary_i_b IS NOT NULL THEN 1 ELSE 0 END) AS primary_current_phase_count,
        (CASE WHEN d.secondary_i_r IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN d.secondary_i_y IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN d.secondary_i_b IS NOT NULL THEN 1 ELSE 0 END) AS secondary_current_phase_count
    FROM public.vw_trf71_reading_detail AS d
),
imbalance_scores AS (
    SELECT
        p.*,
        CASE
            WHEN p.primary_voltage_phase_count <> 3 THEN NULL
            WHEN p.primary_voltage_mean = 0
             AND p.primary_v_ry = 0 AND p.primary_v_yb = 0 AND p.primary_v_br = 0 THEN 0::numeric
            WHEN p.primary_voltage_mean > 0
            THEN GREATEST(ABS(p.primary_v_ry - p.primary_voltage_mean),
                          ABS(p.primary_v_yb - p.primary_voltage_mean),
                          ABS(p.primary_v_br - p.primary_voltage_mean))
                 / p.primary_voltage_mean * 100.0
        END AS primary_voltage_imbalance_pct,
        CASE
            WHEN p.secondary_voltage_phase_count <> 3 THEN NULL
            WHEN p.secondary_voltage_mean = 0
             AND p.secondary_v_ry = 0 AND p.secondary_v_yb = 0 AND p.secondary_v_br = 0 THEN 0::numeric
            WHEN p.secondary_voltage_mean > 0
            THEN GREATEST(ABS(p.secondary_v_ry - p.secondary_voltage_mean),
                          ABS(p.secondary_v_yb - p.secondary_voltage_mean),
                          ABS(p.secondary_v_br - p.secondary_voltage_mean))
                 / p.secondary_voltage_mean * 100.0
        END AS secondary_voltage_imbalance_pct,
        CASE
            WHEN p.primary_current_phase_count <> 3 THEN NULL
            WHEN p.primary_current_mean = 0
             AND p.primary_i_r = 0 AND p.primary_i_y = 0 AND p.primary_i_b = 0 THEN 0::numeric
            WHEN p.primary_current_mean > 0
            THEN GREATEST(ABS(p.primary_i_r - p.primary_current_mean),
                          ABS(p.primary_i_y - p.primary_current_mean),
                          ABS(p.primary_i_b - p.primary_current_mean))
                 / p.primary_current_mean * 100.0
        END AS primary_current_imbalance_pct,
        CASE
            WHEN p.secondary_current_phase_count <> 3 THEN NULL
            WHEN p.secondary_current_mean = 0
             AND p.secondary_i_r = 0 AND p.secondary_i_y = 0 AND p.secondary_i_b = 0 THEN 0::numeric
            WHEN p.secondary_current_mean > 0
            THEN GREATEST(ABS(p.secondary_i_r - p.secondary_current_mean),
                          ABS(p.secondary_i_y - p.secondary_current_mean),
                          ABS(p.secondary_i_b - p.secondary_current_mean))
                 / p.secondary_current_mean * 100.0
        END AS secondary_current_imbalance_pct
    FROM phase_means AS p
)
SELECT
    s.*,
    s.primary_voltage_phase_count = 3 AS primary_voltage_triplet_complete,
    s.secondary_voltage_phase_count = 3 AS secondary_voltage_triplet_complete,
    s.primary_current_phase_count = 3 AS primary_current_triplet_complete,
    s.secondary_current_phase_count = 3 AS secondary_current_triplet_complete
FROM imbalance_scores AS s;

CREATE VIEW public.vw_trf71_record_quality AS
SELECT
    d.reading_id,
    d.asset_id,
    d.asset_code,
    d.asset_name,
    d.plaza_id,
    d.operational_date,
    d.reading_datetime,
    1::bigint AS total_records,
    CASE WHEN d.source_quality_class = 'VALID' THEN 1::bigint ELSE 0::bigint END AS source_valid_records,
    CASE WHEN d.source_quality_class = 'EXCEPTION' THEN 1::bigint ELSE 0::bigint END AS source_exception_records,
    CASE WHEN d.source_quality_class = 'VALID' AND (d.pf IS NULL OR d.pf BETWEEN 0 AND 1)
         THEN 1::bigint ELSE 0::bigint END AS valid_records,
    CASE WHEN d.source_quality_class <> 'VALID' OR (d.pf IS NOT NULL AND (d.pf < 0 OR d.pf > 1))
         THEN 1::bigint ELSE 0::bigint END AS exception_records,
    CASE WHEN d.source_quality_class = 'VALID' AND (d.pf IS NULL OR d.pf BETWEEN 0 AND 1)
         THEN 'VALID' ELSE 'EXCEPTION' END AS analytics_quality_class,
    1::bigint
      - CASE WHEN d.source_quality_class = 'VALID' AND (d.pf IS NULL OR d.pf BETWEEN 0 AND 1)
             THEN 1::bigint ELSE 0::bigint END
      - CASE WHEN d.source_quality_class <> 'VALID' OR (d.pf IS NOT NULL AND (d.pf < 0 OR d.pf > 1))
             THEN 1::bigint ELSE 0::bigint END AS reconciliation_difference,
    d.source_data_quality_status,
    CASE
        WHEN d.source_quality_class <> 'VALID' THEN 'SOURCE_STATUS_EXCEPTION'
        WHEN d.pf IS NOT NULL AND (d.pf < 0 OR d.pf > 1) THEN 'POWER_FACTOR_OUTSIDE_0_TO_1'
        ELSE NULL
    END AS analytics_exception_reasons
FROM public.vw_trf71_reading_detail AS d;

CREATE VIEW public.vw_trf71_entry_audit AS
SELECT
    d.reading_id,
    d.asset_id,
    d.asset_code,
    d.asset_name,
    d.plaza_id,
    d.operational_date,
    d.reading_datetime,
    d.created_on,
    d.created_by,
    d.created_at AS database_inserted_at,
    d.created_on - d.reading_datetime AS entry_delay,
    EXTRACT(EPOCH FROM (d.created_on - d.reading_datetime)) / 3600.0 AS entry_delay_hours,
    CASE WHEN d.created_on IS NULL THEN NULL
         WHEN d.created_on < d.reading_datetime THEN TRUE ELSE FALSE
    END AS negative_entry_delay_timestamp_anomaly,
    CASE WHEN d.created_on IS NULL OR d.created_on < d.reading_datetime THEN NULL
         WHEN d.created_on - d.reading_datetime >= INTERVAL '24 hours' THEN TRUE ELSE FALSE
    END AS delayed_entry_24h_or_more,
    CASE WHEN d.created_on IS NULL OR d.created_on < d.reading_datetime THEN NULL
         WHEN d.created_on - d.reading_datetime < INTERVAL '24 hours' THEN TRUE ELSE FALSE
    END AS entry_within_24h,
    CASE
        WHEN pg_typeof(d.reading_datetime) = 'timestamp without time zone'::regtype
            THEN (d.reading_datetime::time >= TIME '22:00'
                  OR d.reading_datetime::time < TIME '06:00')
        ELSE ((d.reading_datetime AT TIME ZONE 'Asia/Kolkata')::time >= TIME '22:00'
              OR (d.reading_datetime AT TIME ZONE 'Asia/Kolkata')::time < TIME '06:00')
    END
        AS reading_datetime_night_indicator,
    CASE WHEN d.created_on IS NULL THEN NULL
         WHEN pg_typeof(d.created_on) = 'timestamp without time zone'::regtype
            THEN (d.created_on::time >= TIME '22:00'
                  OR d.created_on::time < TIME '06:00')
         ELSE ((d.created_on AT TIME ZONE 'Asia/Kolkata')::time >= TIME '22:00'
               OR (d.created_on AT TIME ZONE 'Asia/Kolkata')::time < TIME '06:00')
    END AS created_on_night_indicator,
    q.analytics_quality_class
FROM public.vw_trf71_reading_detail AS d
JOIN public.vw_trf71_record_quality AS q USING (reading_id);

CREATE VIEW public.vw_trf71_daily_summary AS
WITH reading_metrics AS (
    SELECT
        d.reading_id,
        d.asset_id,
        d.asset_code,
        d.asset_name,
        d.plaza_id,
        d.asset_partition_key,
        d.operational_date,
        q.analytics_quality_class,
        q.valid_records,
        q.exception_records,
        q.source_valid_records,
        q.source_exception_records,
        e.pf,
        e.frequency_hz,
        e.oil_temperature_c,
        e.winding_temperature_c,
        e.primary_voltage_imbalance_pct,
        e.secondary_voltage_imbalance_pct,
        e.primary_current_imbalance_pct,
        e.secondary_current_imbalance_pct,
        e.primary_voltage_phase_count,
        e.secondary_voltage_phase_count,
        e.primary_current_phase_count,
        e.secondary_current_phase_count,
        a.entry_delay,
        a.delayed_entry_24h_or_more,
        a.negative_entry_delay_timestamp_anomaly,
        a.reading_datetime_night_indicator,
        a.created_on_night_indicator
    FROM public.vw_trf71_reading_detail AS d
    JOIN public.vw_trf71_record_quality AS q USING (reading_id)
    JOIN public.vw_trf71_electrical_reading AS e USING (reading_id)
    JOIN public.vw_trf71_entry_audit AS a USING (reading_id)
)
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    asset_partition_key,
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
    SUM(pf) FILTER (WHERE analytics_quality_class = 'VALID' AND pf IS NOT NULL) AS valid_pf_sum,
    COUNT(pf) FILTER (WHERE analytics_quality_class = 'VALID')::bigint AS valid_pf_count,
    AVG(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS average_pf,
    MIN(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_pf,
    MAX(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_pf,
    AVG(frequency_hz) FILTER (WHERE analytics_quality_class = 'VALID') AS average_frequency_hz,
    SUM(frequency_hz) FILTER (WHERE analytics_quality_class = 'VALID' AND frequency_hz IS NOT NULL)
        AS valid_frequency_sum,
    COUNT(frequency_hz) FILTER (WHERE analytics_quality_class = 'VALID')::bigint AS valid_frequency_count,
    MIN(frequency_hz) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_frequency_hz,
    MAX(frequency_hz) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_frequency_hz,
    SUM(oil_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID' AND oil_temperature_c IS NOT NULL)
        AS valid_oil_temperature_sum,
    COUNT(oil_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID')::bigint AS valid_oil_temperature_count,
    AVG(oil_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS average_oil_temperature_c,
    MIN(oil_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_oil_temperature_c,
    MAX(oil_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_oil_temperature_c,
    SUM(winding_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID' AND winding_temperature_c IS NOT NULL)
        AS valid_winding_temperature_sum,
    COUNT(winding_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID')::bigint
        AS valid_winding_temperature_count,
    AVG(winding_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS average_winding_temperature_c,
    MIN(winding_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_winding_temperature_c,
    MAX(winding_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_winding_temperature_c,
    SUM(primary_voltage_imbalance_pct)
        FILTER (WHERE analytics_quality_class = 'VALID' AND primary_voltage_imbalance_pct IS NOT NULL)
        AS valid_primary_voltage_imbalance_sum,
    COUNT(primary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')::bigint
        AS valid_primary_voltage_imbalance_count,
    AVG(primary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')
        AS average_primary_voltage_imbalance_pct,
    MAX(primary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')
        AS maximum_primary_voltage_imbalance_pct,
    SUM(secondary_voltage_imbalance_pct)
        FILTER (WHERE analytics_quality_class = 'VALID' AND secondary_voltage_imbalance_pct IS NOT NULL)
        AS valid_secondary_voltage_imbalance_sum,
    COUNT(secondary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')::bigint
        AS valid_secondary_voltage_imbalance_count,
    AVG(secondary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')
        AS average_secondary_voltage_imbalance_pct,
    MAX(secondary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')
        AS maximum_secondary_voltage_imbalance_pct,
    SUM(primary_current_imbalance_pct)
        FILTER (WHERE analytics_quality_class = 'VALID' AND primary_current_imbalance_pct IS NOT NULL)
        AS valid_primary_current_imbalance_sum,
    COUNT(primary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')::bigint
        AS valid_primary_current_imbalance_count,
    AVG(primary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')
        AS average_primary_current_imbalance_pct,
    MAX(primary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')
        AS maximum_primary_current_imbalance_pct,
    SUM(secondary_current_imbalance_pct)
        FILTER (WHERE analytics_quality_class = 'VALID' AND secondary_current_imbalance_pct IS NOT NULL)
        AS valid_secondary_current_imbalance_sum,
    COUNT(secondary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')::bigint
        AS valid_secondary_current_imbalance_count,
    AVG(secondary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')
        AS average_secondary_current_imbalance_pct,
    MAX(secondary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID')
        AS maximum_secondary_current_imbalance_pct,
    COUNT(*) FILTER (WHERE primary_voltage_phase_count < 3)::bigint AS incomplete_primary_voltage_triplet_count,
    COUNT(*) FILTER (WHERE secondary_voltage_phase_count < 3)::bigint AS incomplete_secondary_voltage_triplet_count,
    COUNT(*) FILTER (WHERE primary_current_phase_count < 3)::bigint AS incomplete_primary_current_triplet_count,
    COUNT(*) FILTER (WHERE secondary_current_phase_count < 3)::bigint AS incomplete_secondary_current_triplet_count,
    COUNT(*) FILTER (WHERE pf IS NOT NULL AND (pf < 0 OR pf > 1))::bigint AS out_of_range_pf_count,
    COUNT(*) FILTER (WHERE delayed_entry_24h_or_more IS TRUE)::bigint AS delayed_entry_count,
    COUNT(*) FILTER (WHERE entry_delay IS NOT NULL AND entry_delay >= INTERVAL '0 seconds')::bigint
        AS entry_delay_eligible_count,
    100.0 * COUNT(*) FILTER (WHERE delayed_entry_24h_or_more IS TRUE)
        / NULLIF(COUNT(*) FILTER (WHERE entry_delay IS NOT NULL AND entry_delay >= INTERVAL '0 seconds'), 0)
        AS delayed_entry_percentage,
    AVG(entry_delay) FILTER (WHERE entry_delay >= INTERVAL '0 seconds') AS average_entry_delay,
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
GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_date;

CREATE VIEW public.vw_trf71_monthly_summary AS
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    asset_partition_key,
    operational_month,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    SUM(valid_pf_sum) / NULLIF(SUM(valid_pf_count), 0) AS average_pf,
    MIN(minimum_pf) AS minimum_pf,
    MAX(maximum_pf) AS maximum_pf,
    SUM(valid_frequency_sum) / NULLIF(SUM(valid_frequency_count), 0) AS average_frequency_hz,
    MIN(minimum_frequency_hz) AS minimum_frequency_hz,
    MAX(maximum_frequency_hz) AS maximum_frequency_hz,
    SUM(valid_oil_temperature_sum) / NULLIF(SUM(valid_oil_temperature_count), 0) AS average_oil_temperature_c,
    MIN(minimum_oil_temperature_c) AS minimum_oil_temperature_c,
    MAX(maximum_oil_temperature_c) AS maximum_oil_temperature_c,
    SUM(valid_winding_temperature_sum) / NULLIF(SUM(valid_winding_temperature_count), 0)
        AS average_winding_temperature_c,
    MIN(minimum_winding_temperature_c) AS minimum_winding_temperature_c,
    MAX(maximum_winding_temperature_c) AS maximum_winding_temperature_c,
    SUM(valid_primary_voltage_imbalance_sum) / NULLIF(SUM(valid_primary_voltage_imbalance_count), 0)
        AS average_primary_voltage_imbalance_pct,
    MAX(maximum_primary_voltage_imbalance_pct) AS maximum_primary_voltage_imbalance_pct,
    SUM(valid_secondary_voltage_imbalance_sum) / NULLIF(SUM(valid_secondary_voltage_imbalance_count), 0)
        AS average_secondary_voltage_imbalance_pct,
    MAX(maximum_secondary_voltage_imbalance_pct) AS maximum_secondary_voltage_imbalance_pct,
    SUM(valid_primary_current_imbalance_sum) / NULLIF(SUM(valid_primary_current_imbalance_count), 0)
        AS average_primary_current_imbalance_pct,
    MAX(maximum_primary_current_imbalance_pct) AS maximum_primary_current_imbalance_pct,
    SUM(valid_secondary_current_imbalance_sum) / NULLIF(SUM(valid_secondary_current_imbalance_count), 0)
        AS average_secondary_current_imbalance_pct,
    MAX(maximum_secondary_current_imbalance_pct) AS maximum_secondary_current_imbalance_pct,
    SUM(incomplete_primary_voltage_triplet_count)::bigint AS incomplete_primary_voltage_triplet_count,
    SUM(incomplete_secondary_voltage_triplet_count)::bigint AS incomplete_secondary_voltage_triplet_count,
    SUM(incomplete_primary_current_triplet_count)::bigint AS incomplete_primary_current_triplet_count,
    SUM(incomplete_secondary_current_triplet_count)::bigint AS incomplete_secondary_current_triplet_count,
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
FROM public.vw_trf71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_month;

CREATE VIEW public.vw_trf71_yearly_summary AS
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    asset_partition_key,
    operational_year,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    SUM(valid_pf_sum) / NULLIF(SUM(valid_pf_count), 0) AS average_pf,
    MIN(minimum_pf) AS minimum_pf,
    MAX(maximum_pf) AS maximum_pf,
    SUM(valid_frequency_sum) / NULLIF(SUM(valid_frequency_count), 0) AS average_frequency_hz,
    MIN(minimum_frequency_hz) AS minimum_frequency_hz,
    MAX(maximum_frequency_hz) AS maximum_frequency_hz,
    SUM(valid_oil_temperature_sum) / NULLIF(SUM(valid_oil_temperature_count), 0) AS average_oil_temperature_c,
    MIN(minimum_oil_temperature_c) AS minimum_oil_temperature_c,
    MAX(maximum_oil_temperature_c) AS maximum_oil_temperature_c,
    SUM(valid_winding_temperature_sum) / NULLIF(SUM(valid_winding_temperature_count), 0)
        AS average_winding_temperature_c,
    MIN(minimum_winding_temperature_c) AS minimum_winding_temperature_c,
    MAX(maximum_winding_temperature_c) AS maximum_winding_temperature_c,
    SUM(valid_primary_voltage_imbalance_sum) / NULLIF(SUM(valid_primary_voltage_imbalance_count), 0)
        AS average_primary_voltage_imbalance_pct,
    MAX(maximum_primary_voltage_imbalance_pct) AS maximum_primary_voltage_imbalance_pct,
    SUM(valid_secondary_voltage_imbalance_sum) / NULLIF(SUM(valid_secondary_voltage_imbalance_count), 0)
        AS average_secondary_voltage_imbalance_pct,
    MAX(maximum_secondary_voltage_imbalance_pct) AS maximum_secondary_voltage_imbalance_pct,
    SUM(valid_primary_current_imbalance_sum) / NULLIF(SUM(valid_primary_current_imbalance_count), 0)
        AS average_primary_current_imbalance_pct,
    MAX(maximum_primary_current_imbalance_pct) AS maximum_primary_current_imbalance_pct,
    SUM(valid_secondary_current_imbalance_sum) / NULLIF(SUM(valid_secondary_current_imbalance_count), 0)
        AS average_secondary_current_imbalance_pct,
    MAX(maximum_secondary_current_imbalance_pct) AS maximum_secondary_current_imbalance_pct,
    SUM(incomplete_primary_voltage_triplet_count)::bigint AS incomplete_primary_voltage_triplet_count,
    SUM(incomplete_secondary_voltage_triplet_count)::bigint AS incomplete_secondary_voltage_triplet_count,
    SUM(incomplete_primary_current_triplet_count)::bigint AS incomplete_primary_current_triplet_count,
    SUM(incomplete_secondary_current_triplet_count)::bigint AS incomplete_secondary_current_triplet_count,
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
FROM public.vw_trf71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_year;

CREATE VIEW public.vw_trf71_analytics_summary AS
SELECT
    asset_id,
    asset_code,
    asset_name,
    plaza_id,
    asset_partition_key,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    SUM(valid_pf_sum) / NULLIF(SUM(valid_pf_count), 0) AS average_pf,
    MIN(minimum_pf) AS minimum_pf,
    MAX(maximum_pf) AS maximum_pf,
    SUM(valid_frequency_sum) / NULLIF(SUM(valid_frequency_count), 0) AS average_frequency_hz,
    MIN(minimum_frequency_hz) AS minimum_frequency_hz,
    MAX(maximum_frequency_hz) AS maximum_frequency_hz,
    SUM(valid_oil_temperature_sum) / NULLIF(SUM(valid_oil_temperature_count), 0) AS average_oil_temperature_c,
    MIN(minimum_oil_temperature_c) AS minimum_oil_temperature_c,
    MAX(maximum_oil_temperature_c) AS maximum_oil_temperature_c,
    SUM(valid_winding_temperature_sum) / NULLIF(SUM(valid_winding_temperature_count), 0)
        AS average_winding_temperature_c,
    MIN(minimum_winding_temperature_c) AS minimum_winding_temperature_c,
    MAX(maximum_winding_temperature_c) AS maximum_winding_temperature_c,
    SUM(valid_primary_voltage_imbalance_sum) / NULLIF(SUM(valid_primary_voltage_imbalance_count), 0)
        AS average_primary_voltage_imbalance_pct,
    MAX(maximum_primary_voltage_imbalance_pct) AS maximum_primary_voltage_imbalance_pct,
    SUM(valid_secondary_voltage_imbalance_sum) / NULLIF(SUM(valid_secondary_voltage_imbalance_count), 0)
        AS average_secondary_voltage_imbalance_pct,
    MAX(maximum_secondary_voltage_imbalance_pct) AS maximum_secondary_voltage_imbalance_pct,
    SUM(valid_primary_current_imbalance_sum) / NULLIF(SUM(valid_primary_current_imbalance_count), 0)
        AS average_primary_current_imbalance_pct,
    MAX(maximum_primary_current_imbalance_pct) AS maximum_primary_current_imbalance_pct,
    SUM(valid_secondary_current_imbalance_sum) / NULLIF(SUM(valid_secondary_current_imbalance_count), 0)
        AS average_secondary_current_imbalance_pct,
    MAX(maximum_secondary_current_imbalance_pct) AS maximum_secondary_current_imbalance_pct,
    SUM(incomplete_primary_voltage_triplet_count)::bigint AS incomplete_primary_voltage_triplet_count,
    SUM(incomplete_secondary_voltage_triplet_count)::bigint AS incomplete_secondary_voltage_triplet_count,
    SUM(incomplete_primary_current_triplet_count)::bigint AS incomplete_primary_current_triplet_count,
    SUM(incomplete_secondary_current_triplet_count)::bigint AS incomplete_secondary_current_triplet_count,
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
FROM public.vw_trf71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key;

CREATE VIEW public.vw_trf71_asset_latest_reading AS
SELECT *
FROM (
    SELECT
        d.*,
        ROW_NUMBER() OVER (
            PARTITION BY d.asset_partition_key
            ORDER BY d.reading_datetime DESC, d.reading_id DESC
        ) AS asset_latest_rank
    FROM public.vw_trf71_reading_detail AS d
) AS ranked
WHERE asset_latest_rank = 1;


-- >>> END OF Transformer_Module_Analytics_Proposed.sql <<<


-- >>> START OF UPS_Module_7_Analytics_Proposed.sql <<<

-- SRTPL Energy Command Center - UPS Module 7 Analytics
-- PROPOSAL ONLY. Uses only new public.vw_ups71_* view names.
-- No schema/table changes, source-data writes, DROP, or view replacement.

CREATE VIEW public.vw_ups71_reading_detail AS
SELECT
    u.reading_id,
    u.asset_id,
    COALESCE(u.asset_code, a.asset_code) AS asset_code,
    a.asset_name,
    a.plaza_id,
    COALESCE('ID:' || u.asset_id::text,
             'CODE:' || COALESCE(u.asset_code, a.asset_code),
             'ROW:' || u.reading_id::text) AS asset_partition_key,
    u.reading_datetime,
    (u.reading_datetime AT TIME ZONE 'Asia/Kolkata')::date AS operational_date,
    u.output_voltage,
    u.output_current,
    u.output_frequency,
    u.battery_vdc,
    u.battery_temperature,
    u.rectifier_voltage,
    u.created_by,
    u.created_on,
    u.created_at,
    u.remarks,
    u.location,
    u.data_quality_status AS source_data_quality_status,
    CASE WHEN UPPER(BTRIM(COALESCE(u.data_quality_status, ''))) = 'VALID'
         THEN 'VALID' ELSE 'EXCEPTION' END AS source_quality_class
FROM energy_readings.ups AS u
LEFT JOIN energy_master.asset AS a
    ON (u.asset_id IS NOT NULL AND a.asset_id = u.asset_id)
    OR (u.asset_id IS NULL AND a.asset_code = u.asset_code AND a.source_type = 'UPS');

CREATE VIEW public.vw_ups71_record_quality AS
SELECT
    d.reading_id,
    d.asset_id,
    d.asset_code,
    d.asset_name,
    d.plaza_id,
    d.asset_partition_key,
    d.operational_date,
    d.reading_datetime,
    1::bigint AS total_records,
    CASE WHEN d.source_quality_class = 'VALID' THEN 1::bigint ELSE 0::bigint END AS source_valid_records,
    CASE WHEN d.source_quality_class = 'EXCEPTION' THEN 1::bigint ELSE 0::bigint END AS source_exception_records,
    CASE WHEN d.source_quality_class = 'VALID' THEN 1::bigint ELSE 0::bigint END AS valid_records,
    CASE WHEN d.source_quality_class = 'EXCEPTION' THEN 1::bigint ELSE 0::bigint END AS exception_records,
    0::bigint AS reconciliation_difference,
    d.source_quality_class AS analytics_quality_class,
    d.source_data_quality_status,
    CASE WHEN d.source_quality_class = 'EXCEPTION' THEN 'SOURCE_STATUS_EXCEPTION' END
        AS analytics_exception_reasons
FROM public.vw_ups71_reading_detail AS d;

CREATE VIEW public.vw_ups71_entry_audit AS
SELECT
    d.reading_id,
    d.asset_id,
    d.asset_code,
    d.asset_name,
    d.plaza_id,
    d.asset_partition_key,
    d.operational_date,
    d.reading_datetime,
    d.created_on,
    d.created_by,
    d.created_at AS database_inserted_at,
    d.created_on - d.reading_datetime AS entry_delay,
    EXTRACT(EPOCH FROM (d.created_on - d.reading_datetime)) / 3600.0 AS entry_delay_hours,
    CASE WHEN d.created_on IS NULL THEN NULL
         WHEN d.created_on < d.reading_datetime THEN TRUE ELSE FALSE END
        AS negative_entry_delay_timestamp_anomaly,
    CASE WHEN d.created_on IS NULL OR d.created_on < d.reading_datetime THEN NULL
         WHEN d.created_on - d.reading_datetime >= INTERVAL '24 hours' THEN TRUE ELSE FALSE END
        AS delayed_entry_24h_or_more,
    CASE WHEN d.created_on IS NULL OR d.created_on < d.reading_datetime THEN NULL
         WHEN d.created_on - d.reading_datetime < INTERVAL '24 hours' THEN TRUE ELSE FALSE END
        AS entry_within_24h,
    ((d.reading_datetime AT TIME ZONE 'Asia/Kolkata')::time >= TIME '22:00'
      OR (d.reading_datetime AT TIME ZONE 'Asia/Kolkata')::time < TIME '06:00')
        AS reading_datetime_night_indicator,
    CASE WHEN d.created_on IS NULL THEN NULL
         ELSE ((d.created_on AT TIME ZONE 'Asia/Kolkata')::time >= TIME '22:00'
                OR (d.created_on AT TIME ZONE 'Asia/Kolkata')::time < TIME '06:00') END
        AS created_on_night_indicator,
    q.analytics_quality_class
FROM public.vw_ups71_reading_detail AS d
JOIN public.vw_ups71_record_quality AS q USING (reading_id);

CREATE VIEW public.vw_ups71_daily_summary AS
WITH metrics AS (
    SELECT
        d.reading_id, d.asset_id, d.asset_code, d.asset_name, d.plaza_id,
        d.asset_partition_key, d.operational_date, d.created_on,
        d.output_voltage, d.output_current, d.output_frequency,
        d.battery_vdc, d.battery_temperature, d.rectifier_voltage,
        q.valid_records, q.exception_records, q.source_valid_records, q.source_exception_records,
        q.analytics_quality_class,
        a.entry_delay, a.entry_delay_hours, a.delayed_entry_24h_or_more,
        a.negative_entry_delay_timestamp_anomaly,
        a.reading_datetime_night_indicator, a.created_on_night_indicator
    FROM public.vw_ups71_reading_detail AS d
    JOIN public.vw_ups71_record_quality AS q USING (reading_id)
    JOIN public.vw_ups71_entry_audit AS a USING (reading_id)
)
SELECT
    asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_date,
    DATE_TRUNC('month', operational_date::timestamp)::date AS operational_month,
    EXTRACT(YEAR FROM operational_date)::integer AS operational_year,
    COUNT(*)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(source_valid_records)::bigint AS source_valid_records,
    SUM(source_exception_records)::bigint AS source_exception_records,
    COUNT(*) - SUM(valid_records) - SUM(exception_records) AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(COUNT(*), 0) AS observed_record_availability_pct,
    SUM(output_voltage) FILTER (WHERE analytics_quality_class = 'VALID' AND output_voltage IS NOT NULL)
        AS valid_output_voltage_sum,
    COUNT(output_voltage) FILTER (WHERE analytics_quality_class = 'VALID')::bigint AS valid_output_voltage_count,
    AVG(output_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS average_output_voltage,
    MIN(output_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_output_voltage,
    MAX(output_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_output_voltage,
    SUM(output_current) FILTER (WHERE analytics_quality_class = 'VALID' AND output_current IS NOT NULL)
        AS valid_output_current_sum,
    COUNT(output_current) FILTER (WHERE analytics_quality_class = 'VALID')::bigint AS valid_output_current_count,
    AVG(output_current) FILTER (WHERE analytics_quality_class = 'VALID') AS average_output_current,
    MIN(output_current) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_output_current,
    MAX(output_current) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_output_current,
    SUM(output_frequency) FILTER (WHERE analytics_quality_class = 'VALID' AND output_frequency IS NOT NULL)
        AS valid_output_frequency_sum,
    COUNT(output_frequency) FILTER (WHERE analytics_quality_class = 'VALID')::bigint AS valid_output_frequency_count,
    AVG(output_frequency) FILTER (WHERE analytics_quality_class = 'VALID') AS average_output_frequency,
    MIN(output_frequency) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_output_frequency,
    MAX(output_frequency) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_output_frequency,
    SUM(battery_vdc) FILTER (WHERE analytics_quality_class = 'VALID' AND battery_vdc IS NOT NULL)
        AS valid_battery_vdc_sum,
    COUNT(battery_vdc) FILTER (WHERE analytics_quality_class = 'VALID')::bigint AS valid_battery_vdc_count,
    AVG(battery_vdc) FILTER (WHERE analytics_quality_class = 'VALID') AS average_battery_vdc,
    MIN(battery_vdc) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_battery_vdc,
    MAX(battery_vdc) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_battery_vdc,
    SUM(battery_temperature) FILTER (WHERE analytics_quality_class = 'VALID' AND battery_temperature IS NOT NULL)
        AS valid_battery_temperature_sum,
    COUNT(battery_temperature) FILTER (WHERE analytics_quality_class = 'VALID')::bigint
        AS valid_battery_temperature_count,
    AVG(battery_temperature) FILTER (WHERE analytics_quality_class = 'VALID') AS average_battery_temperature,
    MIN(battery_temperature) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_battery_temperature,
    MAX(battery_temperature) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_battery_temperature,
    SUM(rectifier_voltage) FILTER (WHERE analytics_quality_class = 'VALID' AND rectifier_voltage IS NOT NULL)
        AS valid_rectifier_voltage_sum,
    COUNT(rectifier_voltage) FILTER (WHERE analytics_quality_class = 'VALID')::bigint
        AS valid_rectifier_voltage_count,
    AVG(rectifier_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS average_rectifier_voltage,
    MIN(rectifier_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_rectifier_voltage,
    MAX(rectifier_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_rectifier_voltage,
    COUNT(*) FILTER (WHERE delayed_entry_24h_or_more IS TRUE)::bigint AS delayed_entry_count,
    COUNT(*) FILTER (WHERE entry_delay IS NOT NULL AND entry_delay >= INTERVAL '0 seconds')::bigint
        AS entry_delay_eligible_count,
    100.0 * COUNT(*) FILTER (WHERE delayed_entry_24h_or_more IS TRUE)
        / NULLIF(COUNT(*) FILTER (WHERE entry_delay IS NOT NULL AND entry_delay >= INTERVAL '0 seconds'), 0)
        AS delayed_entry_percentage,
    AVG(entry_delay_hours) FILTER (WHERE entry_delay >= INTERVAL '0 seconds') AS average_entry_delay_hours,
    MAX(entry_delay_hours) FILTER (WHERE entry_delay >= INTERVAL '0 seconds') AS maximum_entry_delay_hours,
    COUNT(*) FILTER (WHERE negative_entry_delay_timestamp_anomaly IS TRUE)::bigint
        AS negative_entry_delay_timestamp_anomaly_count,
    COUNT(*) FILTER (WHERE created_on IS NOT NULL)::bigint AS created_on_timestamp_count,
    COUNT(*) FILTER (WHERE reading_datetime_night_indicator IS TRUE)::bigint AS night_reading_count,
    COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE)::bigint AS night_entry_count,
    100.0 * COUNT(*) FILTER (WHERE reading_datetime_night_indicator IS TRUE)
        / NULLIF(COUNT(*), 0) AS night_reading_percentage,
    100.0 * COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE)
        / NULLIF(COUNT(*) FILTER (WHERE created_on IS NOT NULL), 0) AS night_entry_percentage,
    COUNT(*) FILTER (WHERE reading_datetime_night_indicator IS TRUE
                       AND analytics_quality_class = 'VALID')::bigint AS valid_night_reading_count,
    COUNT(*) FILTER (WHERE reading_datetime_night_indicator IS TRUE
                       AND analytics_quality_class = 'EXCEPTION')::bigint AS exception_night_reading_count,
    COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE
                       AND analytics_quality_class = 'VALID')::bigint AS valid_night_entry_count,
    COUNT(*) FILTER (WHERE created_on_night_indicator IS TRUE
                       AND analytics_quality_class = 'EXCEPTION')::bigint AS exception_night_entry_count
FROM metrics
GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_date;

CREATE VIEW public.vw_ups71_monthly_summary AS
SELECT
    asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_month,
    COUNT(*)::bigint AS observed_asset_days,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
    SUM(valid_output_voltage_sum) / NULLIF(SUM(valid_output_voltage_count), 0) AS average_output_voltage,
    MIN(minimum_output_voltage) AS minimum_output_voltage, MAX(maximum_output_voltage) AS maximum_output_voltage,
    SUM(valid_output_current_sum) / NULLIF(SUM(valid_output_current_count), 0) AS average_output_current,
    MIN(minimum_output_current) AS minimum_output_current, MAX(maximum_output_current) AS maximum_output_current,
    SUM(valid_output_frequency_sum) / NULLIF(SUM(valid_output_frequency_count), 0) AS average_output_frequency,
    MIN(minimum_output_frequency) AS minimum_output_frequency, MAX(maximum_output_frequency) AS maximum_output_frequency,
    SUM(valid_battery_vdc_sum) / NULLIF(SUM(valid_battery_vdc_count), 0) AS average_battery_vdc,
    MIN(minimum_battery_vdc) AS minimum_battery_vdc, MAX(maximum_battery_vdc) AS maximum_battery_vdc,
    SUM(valid_battery_temperature_sum) / NULLIF(SUM(valid_battery_temperature_count), 0) AS average_battery_temperature,
    MIN(minimum_battery_temperature) AS minimum_battery_temperature,
    MAX(maximum_battery_temperature) AS maximum_battery_temperature,
    SUM(valid_rectifier_voltage_sum) / NULLIF(SUM(valid_rectifier_voltage_count), 0) AS average_rectifier_voltage,
    MIN(minimum_rectifier_voltage) AS minimum_rectifier_voltage,
    MAX(maximum_rectifier_voltage) AS maximum_rectifier_voltage,
    SUM(delayed_entry_count)::bigint AS delayed_entry_count,
    SUM(entry_delay_eligible_count)::bigint AS entry_delay_eligible_count,
    100.0 * SUM(delayed_entry_count) / NULLIF(SUM(entry_delay_eligible_count), 0) AS delayed_entry_percentage,
    SUM(average_entry_delay_hours * entry_delay_eligible_count)
        / NULLIF(SUM(entry_delay_eligible_count), 0)
        AS weighted_average_entry_delay_hours,
    MAX(maximum_entry_delay_hours) AS maximum_entry_delay_hours,
    SUM(negative_entry_delay_timestamp_anomaly_count)::bigint AS negative_entry_delay_timestamp_anomaly_count,
    SUM(created_on_timestamp_count)::bigint AS created_on_timestamp_count,
    SUM(night_reading_count)::bigint AS night_reading_count,
    SUM(night_entry_count)::bigint AS night_entry_count,
    100.0 * SUM(night_reading_count) / NULLIF(SUM(total_records), 0) AS night_reading_percentage,
    100.0 * SUM(night_entry_count) / NULLIF(SUM(created_on_timestamp_count), 0) AS night_entry_percentage,
    SUM(valid_night_reading_count)::bigint AS valid_night_reading_count,
    SUM(exception_night_reading_count)::bigint AS exception_night_reading_count,
    SUM(valid_night_entry_count)::bigint AS valid_night_entry_count,
    SUM(exception_night_entry_count)::bigint AS exception_night_entry_count
FROM public.vw_ups71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_month;

CREATE VIEW public.vw_ups71_yearly_summary AS
SELECT
    asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_year,
    COUNT(*)::bigint AS observed_asset_days,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
    SUM(valid_output_voltage_sum) / NULLIF(SUM(valid_output_voltage_count), 0) AS average_output_voltage,
    MIN(minimum_output_voltage) AS minimum_output_voltage, MAX(maximum_output_voltage) AS maximum_output_voltage,
    SUM(valid_output_current_sum) / NULLIF(SUM(valid_output_current_count), 0) AS average_output_current,
    MIN(minimum_output_current) AS minimum_output_current, MAX(maximum_output_current) AS maximum_output_current,
    SUM(valid_output_frequency_sum) / NULLIF(SUM(valid_output_frequency_count), 0) AS average_output_frequency,
    MIN(minimum_output_frequency) AS minimum_output_frequency, MAX(maximum_output_frequency) AS maximum_output_frequency,
    SUM(valid_battery_vdc_sum) / NULLIF(SUM(valid_battery_vdc_count), 0) AS average_battery_vdc,
    MIN(minimum_battery_vdc) AS minimum_battery_vdc, MAX(maximum_battery_vdc) AS maximum_battery_vdc,
    SUM(valid_battery_temperature_sum) / NULLIF(SUM(valid_battery_temperature_count), 0) AS average_battery_temperature,
    MIN(minimum_battery_temperature) AS minimum_battery_temperature,
    MAX(maximum_battery_temperature) AS maximum_battery_temperature,
    SUM(valid_rectifier_voltage_sum) / NULLIF(SUM(valid_rectifier_voltage_count), 0) AS average_rectifier_voltage,
    MIN(minimum_rectifier_voltage) AS minimum_rectifier_voltage,
    MAX(maximum_rectifier_voltage) AS maximum_rectifier_voltage,
    SUM(delayed_entry_count)::bigint AS delayed_entry_count,
    SUM(entry_delay_eligible_count)::bigint AS entry_delay_eligible_count,
    100.0 * SUM(delayed_entry_count) / NULLIF(SUM(entry_delay_eligible_count), 0) AS delayed_entry_percentage,
    SUM(average_entry_delay_hours * entry_delay_eligible_count)
        / NULLIF(SUM(entry_delay_eligible_count), 0)
        AS weighted_average_entry_delay_hours,
    MAX(maximum_entry_delay_hours) AS maximum_entry_delay_hours,
    SUM(negative_entry_delay_timestamp_anomaly_count)::bigint AS negative_entry_delay_timestamp_anomaly_count,
    SUM(created_on_timestamp_count)::bigint AS created_on_timestamp_count,
    SUM(night_reading_count)::bigint AS night_reading_count,
    SUM(night_entry_count)::bigint AS night_entry_count,
    100.0 * SUM(night_reading_count) / NULLIF(SUM(total_records), 0) AS night_reading_percentage,
    100.0 * SUM(night_entry_count) / NULLIF(SUM(created_on_timestamp_count), 0) AS night_entry_percentage,
    SUM(valid_night_reading_count)::bigint AS valid_night_reading_count,
    SUM(exception_night_reading_count)::bigint AS exception_night_reading_count,
    SUM(valid_night_entry_count)::bigint AS valid_night_entry_count,
    SUM(exception_night_entry_count)::bigint AS exception_night_entry_count
FROM public.vw_ups71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_year;

CREATE VIEW public.vw_ups71_analytics_summary AS
SELECT
    asset_id, asset_code, asset_name, plaza_id, asset_partition_key,
    COUNT(*)::bigint AS observed_asset_days,
    SUM(total_records)::bigint AS total_records,
    SUM(valid_records)::bigint AS valid_records,
    SUM(exception_records)::bigint AS exception_records,
    SUM(total_records - valid_records - exception_records)::bigint AS reconciliation_difference,
    100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
    SUM(valid_output_voltage_sum) / NULLIF(SUM(valid_output_voltage_count), 0) AS average_output_voltage,
    MIN(minimum_output_voltage) AS minimum_output_voltage, MAX(maximum_output_voltage) AS maximum_output_voltage,
    SUM(valid_output_current_sum) / NULLIF(SUM(valid_output_current_count), 0) AS average_output_current,
    MIN(minimum_output_current) AS minimum_output_current, MAX(maximum_output_current) AS maximum_output_current,
    SUM(valid_output_frequency_sum) / NULLIF(SUM(valid_output_frequency_count), 0) AS average_output_frequency,
    MIN(minimum_output_frequency) AS minimum_output_frequency, MAX(maximum_output_frequency) AS maximum_output_frequency,
    SUM(valid_battery_vdc_sum) / NULLIF(SUM(valid_battery_vdc_count), 0) AS average_battery_vdc,
    MIN(minimum_battery_vdc) AS minimum_battery_vdc, MAX(maximum_battery_vdc) AS maximum_battery_vdc,
    SUM(valid_battery_temperature_sum) / NULLIF(SUM(valid_battery_temperature_count), 0) AS average_battery_temperature,
    MIN(minimum_battery_temperature) AS minimum_battery_temperature,
    MAX(maximum_battery_temperature) AS maximum_battery_temperature,
    SUM(valid_rectifier_voltage_sum) / NULLIF(SUM(valid_rectifier_voltage_count), 0) AS average_rectifier_voltage,
    MIN(minimum_rectifier_voltage) AS minimum_rectifier_voltage,
    MAX(maximum_rectifier_voltage) AS maximum_rectifier_voltage,
    SUM(delayed_entry_count)::bigint AS delayed_entry_count,
    SUM(entry_delay_eligible_count)::bigint AS entry_delay_eligible_count,
    100.0 * SUM(delayed_entry_count) / NULLIF(SUM(entry_delay_eligible_count), 0) AS delayed_entry_percentage,
    SUM(average_entry_delay_hours * entry_delay_eligible_count)
        / NULLIF(SUM(entry_delay_eligible_count), 0)
        AS weighted_average_entry_delay_hours,
    MAX(maximum_entry_delay_hours) AS maximum_entry_delay_hours,
    SUM(negative_entry_delay_timestamp_anomaly_count)::bigint AS negative_entry_delay_timestamp_anomaly_count,
    SUM(created_on_timestamp_count)::bigint AS created_on_timestamp_count,
    SUM(night_reading_count)::bigint AS night_reading_count,
    SUM(night_entry_count)::bigint AS night_entry_count,
    100.0 * SUM(night_reading_count) / NULLIF(SUM(total_records), 0) AS night_reading_percentage,
    100.0 * SUM(night_entry_count) / NULLIF(SUM(created_on_timestamp_count), 0) AS night_entry_percentage,
    SUM(valid_night_reading_count)::bigint AS valid_night_reading_count,
    SUM(exception_night_reading_count)::bigint AS exception_night_reading_count,
    SUM(valid_night_entry_count)::bigint AS valid_night_entry_count,
    SUM(exception_night_entry_count)::bigint AS exception_night_entry_count
FROM public.vw_ups71_daily_summary
GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key;

CREATE VIEW public.vw_ups71_asset_latest_reading AS
SELECT
    a.asset_id, a.asset_code, a.asset_name, a.plaza_id, a.source_type, a.capacity_kva,
    l.reading_id, l.reading_datetime,
    l.output_voltage AS latest_output_voltage,
    l.output_current AS latest_output_current,
    l.output_frequency AS latest_output_frequency,
    l.battery_vdc AS latest_battery_vdc,
    l.battery_temperature AS latest_battery_temperature,
    l.rectifier_voltage AS latest_rectifier_voltage,
    l.source_data_quality_status,
    q.analytics_quality_class,
    l.created_by, l.created_on, l.remarks
FROM energy_master.asset AS a
LEFT JOIN LATERAL (
    SELECT d.*
    FROM public.vw_ups71_reading_detail AS d
    WHERE d.asset_id = a.asset_id
       OR (d.asset_id IS NULL AND d.asset_code = a.asset_code)
    ORDER BY d.reading_datetime DESC NULLS LAST, d.reading_id DESC
    LIMIT 1
) AS l ON TRUE
LEFT JOIN public.vw_ups71_record_quality AS q USING (reading_id)
WHERE a.source_type = 'UPS';


-- >>> END OF UPS_Module_7_Analytics_Proposed.sql <<<


-- >>> START OF Module_7_Unified_Views_Proposed.sql <<<

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
        NULL::numeric AS cumulative_kvah, NULL::numeric AS interval_kvah,
        1::numeric AS multiplying_factor,
        NULL::numeric AS billed_interval_kvah, (d.source_interval_kwh::numeric * 1)::numeric AS billed_interval_kwh,
        d.pf::numeric AS power_factor, NULL::numeric AS output_voltage, NULL::numeric AS battery_vdc,
        rt.cumulative_runtime_hh_mm::text AS cumulative_running_hours_hh_mm,
        d.source_data_quality_status::text AS source_data_quality_status, d.created_by, d.created_on
    FROM public.vw_dg71_interval_classification AS d
    LEFT JOIN public.vw_dg71_runtime_interval AS rt USING (reading_id)
    UNION ALL
    SELECT
        'EB', e.reading_id, e.asset_id, e.asset_code, e.asset_name, e.plaza_id,
        e.asset_partition_key, e.reading_datetime, e.operational_date,
        e.cumulative_kwh::numeric, e.interval_kwh::numeric,
        e.cumulative_kvah::numeric, e.interval_kvah::numeric,
        200::numeric AS multiplying_factor,
        (e.normalized_interval_kvah * 200)::numeric AS billed_interval_kvah,
        (e.normalized_interval_kwh * 200)::numeric AS billed_interval_kwh,
        e.pf::numeric,
        NULL::numeric, NULL::numeric, NULL::text, e.source_data_quality_status::text, e.created_by, e.created_on
    FROM public.vw_eb71_interval_detail AS e
    UNION ALL
    SELECT
        'SOLAR', s.reading_id, s.asset_id, s.asset_code, s.asset_name, s.plaza_id,
        s.asset_partition_key, s.reading_datetime, s.operational_date,
        s.cumulative_kwh::numeric, s.interval_kwh::numeric,
        NULL::numeric, NULL::numeric,
        1::numeric AS multiplying_factor,
        NULL::numeric AS billed_interval_kvah, (s.interval_kwh::numeric * 1)::numeric AS billed_interval_kwh,
        NULL::numeric,
        NULL::numeric, NULL::numeric, NULL::text, s.source_data_quality_status::text, s.created_by, s.created_on
    FROM public.vw_sol71_reading_detail AS s
    UNION ALL
    SELECT
        'TRANSFORMER', t.reading_id, t.asset_id, t.asset_code, t.asset_name, t.plaza_id,
        t.asset_partition_key, t.reading_datetime, t.operational_date,
        t.cumulative_kwh_value::numeric, t.interval_kwh_value::numeric,
        t.cumulative_kvah_value::numeric, t.interval_kvah_value::numeric,
        1::numeric AS multiplying_factor,
        (t.interval_kvah_value::numeric * 1)::numeric AS billed_interval_kvah,
        (t.interval_kwh_value::numeric * 1)::numeric AS billed_interval_kwh,
        t.pf::numeric,
        NULL::numeric, NULL::numeric, NULL::text, t.source_data_quality_status::text, t.created_by, t.created_on
    FROM public.vw_trf71_reading_detail AS t
    UNION ALL
    SELECT
        'UPS', u.reading_id, u.asset_id, u.asset_code, u.asset_name, u.plaza_id,
        u.asset_partition_key, u.reading_datetime, u.operational_date,
        NULL::numeric, NULL::numeric,
        NULL::numeric, NULL::numeric,
        1::numeric AS multiplying_factor,
        NULL::numeric AS billed_interval_kvah, NULL::numeric AS billed_interval_kwh,
        NULL::numeric,
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
    r.cumulative_kvah AS latest_cumulative_kvah,
    r.interval_kvah AS latest_interval_kvah,
    r.multiplying_factor,
    r.billed_interval_kvah AS latest_billed_kvah,
    r.billed_interval_kwh AS latest_billed_kwh,
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


-- >>> END OF Module_7_Unified_Views_Proposed.sql <<<


-- >>> START OF Module_7_Correction_Audit_Optional.sql <<<

-- Optional cross-module correction audit.
-- This guarded block skips missing audit dependencies and never replaces a view.

DO $module7_correction_audit$
BEGIN
    IF to_regclass('energy_audit.audit_log') IS NULL
       OR to_regclass('public.vw_m7_record_quality') IS NULL THEN
        RAISE NOTICE 'Skipping vw_m7_correction_audit: audit_log or Module 7 quality view is missing.';
    ELSIF to_regclass('public.vw_m7_correction_audit') IS NOT NULL THEN
        RAISE NOTICE 'Skipping vw_m7_correction_audit: target relation already exists; it was left unchanged.';
    ELSIF EXISTS (
        SELECT 1
        FROM (VALUES
            ('energy_audit', 'audit_log', 'audit_id'),
            ('energy_audit', 'audit_log', 'actor_user_id'),
            ('energy_audit', 'audit_log', 'action'),
            ('energy_audit', 'audit_log', 'entity_type'),
            ('energy_audit', 'audit_log', 'entity_id'),
            ('energy_audit', 'audit_log', 'old_value'),
            ('energy_audit', 'audit_log', 'new_value'),
            ('energy_audit', 'audit_log', 'reason'),
            ('energy_audit', 'audit_log', 'created_at')
        ) AS required(table_schema, table_name, column_name)
        WHERE NOT EXISTS (
            SELECT 1 FROM information_schema.columns AS c
            WHERE c.table_schema = required.table_schema
              AND c.table_name = required.table_name
              AND c.column_name = required.column_name
        )
    ) THEN
        RAISE NOTICE 'Skipping vw_m7_correction_audit: one or more audit columns are missing.';
    ELSE
        EXECUTE $view$
            CREATE VIEW public.vw_m7_correction_audit AS
            SELECT
                a.audit_id,
                q.source_type,
                q.reading_id,
                q.asset_id,
                q.asset_code,
                q.plaza_id,
                q.reading_datetime,
                q.source_data_quality_status,
                q.analytics_quality_class,
                a.actor_user_id,
                a.action,
                a.entity_type,
                a.entity_id,
                a.old_value,
                a.new_value,
                a.reason,
                a.created_at AS audit_timestamp
            FROM energy_audit.audit_log AS a
            JOIN public.vw_m7_record_quality AS q
              ON a.entity_id::text = q.reading_id::text
            WHERE a.old_value IS NOT NULL
               OR a.new_value IS NOT NULL
               OR a.action ~* '(correct|update|verify|resolve)'
        $view$;
        RAISE NOTICE 'Created public.vw_m7_correction_audit.';
    END IF;
END
$module7_correction_audit$;


-- >>> END OF Module_7_Correction_Audit_Optional.sql <<<

