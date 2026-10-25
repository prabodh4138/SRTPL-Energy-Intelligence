# Phase 5.3.1 — DG Application Upload Gate

## Objective
Connect the actual browser application to the DG JUNO pipeline so the user can:

`JUNO DG CSV → Application Upload → Original File Preservation → Raw Import → Normalization/Validation → DG KPI → Traceability`

## Application changes
- `streamlit_app.py` is now the single browser-facing entry point and loads `active_app`.
- `DG JUNO Import` is now wired into the main application navigation.
- `active_app/pages/dg_juno_import.py` now performs the complete controlled flow when Supabase credentials are configured.
- The application shows detected report type, parsed row count, asset code, file size, parser metadata, import result, validation result, KPI results and source-reading trace.
- Import success is never shown if the Supabase pipeline fails.
- Original uploaded CSV bytes are passed to the storage/import pipeline without editing the source headings or rows.

## DG KPI output
After a successful Supabase import and normalization, the page calculates:
- `DG-GEN-D` — validated DG generation (kWh)
- `DG-RUN-D` — validated DG runtime (hour)
- `DG-KWH-HR` — validated generation / validated runtime (kWh/hour)
- `DG-PF` — average validated PF

Only readings marked `VALID` are used by the KPI engine. Exception readings remain traceable and are excluded from KPI aggregation.

## Local test
From the project root in VS Code PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts\verify_dg_app_wiring.py
.\.venv\Scripts\python.exe scripts\verify_dg_phase5_3.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Then open **DG JUNO Import**, upload the untouched real DG CSV, and click:

**Import DG → Supabase → Validate → Calculate KPI**

## Required environment
The project root `.env` must contain the existing working Supabase connection values, for example:

```text
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
ADMIN_EMAIL=...
ADMIN_TOKEN=...
```

Do not put `.env` into the ZIP or source control.

## Gate before Phase 5.4
Do not move to Solar until the DG application upload has been successfully tested against the real Supabase database and the resulting batch, raw rows, normalized rows, exceptions and KPI results have been verified.
