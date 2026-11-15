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
