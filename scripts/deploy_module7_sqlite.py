"""
Module 7 SQL View Deployment Script for SQLite Local Database.
Deploys all versioned Module 7 views with 100% parity:
- DG: vw_dg71_*
- EB: vw_eb71_*
- Solar: vw_sol71_*
- Transformer: vw_trf71_*
- UPS: vw_ups71_*
- Unified: vw_m7_*
"""
import sqlite3
import os

DB_PATH = os.path.join("active_app", "data", "srtpl_power.db")

def deploy_all_views():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Deploying all Module 7 views to SQLite...")

    # Drop views in reverse dependency order
    views_to_drop = [
        "vw_m7_submodule_summary", "vw_m7_asset_latest_reading", "vw_m7_technician_summary",
        "vw_m7_plaza_summary", "vw_m7_module_yearly_quality_summary",
        "vw_m7_module_monthly_quality_summary", "vw_m7_module_daily_quality_summary",
        "vw_m7_night_entry_detail", "vw_m7_exception_register", "vw_m7_entry_audit",
        "vw_m7_record_quality", "vw_m7_correction_audit",
        # UPS
        "vw_ups71_asset_latest_reading", "vw_ups71_analytics_summary", "vw_ups71_yearly_summary",
        "vw_ups71_monthly_summary", "vw_ups71_daily_summary", "vw_ups71_entry_audit",
        "vw_ups71_record_quality", "vw_ups71_reading_detail",
        # Transformer
        "vw_trf71_asset_latest_reading", "vw_trf71_analytics_summary", "vw_trf71_yearly_summary",
        "vw_trf71_monthly_summary", "vw_trf71_daily_summary", "vw_trf71_entry_audit",
        "vw_trf71_record_quality", "vw_trf71_electrical_reading", "vw_trf71_reading_detail",
        # Solar
        "vw_sol71_asset_latest_reading", "vw_sol71_analytics_summary", "vw_sol71_yearly_summary",
        "vw_sol71_monthly_summary", "vw_sol71_daily_summary", "vw_sol71_entry_audit",
        "vw_sol71_record_quality", "vw_sol71_interval_reading", "vw_sol71_reading_detail",
        # EB
        "vw_eb71_asset_latest_reading", "vw_eb71_analytics_summary", "vw_eb71_yearly_summary",
        "vw_eb71_monthly_summary", "vw_eb71_daily_summary", "vw_eb71_entry_audit",
        "vw_eb71_record_quality", "vw_eb71_interval_detail",
        # DG
        "vw_dg71_analytics_summary", "vw_dg71_yearly_summary", "vw_dg71_monthly_summary",
        "vw_dg71_daily_summary", "vw_dg71_record_quality", "vw_dg71_entry_audit",
        "vw_dg71_electrical_reading", "vw_dg71_diesel_interval", "vw_dg71_runtime_interval",
        "vw_dg71_interval_classification",
    ]
    for v in views_to_drop:
        cur.execute(f"DROP VIEW IF EXISTS {v}")

    # =========================================================================
    # 1. DG VIEWS
    # =========================================================================
    cur.execute("""
    CREATE VIEW vw_dg71_interval_classification AS
    WITH raw_readings AS (
        SELECT
            d.reading_id,
            d.asset_id,
            COALESCE(d.asset_code, a.asset_code) AS asset_code,
            a.asset_name,
            COALESCE(a.plaza_id, d.location) AS plaza_id,
            a.capacity_kva AS registered_capacity_kva,
            d.reading_datetime,
            SUBSTR(d.reading_datetime, 1, 10) AS operational_date,
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
                WHEN UPPER(TRIM(COALESCE(d.data_quality_status, ''))) = 'VALID' THEN 'VALID'
                ELSE 'EXCEPTION'
            END AS source_quality_class
        FROM energy_readings_dg AS d
        LEFT JOIN energy_master_asset AS a
            ON a.asset_id = d.asset_id OR a.asset_code = d.asset_id OR a.asset_code = d.asset_code
    ),
    sequenced_readings AS (
        SELECT
            r.*,
            COALESCE('ID:' || r.asset_id, 'CODE:' || r.asset_code, 'ROW:' || r.reading_id) AS asset_partition_key,
            ROW_NUMBER() OVER (
                PARTITION BY COALESCE('ID:' || r.asset_id, 'CODE:' || r.asset_code, 'ROW:' || r.reading_id)
                ORDER BY r.reading_datetime, r.reading_id
            ) AS reading_sequence,
            LAG(r.reading_id) OVER (
                PARTITION BY COALESCE('ID:' || r.asset_id, 'CODE:' || r.asset_code, 'ROW:' || r.reading_id)
                ORDER BY r.reading_datetime, r.reading_id
            ) AS previous_reading_id,
            LAG(r.reading_datetime) OVER (
                PARTITION BY COALESCE('ID:' || r.asset_id, 'CODE:' || r.asset_code, 'ROW:' || r.reading_id)
                ORDER BY r.reading_datetime, r.reading_id
            ) AS previous_reading_datetime,
            LAG(r.cumulative_kwh) OVER (
                PARTITION BY COALESCE('ID:' || r.asset_id, 'CODE:' || r.asset_code, 'ROW:' || r.reading_id)
                ORDER BY r.reading_datetime, r.reading_id
            ) AS previous_cumulative_kwh,
            LAG(r.cumulative_running_hours) OVER (
                PARTITION BY COALESCE('ID:' || r.asset_id, 'CODE:' || r.asset_code, 'ROW:' || r.reading_id)
                ORDER BY r.reading_datetime, r.reading_id
            ) AS previous_cumulative_running_hours,
            LAG(r.diesel_level_l) OVER (
                PARTITION BY COALESCE('ID:' || r.asset_id, 'CODE:' || r.asset_code, 'ROW:' || r.reading_id)
                ORDER BY r.reading_datetime, r.reading_id
            ) AS previous_diesel_level_l,
            LAG(r.diesel_topup_l) OVER (
                PARTITION BY COALESCE('ID:' || r.asset_id, 'CODE:' || r.asset_code, 'ROW:' || r.reading_id)
                ORDER BY r.reading_datetime, r.reading_id
            ) AS previous_diesel_topup_l,
            LAG(r.source_quality_class) OVER (
                PARTITION BY COALESCE('ID:' || r.asset_id, 'CODE:' || r.asset_code, 'ROW:' || r.reading_id)
                ORDER BY r.reading_datetime, r.reading_id
            ) AS previous_source_quality_class
        FROM raw_readings AS r
    ),
    runtime_values AS (
        SELECT
            s.*,
            CASE
                WHEN s.cumulative_running_hours >= 0
                 AND ROUND((s.cumulative_running_hours - CAST(s.cumulative_running_hours AS INTEGER)) * 100) BETWEEN 0 AND 59
                THEN (CAST(s.cumulative_running_hours AS INTEGER) * 60
                     + ROUND((s.cumulative_running_hours - CAST(s.cumulative_running_hours AS INTEGER)) * 100))
            END AS cumulative_runtime_minutes,
            CASE
                WHEN s.previous_cumulative_running_hours >= 0
                 AND ROUND((s.previous_cumulative_running_hours - CAST(s.previous_cumulative_running_hours AS INTEGER)) * 100) BETWEEN 0 AND 59
                THEN (CAST(s.previous_cumulative_running_hours AS INTEGER) * 60
                     + ROUND((s.previous_cumulative_running_hours - CAST(s.previous_cumulative_running_hours AS INTEGER)) * 100))
            END AS previous_cumulative_runtime_minutes
        FROM sequenced_readings AS s
    ),
    interval_values AS (
        SELECT
            r.*,
            r.cumulative_kwh - r.previous_cumulative_kwh AS generation_delta_kwh,
            r.cumulative_runtime_minutes - r.previous_cumulative_runtime_minutes AS runtime_interval_minutes,
            r.previous_diesel_level_l
                + COALESCE(r.previous_diesel_topup_l, 0.0)
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
                THEN 1 ELSE 0
            END AS is_validated_runtime_interval,
            CASE
                WHEN i.runtime_interval_minutes > 0
                 AND i.cumulative_runtime_minutes IS NOT NULL
                 AND i.previous_cumulative_runtime_minutes IS NOT NULL
                 AND i.source_quality_class = 'VALID'
                 AND i.previous_source_quality_class = 'VALID'
                THEN 1 ELSE 0
            END AS has_positive_validated_runtime,
            CASE
                WHEN i.generation_delta_kwh > 0
                 AND i.runtime_interval_minutes > 0
                 AND i.cumulative_runtime_minutes IS NOT NULL
                 AND i.previous_cumulative_runtime_minutes IS NOT NULL
                 AND i.source_quality_class = 'VALID'
                 AND i.previous_source_quality_class = 'VALID'
                THEN 1 ELSE 0
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
                THEN 1 ELSE 0
            END AS positive_fuel_without_confirmed_generation_or_runtime,
            CASE
                WHEN i.cumulative_running_hours IS NOT NULL
                 AND i.cumulative_runtime_minutes IS NULL
                THEN 1 ELSE 0
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
                WHEN f.has_confirmed_generation = 1 THEN 'CONFIRMED_GENERATION'
                WHEN f.generation_delta_kwh > 0 THEN 'UNVERIFIED_GENERATION'
                ELSE 'UNUSABLE_INTERVAL'
            END AS generation_classification,
            CASE
                WHEN f.source_quality_class <> 'VALID'
                  OR f.current_runtime_encoding_invalid = 1
                  OR f.generation_delta_kwh < 0
                  OR f.runtime_interval_minutes < 0
                  OR f.fuel_reconciliation_l < 0
                  OR f.positive_fuel_without_confirmed_generation_or_runtime = 1
                THEN 'EXCEPTION'
                ELSE 'VALID'
            END AS analytics_quality_class
        FROM interval_flags AS f
    )
    SELECT
        c.*,
        CASE
            WHEN c.analytics_quality_class = 'VALID' AND c.has_confirmed_generation = 1
            THEN c.generation_delta_kwh
        END AS confirmed_generation_kwh,
        CASE
            WHEN c.analytics_quality_class = 'VALID' AND c.is_validated_runtime_interval = 1
            THEN c.runtime_interval_minutes
        END AS validated_runtime_interval_minutes,
        TRIM(
            (CASE WHEN c.source_quality_class <> 'VALID' THEN 'SOURCE_STATUS_EXCEPTION; ' ELSE '' END) ||
            (CASE WHEN c.current_runtime_encoding_invalid = 1 THEN 'INVALID_HH_MM_RUNTIME_ENCODING; ' ELSE '' END) ||
            (CASE WHEN c.generation_delta_kwh < 0 THEN 'NEGATIVE_GENERATION_DELTA; ' ELSE '' END) ||
            (CASE WHEN c.runtime_interval_minutes < 0 THEN 'NEGATIVE_RUNTIME_DELTA; ' ELSE '' END) ||
            (CASE WHEN c.fuel_reconciliation_l < 0 THEN 'NEGATIVE_FUEL_RECONCILIATION; ' ELSE '' END) ||
            (CASE WHEN c.positive_fuel_without_confirmed_generation_or_runtime = 1
                  THEN 'FUEL_CONSUMPTION_WITHOUT_CONFIRMED_GENERATION_AND_RUNTIME; ' ELSE '' END),
            '; '
        ) AS analytics_exception_reasons
    FROM classified_rows AS c;
    """)

    cur.execute("""
    CREATE VIEW vw_dg71_runtime_interval AS
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
             ELSE PRINTF('%02d:%02d', i.cumulative_runtime_minutes / 60, i.cumulative_runtime_minutes % 60)
        END AS cumulative_runtime_hh_mm,
        i.runtime_interval_minutes,
        CASE
            WHEN i.runtime_interval_minutes IS NULL THEN NULL
            WHEN i.runtime_interval_minutes < 0 THEN '-' || PRINTF('%02d:%02d', ABS(i.runtime_interval_minutes) / 60, ABS(i.runtime_interval_minutes) % 60)
            ELSE PRINTF('%02d:%02d', i.runtime_interval_minutes / 60, i.runtime_interval_minutes % 60)
        END AS runtime_interval_hh_mm,
        i.validated_runtime_interval_minutes,
        CASE WHEN i.cumulative_running_hours IS NULL THEN 1 ELSE 0 END AS runtime_missing,
        i.current_runtime_encoding_invalid AS runtime_encoding_invalid,
        i.analytics_quality_class
    FROM vw_dg71_interval_classification AS i;
    """)

    cur.execute("""
    CREATE VIEW vw_dg71_diesel_interval AS
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
        COALESCE(i.previous_diesel_topup_l, 0.0) AS previous_row_topup_l,
        i.fuel_reconciliation_l AS calculated_fuel_movement_l,
        CASE WHEN i.fuel_reconciliation_l < 0 THEN 1 ELSE 0 END AS negative_fuel_reconciliation_exception,
        CASE WHEN i.positive_fuel_without_confirmed_generation_or_runtime = 1 THEN 1 ELSE 0 END
            AS consumption_without_confirmed_generation_or_runtime_exception,
        CASE
            WHEN i.fuel_reconciliation_l > 0
             AND i.has_confirmed_generation = 1
             AND i.analytics_quality_class = 'VALID'
            THEN i.fuel_reconciliation_l
        END AS confirmed_diesel_consumption_l,
        CASE
            WHEN i.fuel_reconciliation_l > 0
             AND i.has_confirmed_generation = 1
             AND i.analytics_quality_class = 'VALID'
            THEN i.runtime_interval_minutes
        END AS efficiency_runtime_minutes,
        CASE
            WHEN i.fuel_reconciliation_l > 0
             AND i.has_confirmed_generation = 1
             AND i.analytics_quality_class = 'VALID'
            THEN i.generation_delta_kwh
        END AS efficiency_generation_kwh,
        CASE
            WHEN i.fuel_reconciliation_l IS NULL THEN 'MISSING_CURRENT_OR_PREVIOUS_FUEL_LEVEL'
            WHEN i.fuel_reconciliation_l <= 0 THEN 'NO_POSITIVE_CONFIRMED_CONSUMPTION'
            WHEN i.has_confirmed_generation = 0 THEN 'NO_CONFIRMED_POSITIVE_GENERATION_AND_RUNTIME'
            WHEN i.analytics_quality_class <> 'VALID' THEN 'ANALYTICS_EXCEPTION'
            ELSE NULL
        END AS fuel_efficiency_exclusion_reason,
        i.source_quality_class,
        i.analytics_quality_class
    FROM vw_dg71_interval_classification AS i;
    """)

    cur.execute("""
    CREATE VIEW vw_dg71_electrical_reading AS
    WITH phase_means AS (
        SELECT
            i.*,
            CASE WHEN i.voltage_ry IS NOT NULL AND i.voltage_yb IS NOT NULL AND i.voltage_br IS NOT NULL
                 THEN (i.voltage_ry + i.voltage_yb + i.voltage_br) / 3.0 END AS voltage_phase_mean,
            CASE WHEN i.current_r IS NOT NULL AND i.current_y IS NOT NULL AND i.current_b IS NOT NULL
                 THEN (i.current_r + i.current_y + i.current_b) / 3.0 END AS current_phase_mean,
            ((CASE WHEN i.voltage_ry IS NOT NULL THEN 1 ELSE 0 END)
             + (CASE WHEN i.voltage_yb IS NOT NULL THEN 1 ELSE 0 END)
             + (CASE WHEN i.voltage_br IS NOT NULL THEN 1 ELSE 0 END)) AS voltage_phase_count,
            ((CASE WHEN i.current_r IS NOT NULL THEN 1 ELSE 0 END)
             + (CASE WHEN i.current_y IS NOT NULL THEN 1 ELSE 0 END)
             + (CASE WHEN i.current_b IS NOT NULL THEN 1 ELSE 0 END)) AS current_phase_count
        FROM vw_dg71_interval_classification AS i
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
        p.voltage_phase_count,
        p.current_phase_count,
        CASE
            WHEN p.voltage_phase_count = 3 AND p.voltage_phase_mean > 0
            THEN 100.0 * MAX(
                ABS(p.voltage_ry - p.voltage_phase_mean),
                MAX(ABS(p.voltage_yb - p.voltage_phase_mean), ABS(p.voltage_br - p.voltage_phase_mean))
            ) / p.voltage_phase_mean
        END AS voltage_imbalance_pct,
        CASE
            WHEN p.current_phase_count = 3 AND p.current_phase_mean > 0
            THEN 100.0 * MAX(
                ABS(p.current_r - p.current_phase_mean),
                MAX(ABS(p.current_y - p.current_phase_mean), ABS(p.current_b - p.current_phase_mean))
            ) / p.current_phase_mean
        END AS current_imbalance_pct,
        p.analytics_quality_class,
        p.analytics_exception_reasons
    FROM phase_means AS p;
    """)

    cur.execute("""
    CREATE VIEW vw_dg71_entry_audit AS
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
        CASE 
            WHEN i.created_on IS NOT NULL 
            THEN (JULIANDAY(SUBSTR(i.created_on, 1, 19)) - JULIANDAY(SUBSTR(i.reading_datetime, 1, 19))) * 24.0 
        END AS entry_delay_hours,
        CASE 
            WHEN i.created_on IS NULL THEN NULL
            WHEN (JULIANDAY(SUBSTR(i.created_on, 1, 19)) - JULIANDAY(SUBSTR(i.reading_datetime, 1, 19))) < 0 THEN 1 ELSE 0
        END AS negative_entry_delay_timestamp_anomaly,
        CASE 
            WHEN i.created_on IS NULL OR (JULIANDAY(SUBSTR(i.created_on, 1, 19)) - JULIANDAY(SUBSTR(i.reading_datetime, 1, 19))) < 0 THEN NULL
            WHEN (JULIANDAY(SUBSTR(i.created_on, 1, 19)) - JULIANDAY(SUBSTR(i.reading_datetime, 1, 19))) >= 1.0 THEN 1 ELSE 0
        END AS delayed_entry_24h_or_more,
        CASE 
            WHEN i.created_on IS NULL OR (JULIANDAY(SUBSTR(i.created_on, 1, 19)) - JULIANDAY(SUBSTR(i.reading_datetime, 1, 19))) < 0 THEN NULL
            WHEN (JULIANDAY(SUBSTR(i.created_on, 1, 19)) - JULIANDAY(SUBSTR(i.reading_datetime, 1, 19))) < 1.0 THEN 1 ELSE 0
        END AS entry_within_24h,
        CASE 
            WHEN CAST(SUBSTR(i.reading_datetime, 12, 2) AS INTEGER) >= 22 
              OR CAST(SUBSTR(i.reading_datetime, 12, 2) AS INTEGER) < 6 
            THEN 1 ELSE 0 
        END AS reading_datetime_night_indicator,
        CASE 
            WHEN i.created_on IS NULL THEN NULL
            WHEN CAST(SUBSTR(i.created_on, 12, 2) AS INTEGER) >= 22 
              OR CAST(SUBSTR(i.created_on, 12, 2) AS INTEGER) < 6 
            THEN 1 ELSE 0 
        END AS created_on_night_indicator,
        i.analytics_quality_class
    FROM vw_dg71_interval_classification AS i;
    """)

    cur.execute("""
    CREATE VIEW vw_dg71_record_quality AS
    SELECT
        i.reading_id,
        i.asset_id,
        i.asset_code,
        i.asset_name,
        i.plaza_id,
        i.operational_date,
        i.reading_datetime,
        1 AS total_records,
        CASE WHEN i.source_quality_class = 'VALID' THEN 1 ELSE 0 END AS source_valid_records,
        CASE WHEN i.source_quality_class = 'EXCEPTION' THEN 1 ELSE 0 END AS source_exception_records,
        CASE WHEN i.analytics_quality_class = 'VALID' THEN 1 ELSE 0 END AS valid_records,
        CASE WHEN i.analytics_quality_class = 'EXCEPTION' THEN 1 ELSE 0 END AS exception_records,
        0 AS reconciliation_difference,
        i.source_data_quality_status,
        i.source_quality_class,
        i.analytics_quality_class,
        i.analytics_exception_reasons
    FROM vw_dg71_interval_classification AS i;
    """)

    cur.execute("""
    CREATE VIEW vw_dg71_daily_summary AS
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
            e.entry_delay_hours,
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
        FROM vw_dg71_interval_classification AS i
        JOIN vw_dg71_record_quality AS q USING (reading_id)
        JOIN vw_dg71_entry_audit AS e USING (reading_id)
        JOIN vw_dg71_diesel_interval AS x USING (reading_id)
        JOIN vw_dg71_electrical_reading AS el USING (reading_id)
    )
    SELECT
        asset_id,
        asset_code,
        asset_name,
        plaza_id,
        operational_date,
        SUBSTR(operational_date, 1, 7) AS operational_month,
        CAST(SUBSTR(operational_date, 1, 4) AS INTEGER) AS operational_year,
        COUNT(*) AS total_records,
        SUM(valid_records) AS valid_records,
        SUM(exception_records) AS exception_records,
        SUM(source_valid_records) AS source_valid_records,
        SUM(source_exception_records) AS source_exception_records,
        (COUNT(*) - SUM(valid_records) - SUM(exception_records)) AS reconciliation_difference,
        100.0 * SUM(exception_records) / NULLIF(COUNT(*), 0) AS exception_percentage,
        COUNT(*) FILTER (WHERE generation_classification = 'FIRST_READING') AS first_reading_count,
        COUNT(*) FILTER (WHERE generation_classification = 'CONFIRMED_GENERATION' AND analytics_quality_class = 'VALID') AS confirmed_generation_interval_count,
        COALESCE(SUM(confirmed_generation_kwh), 0.0) AS confirmed_generation_kwh,
        COUNT(*) FILTER (WHERE generation_classification = 'UNVERIFIED_GENERATION') AS unverified_generation_interval_count,
        COUNT(*) FILTER (WHERE generation_classification = 'ZERO_GENERATION') AS zero_generation_interval_count,
        COUNT(*) FILTER (WHERE generation_classification = 'NEGATIVE_GENERATION') AS negative_generation_exception_count,
        COUNT(*) FILTER (WHERE generation_classification = 'UNUSABLE_INTERVAL') AS unusable_generation_interval_count,
        COALESCE(SUM(validated_runtime_interval_minutes), 0.0) AS validated_runtime_minutes,
        COALESCE(SUM(efficiency_runtime_minutes), 0.0) AS efficiency_runtime_minutes,
        COALESCE(SUM(efficiency_generation_kwh), 0.0) AS efficiency_generation_kwh,
        COUNT(*) FILTER (WHERE runtime_interval_minutes = 0) AS zero_runtime_interval_count,
        COUNT(*) FILTER (WHERE runtime_interval_minutes < 0) AS negative_runtime_exception_count,
        COUNT(*) FILTER (WHERE runtime_interval_minutes IS NULL) AS unavailable_runtime_interval_count,
        COUNT(*) FILTER (WHERE diesel_topup_l IS NOT NULL) AS topup_report_count,
        COALESCE(SUM(diesel_topup_l), 0.0) AS reported_diesel_topup_l,
        COALESCE(SUM(fuel_reconciliation_l), 0.0) AS net_calculated_fuel_movement_l,
        COALESCE(SUM(confirmed_diesel_consumption_l), 0.0) AS confirmed_diesel_consumption_l,
        COUNT(*) FILTER (WHERE negative_fuel_reconciliation_exception = 1) AS negative_fuel_reconciliation_exception_count,
        COUNT(*) FILTER (WHERE consumption_without_confirmed_generation_or_runtime_exception = 1) AS consumption_without_confirmed_generation_or_runtime_count,
        SUM(confirmed_diesel_consumption_l) / NULLIF(SUM(efficiency_runtime_minutes) / 60.0, 0) AS diesel_l_per_runtime_hour,
        SUM(confirmed_diesel_consumption_l) / NULLIF(SUM(efficiency_generation_kwh), 0) AS diesel_l_per_kwh,
        SUM(efficiency_generation_kwh) / NULLIF(SUM(confirmed_diesel_consumption_l), 0) AS generation_kwh_per_l,
        AVG(kva) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_kva,
        MIN(kva) FILTER (WHERE analytics_quality_class = 'VALID') AS min_kva,
        MAX(kva) FILTER (WHERE analytics_quality_class = 'VALID') AS max_kva,
        AVG(kw) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_kw,
        MIN(kw) FILTER (WHERE analytics_quality_class = 'VALID') AS min_kw,
        MAX(kw) FILTER (WHERE analytics_quality_class = 'VALID') AS max_kw,
        AVG(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_pf,
        SUM(pf) FILTER (WHERE analytics_quality_class = 'VALID' AND pf IS NOT NULL) AS valid_pf_sum,
        COUNT(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_pf_count,
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
        SUM(voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID' AND voltage_imbalance_pct IS NOT NULL) AS valid_voltage_imbalance_sum,
        COUNT(voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_voltage_imbalance_count,
        MAX(voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS max_voltage_imbalance_pct,
        AVG(current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS avg_current_imbalance_pct,
        SUM(current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID' AND current_imbalance_pct IS NOT NULL) AS valid_current_imbalance_sum,
        COUNT(current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_current_imbalance_count,
        MAX(current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS max_current_imbalance_pct,
        COUNT(*) FILTER (WHERE voltage_phase_count < 3) AS incomplete_voltage_triplet_count,
        COUNT(*) FILTER (WHERE current_phase_count < 3) AS incomplete_current_triplet_count,
        COUNT(*) FILTER (WHERE delayed_entry_24h_or_more = 1) AS delayed_entry_count,
        COUNT(*) FILTER (WHERE entry_delay_hours IS NOT NULL AND entry_delay_hours >= 0) AS entry_delay_eligible_count,
        100.0 * COUNT(*) FILTER (WHERE delayed_entry_24h_or_more = 1) / NULLIF(COUNT(*) FILTER (WHERE entry_delay_hours IS NOT NULL AND entry_delay_hours >= 0), 0) AS delayed_entry_percentage,
        AVG(entry_delay_hours) FILTER (WHERE entry_delay_hours >= 0) AS average_entry_delay,
        SUM(entry_delay_hours * 3600.0) FILTER (WHERE entry_delay_hours >= 0) AS eligible_entry_delay_sum_seconds,
        MAX(entry_delay_hours) FILTER (WHERE entry_delay_hours >= 0) AS maximum_entry_delay,
        COUNT(*) FILTER (WHERE negative_entry_delay_timestamp_anomaly = 1) AS negative_entry_delay_timestamp_anomaly_count,
        COUNT(*) FILTER (WHERE reading_datetime_night_indicator = 1) AS night_reading_count,
        COUNT(*) FILTER (WHERE created_on_night_indicator = 1) AS night_entry_count,
        COUNT(*) FILTER (WHERE reading_datetime_night_indicator = 1 AND analytics_quality_class = 'VALID') AS valid_night_reading_count,
        COUNT(*) FILTER (WHERE reading_datetime_night_indicator = 1 AND analytics_quality_class = 'EXCEPTION') AS exception_night_reading_count,
        COUNT(*) FILTER (WHERE created_on_night_indicator = 1 AND analytics_quality_class = 'VALID') AS valid_night_entry_count,
        COUNT(*) FILTER (WHERE created_on_night_indicator = 1 AND analytics_quality_class = 'EXCEPTION') AS exception_night_entry_count
    FROM reading_metrics
    GROUP BY asset_id, asset_code, asset_name, plaza_id, operational_date;
    """)

    # =========================================================================
    # 2. EB SUBMODULE VIEWS
    # =========================================================================
    cur.execute("""
    CREATE VIEW vw_eb71_interval_detail AS
    WITH reading_source AS (
        SELECT
            d.reading_id,
            d.asset_id,
            COALESCE(d.asset_code, a.asset_code) AS asset_code,
            a.asset_name,
            COALESCE(a.plaza_id, d.location) AS plaza_id,
            d.consumer_number,
            d.reading_datetime,
            SUBSTR(d.reading_datetime, 1, 10) AS operational_date,
            d.cumulative_kwh,
            d.cumulative_kvah,
            d.cumulative_kvarh,
            d.interval_kwh,
            d.interval_kvah,
            d.interval_kvarh,
            d.pf,
            CAST(d.maximum_demand AS REAL) AS maximum_demand_value,
            d.created_by,
            d.created_on,
            d.created_at,
            d.remarks,
            d.location,
            d.category,
            d.data_quality_status AS source_data_quality_status,
            CASE
                WHEN UPPER(TRIM(COALESCE(d.data_quality_status, ''))) = 'VALID' THEN 'VALID'
                ELSE 'EXCEPTION'
            END AS source_quality_class,
            COALESCE('ID:' || d.asset_id, 'CODE:' || COALESCE(d.asset_code, a.asset_code), 'ROW:' || d.reading_id) AS asset_partition_key
        FROM energy_readings_eb AS d
        LEFT JOIN energy_master_asset AS a
            ON a.asset_id = d.asset_id OR a.asset_code = d.asset_id OR a.asset_code = d.asset_code
    ),
    sequenced_readings AS (
        SELECT
            r.*,
            ROW_NUMBER() OVER (PARTITION BY r.asset_partition_key ORDER BY r.reading_datetime, r.reading_id) AS reading_sequence,
            LAG(r.reading_id) OVER (PARTITION BY r.asset_partition_key ORDER BY r.reading_datetime, r.reading_id) AS previous_reading_id,
            LAG(r.reading_datetime) OVER (PARTITION BY r.asset_partition_key ORDER BY r.reading_datetime, r.reading_id) AS previous_reading_datetime,
            LAG(r.cumulative_kwh) OVER (PARTITION BY r.asset_partition_key ORDER BY r.reading_datetime, r.reading_id) AS previous_cumulative_kwh,
            LAG(r.cumulative_kvah) OVER (PARTITION BY r.asset_partition_key ORDER BY r.reading_datetime, r.reading_id) AS previous_cumulative_kvah,
            LAG(r.cumulative_kvarh) OVER (PARTITION BY r.asset_partition_key ORDER BY r.reading_datetime, r.reading_id) AS previous_cumulative_kvarh
        FROM reading_source AS r
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
            TRIM(
                (CASE WHEN i.source_quality_class <> 'VALID' THEN 'SOURCE_STATUS_EXCEPTION; ' ELSE '' END) ||
                (CASE WHEN i.cumulative_delta_kwh < 0 THEN 'DECREASING_CUMULATIVE_KWH; ' ELSE '' END) ||
                (CASE WHEN i.cumulative_delta_kvah < 0 THEN 'DECREASING_CUMULATIVE_KVAH; ' ELSE '' END) ||
                (CASE WHEN i.cumulative_delta_kvarh < 0 THEN 'DECREASING_CUMULATIVE_KVARH; ' ELSE '' END) ||
                (CASE WHEN i.pf < 0 OR i.pf > 1 THEN 'POWER_FACTOR_OUTSIDE_0_TO_1; ' ELSE '' END),
                '; '
            ) AS analytics_exception_reasons
        FROM interval_values AS i
    )
    SELECT * FROM classified_readings;
    """)

    cur.execute("""
    CREATE VIEW vw_eb71_record_quality AS
    SELECT
        i.reading_id,
        i.asset_id,
        i.asset_code,
        i.asset_name,
        i.plaza_id,
        i.operational_date,
        i.reading_datetime,
        1 AS total_records,
        CASE WHEN i.source_quality_class = 'VALID' THEN 1 ELSE 0 END AS source_valid_records,
        CASE WHEN i.source_quality_class = 'EXCEPTION' THEN 1 ELSE 0 END AS source_exception_records,
        CASE WHEN i.analytics_quality_class = 'VALID' THEN 1 ELSE 0 END AS valid_records,
        CASE WHEN i.analytics_quality_class = 'EXCEPTION' THEN 1 ELSE 0 END AS exception_records,
        0 AS reconciliation_difference,
        i.source_data_quality_status,
        i.source_quality_class,
        i.analytics_quality_class,
        i.analytics_exception_reasons
    FROM vw_eb71_interval_detail AS i;
    """)

    cur.execute("""
    CREATE VIEW vw_eb71_entry_audit AS
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
        CASE 
            WHEN i.created_on IS NOT NULL 
            THEN (JULIANDAY(SUBSTR(i.created_on, 1, 19)) - JULIANDAY(SUBSTR(i.reading_datetime, 1, 19))) * 24.0 
        END AS entry_delay_hours,
        CASE 
            WHEN i.created_on IS NULL THEN NULL
            WHEN (JULIANDAY(SUBSTR(i.created_on, 1, 19)) - JULIANDAY(SUBSTR(i.reading_datetime, 1, 19))) < 0 THEN 1 ELSE 0
        END AS negative_entry_delay_timestamp_anomaly,
        CASE 
            WHEN i.created_on IS NULL OR (JULIANDAY(SUBSTR(i.created_on, 1, 19)) - JULIANDAY(SUBSTR(i.reading_datetime, 1, 19))) < 0 THEN NULL
            WHEN (JULIANDAY(SUBSTR(i.created_on, 1, 19)) - JULIANDAY(SUBSTR(i.reading_datetime, 1, 19))) >= 1.0 THEN 1 ELSE 0
        END AS delayed_entry_24h_or_more,
        CASE 
            WHEN i.created_on IS NULL OR (JULIANDAY(SUBSTR(i.created_on, 1, 19)) - JULIANDAY(SUBSTR(i.reading_datetime, 1, 19))) < 0 THEN NULL
            WHEN (JULIANDAY(SUBSTR(i.created_on, 1, 19)) - JULIANDAY(SUBSTR(i.reading_datetime, 1, 19))) < 1.0 THEN 1 ELSE 0
        END AS entry_within_24h,
        CASE 
            WHEN CAST(SUBSTR(i.reading_datetime, 12, 2) AS INTEGER) >= 22 
              OR CAST(SUBSTR(i.reading_datetime, 12, 2) AS INTEGER) < 6 
            THEN 1 ELSE 0 
        END AS reading_datetime_night_indicator,
        CASE 
            WHEN i.created_on IS NULL THEN NULL
            WHEN CAST(SUBSTR(i.created_on, 12, 2) AS INTEGER) >= 22 
              OR CAST(SUBSTR(i.created_on, 12, 2) AS INTEGER) < 6 
            THEN 1 ELSE 0 
        END AS created_on_night_indicator,
        i.analytics_quality_class
    FROM vw_eb71_interval_detail AS i;
    """)

    cur.execute("""
    CREATE VIEW vw_eb71_daily_summary AS
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
            e.entry_delay_hours,
            e.delayed_entry_24h_or_more,
            e.negative_entry_delay_timestamp_anomaly,
            e.reading_datetime_night_indicator,
            e.created_on_night_indicator
        FROM vw_eb71_interval_detail AS i
        JOIN vw_eb71_record_quality AS q USING (reading_id)
        JOIN vw_eb71_entry_audit AS e USING (reading_id)
    )
    SELECT
        asset_id,
        asset_code,
        asset_name,
        plaza_id,
        operational_date,
        SUBSTR(operational_date, 1, 7) AS operational_month,
        CAST(SUBSTR(operational_date, 1, 4) AS INTEGER) AS operational_year,
        COUNT(*) AS total_records,
        SUM(valid_records) AS valid_records,
        SUM(exception_records) AS exception_records,
        SUM(source_valid_records) AS source_valid_records,
        SUM(source_exception_records) AS source_exception_records,
        (COUNT(*) - SUM(valid_records) - SUM(exception_records)) AS reconciliation_difference,
        100.0 * SUM(exception_records) / NULLIF(COUNT(*), 0) AS exception_percentage,
        COALESCE(SUM(normalized_interval_kwh) FILTER (WHERE analytics_quality_class = 'VALID'), 0.0) AS valid_interval_kwh,
        COALESCE(SUM(normalized_interval_kvah) FILTER (WHERE analytics_quality_class = 'VALID'), 0.0) AS valid_interval_kvah,
        COALESCE(SUM(normalized_interval_kvarh) FILTER (WHERE analytics_quality_class = 'VALID'), 0.0) AS valid_interval_kvarh,
        COUNT(*) FILTER (WHERE normalized_interval_kwh IS NULL AND analytics_quality_class = 'VALID') AS valid_rows_missing_interval_kwh,
        COUNT(*) FILTER (WHERE normalized_interval_kvah IS NULL AND analytics_quality_class = 'VALID') AS valid_rows_missing_interval_kvah,
        COUNT(*) FILTER (WHERE normalized_interval_kvarh IS NULL AND analytics_quality_class = 'VALID') AS valid_rows_missing_interval_kvarh,
        SUM(pf) FILTER (WHERE analytics_quality_class = 'VALID' AND pf IS NOT NULL) AS valid_pf_sum,
        COUNT(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_pf_count,
        AVG(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS average_pf,
        MIN(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_pf,
        MAX(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_pf,
        MIN(maximum_demand_value) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_recorded_demand,
        AVG(maximum_demand_value) FILTER (WHERE analytics_quality_class = 'VALID') AS average_recorded_demand,
        MAX(maximum_demand_value) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_recorded_demand,
        SUM(normalized_interval_kwh) FILTER (WHERE analytics_quality_class = 'VALID')
            / NULLIF(SUM(normalized_interval_kvah) FILTER (WHERE analytics_quality_class = 'VALID'), 0) AS kwh_to_kvah_ratio,
        COUNT(*) FILTER (WHERE cumulative_delta_kwh < 0) AS decreasing_cumulative_kwh_count,
        COUNT(*) FILTER (WHERE cumulative_delta_kvah < 0) AS decreasing_cumulative_kvah_count,
        COUNT(*) FILTER (WHERE cumulative_delta_kvarh < 0) AS decreasing_cumulative_kvarh_count,
        COUNT(*) FILTER (WHERE pf < 0 OR pf > 1) AS out_of_range_pf_count,
        COUNT(*) FILTER (WHERE delayed_entry_24h_or_more = 1) AS delayed_entry_count,
        COUNT(*) FILTER (WHERE entry_delay_hours IS NOT NULL AND entry_delay_hours >= 0) AS entry_delay_eligible_count,
        100.0 * COUNT(*) FILTER (WHERE delayed_entry_24h_or_more = 1)
            / NULLIF(COUNT(*) FILTER (WHERE entry_delay_hours IS NOT NULL AND entry_delay_hours >= 0), 0) AS delayed_entry_percentage,
        AVG(entry_delay_hours) FILTER (WHERE entry_delay_hours >= 0) AS average_entry_delay,
        MAX(entry_delay_hours) FILTER (WHERE entry_delay_hours >= 0) AS maximum_entry_delay,
        COUNT(*) FILTER (WHERE negative_entry_delay_timestamp_anomaly = 1) AS negative_entry_delay_timestamp_anomaly_count,
        COUNT(*) FILTER (WHERE reading_datetime_night_indicator = 1) AS night_reading_count,
        COUNT(*) FILTER (WHERE created_on_night_indicator = 1) AS night_entry_count,
        COUNT(*) FILTER (WHERE reading_datetime_night_indicator = 1 AND analytics_quality_class = 'VALID') AS valid_night_reading_count,
        COUNT(*) FILTER (WHERE reading_datetime_night_indicator = 1 AND analytics_quality_class = 'EXCEPTION') AS exception_night_reading_count,
        COUNT(*) FILTER (WHERE created_on_night_indicator = 1 AND analytics_quality_class = 'VALID') AS valid_night_entry_count,
        COUNT(*) FILTER (WHERE created_on_night_indicator = 1 AND analytics_quality_class = 'EXCEPTION') AS exception_night_entry_count
    FROM reading_metrics
    GROUP BY asset_id, asset_code, asset_name, plaza_id, operational_date;
    """)

    cur.execute("""
    CREATE VIEW vw_eb71_asset_latest_reading AS
    SELECT *
    FROM (
        SELECT
            i.*,
            ROW_NUMBER() OVER (
                PARTITION BY i.asset_partition_key
                ORDER BY i.reading_datetime DESC, i.reading_id DESC
            ) AS asset_latest_rank
        FROM vw_eb71_interval_detail AS i
    ) AS ranked
    WHERE asset_latest_rank = 1;
    """)

    # =========================================================================
    # 3. SOLAR SUBMODULE VIEWS
    # =========================================================================
    cur.execute("""
    CREATE VIEW vw_sol71_reading_detail AS
    SELECT
        d.reading_id,
        d.asset_id,
        COALESCE(d.asset_code, a.asset_code) AS asset_code,
        a.asset_name,
        COALESCE(a.plaza_id, d.location) AS plaza_id,
        a.capacity_kva AS registered_capacity_kva,
        d.reading_datetime,
        SUBSTR(d.reading_datetime, 1, 10) AS operational_date,
        d.cumulative_kwh,
        d.interval_kwh,
                d.created_by,
        d.created_on,
        d.created_at,
        d.remarks,
        d.location,
        d.data_quality_status AS source_data_quality_status,
        CASE
            WHEN UPPER(TRIM(COALESCE(d.data_quality_status, ''))) = 'VALID' THEN 'VALID'
            ELSE 'EXCEPTION'
        END AS source_quality_class,
        COALESCE('ID:' || d.asset_id, 'CODE:' || COALESCE(d.asset_code, a.asset_code), 'ROW:' || d.reading_id) AS asset_partition_key
    FROM energy_readings_solar AS d
    LEFT JOIN energy_master_asset AS a
        ON a.asset_id = d.asset_id OR a.asset_code = d.asset_id OR a.asset_code = d.asset_code;
    """)

    cur.execute("""
    CREATE VIEW vw_sol71_interval_reading AS
    WITH sequenced AS (
        SELECT
            r.*,
            ROW_NUMBER() OVER (PARTITION BY r.asset_partition_key ORDER BY r.reading_datetime, r.reading_id) AS reading_sequence,
            LAG(r.reading_id) OVER (PARTITION BY r.asset_partition_key ORDER BY r.reading_datetime, r.reading_id) AS previous_reading_id,
            LAG(r.reading_datetime) OVER (PARTITION BY r.asset_partition_key ORDER BY r.reading_datetime, r.reading_id) AS previous_reading_datetime,
            LAG(r.cumulative_kwh) OVER (PARTITION BY r.asset_partition_key ORDER BY r.reading_datetime, r.reading_id) AS previous_cumulative_kwh
        FROM vw_sol71_reading_detail AS r
    )
    SELECT
        s.*,
        s.cumulative_kwh - s.previous_cumulative_kwh AS cumulative_delta_kwh,
        CASE
            WHEN s.reading_sequence = 1 THEN 'FIRST_READING'
            WHEN s.cumulative_kwh IS NULL THEN 'MISSING_CUMULATIVE_KWH'
            WHEN s.previous_cumulative_kwh IS NULL THEN 'MISSING_PREVIOUS_CUMULATIVE_KWH'
            WHEN s.cumulative_kwh - s.previous_cumulative_kwh < 0 THEN 'NEGATIVE_GENERATION_DELTA'
            ELSE 'VALID_INTERVAL'
        END AS generation_interval_class,
        s.interval_kwh - (s.cumulative_kwh - s.previous_cumulative_kwh) AS reported_vs_cumulative_delta_kwh
    FROM sequenced AS s;
    """)

    cur.execute("""
    CREATE VIEW vw_sol71_record_quality AS
    SELECT
        i.reading_id,
        i.asset_id,
        i.asset_code,
        i.asset_name,
        i.plaza_id,
        i.operational_date,
        i.reading_datetime,
        1 AS total_records,
        CASE WHEN i.source_quality_class = 'VALID' THEN 1 ELSE 0 END AS source_valid_records,
        CASE WHEN i.source_quality_class = 'EXCEPTION' THEN 1 ELSE 0 END AS source_exception_records,
        CASE WHEN i.source_quality_class = 'VALID' AND (i.cumulative_delta_kwh IS NULL OR i.cumulative_delta_kwh >= 0) THEN 1 ELSE 0 END AS valid_records,
        CASE WHEN i.source_quality_class <> 'VALID' OR i.cumulative_delta_kwh < 0 THEN 1 ELSE 0 END AS exception_records,
        0 AS reconciliation_difference,
        i.source_data_quality_status,
        i.source_quality_class,
        CASE WHEN i.source_quality_class = 'VALID' AND (i.cumulative_delta_kwh IS NULL OR i.cumulative_delta_kwh >= 0) THEN 'VALID' ELSE 'EXCEPTION' END AS analytics_quality_class,
        CASE WHEN i.cumulative_delta_kwh < 0 THEN 'DECREASING_CUMULATIVE_KWH' ELSE '' END AS analytics_exception_reasons
    FROM vw_sol71_interval_reading AS i;
    """)

    cur.execute("""
    CREATE VIEW vw_sol71_entry_audit AS
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
        CASE 
            WHEN d.created_on IS NOT NULL 
            THEN (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) * 24.0 
        END AS entry_delay_hours,
        CASE 
            WHEN d.created_on IS NULL THEN NULL
            WHEN (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) < 0 THEN 1 ELSE 0
        END AS negative_entry_delay_timestamp_anomaly,
        CASE 
            WHEN d.created_on IS NULL OR (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) < 0 THEN NULL
            WHEN (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) >= 1.0 THEN 1 ELSE 0
        END AS delayed_entry_24h_or_more,
        CASE 
            WHEN d.created_on IS NULL OR (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) < 0 THEN NULL
            WHEN (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) < 1.0 THEN 1 ELSE 0
        END AS entry_within_24h,
        CASE 
            WHEN CAST(SUBSTR(d.reading_datetime, 12, 2) AS INTEGER) >= 22 
              OR CAST(SUBSTR(d.reading_datetime, 12, 2) AS INTEGER) < 6 
            THEN 1 ELSE 0 
        END AS reading_datetime_night_indicator,
        CASE 
            WHEN d.created_on IS NULL THEN NULL
            WHEN CAST(SUBSTR(d.created_on, 12, 2) AS INTEGER) >= 22 
              OR CAST(SUBSTR(d.created_on, 12, 2) AS INTEGER) < 6 
            THEN 1 ELSE 0 
        END AS created_on_night_indicator,
        q.analytics_quality_class
    FROM vw_sol71_reading_detail AS d
    JOIN vw_sol71_record_quality AS q USING (reading_id);
    """)

    cur.execute("""
    CREATE VIEW vw_sol71_daily_summary AS
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
            a.entry_delay_hours,
            a.delayed_entry_24h_or_more,
            a.negative_entry_delay_timestamp_anomaly,
            a.reading_datetime_night_indicator,
            a.created_on_night_indicator,
            d.created_on
        FROM vw_sol71_reading_detail AS d
        JOIN vw_sol71_interval_reading AS i USING (reading_id)
        JOIN vw_sol71_record_quality AS q USING (reading_id)
        JOIN vw_sol71_entry_audit AS a USING (reading_id)
    )
    SELECT
        asset_id,
        asset_code,
        asset_name,
        plaza_id,
        asset_partition_key,
        operational_date,
        SUBSTR(operational_date, 1, 7) AS operational_month,
        CAST(SUBSTR(operational_date, 1, 4) AS INTEGER) AS operational_year,
        COUNT(*) AS total_records,
        SUM(valid_records) AS valid_records,
        SUM(exception_records) AS exception_records,
        SUM(source_valid_records) AS source_valid_records,
        SUM(source_exception_records) AS source_exception_records,
        (COUNT(*) - SUM(valid_records) - SUM(exception_records)) AS reconciliation_difference,
        100.0 * SUM(valid_records) / NULLIF(COUNT(*), 0) AS observed_record_availability_pct,
        SUM(interval_kwh) FILTER (WHERE analytics_quality_class = 'VALID' AND interval_kwh >= 0) AS valid_generation_kwh,
        COUNT(interval_kwh) FILTER (WHERE analytics_quality_class = 'VALID' AND interval_kwh >= 0) AS valid_generation_interval_count,
        AVG(interval_kwh) FILTER (WHERE analytics_quality_class = 'VALID' AND interval_kwh >= 0) AS average_generation_interval_kwh,
        MAX(interval_kwh) FILTER (WHERE analytics_quality_class = 'VALID' AND interval_kwh >= 0) AS maximum_generation_interval_kwh,
        COUNT(*) FILTER (WHERE analytics_quality_class = 'VALID' AND interval_kwh = 0) AS zero_generation_interval_count,
        COUNT(*) FILTER (WHERE generation_interval_class = 'FIRST_READING') AS first_reading_count,
        COUNT(*) FILTER (WHERE generation_interval_class = 'MISSING_PREVIOUS_CUMULATIVE_KWH') AS missing_previous_cumulative_kwh_count,
        COUNT(*) FILTER (WHERE generation_interval_class = 'MISSING_CUMULATIVE_KWH') AS missing_cumulative_kwh_count,
        COUNT(*) FILTER (WHERE analytics_quality_class = 'VALID' AND interval_kwh IS NULL) AS missing_interval_kwh_count,
        COUNT(*) FILTER (WHERE cumulative_delta_kwh < 0) AS decreasing_cumulative_kwh_count,
        COALESCE(SUM(reported_vs_cumulative_delta_kwh) FILTER (WHERE analytics_quality_class = 'VALID'), 0.0) AS reported_vs_cumulative_delta_sum_kwh,
        COUNT(*) FILTER (WHERE delayed_entry_24h_or_more = 1) AS delayed_entry_count,
        COUNT(*) FILTER (WHERE entry_delay_hours IS NOT NULL AND entry_delay_hours >= 0) AS entry_delay_eligible_count,
        100.0 * COUNT(*) FILTER (WHERE delayed_entry_24h_or_more = 1)
            / NULLIF(COUNT(*) FILTER (WHERE entry_delay_hours IS NOT NULL AND entry_delay_hours >= 0), 0) AS delayed_entry_percentage,
        AVG(entry_delay_hours) FILTER (WHERE entry_delay_hours >= 0) AS average_entry_delay,
        MAX(entry_delay_hours) FILTER (WHERE entry_delay_hours >= 0) AS maximum_entry_delay,
        COUNT(*) FILTER (WHERE negative_entry_delay_timestamp_anomaly = 1) AS negative_entry_delay_timestamp_anomaly_count,
        COUNT(*) FILTER (WHERE reading_datetime_night_indicator = 1) AS night_reading_count,
        COUNT(*) FILTER (WHERE created_on_night_indicator = 1) AS night_entry_count
    FROM reading_metrics
    GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_date;
    """)

    cur.execute("""
    CREATE VIEW vw_sol71_asset_latest_reading AS
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (PARTITION BY d.asset_partition_key ORDER BY d.reading_datetime DESC, d.reading_id DESC) AS asset_latest_rank
        FROM vw_sol71_reading_detail AS d
    ) ranked
    WHERE asset_latest_rank = 1;
    """)

    # =========================================================================
    # 4. TRANSFORMER SUBMODULE VIEWS
    # =========================================================================
    cur.execute("""
    CREATE VIEW vw_trf71_reading_detail AS
    SELECT
        d.reading_id,
        d.asset_id,
        COALESCE(d.asset_code, a.asset_code) AS asset_code,
        a.asset_name,
        COALESCE(a.plaza_id, d.location) AS plaza_id,
        a.capacity_kva AS registered_capacity_kva,
        d.reading_datetime,
        SUBSTR(d.reading_datetime, 1, 10) AS operational_date,
        d.primary_v_ry, d.primary_v_yb, d.primary_v_br,
        d.secondary_v_ry, d.secondary_v_yb, d.secondary_v_br,
        d.primary_i_r, d.primary_i_y, d.primary_i_b,
        d.secondary_i_r, d.secondary_i_y, d.secondary_i_b,
        d.oil_temperature,
        d.winding_temperature,
        d.pf,
        d.frequency AS frequency_hz,
        NULL AS cumulative_kwh_value,
        NULL AS interval_kwh_value,
        d.created_by,
        d.created_on,
        d.created_at,
        d.remarks,
        d.location,
        d.data_quality_status AS source_data_quality_status,
        CASE
            WHEN UPPER(TRIM(COALESCE(d.data_quality_status, ''))) = 'VALID' THEN 'VALID'
            ELSE 'EXCEPTION'
        END AS source_quality_class,
        COALESCE('ID:' || d.asset_id, 'CODE:' || COALESCE(d.asset_code, a.asset_code), 'ROW:' || d.reading_id) AS asset_partition_key
    FROM energy_readings_transformer AS d
    LEFT JOIN energy_master_asset AS a
        ON a.asset_id = d.asset_id OR a.asset_code = d.asset_id OR a.asset_code = d.asset_code;
    """)

    cur.execute("""
    CREATE VIEW vw_trf71_electrical_reading AS
    WITH means AS (
        SELECT
            d.*,
            CASE WHEN d.primary_v_ry IS NOT NULL AND d.primary_v_yb IS NOT NULL AND d.primary_v_br IS NOT NULL
                 THEN (d.primary_v_ry + d.primary_v_yb + d.primary_v_br) / 3.0 END AS primary_v_mean,
            CASE WHEN d.secondary_v_ry IS NOT NULL AND d.secondary_v_yb IS NOT NULL AND d.secondary_v_br IS NOT NULL
                 THEN (d.secondary_v_ry + d.secondary_v_yb + d.secondary_v_br) / 3.0 END AS secondary_v_mean,
            CASE WHEN d.primary_i_r IS NOT NULL AND d.primary_i_y IS NOT NULL AND d.primary_i_b IS NOT NULL
                 THEN (d.primary_i_r + d.primary_i_y + d.primary_i_b) / 3.0 END AS primary_i_mean,
            CASE WHEN d.secondary_i_r IS NOT NULL AND d.secondary_i_y IS NOT NULL AND d.secondary_i_b IS NOT NULL
                 THEN (d.secondary_i_r + d.secondary_i_y + d.secondary_i_b) / 3.0 END AS secondary_i_mean,
            ((CASE WHEN d.primary_v_ry IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN d.primary_v_yb IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN d.primary_v_br IS NOT NULL THEN 1 ELSE 0 END)) AS primary_voltage_phase_count,
            ((CASE WHEN d.secondary_v_ry IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN d.secondary_v_yb IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN d.secondary_v_br IS NOT NULL THEN 1 ELSE 0 END)) AS secondary_voltage_phase_count,
            ((CASE WHEN d.primary_i_r IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN d.primary_i_y IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN d.primary_i_b IS NOT NULL THEN 1 ELSE 0 END)) AS primary_current_phase_count,
            ((CASE WHEN d.secondary_i_r IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN d.secondary_i_y IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN d.secondary_i_b IS NOT NULL THEN 1 ELSE 0 END)) AS secondary_current_phase_count
        FROM vw_trf71_reading_detail AS d
    )
    SELECT
        m.*,
        CASE
            WHEN m.primary_voltage_phase_count = 3 AND m.primary_v_mean > 0
            THEN 100.0 * MAX(ABS(m.primary_v_ry - m.primary_v_mean), MAX(ABS(m.primary_v_yb - m.primary_v_mean), ABS(m.primary_v_br - m.primary_v_mean))) / m.primary_v_mean
        END AS primary_voltage_imbalance_pct,
        CASE
            WHEN m.secondary_voltage_phase_count = 3 AND m.secondary_v_mean > 0
            THEN 100.0 * MAX(ABS(m.secondary_v_ry - m.secondary_v_mean), MAX(ABS(m.secondary_v_yb - m.secondary_v_mean), ABS(m.secondary_v_br - m.secondary_v_mean))) / m.secondary_v_mean
        END AS secondary_voltage_imbalance_pct,
        CASE
            WHEN m.primary_current_phase_count = 3 AND m.primary_i_mean > 0
            THEN 100.0 * MAX(ABS(m.primary_i_r - m.primary_i_mean), MAX(ABS(m.primary_i_y - m.primary_i_mean), ABS(m.primary_i_b - m.primary_i_mean))) / m.primary_i_mean
        END AS primary_current_imbalance_pct,
        CASE
            WHEN m.secondary_current_phase_count = 3 AND m.secondary_i_mean > 0
            THEN 100.0 * MAX(ABS(m.secondary_i_r - m.secondary_i_mean), MAX(ABS(m.secondary_i_y - m.secondary_i_mean), ABS(m.secondary_i_b - m.secondary_i_mean))) / m.secondary_i_mean
        END AS secondary_current_imbalance_pct
    FROM means AS m;
    """)

    cur.execute("""
    CREATE VIEW vw_trf71_record_quality AS
    SELECT
        d.reading_id,
        d.asset_id,
        d.asset_code,
        d.asset_name,
        d.plaza_id,
        d.operational_date,
        d.reading_datetime,
        1 AS total_records,
        CASE WHEN d.source_quality_class = 'VALID' THEN 1 ELSE 0 END AS source_valid_records,
        CASE WHEN d.source_quality_class = 'EXCEPTION' THEN 1 ELSE 0 END AS source_exception_records,
        CASE WHEN d.source_quality_class = 'VALID' THEN 1 ELSE 0 END AS valid_records,
        CASE WHEN d.source_quality_class <> 'VALID' THEN 1 ELSE 0 END AS exception_records,
        0 AS reconciliation_difference,
        d.source_data_quality_status,
        d.source_quality_class,
        d.source_quality_class AS analytics_quality_class,
        '' AS analytics_exception_reasons
    FROM vw_trf71_reading_detail AS d;
    """)

    cur.execute("""
    CREATE VIEW vw_trf71_entry_audit AS
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
        CASE 
            WHEN d.created_on IS NOT NULL 
            THEN (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) * 24.0 
        END AS entry_delay_hours,
        CASE 
            WHEN d.created_on IS NULL THEN NULL
            WHEN (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) < 0 THEN 1 ELSE 0
        END AS negative_entry_delay_timestamp_anomaly,
        CASE 
            WHEN d.created_on IS NULL OR (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) < 0 THEN NULL
            WHEN (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) >= 1.0 THEN 1 ELSE 0
        END AS delayed_entry_24h_or_more,
        CASE 
            WHEN d.created_on IS NULL OR (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) < 0 THEN NULL
            WHEN (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) < 1.0 THEN 1 ELSE 0
        END AS entry_within_24h,
        CASE 
            WHEN CAST(SUBSTR(d.reading_datetime, 12, 2) AS INTEGER) >= 22 
              OR CAST(SUBSTR(d.reading_datetime, 12, 2) AS INTEGER) < 6 
            THEN 1 ELSE 0 
        END AS reading_datetime_night_indicator,
        CASE 
            WHEN d.created_on IS NULL THEN NULL
            WHEN CAST(SUBSTR(d.created_on, 12, 2) AS INTEGER) >= 22 
              OR CAST(SUBSTR(d.created_on, 12, 2) AS INTEGER) < 6 
            THEN 1 ELSE 0 
        END AS created_on_night_indicator,
        q.analytics_quality_class
    FROM vw_trf71_reading_detail AS d
    JOIN vw_trf71_record_quality AS q USING (reading_id);
    """)

    cur.execute("""
    CREATE VIEW vw_trf71_daily_summary AS
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
            e.oil_temperature AS oil_temperature_c,
            e.winding_temperature AS winding_temperature_c,
            e.primary_voltage_imbalance_pct,
            e.secondary_voltage_imbalance_pct,
            e.primary_current_imbalance_pct,
            e.secondary_current_imbalance_pct,
            a.entry_delay_hours,
            a.delayed_entry_24h_or_more,
            a.negative_entry_delay_timestamp_anomaly,
            a.reading_datetime_night_indicator,
            a.created_on_night_indicator
        FROM vw_trf71_reading_detail AS d
        JOIN vw_trf71_record_quality AS q USING (reading_id)
        JOIN vw_trf71_electrical_reading AS e USING (reading_id)
        JOIN vw_trf71_entry_audit AS a USING (reading_id)
    )
    SELECT
        asset_id,
        asset_code,
        asset_name,
        plaza_id,
        asset_partition_key,
        operational_date,
        SUBSTR(operational_date, 1, 7) AS operational_month,
        CAST(SUBSTR(operational_date, 1, 4) AS INTEGER) AS operational_year,
        COUNT(*) AS total_records,
        SUM(valid_records) AS valid_records,
        SUM(exception_records) AS exception_records,
        SUM(source_valid_records) AS source_valid_records,
        SUM(source_exception_records) AS source_exception_records,
        (COUNT(*) - SUM(valid_records) - SUM(exception_records)) AS reconciliation_difference,
        100.0 * SUM(exception_records) / NULLIF(COUNT(*), 0) AS exception_percentage,
        SUM(pf) FILTER (WHERE analytics_quality_class = 'VALID' AND pf IS NOT NULL) AS valid_pf_sum,
        COUNT(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_pf_count,
        AVG(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS average_pf,
        MIN(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_pf,
        MAX(pf) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_pf,
        AVG(frequency_hz) FILTER (WHERE analytics_quality_class = 'VALID') AS average_frequency_hz,
        SUM(frequency_hz) FILTER (WHERE analytics_quality_class = 'VALID' AND frequency_hz IS NOT NULL) AS valid_frequency_sum,
        COUNT(frequency_hz) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_frequency_count,
        MIN(frequency_hz) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_frequency_hz,
        MAX(frequency_hz) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_frequency_hz,
        SUM(oil_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID' AND oil_temperature_c IS NOT NULL) AS valid_oil_temperature_sum,
        COUNT(oil_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_oil_temperature_count,
        AVG(oil_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS average_oil_temperature_c,
        MIN(oil_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_oil_temperature_c,
        MAX(oil_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_oil_temperature_c,
        SUM(winding_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID' AND winding_temperature_c IS NOT NULL) AS valid_winding_temperature_sum,
        COUNT(winding_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_winding_temperature_count,
        AVG(winding_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS average_winding_temperature_c,
        MIN(winding_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_winding_temperature_c,
        MAX(winding_temperature_c) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_winding_temperature_c,
        SUM(primary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID' AND primary_voltage_imbalance_pct IS NOT NULL) AS valid_primary_voltage_imbalance_sum,
        COUNT(primary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_primary_voltage_imbalance_count,
        AVG(primary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS average_primary_voltage_imbalance_pct,
        MAX(primary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS max_primary_voltage_imbalance_pct,
        SUM(secondary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID' AND secondary_voltage_imbalance_pct IS NOT NULL) AS valid_secondary_voltage_imbalance_sum,
        COUNT(secondary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_secondary_voltage_imbalance_count,
        AVG(secondary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS average_secondary_voltage_imbalance_pct,
        MAX(secondary_voltage_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS max_secondary_voltage_imbalance_pct,
        SUM(primary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID' AND primary_current_imbalance_pct IS NOT NULL) AS valid_primary_current_imbalance_sum,
        COUNT(primary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_primary_current_imbalance_count,
        AVG(primary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS average_primary_current_imbalance_pct,
        MAX(primary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS max_primary_current_imbalance_pct,
        SUM(secondary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID' AND secondary_current_imbalance_pct IS NOT NULL) AS valid_secondary_current_imbalance_sum,
        COUNT(secondary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_secondary_current_imbalance_count,
        AVG(secondary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS average_secondary_current_imbalance_pct,
        MAX(secondary_current_imbalance_pct) FILTER (WHERE analytics_quality_class = 'VALID') AS max_secondary_current_imbalance_pct,
        COUNT(*) FILTER (WHERE delayed_entry_24h_or_more = 1) AS delayed_entry_count,
        COUNT(*) FILTER (WHERE entry_delay_hours IS NOT NULL AND entry_delay_hours >= 0) AS entry_delay_eligible_count,
        100.0 * COUNT(*) FILTER (WHERE delayed_entry_24h_or_more = 1) / NULLIF(COUNT(*) FILTER (WHERE entry_delay_hours IS NOT NULL AND entry_delay_hours >= 0), 0) AS delayed_entry_percentage,
        AVG(entry_delay_hours) FILTER (WHERE entry_delay_hours >= 0) AS average_entry_delay,
        MAX(entry_delay_hours) FILTER (WHERE entry_delay_hours >= 0) AS maximum_entry_delay,
        COUNT(*) FILTER (WHERE negative_entry_delay_timestamp_anomaly = 1) AS negative_entry_delay_timestamp_anomaly_count,
        COUNT(*) FILTER (WHERE reading_datetime_night_indicator = 1) AS night_reading_count,
        COUNT(*) FILTER (WHERE created_on_night_indicator = 1) AS night_entry_count
    FROM reading_metrics
    GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_date;
    """)

    cur.execute("""
    CREATE VIEW vw_trf71_asset_latest_reading AS
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (PARTITION BY d.asset_partition_key ORDER BY d.reading_datetime DESC, d.reading_id DESC) AS asset_latest_rank
        FROM vw_trf71_reading_detail AS d
    ) ranked
    WHERE asset_latest_rank = 1;
    """)

    # =========================================================================
    # 5. UPS SUBMODULE VIEWS
    # =========================================================================
    cur.execute("""
    CREATE VIEW vw_ups71_reading_detail AS
    SELECT
        d.reading_id,
        d.asset_id,
        COALESCE(d.asset_code, a.asset_code) AS asset_code,
        a.asset_name,
        COALESCE(a.plaza_id, d.location) AS plaza_id,
        a.capacity_kva AS registered_capacity_kva,
        d.reading_datetime,
        SUBSTR(d.reading_datetime, 1, 10) AS operational_date,
        d.output_voltage,
        d.output_current,
        d.output_frequency,
        d.battery_vdc,
        d.battery_temperature,
        d.rectifier_voltage,
        d.created_by,
        d.created_on,
        d.created_at,
        d.remarks,
        d.location,
        d.data_quality_status AS source_data_quality_status,
        CASE
            WHEN UPPER(TRIM(COALESCE(d.data_quality_status, ''))) = 'VALID' THEN 'VALID'
            ELSE 'EXCEPTION'
        END AS source_quality_class,
        COALESCE('ID:' || d.asset_id, 'CODE:' || COALESCE(d.asset_code, a.asset_code), 'ROW:' || d.reading_id) AS asset_partition_key
    FROM energy_readings_ups AS d
    LEFT JOIN energy_master_asset AS a
        ON a.asset_id = d.asset_id OR a.asset_code = d.asset_id OR a.asset_code = d.asset_code;
    """)

    cur.execute("""
    CREATE VIEW vw_ups71_record_quality AS
    SELECT
        d.reading_id,
        d.asset_id,
        d.asset_code,
        d.asset_name,
        d.plaza_id,
        d.operational_date,
        d.reading_datetime,
        1 AS total_records,
        CASE WHEN d.source_quality_class = 'VALID' THEN 1 ELSE 0 END AS source_valid_records,
        CASE WHEN d.source_quality_class = 'EXCEPTION' THEN 1 ELSE 0 END AS source_exception_records,
        CASE WHEN d.source_quality_class = 'VALID' THEN 1 ELSE 0 END AS valid_records,
        CASE WHEN d.source_quality_class <> 'VALID' THEN 1 ELSE 0 END AS exception_records,
        0 AS reconciliation_difference,
        d.source_data_quality_status,
        d.source_quality_class,
        d.source_quality_class AS analytics_quality_class,
        '' AS analytics_exception_reasons
    FROM vw_ups71_reading_detail AS d;
    """)

    cur.execute("""
    CREATE VIEW vw_ups71_entry_audit AS
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
        CASE 
            WHEN d.created_on IS NOT NULL 
            THEN (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) * 24.0 
        END AS entry_delay_hours,
        CASE 
            WHEN d.created_on IS NULL THEN NULL
            WHEN (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) < 0 THEN 1 ELSE 0
        END AS negative_entry_delay_timestamp_anomaly,
        CASE 
            WHEN d.created_on IS NULL OR (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) < 0 THEN NULL
            WHEN (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) >= 1.0 THEN 1 ELSE 0
        END AS delayed_entry_24h_or_more,
        CASE 
            WHEN d.created_on IS NULL OR (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) < 0 THEN NULL
            WHEN (JULIANDAY(SUBSTR(d.created_on, 1, 19)) - JULIANDAY(SUBSTR(d.reading_datetime, 1, 19))) < 1.0 THEN 1 ELSE 0
        END AS entry_within_24h,
        CASE 
            WHEN CAST(SUBSTR(d.reading_datetime, 12, 2) AS INTEGER) >= 22 
              OR CAST(SUBSTR(d.reading_datetime, 12, 2) AS INTEGER) < 6 
            THEN 1 ELSE 0 
        END AS reading_datetime_night_indicator,
        CASE 
            WHEN d.created_on IS NULL THEN NULL
            WHEN CAST(SUBSTR(d.created_on, 12, 2) AS INTEGER) >= 22 
              OR CAST(SUBSTR(d.created_on, 12, 2) AS INTEGER) < 6 
            THEN 1 ELSE 0 
        END AS created_on_night_indicator,
        q.analytics_quality_class
    FROM vw_ups71_reading_detail AS d
    JOIN vw_ups71_record_quality AS q USING (reading_id);
    """)

    cur.execute("""
    CREATE VIEW vw_ups71_daily_summary AS
    WITH metrics AS (
        SELECT
            d.reading_id, d.asset_id, d.asset_code, d.asset_name, d.plaza_id,
            d.asset_partition_key, d.operational_date, d.created_on,
            d.output_voltage, d.output_current, d.output_frequency,
            d.battery_vdc, d.battery_temperature, d.rectifier_voltage,
            q.valid_records, q.exception_records, q.source_valid_records, q.source_exception_records,
            q.analytics_quality_class,
            a.entry_delay_hours, a.delayed_entry_24h_or_more,
            a.negative_entry_delay_timestamp_anomaly,
            a.reading_datetime_night_indicator, a.created_on_night_indicator
        FROM vw_ups71_reading_detail AS d
        JOIN vw_ups71_record_quality AS q USING (reading_id)
        JOIN vw_ups71_entry_audit AS a USING (reading_id)
    )
    SELECT
        asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_date,
        SUBSTR(operational_date, 1, 7) AS operational_month,
        CAST(SUBSTR(operational_date, 1, 4) AS INTEGER) AS operational_year,
        COUNT(*) AS total_records,
        SUM(valid_records) AS valid_records,
        SUM(exception_records) AS exception_records,
        SUM(source_valid_records) AS source_valid_records,
        SUM(source_exception_records) AS source_exception_records,
        (COUNT(*) - SUM(valid_records) - SUM(exception_records)) AS reconciliation_difference,
        100.0 * SUM(valid_records) / NULLIF(COUNT(*), 0) AS observed_record_availability_pct,
        SUM(output_voltage) FILTER (WHERE analytics_quality_class = 'VALID' AND output_voltage IS NOT NULL) AS valid_output_voltage_sum,
        COUNT(output_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_output_voltage_count,
        AVG(output_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS average_output_voltage,
        MIN(output_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_output_voltage,
        MAX(output_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_output_voltage,
        SUM(output_current) FILTER (WHERE analytics_quality_class = 'VALID' AND output_current IS NOT NULL) AS valid_output_current_sum,
        COUNT(output_current) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_output_current_count,
        AVG(output_current) FILTER (WHERE analytics_quality_class = 'VALID') AS average_output_current,
        MIN(output_current) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_output_current,
        MAX(output_current) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_output_current,
        SUM(output_frequency) FILTER (WHERE analytics_quality_class = 'VALID' AND output_frequency IS NOT NULL) AS valid_output_frequency_sum,
        COUNT(output_frequency) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_output_frequency_count,
        AVG(output_frequency) FILTER (WHERE analytics_quality_class = 'VALID') AS average_output_frequency,
        MIN(output_frequency) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_output_frequency,
        MAX(output_frequency) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_output_frequency,
        SUM(battery_vdc) FILTER (WHERE analytics_quality_class = 'VALID' AND battery_vdc IS NOT NULL) AS valid_battery_vdc_sum,
        COUNT(battery_vdc) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_battery_vdc_count,
        AVG(battery_vdc) FILTER (WHERE analytics_quality_class = 'VALID') AS average_battery_vdc,
        MIN(battery_vdc) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_battery_vdc,
        MAX(battery_vdc) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_battery_vdc,
        SUM(battery_temperature) FILTER (WHERE analytics_quality_class = 'VALID' AND battery_temperature IS NOT NULL) AS valid_battery_temperature_sum,
        COUNT(battery_temperature) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_battery_temperature_count,
        AVG(battery_temperature) FILTER (WHERE analytics_quality_class = 'VALID') AS average_battery_temperature,
        MIN(battery_temperature) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_battery_temperature,
        MAX(battery_temperature) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_battery_temperature,
        SUM(rectifier_voltage) FILTER (WHERE analytics_quality_class = 'VALID' AND rectifier_voltage IS NOT NULL) AS valid_rectifier_voltage_sum,
        COUNT(rectifier_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS valid_rectifier_voltage_count,
        AVG(rectifier_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS average_rectifier_voltage,
        MIN(rectifier_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS minimum_rectifier_voltage,
        MAX(rectifier_voltage) FILTER (WHERE analytics_quality_class = 'VALID') AS maximum_rectifier_voltage,
        COUNT(*) FILTER (WHERE delayed_entry_24h_or_more = 1) AS delayed_entry_count,
        COUNT(*) FILTER (WHERE entry_delay_hours IS NOT NULL AND entry_delay_hours >= 0) AS entry_delay_eligible_count,
        100.0 * COUNT(*) FILTER (WHERE delayed_entry_24h_or_more = 1) / NULLIF(COUNT(*) FILTER (WHERE entry_delay_hours IS NOT NULL AND entry_delay_hours >= 0), 0) AS delayed_entry_percentage,
        AVG(entry_delay_hours) FILTER (WHERE entry_delay_hours >= 0) AS average_entry_delay_hours,
        MAX(entry_delay_hours) FILTER (WHERE entry_delay_hours >= 0) AS maximum_entry_delay_hours,
        COUNT(*) FILTER (WHERE negative_entry_delay_timestamp_anomaly = 1) AS negative_entry_delay_timestamp_anomaly_count,
        COUNT(*) FILTER (WHERE created_on IS NOT NULL) AS created_on_timestamp_count,
        COUNT(*) FILTER (WHERE reading_datetime_night_indicator = 1) AS night_reading_count,
        COUNT(*) FILTER (WHERE created_on_night_indicator = 1) AS night_entry_count
    FROM metrics
    GROUP BY asset_id, asset_code, asset_name, plaza_id, asset_partition_key, operational_date;
    """)

    cur.execute("""
    CREATE VIEW vw_ups71_asset_latest_reading AS
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (PARTITION BY d.asset_partition_key ORDER BY d.reading_datetime DESC, d.reading_id DESC) AS asset_latest_rank
        FROM vw_ups71_reading_detail AS d
    ) ranked
    WHERE asset_latest_rank = 1;
    """)

    # =========================================================================
    # 6. UNIFIED MODULE 7 VIEWS
    # =========================================================================
    cur.execute("""
    CREATE VIEW vw_m7_record_quality AS
    SELECT
        'DG' AS source_type,
        q.reading_id, q.asset_id, q.asset_code, q.asset_name, q.plaza_id,
        COALESCE('ID:' || q.asset_id, 'CODE:' || q.asset_code, 'ROW:' || q.reading_id) AS asset_partition_key,
        q.operational_date, q.reading_datetime,
        q.total_records, q.valid_records, q.exception_records, q.reconciliation_difference,
        q.source_data_quality_status, q.analytics_quality_class, q.analytics_exception_reasons
    FROM vw_dg71_record_quality AS q
    UNION ALL
    SELECT
        'EB', q.reading_id, q.asset_id, q.asset_code, q.asset_name, q.plaza_id,
        COALESCE('ID:' || q.asset_id, 'CODE:' || q.asset_code, 'ROW:' || q.reading_id),
        q.operational_date, q.reading_datetime,
        q.total_records, q.valid_records, q.exception_records, q.reconciliation_difference,
        q.source_data_quality_status, q.analytics_quality_class, q.analytics_exception_reasons
    FROM vw_eb71_record_quality AS q
    UNION ALL
    SELECT
        'SOLAR', q.reading_id, q.asset_id, q.asset_code, q.asset_name, q.plaza_id,
        COALESCE('ID:' || q.asset_id, 'CODE:' || q.asset_code, 'ROW:' || q.reading_id),
        q.operational_date, q.reading_datetime,
        q.total_records, q.valid_records, q.exception_records, q.reconciliation_difference,
        q.source_data_quality_status, q.analytics_quality_class, q.analytics_exception_reasons
    FROM vw_sol71_record_quality AS q
    UNION ALL
    SELECT
        'TRANSFORMER', q.reading_id, q.asset_id, q.asset_code, q.asset_name, q.plaza_id,
        COALESCE('ID:' || q.asset_id, 'CODE:' || q.asset_code, 'ROW:' || q.reading_id),
        q.operational_date, q.reading_datetime,
        q.total_records, q.valid_records, q.exception_records, q.reconciliation_difference,
        q.source_data_quality_status, q.analytics_quality_class, q.analytics_exception_reasons
    FROM vw_trf71_record_quality AS q
    UNION ALL
    SELECT
        'UPS', q.reading_id, q.asset_id, q.asset_code, q.asset_name, q.plaza_id,
        COALESCE('ID:' || q.asset_id, 'CODE:' || q.asset_code, 'ROW:' || q.reading_id),
        q.operational_date, q.reading_datetime,
        q.total_records, q.valid_records, q.exception_records, q.reconciliation_difference,
        q.source_data_quality_status, q.analytics_quality_class, q.analytics_exception_reasons
    FROM vw_ups71_record_quality AS q;
    """)

    cur.execute("""
    CREATE VIEW vw_m7_entry_audit AS
    SELECT
        'DG' AS source_type, a.reading_id, a.asset_id, a.asset_code, a.asset_name, a.plaza_id,
        COALESCE('ID:' || a.asset_id, 'CODE:' || a.asset_code, 'ROW:' || a.reading_id) AS asset_partition_key,
        a.operational_date, a.reading_datetime, a.created_on, a.created_by,
        a.entry_delay_hours, a.negative_entry_delay_timestamp_anomaly,
        a.delayed_entry_24h_or_more, a.entry_within_24h,
        a.reading_datetime_night_indicator, a.created_on_night_indicator,
        a.analytics_quality_class
    FROM vw_dg71_entry_audit AS a
    UNION ALL
    SELECT
        'EB', a.reading_id, a.asset_id, a.asset_code, a.asset_name, a.plaza_id,
        COALESCE('ID:' || a.asset_id, 'CODE:' || a.asset_code, 'ROW:' || a.reading_id),
        a.operational_date, a.reading_datetime, a.created_on, a.created_by,
        a.entry_delay_hours, a.negative_entry_delay_timestamp_anomaly,
        a.delayed_entry_24h_or_more, a.entry_within_24h,
        a.reading_datetime_night_indicator, a.created_on_night_indicator,
        a.analytics_quality_class
    FROM vw_eb71_entry_audit AS a
    UNION ALL
    SELECT
        'SOLAR', a.reading_id, a.asset_id, a.asset_code, a.asset_name, a.plaza_id,
        COALESCE('ID:' || a.asset_id, 'CODE:' || a.asset_code, 'ROW:' || a.reading_id),
        a.operational_date, a.reading_datetime, a.created_on, a.created_by,
        a.entry_delay_hours, a.negative_entry_delay_timestamp_anomaly,
        a.delayed_entry_24h_or_more, a.entry_within_24h,
        a.reading_datetime_night_indicator, a.created_on_night_indicator,
        a.analytics_quality_class
    FROM vw_sol71_entry_audit AS a
    UNION ALL
    SELECT
        'TRANSFORMER', a.reading_id, a.asset_id, a.asset_code, a.asset_name, a.plaza_id,
        COALESCE('ID:' || a.asset_id, 'CODE:' || a.asset_code, 'ROW:' || a.reading_id),
        a.operational_date, a.reading_datetime, a.created_on, a.created_by,
        a.entry_delay_hours, a.negative_entry_delay_timestamp_anomaly,
        a.delayed_entry_24h_or_more, a.entry_within_24h,
        a.reading_datetime_night_indicator, a.created_on_night_indicator,
        a.analytics_quality_class
    FROM vw_trf71_entry_audit AS a
    UNION ALL
    SELECT
        'UPS', a.reading_id, a.asset_id, a.asset_code, a.asset_name, a.plaza_id,
        COALESCE('ID:' || a.asset_id, 'CODE:' || a.asset_code, 'ROW:' || a.reading_id),
        a.operational_date, a.reading_datetime, a.created_on, a.created_by,
        a.entry_delay_hours, a.negative_entry_delay_timestamp_anomaly,
        a.delayed_entry_24h_or_more, a.entry_within_24h,
        a.reading_datetime_night_indicator, a.created_on_night_indicator,
        a.analytics_quality_class
    FROM vw_ups71_entry_audit AS a;
    """)

    cur.execute("""
    CREATE VIEW vw_m7_exception_register AS
    SELECT
        q.source_type, q.reading_id, q.asset_id, q.asset_code, q.asset_name, q.plaza_id,
        q.asset_partition_key, q.operational_date, q.reading_datetime,
        q.source_data_quality_status, q.analytics_quality_class,
        q.analytics_exception_reasons,
        e.created_on, e.created_by, e.entry_delay_hours,
        e.delayed_entry_24h_or_more, e.reading_datetime_night_indicator,
        e.created_on_night_indicator
    FROM vw_m7_record_quality AS q
    LEFT JOIN vw_m7_entry_audit AS e
        ON e.source_type = q.source_type AND e.reading_id = q.reading_id
    WHERE q.analytics_quality_class = 'EXCEPTION';
    """)

    cur.execute("""
    CREATE VIEW vw_m7_night_entry_detail AS
    SELECT *
    FROM vw_m7_entry_audit
    WHERE reading_datetime_night_indicator = 1
       OR created_on_night_indicator = 1;
    """)

    cur.execute("""
    CREATE VIEW vw_m7_module_daily_quality_summary AS
    SELECT
        source_type, plaza_id, operational_date,
        SUBSTR(operational_date, 1, 7) AS operational_month,
        CAST(SUBSTR(operational_date, 1, 4) AS INTEGER) AS operational_year,
        COUNT(*) AS total_records,
        SUM(valid_records) AS valid_records,
        SUM(exception_records) AS exception_records,
        SUM(reconciliation_difference) AS reconciliation_difference,
        100.0 * SUM(valid_records) / NULLIF(COUNT(*), 0) AS observed_record_availability_pct,
        COUNT(DISTINCT asset_partition_key) AS assets_reporting
    FROM vw_m7_record_quality
    GROUP BY source_type, plaza_id, operational_date;
    """)

    cur.execute("""
    CREATE VIEW vw_m7_module_monthly_quality_summary AS
    SELECT
        source_type, plaza_id, operational_month,
        CAST(SUBSTR(operational_month, 1, 4) AS INTEGER) AS operational_year,
        SUM(total_records) AS total_records,
        SUM(valid_records) AS valid_records,
        SUM(exception_records) AS exception_records,
        SUM(reconciliation_difference) AS reconciliation_difference,
        100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
        MAX(assets_reporting) AS peak_assets_reporting
    FROM vw_m7_module_daily_quality_summary
    GROUP BY source_type, plaza_id, operational_month;
    """)

    cur.execute("""
    CREATE VIEW vw_m7_module_yearly_quality_summary AS
    SELECT
        source_type, plaza_id, operational_year,
        SUM(total_records) AS total_records,
        SUM(valid_records) AS valid_records,
        SUM(exception_records) AS exception_records,
        SUM(reconciliation_difference) AS reconciliation_difference,
        100.0 * SUM(valid_records) / NULLIF(SUM(total_records), 0) AS observed_record_availability_pct,
        MAX(peak_assets_reporting) AS peak_assets_reporting
    FROM vw_m7_module_monthly_quality_summary
    GROUP BY source_type, plaza_id, operational_year;
    """)

    cur.execute("""
    CREATE VIEW vw_m7_plaza_summary AS
    SELECT
        source_type, plaza_id,
        COUNT(*) AS total_records,
        SUM(valid_records) AS valid_records,
        SUM(exception_records) AS exception_records,
        SUM(reconciliation_difference) AS reconciliation_difference,
        100.0 * SUM(valid_records) / NULLIF(COUNT(*), 0) AS observed_record_availability_pct,
        100.0 * SUM(exception_records) / NULLIF(COUNT(*), 0) AS exception_percentage,
        COUNT(DISTINCT asset_partition_key) AS assets_reporting,
        MIN(operational_date) AS earliest_reading_date,
        MAX(operational_date) AS latest_reading_date
    FROM vw_m7_record_quality
    GROUP BY source_type, plaza_id;
    """)

    cur.execute("""
    CREATE VIEW vw_m7_technician_summary AS
    SELECT
        e.source_type,
        e.plaza_id,
        COALESCE(NULLIF(TRIM(e.created_by), ''), 'Unassigned') AS technician_name,
        COUNT(*) AS total_records,
        COUNT(*) FILTER (WHERE e.analytics_quality_class = 'VALID') AS valid_records,
        COUNT(*) FILTER (WHERE e.analytics_quality_class = 'EXCEPTION') AS exception_records,
        COUNT(*) FILTER (WHERE e.delayed_entry_24h_or_more = 1) AS delayed_entry_count,
        COUNT(*) FILTER (WHERE e.entry_delay_hours IS NOT NULL AND e.entry_delay_hours >= 0) AS entry_delay_eligible_count,
        100.0 * COUNT(*) FILTER (WHERE e.delayed_entry_24h_or_more = 1) / NULLIF(COUNT(*) FILTER (WHERE e.entry_delay_hours IS NOT NULL AND e.entry_delay_hours >= 0), 0) AS delayed_entry_percentage,
        COUNT(*) FILTER (WHERE e.reading_datetime_night_indicator = 1) AS night_reading_count,
        COUNT(*) FILTER (WHERE e.created_on_night_indicator = 1) AS night_entry_count,
        AVG(e.entry_delay_hours) FILTER (WHERE e.entry_delay_hours >= 0) AS average_entry_delay_hours,
        MAX(e.entry_delay_hours) FILTER (WHERE e.entry_delay_hours >= 0) AS maximum_entry_delay_hours
    FROM vw_m7_entry_audit AS e
    GROUP BY e.source_type, e.plaza_id, COALESCE(NULLIF(TRIM(e.created_by), ''), 'Unassigned');
    """)

    cur.execute("""
    CREATE VIEW vw_m7_asset_latest_reading AS
    WITH all_readings AS (
        SELECT
            'DG' AS source_type, d.reading_id, d.asset_id, d.asset_code, d.asset_name, d.plaza_id,
            d.asset_partition_key, d.reading_datetime, d.operational_date,
            d.cumulative_kwh, d.source_interval_kwh AS interval_kwh,
            d.pf AS power_factor, NULL AS output_voltage, NULL AS battery_vdc,
            rt.cumulative_runtime_hh_mm AS cumulative_running_hours_hh_mm,
            d.source_data_quality_status, d.created_by, d.created_on
        FROM vw_dg71_interval_classification AS d
        LEFT JOIN vw_dg71_runtime_interval AS rt USING (reading_id)
        UNION ALL
        SELECT
            'EB', e.reading_id, e.asset_id, e.asset_code, e.asset_name, e.plaza_id,
            e.asset_partition_key, e.reading_datetime, e.operational_date,
            e.cumulative_kwh, e.interval_kwh, e.pf,
            NULL, NULL, NULL, e.source_data_quality_status, e.created_by, e.created_on
        FROM vw_eb71_interval_detail AS e
        UNION ALL
        SELECT
            'SOLAR', s.reading_id, s.asset_id, s.asset_code, s.asset_name, s.plaza_id,
            s.asset_partition_key, s.reading_datetime, s.operational_date,
            s.cumulative_kwh, s.interval_kwh, NULL,
            NULL, NULL, NULL, s.source_data_quality_status, s.created_by, s.created_on
        FROM vw_sol71_reading_detail AS s
        UNION ALL
        SELECT
            'TRANSFORMER', t.reading_id, t.asset_id, t.asset_code, t.asset_name, t.plaza_id,
            t.asset_partition_key, t.reading_datetime, t.operational_date,
            t.cumulative_kwh_value, t.interval_kwh_value, t.pf,
            NULL, NULL, NULL, t.source_data_quality_status, t.created_by, t.created_on
        FROM vw_trf71_reading_detail AS t
        UNION ALL
        SELECT
            'UPS', u.reading_id, u.asset_id, u.asset_code, u.asset_name, u.plaza_id,
            u.asset_partition_key, u.reading_datetime, u.operational_date,
            NULL, NULL, NULL,
            u.output_voltage, u.battery_vdc, NULL,
            u.source_data_quality_status, u.created_by, u.created_on
        FROM vw_ups71_reading_detail AS u
    ),
    ranked AS (
        SELECT
            r.*,
            ROW_NUMBER() OVER (
                PARTITION BY r.source_type, r.asset_partition_key
                ORDER BY r.reading_datetime DESC, r.reading_id DESC
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
        CASE WHEN r.reading_id IS NOT NULL THEN 1 ELSE 0 END AS has_reading
    FROM energy_master_asset AS a
    LEFT JOIN ranked AS r
        ON (r.asset_id = a.asset_id OR r.asset_code = a.asset_id OR r.asset_code = a.asset_code)
       AND UPPER(r.source_type) = UPPER(a.source_type)
       AND r.latest_rank = 1
    WHERE UPPER(a.source_type) IN ('DG', 'EB', 'SOLAR', 'TRANSFORMER', 'UPS');
    """)

    cur.execute("""
    CREATE VIEW vw_m7_submodule_summary AS
    SELECT
        source_type,
        COUNT(*) AS total_records,
        SUM(valid_records) AS valid_records,
        SUM(exception_records) AS exception_records,
        SUM(reconciliation_difference) AS reconciliation_difference,
        100.0 * SUM(valid_records) / NULLIF(COUNT(*), 0) AS observed_record_availability_pct,
        100.0 * SUM(exception_records) / NULLIF(COUNT(*), 0) AS exception_percentage,
        COUNT(DISTINCT plaza_id) AS plazas_reporting,
        COUNT(DISTINCT asset_partition_key) AS assets_reporting,
        MIN(operational_date) AS earliest_reading_date,
        MAX(operational_date) AS latest_reading_date
    FROM vw_m7_record_quality
    GROUP BY source_type;
    """)

    # Optional correction audit view
    cur.execute("""
    CREATE VIEW vw_m7_correction_audit AS
    SELECT
        'DG' AS source_type,
        c.plaza_id,
        c.reading_id,
        c.asset_code,
        c.field_name,
        c.old_value,
        c.new_value,
        c.reason AS correction_reason,
        c.actor AS corrected_by,
        c.created_at AS audit_timestamp
    FROM energy_reading_corrections AS c;
    """)

    conn.commit()
    print("ALL MODULE 7 VIEWS DEPLOYED SUCCESSFULLY TO SQLITE!")
    conn.close()

if __name__ == "__main__":
    deploy_all_views()
