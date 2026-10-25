# Phase 5.1 Integration Runbook

## A. Local smoke test
1. Create a Python 3.13 virtual environment.
2. Install `requirements.txt`.
3. Copy `.env.example` to `.env` and configure staging credentials.
4. Start with `streamlit run streamlit_app.py`.
5. Verify System Health and Integration Status before importing data.

## B. Staging database
- Use a dedicated Supabase/PostgreSQL staging project.
- Apply `sql/master_install/INSTALL_ORDER.sql` only after reviewing dependencies.
- Verify schemas, tables, views, functions, triggers and RLS policies.
- Confirm the browser never receives a service-role key.

## C. Storage
- Create the private `energy-original-files` bucket.
- Verify only authorized backend/service paths can write/read originals.
- Verify the original uploaded JUNO bytes and SHA-256 are preserved.

## D. JUNO end-to-end test
Run one representative CSV for each:
- SOLAR
- DG
- EB
- TRANSFORMER
- UPS

For every file verify:
1. Detection and metadata extraction.
2. Exact original CSV preservation.
3. File hash recorded.
4. Import batch/file/row records created.
5. Raw source record created.
6. Validation result generated.
7. Normalized reading generated only when eligible.
8. Cumulative deltas never become negative.
9. Blank cells remain NULL.
10. KPI results are traceable to source.
11. Exceptions are retained and auditable.
12. Re-uploading the same file is idempotent.

## E. UAT gate
Do not release until:
- all five source types import successfully,
- expected row counts reconcile,
- known anomalies produce expected exception codes,
- no source rows disappear,
- no NULL-to-zero conversion occurs,
- dashboards show no-data states correctly,
- report exports reconcile with dashboard data,
- audit logs capture controlled changes,
- RLS is tested with every production role.
