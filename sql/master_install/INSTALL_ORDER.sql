-- SRTPL Energy Phase 5.1 master SQL installation manifest
-- Review each script in a staging Supabase project before production execution.
-- Phase 5.1 intentionally does not auto-run destructive SQL.

-- >>> sql/phase_archive/SRTPL_Energy_Phase2_Core_Schema.sql
\i sql/phase_archive/SRTPL_Energy_Phase2_Core_Schema.sql

-- >>> sql/phase_archive/SRTPL_Energy_Phase2_Supabase.sql
\i sql/phase_archive/SRTPL_Energy_Phase2_Supabase.sql

-- >>> sql/phase_archive/3_3_phase3_3_kpi_analytics.sql
\i sql/phase_archive/3_3_phase3_3_kpi_analytics.sql

-- >>> sql/phase_archive/4_1_phase4_1_dashboard_views.sql
\i sql/phase_archive/4_1_phase4_1_dashboard_views.sql

-- >>> sql/phase_archive/4_2_phase4_2_plaza_views.sql
\i sql/phase_archive/4_2_phase4_2_plaza_views.sql

-- >>> sql/phase_archive/4_3_phase4_3_equipment_views.sql
\i sql/phase_archive/4_3_phase4_3_equipment_views.sql

-- >>> sql/phase_archive/4_4_phase4_4_import_views.sql
\i sql/phase_archive/4_4_phase4_4_import_views.sql

-- >>> sql/phase_archive/4_5_phase4_5_exception_actions.sql
\i sql/phase_archive/4_5_phase4_5_exception_actions.sql

-- >>> sql/phase_archive/4_5_phase4_5_exception_center.sql
\i sql/phase_archive/4_5_phase4_5_exception_center.sql

-- >>> sql/phase_archive/4_6_phase4_6_dq_views.sql
\i sql/phase_archive/4_6_phase4_6_dq_views.sql

-- >>> sql/phase_archive/4_6_phase4_6_source_coverage.sql
\i sql/phase_archive/4_6_phase4_6_source_coverage.sql

-- >>> sql/phase_archive/4_7_phase4_7_report_center.sql
\i sql/phase_archive/4_7_phase4_7_report_center.sql

-- >>> sql/phase_archive/4_7_phase4_7_report_views.sql
\i sql/phase_archive/4_7_phase4_7_report_views.sql

-- >>> sql/phase_archive/4_8_phase4_8_admin_schema.sql
\i sql/phase_archive/4_8_phase4_8_admin_schema.sql

-- >>> sql/phase_archive/4_8_phase4_8_audit_schema.sql
\i sql/phase_archive/4_8_phase4_8_audit_schema.sql

-- >>> sql/phase_archive/4_8_phase4_8_rls_baseline.sql
\i sql/phase_archive/4_8_phase4_8_rls_baseline.sql

-- >>> sql/phase_archive/4_9_phase4_9_master_schema.sql
\i sql/phase_archive/4_9_phase4_9_master_schema.sql

-- >>> sql/phase_archive/4_9_phase4_9_master_views.sql
\i sql/phase_archive/4_9_phase4_9_master_views.sql

-- >>> sql/phase_archive/4_9_phase4_9_seed_catalog.sql
\i sql/phase_archive/4_9_phase4_9_seed_catalog.sql

-- >>> sql/phase_archive/5_0_phase5_0_integration_views.sql
\i sql/phase_archive/5_0_phase5_0_integration_views.sql

-- >>> sql/phase_archive/5_0_phase5_0_security_checks.sql
\i sql/phase_archive/5_0_phase5_0_security_checks.sql

-- >>> active_app/sql/phase5_4_eb_kpi_seed.sql
\i active_app/sql/phase5_4_eb_kpi_seed.sql

-- >>> active_app/sql/phase5_5_solar_kpi_seed.sql
\i active_app/sql/phase5_5_solar_kpi_seed.sql

-- >>> active_app/sql/phase5_6_transformer_kpi_seed.sql
\i active_app/sql/phase5_6_transformer_kpi_seed.sql

-- >>> active_app/sql/phase5_7_ups_kpi_seed.sql
\i active_app/sql/phase5_7_ups_kpi_seed.sql
