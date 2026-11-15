# Module 7 Analytics — SQL View Package

## Package contents

This package proposes the complete Module 7 view layer for DG, EB, Solar, Transformer, and UPS. It uses new `public` view names only. It has not been run against the live database and does not change any source data or existing view definitions.

1. `DG_Module_7_1_Analytics_Proposed.sql`
2. `EB_Module_Analytics_Proposed.sql`
3. `Solar_Module_Analytics_Proposed.sql`
4. `Transformer_Module_Analytics_Proposed.sql`
5. `UPS_Module_7_Analytics_Proposed.sql`
6. `Module_7_Unified_Views_Proposed.sql`
7. `Module_7_ReadOnly_Preflight.sql`
8. `Module_7_Correction_Audit_Optional.sql`

Deploy the five submodule files first, then the unified views. Run the correction-audit block only if its audit source and columns are present. Run the preflight before deployment and its reconciliation queries after deployment.

Before deployment, inspect the preflight's `existing_relation_kind` results. A prior Solar run stopped on the asset-latest view, so some `vw_sol71_*` names may already exist. `CREATE VIEW` intentionally does not replace an existing relation: skip definitions whose names are already occupied, then create only missing views in dependency order. If a name is occupied by a non-view or an older incompatible definition, stop and review it before deployment. The Solar recovery file is limited to the asset-latest view and also checks for its dependencies and name collision.

## Inspected project state

- `sql/create_equipment_reading_and_kpi_views.sql` is the legacy per-submodule installer. It creates schemas/tables and drops existing views with `CASCADE`; it was inspected but not run or modified.
- `sql/energy_analytics_forensic_views.sql` creates `energy_analytics`, drops/replaces forensic views in both `energy_analytics` and `public`, and contains an older 20:00–08:00 night window. It was inspected but not run or modified.
- The Render React Module 7 page now calls the FastAPI analytics endpoint, which reads the versioned Module 7 SQL views and returns date/plaza-filtered summaries, trends, latest readings, exceptions, night indicators, and optional correction history. Render continues to start FastAPI and build the React static site; it does not start the Streamlit entry point. The SQL views still need to be deployed separately before the page can display live results.
- Source schema setup is inconsistent across current project SQL files. `supabase_master_setup.sql` defines the DG table without the operational status, diesel, phase voltage/current, kVA/kW, load, and RPM fields; `align_all_submodule_tables_with_excel_headers.sql` adds those fields and the consolidated fresh setup includes them. The read-only preflight lists every required source column. The full DG diesel/electrical views need those columns present in the target database; do not run any schema-alignment script as part of this view package.
- The package uses `public` and the existing `energy_readings` / `energy_master` schemas. It does not require `energy_dashboard`. Correction audit stays out of the core views because `energy_audit.audit_log` is absent in the earlier reported database; the optional script checks for it before defining an audit view.
- The existing Solar schema has `TIMESTAMPTZ` reading/creation times and the module package follows Phase 5.5's use of VALID `interval_kwh` for generation.
- UPS Phase 5.7 defines availability as VALID received readings divided by all received readings and computes output voltage/current/frequency, battery voltage/temperature, and rectifier voltage from VALID readings.

## Shared Module 7 rules

- Every received reading remains in Total Records. Each record is counted exactly once in VALID or EXCEPTION, and every submodule and unified rollup exposes reconciliation.
- A missing measurement does not remove the source record from Total Records. Module-specific exception rules are applied only where supported by the existing validator or approved requirements.
- Entry delay is `created_on - reading_datetime`; at least 24 hours is delayed. Negative timestamp differences are separately flagged and excluded from delay-rate denominators.
- Night indicators use 22:00 inclusive to 06:00 exclusive in Asia/Kolkata, for reading and creation timestamps independently. They do not change VALID/EXCEPTION classification.
- The unified plaza/technician views report counts and percentages; night records remain indicators.

## Open engineering decisions

- Solar expected reporting cadence is not defined, so Solar/UPS availability is labeled observed-record availability rather than schedule uptime.
- Solar's UI ceiling of capacity × 1.1 needs a confirmed capacity unit (the SQL master stores generic `capacity_kva`, while the UI labels kWp) before automatic exception classification.
- Solar's legacy 0.82 kg/kWh CO₂ factor is omitted pending approval of the factor and source.
- Solar's diurnal no-generation window is not defined; the SQL does not create night-generation exceptions.
- UPS thresholds are database-configurable. The SQL reports values and does not assign WARNING/CRITICAL status without confirmed threshold rows.
- Transformer imbalance zero-mean behavior and warning thresholds are documented in its submodule notes; Transformer loss/efficiency remains excluded pending engineering inputs.
- DG uses the approved HH.MM runtime parsing, fuel reconciliation, and electrical imbalance rules. Threshold severity remains unassigned where no approved threshold value is available.
- The correction audit remains optional because the previously reported target did not have `energy_audit.audit_log`. Its entity ID must map to a reading UUID for the view to return that correction.

## Validation and safety

- Lightweight static delimiter/safety checks are run on the proposed SQL package. A live PostgreSQL parser/catalog check is not available without a database connection.
- `Module_7_ReadOnly_Preflight.sql` contains only SELECT statements. It checks required source columns, name collisions, timestamp types, runtime conversion, night boundaries, and post-deployment reconciliation.
- The five submodule SQL files and unified file contain only additive `CREATE VIEW` statements. They do not create a schema/table, replace or drop existing views, modify source data, or reference the missing audit table in core analytics.
- The separate correction-audit script checks its dependencies and target view before creating anything; it skips when required objects/columns are absent or the target name is already in use.
