# SRTPL Energy Phase 3 — JUNO CSV Importer

Purpose:
- Accept original JUNO CSV files without modifying them.
- Detect report type automatically.
- Extract report metadata and multi-row headers.
- Preserve NULL/blank values as NULL.
- Calculate SHA-256 before import.
- Prepare normalized records for Supabase.
- Keep parser versioned.

Current report types:
- SOLAR
- DG
- EB
- TRANSFORMER
- UPS

TPWODL is intentionally not implemented yet.

## Recommended next integration

Streamlit:
Upload -> ImportService.import_file()

Supabase:
1. Store original CSV in private Storage bucket `energy-original-files`.
2. Insert `energy_import.import_batch`.
3. Insert `energy_import.import_file`.
4. Insert `energy_import.import_row`.
5. Insert raw JUNO record.
6. Run validation.
7. Insert normalized reading.
8. Calculate KPIs.

The parser never edits the source CSV.
