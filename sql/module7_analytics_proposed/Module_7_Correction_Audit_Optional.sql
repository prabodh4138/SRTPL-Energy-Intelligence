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
