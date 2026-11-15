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
