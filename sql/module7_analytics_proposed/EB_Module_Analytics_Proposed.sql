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
