# SRTPL Energy Intelligence — Phase 5.1 Master Project Assembly

## Purpose
This package consolidates Phases 2 through 5.0 into one master project for controlled
integration testing against real JUNO CSV exports.

### Browser-first operating model
JUNO → download CSV → browser upload → original CSV preserved → duplicate check →
validation → normalized readings → KPI calculation → dashboard / reports / audit.

The office laptop does **not** need Python, an EXE, or Excel upload. The final deployed
application is intended to be accessed through a browser.

## What Phase 5.1 does
- One master project root and one browser-facing Streamlit entry point.
- Later phase modules win source-file collisions; every original phase is preserved under
  `legacy_phases/`.
- SQL installation order is centralized under `sql/master_install/`.
- Previous phase SQL is archived under `sql/phase_archive/`.
- Production environment template is centralized.
- Master integration/test documents are added.
- Real JUNO CSVs are expected to be used as integration-test inputs.
- No fake production KPI values are inserted.

## Important status
**This is an integration assembly baseline, not a declaration of production readiness.**
Actual Supabase credentials, RLS verification, database migration execution, Storage
permissions, master-data mapping, and live JUNO end-to-end tests must pass before release.

## Required production traceability
Every KPI should remain traceable:
KPI → normalized reading → raw JUNO row → import row → import file → original CSV.

## NULL rule
Blank JUNO fields remain NULL. NULL must never be silently converted to zero.

## Duplicate rule
File-level SHA-256 and record-level duplicate checks are expected. Re-uploading the same
file must be idempotent.

## Invalid data
Invalid source rows are retained and routed to validation/exception workflows; they are
not silently deleted.

## Transformer caution
Transformer loss/efficiency remains disabled until measurement boundaries, CT/PT ratio,
rating, and meter semantics are formally confirmed.

## EB caution
Maximum-demand unit/interpretation remains source-only until the TPWODL/meter definition
is confirmed.

## Next gate after Phase 5.1
1. Configure staging Supabase.
2. Apply SQL in controlled order.
3. Load approved master data (no fake operational IDs).
4. Configure Storage bucket/RLS.
5. Run the real JUNO Solar/DG/EB/Transformer/UPS CSVs.
6. Compare import counts, validation results and KPIs with source records.
7. Fix integration defects.
8. Only then perform production deployment/UAT.
