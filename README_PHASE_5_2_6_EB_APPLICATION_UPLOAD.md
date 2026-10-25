# Phase 5.2.6 — EB Application Upload Gate

## Current module
**EB is the only active module for testing in this milestone.** Do not proceed to DG, Solar, Transformer or UPS until EB passes all gates.

## Required workflow
JUNO EB CSV → Streamlit upload → exact original file preserved → `energy_import` → `energy_raw.juno_eb` → normalization → validation/exceptions → `energy_readings.eb` → EB KPI → traceability.

## Controlled local source
`source_data/raw/EB/SRTPL_Test_JUNO_EB.csv`

Expected controlled result:
- Parsed rows: 7
- Valid rows: 5
- Exception rows: 2
- EB consumption: 125.0 kWh
- EB KVAH: 125.0 kVAh
- EB KVARH: 47.0 kVARh
- Average PF: 0.95
- Decrease rules: `VAL-EB-001`, `VAL-EB-002`, `VAL-EB-004`

## VS Code test
From the project root:

```powershell
.\.venv\Scripts\python.exe scripts\verify_eb_phase5_2_6.py
.\.venv\Scripts\python.exe scripts\verify_eb_app_wiring.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open **EB JUNO Import**, upload the controlled CSV, and click **Import EB → Supabase → Validate → Calculate KPI**.

## Supabase gate
Use the existing `.env` credentials locally; `.env` is intentionally excluded from this ZIP.

The browser test must confirm:
1. original CSV is stored unchanged in private `energy-original-files`;
2. one import batch/file is created;
3. 7 import rows are created;
4. 7 raw EB rows are created;
5. 7 normalized EB rows are created;
6. 5 rows are VALID and 2 are EXCEPTION;
7. the expected exception codes are present;
8. KPI values are calculated only from valid rows;
9. traceability links KPI → normalized reading → import row → original CSV.

## Gate rule
**No DG work starts until the EB browser + real Supabase test passes.**

## Future roadmap
The final system will include plaza-wise exception scoring, data-entry neglect detection, Excel/PDF reporting, intelligent analytics, and scheduled daily WhatsApp exception summaries. Those are not activated in this milestone.
