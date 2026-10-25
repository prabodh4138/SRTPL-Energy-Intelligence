# SRTPL Energy — Phase 5.3 DG JUNO Raw Import Foundation

## Scope
**DG only.** This is the first controlled multi-module raw JUNO ingestion phase after the EB pipeline validation.

### Operational path
`JUNO DG CSV → application upload → original-file preservation → import rows → energy_raw.juno_dg → normalization/validation → energy_readings.dg → DG KPI results + trace`

## Real JUNO test file
`test_data/DGDailyLogReport_25thSep2026_443_DG Log.csv`

Verified source facts:
- Generator: `SR-E-AP-DGX-000004`
- Parsed DG records: **334**
- Local normalization: **329 VALID / 5 EXCEPTION**
- Exception rules observed: `VAL-DG-001`, `VAL-DG-002`, `VAL-DG-004`
- Validated generation from normalized intervals: **9609.2 kWh**
- Validated runtime from normalized intervals: **1208.41 hour**
- Average valid PF: **0.980442**

## DG KPIs persisted by the live script
- `DG-GEN-D` — validated DG generation
- `DG-RUN-D` — validated DG runtime
- `DG-KWH-HR` — validated generation / validated runtime
- `DG-PF` — average validated PF

Fuel consumption/cost KPIs are **not invented** in Phase 5.3 because the JUNO sample provides diesel level/top-up but no independent fuel-consumed reconciliation or configured fuel price. Those are later controlled work.

## Data-quality rules
- Original JUNO CSV remains untouched.
- NULL is preserved as NULL.
- Cumulative kWh/runtime decreases become exceptions; negative generation/runtime is never silently created.
- Invalid readings remain in raw/normalized layers with traceable exception records.
- KPI calculations use only normalized rows marked `VALID`.
- Production credentials are excluded from the ZIP.

## Local verification
Run:

```powershell
& "<working-python>" ".\\scripts\\verify_dg_phase5_3.py"
```

Expected: `PHASE 5.3 DG LOCAL VERIFICATION: PASS`.

## Live Supabase flow
1. Copy the working `.env` into the project root.
2. Start the application and use **DG JUNO Import** to upload the untouched DG CSV, or use the existing JUNO import pipeline to create a DG batch.
3. Run:

```powershell
& "<working-python>" ".\\scripts\\calculate_dg_phase5_3.py" "<DG_BATCH_ID>"
```

The live script normalizes the batch and persists the four DG KPI results with source-reading traceability.
