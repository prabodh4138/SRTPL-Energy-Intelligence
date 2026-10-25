# Phase 4.1 Integration

1. Copy the dashboard directory into the master project.
2. Copy `pages/executive_dashboard.py`.
3. Add the Executive Dashboard import/render branch to app.py.
4. Apply `sql/phase4_1_dashboard_views.sql` after Phase 2/3 analytics migrations.
5. Replace `DashboardService` query methods with Supabase repository calls.
6. Map actual UUID-based plaza and asset master records.
7. Connect KPI codes to Phase 3.3 `energy_analytics.kpi_result`.
8. Connect exceptions to Phase 3.2 validation tables.
9. Test against real JUNO-imported data.
10. Perform mobile and office-browser UAT.

Do not hard-code calculated KPI values into this dashboard.
