-- ============================================================================
-- SRTPL POWER INTELLIGENCE — EB VIEWS UPDATE FOR KVAH BILLING BASIS (MF = 200)
-- Target: PostgreSQL / Supabase
-- Applies:
-- 1. Industrial EB billing is strictly performed on kVAh, not kWh.
-- 2. Multiplying Factor (MF) is 200 across all toll plaza meters.
-- 3. Calculations updated in vw_eb71_* views and vw_m7_asset_latest_reading.
-- 4. Billed Interval kVAh = normalized_interval_kvah * 200.
-- 5. Cumulative Billed kVAh = cumulative_kvah * 200.
-- ============================================================================

DROP VIEW IF EXISTS public.vw_m7_submodule_summary CASCADE;
DROP VIEW IF EXISTS public.vw_m7_technician_summary CASCADE;
DROP VIEW IF EXISTS public.vw_m7_plaza_summary CASCADE;
DROP VIEW IF EXISTS public.vw_m7_module_yearly_quality_summary CASCADE;
DROP VIEW IF EXISTS public.vw_m7_module_monthly_quality_summary CASCADE;
DROP VIEW IF EXISTS public.vw_m7_module_daily_quality_summary CASCADE;
DROP VIEW IF EXISTS public.vw_m7_night_entry_detail CASCADE;
DROP VIEW IF EXISTS public.vw_m7_exception_register CASCADE;
DROP VIEW IF EXISTS public.vw_m7_asset_latest_reading CASCADE;
DROP VIEW IF EXISTS public.vw_m7_entry_audit CASCADE;
DROP VIEW IF EXISTS public.vw_m7_record_quality CASCADE;

DROP VIEW IF EXISTS public.vw_eb71_asset_latest_reading CASCADE;
DROP VIEW IF EXISTS public.vw_eb71_analytics_summary CASCADE;
DROP VIEW IF EXISTS public.vw_eb71_yearly_summary CASCADE;
DROP VIEW IF EXISTS public.vw_eb71_monthly_summary CASCADE;
DROP VIEW IF EXISTS public.vw_eb71_daily_summary CASCADE;
DROP VIEW IF EXISTS public.vw_eb71_entry_audit CASCADE;
DROP VIEW IF EXISTS public.vw_eb71_record_quality CASCADE;
DROP VIEW IF EXISTS public.vw_eb71_interval_detail CASCADE;

-- 1. Interval Detail with Multiplying Factor 200 & Billed kVAh / kWh
CREATE OR REPLACE VIEW public.vw_eb71_interval_detail AS
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

-- 2. Record Quality
CREATE OR REPLACE VIEW public.vw_eb71_record_quality AS
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

-- 3. Entry Audit
CREATE OR REPLACE VIEW public.vw_eb71_entry_audit AS
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

-- 4. Daily Summary with Valid Billed kVAh & kWh (MF = 200)
CREATE OR REPLACE VIEW public.vw_eb71_daily_summary AS
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

-- 5. Monthly Summary
CREATE OR REPLACE VIEW public.vw_eb71_monthly_summary AS
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

-- 6. Yearly Summary
CREATE OR REPLACE VIEW public.vw_eb71_yearly_summary AS
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

-- 7. Analytics Summary
CREATE OR REPLACE VIEW public.vw_eb71_analytics_summary AS
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

-- 8. EB Asset Latest Reading
CREATE OR REPLACE VIEW public.vw_eb71_asset_latest_reading AS
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

-- 9. Recreate Unified Module 7 Views
CREATE OR REPLACE VIEW public.vw_m7_record_quality AS
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

CREATE OR REPLACE VIEW public.vw_m7_entry_audit AS
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

CREATE OR REPLACE VIEW public.vw_m7_exception_register AS
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

CREATE OR REPLACE VIEW public.vw_m7_asset_latest_reading AS
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

-- 10. Module Summary & Submodule Summary
CREATE OR REPLACE VIEW public.vw_m7_submodule_summary AS
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

