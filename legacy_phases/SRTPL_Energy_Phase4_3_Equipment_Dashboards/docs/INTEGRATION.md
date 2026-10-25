# Phase 4.3 Integration

1. Add `pages/equipment_dashboard.py` to the Phase 3.4 app.
2. Add Equipment Dashboard to navigation.
3. Replace `EquipmentDashboardService` placeholders with Supabase repository calls.
4. Read assets from `energy_master.asset`.
5. Read asset parameters from `energy_master.asset_parameter`.
6. Read KPI results from `energy_analytics.kpi_result`.
7. Read normalized readings from the Phase 3.2 normalized tables.
8. Read exceptions from validation tables.
9. Use source_reading_ids for traceability.
10. Link raw/import/original-file IDs to the source chain.
11. Test every equipment type using actual JUNO data.

No engineering KPI formula should be duplicated in the UI.
