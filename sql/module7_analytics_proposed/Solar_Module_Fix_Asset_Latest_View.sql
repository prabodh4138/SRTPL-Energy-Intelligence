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
