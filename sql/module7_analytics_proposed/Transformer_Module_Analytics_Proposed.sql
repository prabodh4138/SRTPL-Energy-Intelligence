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