-- 11. Equipment KPI View Update for EB
DROP VIEW IF EXISTS public.vw_eb_reading_kpis CASCADE;
CREATE OR REPLACE VIEW public.vw_eb_reading_kpis AS
SELECT
    'EB' AS source_type,
    COUNT(DISTINCT r.asset_code) AS active_meters,
    200::numeric AS multiplying_factor,
    COALESCE(SUM(r.cumulative_kwh), 0.0) AS total_cumulative_kwh,
    COALESCE(SUM(r.interval_kwh), 0.0) AS total_interval_kwh,
    COALESCE(SUM(r.cumulative_kvah), 0.0) AS total_cumulative_kvah,
    COALESCE(SUM(r.interval_kvah), 0.0) AS total_interval_kvah,
    COALESCE(SUM(r.interval_kvah * 200), 0.0) AS total_billed_kvah,
    COALESCE(SUM(r.cumulative_kvah * 200), 0.0) AS total_billed_cumulative_kvah,
    COALESCE(SUM(r.interval_kwh * 200), 0.0) AS total_billed_kwh,
    COALESCE(AVG(CASE WHEN r.pf > 0 THEN r.pf ELSE NULL END), 0.98) AS avg_power_factor,
    COALESCE(MAX(r.maximum_demand), 0.0) AS peak_demand,
    COUNT(r.reading_id) AS total_reading_count,
    COALESCE(SUM(CASE WHEN r.data_quality_status = 'VALID' THEN 1 ELSE 0 END), 0) AS valid_count,
    COALESCE(SUM(CASE WHEN r.data_quality_status != 'VALID' THEN 1 ELSE 0 END), 0) AS exception_count
FROM energy_readings.eb r;

DROP VIEW IF EXISTS public.vw_eb_asset_latest_reading CASCADE;
CREATE OR REPLACE VIEW public.vw_eb_asset_latest_reading AS
SELECT 
    a.asset_id,
    a.asset_code,
    a.asset_name,
    a.plaza_id,
    a.source_type,
    a.capacity_kva,
    200::numeric AS multiplying_factor,
    s.start_date,
    s.last_date,
    COALESCE(s.total_readings, 0)::bigint AS total_readings,
    r.reading_id,
    r.reading_datetime,
    r.cumulative_kwh AS latest_cumulative_kwh,
    r.interval_kwh AS latest_interval_kwh,
    r.cumulative_kvah AS latest_cumulative_kvah,
    r.interval_kvah AS latest_interval_kvah,
    (r.interval_kvah * 200)::numeric AS latest_billed_kvah,
    (r.cumulative_kvah * 200)::numeric AS latest_billed_cumulative_kvah,
    (r.interval_kwh * 200)::numeric AS latest_billed_kwh,
    r.cumulative_kvarh AS latest_cumulative_kvarh,
    r.interval_kvarh AS latest_interval_kvarh,
    r.pf AS latest_pf,
    r.maximum_demand AS latest_maximum_demand,
    r.data_quality_status,
    r.created_by,
    r.remarks
FROM energy_master.asset a
LEFT JOIN LATERAL (
    SELECT 
        MIN(e.reading_datetime) AS start_date,
        MAX(e.reading_datetime) AS last_date,
        COUNT(e.reading_id) AS total_readings
    FROM energy_readings.eb e
    WHERE e.asset_code = a.asset_code OR e.asset_id = a.asset_id
) s ON true
LEFT JOIN LATERAL (
    SELECT *
    FROM energy_readings.eb e
    WHERE e.asset_code = a.asset_code OR e.asset_id = a.asset_id
    ORDER BY e.reading_datetime DESC NULLS LAST
    LIMIT 1
) r ON true
WHERE a.source_type = 'EB'
ORDER BY a.plaza_id, a.asset_code;

GRANT USAGE ON SCHEMA energy_master, energy_readings, energy_analytics TO anon, authenticated, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public, energy_master, energy_readings, energy_analytics TO anon, authenticated, service_role;
